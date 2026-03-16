import uuid
from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.models.agence import Agence
from app.models.offre import OffreEmploi, TypePoste
from app.schemas.offre import OffreList

router = APIRouter(prefix="/api", tags=["offres"])


@router.get("/offres", response_model=OffreList)
def list_offres(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    type_poste: TypePoste | None = None,
    region: str | None = None,
    active: bool | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    db: Session = Depends(get_db),
):
    query = select(OffreEmploi)
    count_query = select(func.count()).select_from(OffreEmploi)

    if type_poste:
        query = query.where(OffreEmploi.type_poste == type_poste)
        count_query = count_query.where(OffreEmploi.type_poste == type_poste)
    if active is not None:
        query = query.where(OffreEmploi.active == active)
        count_query = count_query.where(OffreEmploi.active == active)
    if region:
        query = query.join(Agence).where(Agence.region == region)
        count_query = count_query.join(Agence).where(Agence.region == region)
    if date_from:
        query = query.where(OffreEmploi.date_publication >= date_from)
        count_query = count_query.where(OffreEmploi.date_publication >= date_from)
    if date_to:
        query = query.where(OffreEmploi.date_publication <= date_to)
        count_query = count_query.where(OffreEmploi.date_publication <= date_to)

    total = db.execute(count_query).scalar()
    offset = (page - 1) * limit
    results = db.execute(query.offset(offset).limit(limit)).scalars().all()
    pages = (total + limit - 1) // limit if total > 0 else 0

    return OffreList(items=results, total=total, page=page, limit=limit, pages=pages)


@router.get("/agences/{agence_id}/offres", response_model=OffreList)
def list_agence_offres(
    agence_id: uuid.UUID,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    query = select(OffreEmploi).where(OffreEmploi.agence_id == agence_id)
    count_query = select(func.count()).select_from(OffreEmploi).where(OffreEmploi.agence_id == agence_id)

    total = db.execute(count_query).scalar()
    offset = (page - 1) * limit
    results = db.execute(query.offset(offset).limit(limit)).scalars().all()
    pages = (total + limit - 1) // limit if total > 0 else 0

    return OffreList(items=results, total=total, page=page, limit=limit, pages=pages)
