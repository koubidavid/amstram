import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.models.avis import Avis, SourceAvis
from app.schemas.avis import AvisList

router = APIRouter(prefix="/api", tags=["avis"])


@router.get("/agences/{agence_id}/avis", response_model=AvisList)
def list_agence_avis(
    agence_id: uuid.UUID,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    source: SourceAvis | None = None,
    note_max: float | None = None,
    db: Session = Depends(get_db),
):
    query = select(Avis).where(Avis.agence_id == agence_id)
    count_query = select(func.count()).select_from(Avis).where(Avis.agence_id == agence_id)

    if source:
        query = query.where(Avis.source == source)
        count_query = count_query.where(Avis.source == source)
    if note_max is not None:
        query = query.where(Avis.note <= note_max)
        count_query = count_query.where(Avis.note <= note_max)

    total = db.execute(count_query).scalar()
    offset = (page - 1) * limit
    results = db.execute(query.order_by(Avis.date_avis.desc()).offset(offset).limit(limit)).scalars().all()
    pages = (total + limit - 1) // limit if total > 0 else 0

    return AvisList(items=results, total=total, page=page, limit=limit, pages=pages)
