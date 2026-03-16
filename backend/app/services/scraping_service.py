"""Direct scraping service — calls the French government API and stores results."""
import re
from datetime import datetime, timezone

import httpx
from sqlalchemy.orm import Session

from app.models.agence import Agence
from app.models.agence_snapshot import AgenceSnapshot


SEARCH_TERMS = [
    "gestion locative",
    "syndic copropriete",
    "gestion immobiliere",
    "administrateur biens",
    "gerance immobiliere",
]

API_BASE = "https://recherche-entreprises.api.gouv.fr/search"


GROUPS = {
    "foncia": "Foncia", "nexity": "Nexity", "citya": "Citya",
    "oralia": "Oralia", "immo de france": "Immo de France",
    "sergic": "Sergic", "lamy": "Lamy", "laforêt": "Laforêt",
    "century 21": "Century 21", "guy hoquet": "Guy Hoquet",
    "square habitat": "Square Habitat", "gestrim": "Gestrim",
    "icade": "Icade",
}

EMPLOYEE_RANGES = {
    "00": 0, "01": 1, "02": 4, "03": 8, "11": 15,
    "12": 30, "21": 75, "22": 150, "31": 350, "32": 750,
}

REGIONS = {
    "75": "Île-de-France", "77": "Île-de-France", "78": "Île-de-France",
    "91": "Île-de-France", "92": "Île-de-France", "93": "Île-de-France",
    "94": "Île-de-France", "95": "Île-de-France",
    "13": "PACA", "83": "PACA", "06": "PACA", "84": "PACA",
    "69": "Auvergne-Rhône-Alpes", "38": "Auvergne-Rhône-Alpes",
    "42": "Auvergne-Rhône-Alpes", "63": "Auvergne-Rhône-Alpes",
    "31": "Occitanie", "34": "Occitanie", "30": "Occitanie", "66": "Occitanie",
    "33": "Nouvelle-Aquitaine", "87": "Nouvelle-Aquitaine",
    "44": "Pays de la Loire", "49": "Pays de la Loire",
    "35": "Bretagne", "29": "Bretagne", "56": "Bretagne",
    "59": "Hauts-de-France", "62": "Hauts-de-France", "80": "Hauts-de-France",
    "67": "Grand Est", "57": "Grand Est", "51": "Grand Est",
    "25": "Bourgogne-Franche-Comté", "21": "Bourgogne-Franche-Comté",
    "76": "Normandie", "14": "Normandie",
    "37": "Centre-Val de Loire", "45": "Centre-Val de Loire",
}


def run_scraping(db: Session, job_id: str):
    """Scrape agencies from the French government API and store in DB."""
    from app.models.scraping_job import ScrapingJob, JobStatut
    import uuid

    job = db.get(ScrapingJob, uuid.UUID(job_id))
    job.statut = JobStatut.running
    job.started_at = datetime.now(timezone.utc)
    db.commit()

    total_new = 0
    total_updated = 0
    errors = []

    try:
        with httpx.Client(timeout=30.0) as client:
            for term in SEARCH_TERMS:
                for page in range(1, 6):  # up to 5 pages per term = 125 results
                    try:
                        resp = client.get(API_BASE, params={
                            "q": term,
                            "page": page,
                            "per_page": 25,
                            "activite_principale": "68.32A,68.31Z",
                            "etat_administratif": "A",
                        })
                        resp.raise_for_status()
                        data = resp.json()
                    except Exception as e:
                        errors.append(f"{term} page {page}: {str(e)[:100]}")
                        break

                    results = data.get("results", [])
                    if not results:
                        break  # No more results for this term

                    for entry in results:
                        new, updated = _upsert_agence(db, entry)
                        total_new += new
                        total_updated += updated

                    db.commit()

        job.statut = JobStatut.done
        job.nb_agences_scrappees = total_new + total_updated
        job.finished_at = datetime.now(timezone.utc)
        if errors:
            job.erreurs = {"api_errors": errors}

    except Exception as e:
        job.statut = JobStatut.failed
        job.finished_at = datetime.now(timezone.utc)
        job.erreurs = {"error": str(e)}

    db.commit()
    return {"new": total_new, "updated": total_updated}


def _upsert_agence(db: Session, entry: dict) -> tuple[int, int]:
    """Insert or update an agency from API data. Returns (new_count, updated_count)."""
    nom = entry.get("nom_complet", "")
    if not nom or len(nom) < 3:
        return 0, 0

    siege = entry.get("siege", {})
    if not siege:
        return 0, 0

    adresse = siege.get("adresse", "")
    code_postal = siege.get("code_postal", "")
    ville = siege.get("libelle_commune", "")
    region = siege.get("libelle_region", "") or REGIONS.get(code_postal[:2], "") if code_postal else ""

    # Detect group
    nom_lower = nom.lower()
    groupe = ""
    for key, value in GROUPS.items():
        if key in nom_lower:
            groupe = value
            break

    # Estimate employees
    tranche = entry.get("tranche_effectif_salarie", "") or siege.get("tranche_effectif_salarie", "")
    nb_collab = EMPLOYEE_RANGES.get(tranche)

    # Check if already exists (by name + postal code)
    existing = db.query(Agence).filter(
        Agence.nom == nom.title(),
        Agence.code_postal == code_postal,
    ).first()

    if existing:
        existing.derniere_maj = datetime.now(timezone.utc)
        if nb_collab is not None:
            existing.nb_collaborateurs = nb_collab
        if groupe:
            existing.groupe = groupe
        # Create snapshot
        snapshot = AgenceSnapshot(
            agence_id=existing.id,
            nb_lots_geres=existing.nb_lots_geres,
            nb_collaborateurs=existing.nb_collaborateurs,
            a_service_travaux=existing.a_service_travaux,
            note_google=existing.note_google,
            note_trustpilot=existing.note_trustpilot,
        )
        db.add(snapshot)
        return 0, 1
    else:
        agence = Agence(
            nom=nom.title(),
            groupe=groupe,
            adresse=adresse,
            ville=ville.title() if ville else "",
            region=region,
            code_postal=code_postal,
            site_web="",
            nb_lots_geres=None,
            nb_collaborateurs=nb_collab,
            a_service_travaux=False,
            derniere_maj=datetime.now(timezone.utc),
        )
        db.add(agence)
        db.flush()
        # Create initial snapshot
        snapshot = AgenceSnapshot(
            agence_id=agence.id,
            nb_lots_geres=None,
            nb_collaborateurs=nb_collab,
            a_service_travaux=False,
        )
        db.add(snapshot)
        return 1, 0
