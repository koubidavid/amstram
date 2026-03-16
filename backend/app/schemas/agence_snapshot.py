import uuid
from datetime import datetime

from pydantic import BaseModel


class AgenceSnapshotRead(BaseModel):
    id: uuid.UUID
    agence_id: uuid.UUID
    nb_lots_geres: int | None = None
    nb_collaborateurs: int | None = None
    a_service_travaux: bool = False
    note_google: float | None = None
    note_trustpilot: float | None = None
    scraping_job_id: uuid.UUID | None = None
    created_at: datetime

    class Config:
        from_attributes = True
