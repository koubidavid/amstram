import uuid
from datetime import datetime

from pydantic import BaseModel

from app.models.scraping_job import JobStatut, JobType


class ScrapingJobCreate(BaseModel):
    type: JobType = JobType.manuel
    cron_expression: str | None = None


class ScrapingJobRead(BaseModel):
    id: uuid.UUID
    type: JobType
    cron_expression: str | None = None
    statut: JobStatut
    created_at: datetime
    started_at: datetime | None = None
    finished_at: datetime | None = None
    nb_agences_scrappees: int
    progression: dict | None = None
    erreurs: dict | None = None

    class Config:
        from_attributes = True


class ScrapingJobList(BaseModel):
    items: list[ScrapingJobRead]
    total: int
    page: int
    limit: int
    pages: int
