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
