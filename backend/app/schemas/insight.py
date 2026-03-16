import uuid
from datetime import datetime

from pydantic import BaseModel


class InsightRead(BaseModel):
    id: uuid.UUID
    agence_id: uuid.UUID
    score_besoin: int
    signaux: dict | None = None
    ratio_lots_collab: float | None = None
    turnover_score: float | None = None
    avis_negatifs_travaux: int | None = None
    croissance_parc: float | None = None
    has_service_travaux: bool = False
    recommandation: str | None = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class InsightList(BaseModel):
    items: list[InsightRead]
    total: int
    page: int
    limit: int
    pages: int
