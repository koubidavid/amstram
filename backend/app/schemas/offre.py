import uuid
from datetime import date, datetime

from pydantic import BaseModel

from app.models.offre import TypePoste


class OffreBase(BaseModel):
    titre: str
    description: str | None = None
    type_poste: TypePoste
    url_source: str | None = None
    date_publication: date | None = None
    active: bool = True


class OffreRead(OffreBase):
    id: uuid.UUID
    agence_id: uuid.UUID
    date_scrappee: datetime
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class OffreList(BaseModel):
    items: list[OffreRead]
    total: int
    page: int
    limit: int
    pages: int
