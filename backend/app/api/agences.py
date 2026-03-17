import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.models.agence import Agence
from app.models.agence_snapshot import AgenceSnapshot
from app.schemas.agence import AgenceList, AgenceRead

router = APIRouter(prefix="/api/agences", tags=["agences"])


@router.get("", response_model=AgenceList)
def list_agences(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    ville: str | None = None,
    region: str | None = None,
    nb_lots_min: int | None = None,
    nb_lots_max: int | None = None,
    db: Session = Depends(get_db),
):
    query = select(Agence)
    count_query = select(func.count()).select_from(Agence)

    if ville:
        query = query.where(Agence.ville == ville)
        count_query = count_query.where(Agence.ville == ville)
    if region:
        query = query.where(Agence.region == region)
        count_query = count_query.where(Agence.region == region)
    if nb_lots_min is not None:
        query = query.where(Agence.nb_lots_geres >= nb_lots_min)
        count_query = count_query.where(Agence.nb_lots_geres >= nb_lots_min)
    if nb_lots_max is not None:
        query = query.where(Agence.nb_lots_geres <= nb_lots_max)
        count_query = count_query.where(Agence.nb_lots_geres <= nb_lots_max)

    total = db.execute(count_query).scalar()
    offset = (page - 1) * limit
    results = db.execute(query.offset(offset).limit(limit)).scalars().all()
    pages = (total + limit - 1) // limit if total > 0 else 0

    return AgenceList(items=results, total=total, page=page, limit=limit, pages=pages)


@router.get("/{agence_id}", response_model=AgenceRead)
def get_agence(agence_id: uuid.UUID, db: Session = Depends(get_db)):
    agence = db.get(Agence, agence_id)
    if not agence:
        raise HTTPException(status_code=404, detail="Agence not found")
    return agence


@router.patch("/{agence_id}/commercial")
def update_commercial_status(
    agence_id: uuid.UUID,
    data: dict,
    db: Session = Depends(get_db),
):
    """Update commercial tracking fields."""
    agence = db.get(Agence, agence_id)
    if not agence:
        raise HTTPException(status_code=404, detail="Agence not found")

    if "statut_commercial" in data:
        agence.statut_commercial = data["statut_commercial"]
    if "notes_commercial" in data:
        agence.notes_commercial = data["notes_commercial"]
    if "telephone" in data:
        agence.telephone = data["telephone"]

    db.commit()
    db.refresh(agence)
    return agence


@router.post("/{agence_id}/appel")
def log_appel(
    agence_id: uuid.UUID,
    data: dict,
    db: Session = Depends(get_db),
):
    """Log a phone call on an agence."""
    from datetime import datetime, timezone

    agence = db.get(Agence, agence_id)
    if not agence:
        raise HTTPException(status_code=404, detail="Agence not found")

    appels = agence.appels or []
    appels.append({
        "date": datetime.now(timezone.utc).isoformat(),
        "resume": data.get("resume", ""),
        "resultat": data.get("resultat", ""),
        "statut_avant": agence.statut_commercial,
    })
    agence.appels = appels

    # Update status if provided
    if data.get("nouveau_statut"):
        agence.statut_commercial = data["nouveau_statut"]

    db.commit()
    db.refresh(agence)
    return agence


@router.get("/kanban")
def get_kanban(db: Session = Depends(get_db)):
    """Get agences grouped by commercial status for kanban view."""
    agences = db.query(Agence).filter(
        Agence.statut_commercial.isnot(None),
        Agence.statut_commercial != "nouveau",
    ).all()

    # Also include top targets that are still "nouveau"
    from app.models.insight import Insight
    top_nouveaux = (
        db.query(Agence)
        .join(Insight)
        .filter(Agence.statut_commercial.in_(["nouveau", None]))
        .filter(Insight.score_besoin >= 50)
        .order_by(Insight.score_besoin.desc())
        .limit(20)
        .all()
    )

    all_agences = {a.id: a for a in list(agences) + list(top_nouveaux)}

    columns = {}
    for a in all_agences.values():
        statut = a.statut_commercial or "nouveau"
        if statut not in columns:
            columns[statut] = []
        columns[statut].append({
            "id": str(a.id),
            "nom": a.nom,
            "ville": a.ville,
            "dirigeant_nom": a.dirigeant_nom,
            "telephone": a.telephone,
            "nb_lots_geres": a.nb_lots_geres,
            "nb_appels": len(a.appels) if a.appels else 0,
            "dernier_appel": a.appels[-1]["date"] if a.appels else None,
        })

    return columns


@router.get("/{agence_id}/snapshots")
def list_agence_snapshots(
    agence_id: uuid.UUID,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    query = select(AgenceSnapshot).where(AgenceSnapshot.agence_id == agence_id).order_by(AgenceSnapshot.created_at.desc())
    count_query = select(func.count()).select_from(AgenceSnapshot).where(AgenceSnapshot.agence_id == agence_id)

    total = db.execute(count_query).scalar()
    offset = (page - 1) * limit
    results = db.execute(query.offset(offset).limit(limit)).scalars().all()
    pages = (total + limit - 1) // limit if total > 0 else 0

    return {"items": results, "total": total, "page": page, "limit": limit, "pages": pages}
