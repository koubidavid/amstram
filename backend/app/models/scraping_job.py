import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class JobType(str, enum.Enum):
    manuel = "manuel"
    cron = "cron"


class JobStatut(str, enum.Enum):
    pending = "pending"
    running = "running"
    done = "done"
    failed = "failed"


class ScrapingJob(Base):
    __tablename__ = "scraping_jobs"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    type: Mapped[JobType] = mapped_column(Enum(JobType))
    cron_expression: Mapped[str | None] = mapped_column(String(100))
    statut: Mapped[JobStatut] = mapped_column(Enum(JobStatut), default=JobStatut.pending)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    started_at: Mapped[datetime | None] = mapped_column(DateTime)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime)
    nb_agences_scrappees: Mapped[int] = mapped_column(Integer, default=0)
    erreurs: Mapped[dict | None] = mapped_column(JSON)
