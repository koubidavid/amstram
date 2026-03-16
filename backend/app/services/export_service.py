import csv
import io

import openpyxl
from sqlalchemy.orm import Session

from app.models.agence import Agence
from app.models.insight import Insight
from app.models.offre import OffreEmploi


def _write_excel(headers: list[str], rows: list[list]) -> io.BytesIO:
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(headers)
    for row in rows:
        ws.append(row)
    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    return output


def _write_csv(headers: list[str], rows: list[list]) -> io.StringIO:
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(headers)
    writer.writerows(rows)
    output.seek(0)
    return output


def export_agences(db: Session, fmt: str):
    agences = db.query(Agence).all()
    headers = ["Nom", "Groupe", "Ville", "Région", "Lots gérés", "Collaborateurs",
               "Service travaux", "Note Google", "Note Trustpilot"]
    rows = [[a.nom, a.groupe, a.ville, a.region, a.nb_lots_geres,
             a.nb_collaborateurs, a.a_service_travaux, a.note_google,
             a.note_trustpilot] for a in agences]
    return _write_excel(headers, rows) if fmt == "excel" else _write_csv(headers, rows)


def export_offres(db: Session, fmt: str):
    offres = db.query(OffreEmploi).all()
    headers = ["Titre", "Type poste", "Agence ID", "Date publication", "Active", "URL"]
    rows = [[o.titre, o.type_poste.value, str(o.agence_id), str(o.date_publication),
             o.active, o.url_source] for o in offres]
    return _write_excel(headers, rows) if fmt == "excel" else _write_csv(headers, rows)


def export_insights(db: Session, fmt: str):
    insights = db.query(Insight).all()
    headers = ["Agence ID", "Score", "Ratio lots/collab", "Turnover", "Avis négatifs",
               "Croissance parc", "Service travaux", "Recommandation"]
    rows = [[str(i.agence_id), i.score_besoin, i.ratio_lots_collab, i.turnover_score,
             i.avis_negatifs_travaux, i.croissance_parc, i.has_service_travaux,
             i.recommandation] for i in insights]
    return _write_excel(headers, rows) if fmt == "excel" else _write_csv(headers, rows)
