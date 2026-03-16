import uuid
from datetime import date, datetime

from pydantic import BaseModel

from app.models.avis import SourceAvis


class AvisRead(BaseModel):
    id: uuid.UUID
    agence_id: uuid.UUID
    source: SourceAvis
    note: float
    texte: str | None = None
    mentionne_travaux: bool = False
    mentionne_reactivite: bool = False
    date_avis: date | None = None
    created_at: datetime

    class Config:
        from_attributes = True


class AvisList(BaseModel):
    items: list[AvisRead]
    total: int
    page: int
    limit: int
    pages: int
