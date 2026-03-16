"""Scraping service — collects agencies from govt API, enriches with RNIC, computes insights."""
import csv
import io
import logging
import uuid
from collections import defaultdict
from datetime import datetime, timedelta, timezone

import httpx
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.agence import Agence
from app.models.agence_snapshot import AgenceSnapshot
from app.models.avis import Avis
from app.models.insight import Insight
from app.models.offre import OffreEmploi

logger = logging.getLogger(__name__)

SEARCH_TERMS = [
    "gestion locative",
    "syndic copropriete",
    "gestion immobiliere",
    "administrateur biens",
    "gerance immobiliere",
]

GOV_API = "https://recherche-entreprises.api.gouv.fr/search"

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
    """Full pipeline: collect → analyze → generate honest insights."""
    from app.models.scraping_job import ScrapingJob, JobStatut

    job = db.get(ScrapingJob, uuid.UUID(job_id))
    job.statut = JobStatut.running
    job.started_at = datetime.now(timezone.utc)
    db.commit()

    errors = []

    try:
        # Step 1: Collect agencies from government API
        total_new, total_updated = _step_collect(db, errors)

        # Step 2: Enrich with RNIC (if file is available and small enough)
        # Note: RNIC enrichment is done separately via POST /api/scraping/enrich-rnic
        # because the 458MB file takes too long to parse in the main scraping thread

        # Step 3: Generate honest insights
        _step_generate_insights(db)

        job.statut = JobStatut.done
        job.nb_agences_scrappees = total_new + total_updated
        job.finished_at = datetime.now(timezone.utc)
        if errors:
            job.erreurs = {"warnings": errors}

    except Exception as e:
        job.statut = JobStatut.failed
        job.finished_at = datetime.now(timezone.utc)
        job.erreurs = {"error": str(e)}

    db.commit()


# ─── Step 1: Collect from government API ──────────────────────────────────────

def _step_collect(db: Session, errors: list) -> tuple[int, int]:
    total_new = 0
    total_updated = 0

    with httpx.Client(timeout=30.0) as client:
        for term in SEARCH_TERMS:
            for page in range(1, 6):
                try:
                    resp = client.get(GOV_API, params={
                        "q": term, "page": page, "per_page": 25,
                        "activite_principale": "68.32A,68.31Z",
                        "etat_administratif": "A",
                    })
                    resp.raise_for_status()
                    data = resp.json()
                except Exception as e:
                    errors.append(f"{term} p{page}: {str(e)[:80]}")
                    break

                results = data.get("results", [])
                if not results:
                    break

                for entry in results:
                    new, updated = _upsert_agence(db, entry)
                    total_new += new
                    total_updated += updated

                db.commit()

    return total_new, total_updated


# ─── Step 2: Enrich with RNIC (Registre National des Copropriétés) ───────────

RNIC_CSV_URL = "https://static.data.gouv.fr/resources/registre-national-dimmatriculation-des-coproprietes/20260105-114009/rnc-data-gouv-with-qpv.csv"


def _step_enrich_rnic(db: Session, errors: list) -> int:
    """Parse local RNIC CSV file, match by SIREN, enrich agences with real lot counts.

    The RNIC file must be pre-downloaded to /app/data/rnic.csv (437 MB).
    Download command: curl -L -o backend/data/rnic.csv "https://static.data.gouv.fr/resources/registre-national-dimmatriculation-des-coproprietes/20260105-114009/rnc-data-gouv-with-qpv.csv"
    """
    import os

    agences = db.query(Agence).filter(Agence.siren.isnot(None), Agence.siren != "").all()
    if not agences:
        errors.append("RNIC: no agences with SIREN, skipping")
        return 0

    our_sirens = {a.siren: a for a in agences}

    rnic_path = "/app/data/rnic.csv"
    if not os.path.exists(rnic_path):
        errors.append("RNIC: fichier /app/data/rnic.csv non trouvé. Téléchargez-le d'abord.")
        return 0

    # Parse — only process rows matching our SIRENs (fast: skips 99%+ of rows)
    siren_data = defaultdict(lambda: {"nb_copros": 0, "total_lots": 0, "nb_arretes_peril": 0})

    try:
        with open(rnic_path, "r", encoding="utf-8", errors="replace") as f:
            # Read header to find column indices (fast: no DictReader overhead)
            header = f.readline().strip().split(",")
            col_map = {name.strip().strip('"').lower(): i for i, name in enumerate(header)}

            idx_siret = col_map.get("siret_du_representant_legal", -1)
            idx_lots = col_map.get("nombre_total_de_lots_a_usage_d_habitation_de_bureaux_ou_de_comm", -1)
            idx_arretes = col_map.get("nombre_d_arretes_de_peril", -1)

            if idx_siret < 0:
                errors.append(f"RNIC: SIRET column not found. Available: {list(col_map.keys())[:10]}")
                return 0

            max_idx = max(idx_siret, idx_lots, idx_arretes)

            for line in f:
                # Fast: split only what we need, skip most lines early
                parts = line.split(",")
                if len(parts) <= max_idx:
                    continue

                siret_val = parts[idx_siret].strip().strip('"')
                siren = siret_val[:9]
                if len(siren) < 9 or siren not in our_sirens:
                    continue

                lots = _safe_int(parts[idx_lots]) if idx_lots >= 0 else 0
                arretes = _safe_int(parts[idx_arretes]) if idx_arretes >= 0 else 0

                d = siren_data[siren]
                d["nb_copros"] += 1
                d["total_lots"] += lots
                d["nb_arretes_peril"] += arretes

    except Exception as e:
        errors.append(f"RNIC parse failed: {str(e)[:100]}")
        return 0

    # Apply to our agences
    matched = 0
    for siren, data in siren_data.items():
        agence = our_sirens.get(siren)
        if agence and data["total_lots"] > 0:
            agence.nb_lots_geres = data["total_lots"]
            agence.nb_coproprietes = data["nb_copros"]
            agence.nb_arretes_peril = data["nb_arretes_peril"]
            matched += 1

    db.commit()
    return matched


def _safe_int(val) -> int:
    """Safely convert a value to int, returning 0 on failure."""
    if val is None:
        return 0
    try:
        return int(str(val).strip().replace(" ", ""))
    except (ValueError, TypeError):
        return 0


# ─── Step 3: Generate HONEST insights ────────────────────────────────────────

def _step_generate_insights(db: Session):
    """Generate insights based ONLY on verified data. Flag missing info."""
    agences = db.query(Agence).all()

    for agence in agences:
        # Collect what we KNOW
        known = {}
        missing = []

        # From government API (verified)
        if agence.nb_collaborateurs is not None:
            known["nb_collaborateurs"] = agence.nb_collaborateurs
        else:
            missing.append("Nombre de collaborateurs (non disponible via l'API INSEE)")

        if agence.nb_lots_geres is not None:
            known["nb_lots_geres"] = agence.nb_lots_geres
            known["source_lots"] = "RNIC (Registre National des Copropriétés)"
        else:
            missing.append("Nombre de lots gérés (non trouvé dans le RNIC — vérifier sur le site ou en rdv)")

        # Google reviews (not scraped yet)
        if agence.note_google is not None:
            known["note_google"] = agence.note_google
        else:
            missing.append("Note Google (à vérifier manuellement sur Google Maps)")

        # Trustpilot (not scraped yet)
        if agence.note_trustpilot is not None:
            known["note_trustpilot"] = agence.note_trustpilot
        else:
            missing.append("Note Trustpilot (à vérifier sur trustpilot.com)")

        # Service travaux detection
        nom_lower = agence.nom.lower()
        has_travaux_in_name = any(kw in nom_lower for kw in ["travaux", "rénovation", "maintenance"])
        if has_travaux_in_name:
            known["service_travaux_detecte"] = True
        else:
            missing.append("Présence d'un service travaux (à vérifier sur leur site web ou en rdv)")

        # Offres d'emploi
        nb_offres = db.query(func.count(OffreEmploi.id)).filter(
            OffreEmploi.agence_id == agence.id
        ).scalar() or 0
        if nb_offres > 0:
            known["offres_emploi"] = nb_offres
        else:
            missing.append("Offres d'emploi (à vérifier sur leur site carrières)")

        # Avis
        nb_avis = db.query(func.count(Avis.id)).filter(
            Avis.agence_id == agence.id
        ).scalar() or 0

        # ── Calculate score based ONLY on what we know ──
        score = 0
        signaux = {}
        details = []

        # Signal: Taille de l'agence (source: API INSEE — fiable)
        if agence.nb_collaborateurs is not None:
            if agence.nb_collaborateurs >= 5:
                score += 15
                signaux["taille_agence"] = 15
                details.append(f"✓ Agence de taille significative ({agence.nb_collaborateurs} salariés) — plus susceptible d'avoir besoin d'aide travaux")
            elif agence.nb_collaborateurs >= 1:
                score += 5
                signaux["taille_agence"] = 5
                details.append(f"✓ Petite structure ({agence.nb_collaborateurs} salarié(s)) — potentiellement débordée")

        # Signal: Pas de service travaux détecté dans le nom
        if not has_travaux_in_name:
            score += 10
            signaux["absence_service_travaux"] = 10
            details.append("✓ Pas de mention 'travaux/maintenance' dans le nom — probablement pas de service dédié (à confirmer)")
        else:
            signaux["absence_service_travaux"] = 0
            details.append("✗ Mention travaux/maintenance dans le nom — pourrait avoir un service dédié")

        # Signal: Groupe connu = structure plus complexe = plus de besoins
        if agence.groupe:
            score += 5
            signaux["appartenance_groupe"] = 5
            details.append(f"✓ Fait partie du groupe {agence.groupe} — structures de groupe ont souvent des besoins en sous-traitance travaux")

        # Signal: Activité vérifiée (code NAF 68.32A = administration d'immeubles)
        score += 10
        signaux["activite_verifiee"] = 10
        details.append("✓ Activité vérifiée : administration d'immeubles / agence immobilière (source: INSEE)")

        # Signal: Volume de lots gérés (source: RNIC — très fiable)
        if agence.nb_lots_geres is not None:
            if agence.nb_lots_geres >= 500:
                score += 25
                signaux["volume_lots_rnic"] = 25
                details.append(f"✓ Gère {agence.nb_lots_geres} lots (source: RNIC) — volume très important, fort besoin potentiel en gestion de travaux")
            elif agence.nb_lots_geres >= 100:
                score += 20
                signaux["volume_lots_rnic"] = 20
                details.append(f"✓ Gère {agence.nb_lots_geres} lots (source: RNIC) — volume significatif de travaux à gérer")
            elif agence.nb_lots_geres >= 30:
                score += 10
                signaux["volume_lots_rnic"] = 10
                details.append(f"✓ Gère {agence.nb_lots_geres} lots (source: RNIC) — volume modéré")
            else:
                signaux["volume_lots_rnic"] = 0
                details.append(f"○ Gère seulement {agence.nb_lots_geres} lots (source: RNIC) — petit portefeuille")

        # Signal: Ratio lots/collaborateurs (si les deux données sont dispo)
        if agence.nb_lots_geres and agence.nb_collaborateurs and agence.nb_collaborateurs > 0:
            ratio = agence.nb_lots_geres / agence.nb_collaborateurs
            if ratio >= 80:
                score += 15
                signaux["ratio_lots_collab"] = 15
                details.append(f"✓ Ratio {ratio:.0f} lots/collaborateur (sources: RNIC+INSEE) — équipe potentiellement surchargée, besoin d'externalisation")
            elif ratio >= 50:
                score += 10
                signaux["ratio_lots_collab"] = 10
                details.append(f"✓ Ratio {ratio:.0f} lots/collaborateur (sources: RNIC+INSEE) — charge élevée")
            else:
                signaux["ratio_lots_collab"] = 0
                details.append(f"○ Ratio {ratio:.0f} lots/collaborateur (sources: RNIC+INSEE) — charge raisonnable")

        # Signal: Copropriétés en difficulté (arrêtés de péril — source RNIC)
        if agence.nb_arretes_peril and agence.nb_arretes_peril > 0:
            score += 15
            signaux["copros_en_difficulte"] = 15
            details.append(f"✓ {agence.nb_arretes_peril} arrêté(s) de péril dans son portefeuille (source: RNIC) — besoin urgent de suivi travaux")
            known["arretes_peril"] = agence.nb_arretes_peril

        # Signal: Nombre de copropriétés gérées (source RNIC)
        if agence.nb_coproprietes and agence.nb_coproprietes > 0:
            known["nb_coproprietes"] = agence.nb_coproprietes
            if agence.nb_coproprietes >= 50:
                score += 10
                signaux["nb_coproprietes"] = 10
                details.append(f"✓ Gère {agence.nb_coproprietes} copropriétés (source: RNIC) — portefeuille important")

        # Completeness score
        completeness = len(known) / (len(known) + len(missing)) if (known or missing) else 0
        signaux["completude_donnees"] = round(completeness * 100)

        # Generate recommendation
        if score >= 50:
            recommandation = "Cible prioritaire — fort potentiel pour Monga"
        elif score >= 35:
            recommandation = "Cible potentielle — à investiguer"
        elif score >= 20:
            recommandation = "Profil intéressant — données complémentaires nécessaires"
        else:
            recommandation = "Données insuffisantes — investigation manuelle requise"

        # Build full insight
        insight = Insight(
            agence_id=agence.id,
            score_besoin=score,
            signaux={
                "scores": signaux,
                "details": details,
                "donnees_verifiees": list(known.keys()),
                "donnees_manquantes": missing,
                "source": "API INSEE + RNIC (Registre National des Copropriétés)",
                "fiabilite": f"{signaux['completude_donnees']}% des données disponibles",
            },
            ratio_lots_collab=(
                agence.nb_lots_geres / agence.nb_collaborateurs
                if agence.nb_lots_geres and agence.nb_collaborateurs
                else None
            ),
            turnover_score=float(nb_offres),
            avis_negatifs_travaux=0,
            croissance_parc=None,
            has_service_travaux=has_travaux_in_name,
            recommandation=recommandation,
        )
        db.add(insight)

    db.commit()


# ─── Upsert agence ───────────────────────────────────────────────────────────

def _upsert_agence(db: Session, entry: dict) -> tuple[int, int]:
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

    nom_lower = nom.lower()
    groupe = ""
    for key, value in GROUPS.items():
        if key in nom_lower:
            groupe = value
            break

    tranche = entry.get("tranche_effectif_salarie", "") or siege.get("tranche_effectif_salarie", "")
    nb_collab = EMPLOYEE_RANGES.get(tranche)

    # Get SIREN from the API response
    siren = entry.get("siren", "")

    existing = db.query(Agence).filter(
        Agence.nom == nom.title(), Agence.code_postal == code_postal,
    ).first()

    if existing:
        existing.derniere_maj = datetime.now(timezone.utc)
        if nb_collab is not None:
            existing.nb_collaborateurs = nb_collab
        if groupe:
            existing.groupe = groupe
        if siren:
            existing.siren = siren
        snapshot = AgenceSnapshot(
            agence_id=existing.id, nb_lots_geres=existing.nb_lots_geres,
            nb_collaborateurs=existing.nb_collaborateurs,
            a_service_travaux=existing.a_service_travaux,
            note_google=existing.note_google, note_trustpilot=existing.note_trustpilot,
        )
        db.add(snapshot)
        return 0, 1
    else:
        agence = Agence(
            nom=nom.title(), siren=siren, groupe=groupe, adresse=adresse,
            ville=ville.title() if ville else "", region=region,
            code_postal=code_postal, site_web="",
            nb_lots_geres=None, nb_collaborateurs=nb_collab,
            a_service_travaux=False, derniere_maj=datetime.now(timezone.utc),
        )
        db.add(agence)
        db.flush()
        snapshot = AgenceSnapshot(
            agence_id=agence.id, nb_lots_geres=None,
            nb_collaborateurs=nb_collab, a_service_travaux=False,
        )
        db.add(snapshot)
        return 1, 0
