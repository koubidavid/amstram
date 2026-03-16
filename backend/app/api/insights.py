import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.models.agence import Agence
from app.models.insight import Insight
from app.schemas.insight import InsightList, InsightRead

router = APIRouter(prefix="/api", tags=["insights"])


@router.get("/insights")
def list_insights(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    score_min: int | None = None,
    db: Session = Depends(get_db),
):
    """Return insights joined with agence info."""
    latest_subq = (
        select(Insight.agence_id, func.max(Insight.created_at).label("max_date"))
        .group_by(Insight.agence_id)
        .subquery()
    )
    query = (
        select(Insight, Agence)
        .join(latest_subq, (Insight.agence_id == latest_subq.c.agence_id) & (Insight.created_at == latest_subq.c.max_date))
        .join(Agence, Insight.agence_id == Agence.id)
        .order_by(Insight.score_besoin.desc())
    )

    if score_min is not None:
        query = query.where(Insight.score_besoin >= score_min)

    # Count
    count_subq = (
        select(func.count(Insight.id))
        .join(latest_subq, (Insight.agence_id == latest_subq.c.agence_id) & (Insight.created_at == latest_subq.c.max_date))
    )
    if score_min is not None:
        count_subq = count_subq.where(Insight.score_besoin >= score_min)
    total = db.execute(count_subq).scalar() or 0

    offset = (page - 1) * limit
    rows = db.execute(query.offset(offset).limit(limit)).all()
    pages = (total + limit - 1) // limit if total > 0 else 0

    items = []
    for insight, agence in rows:
        items.append({
            "id": str(insight.id),
            "agence_id": str(insight.agence_id),
            "agence_nom": agence.nom,
            "agence_ville": agence.ville,
            "agence_region": agence.region,
            "agence_groupe": agence.groupe,
            "agence_nb_lots": agence.nb_lots_geres,
            "agence_nb_collab": agence.nb_collaborateurs,
            "agence_note_google": agence.note_google,
            "agence_a_service_travaux": agence.a_service_travaux,
            "score_besoin": insight.score_besoin,
            "signaux": insight.signaux,
            "ratio_lots_collab": insight.ratio_lots_collab,
            "turnover_score": insight.turnover_score,
            "avis_negatifs_travaux": insight.avis_negatifs_travaux,
            "croissance_parc": insight.croissance_parc,
            "has_service_travaux": insight.has_service_travaux,
            "recommandation": insight.recommandation,
            "created_at": insight.created_at.isoformat() if insight.created_at else None,
        })

    return {"items": items, "total": total, "page": page, "limit": limit, "pages": pages}


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
