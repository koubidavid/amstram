import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.models.insight import Insight
from app.schemas.insight import InsightList, InsightRead

router = APIRouter(prefix="/api", tags=["insights"])


@router.get("/insights", response_model=InsightList)
def list_insights(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    score_min: int | None = None,
    db: Session = Depends(get_db),
):
    latest_subq = (
        select(Insight.agence_id, func.max(Insight.created_at).label("max_date"))
        .group_by(Insight.agence_id)
        .subquery()
    )
    query = (
        select(Insight)
        .join(latest_subq, (Insight.agence_id == latest_subq.c.agence_id) & (Insight.created_at == latest_subq.c.max_date))
        .order_by(Insight.score_besoin.desc())
    )

    if score_min is not None:
        query = query.where(Insight.score_besoin >= score_min)

    # Count total
    count_subq = query.subquery()
    total = db.execute(select(func.count()).select_from(count_subq)).scalar()

    offset = (page - 1) * limit
    results = db.execute(query.offset(offset).limit(limit)).scalars().all()
    pages = (total + limit - 1) // limit if total > 0 else 0

    return InsightList(items=results, total=total, page=page, limit=limit, pages=pages)


@router.get("/agences/{agence_id}/insights/historique", response_model=list[InsightRead])
def get_agence_insights_history(
    agence_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    results = (
        db.execute(
            select(Insight)
            .where(Insight.agence_id == agence_id)
            .order_by(Insight.created_at.asc())
        )
        .scalars()
        .all()
    )
    return results
