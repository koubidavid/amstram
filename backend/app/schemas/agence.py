import uuid
from datetime import datetime

from pydantic import BaseModel


class AgenceBase(BaseModel):
    nom: str
    groupe: str | None = None
    adresse: str | None = None
    ville: str | None = None
    region: str | None = None
    code_postal: str | None = None
    site_web: str | None = None
    nb_lots_geres: int | None = None
    nb_collaborateurs: int | None = None
    a_service_travaux: bool = False
    note_google: float | None = None
    nb_avis_google: int | None = None
    note_trustpilot: float | None = None
    nb_avis_trustpilot: int | None = None


class AgenceRead(AgenceBase):
    id: uuid.UUID
    derniere_maj: datetime | None = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AgenceList(BaseModel):
    items: list[AgenceRead]
    total: int
    page: int
    limit: int
    pages: int
