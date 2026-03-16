from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class AgenceSnapshot(Base):
    __tablename__ = "agence_snapshots"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    agence_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("agences.id"))
    nb_lots_geres: Mapped[int | None] = mapped_column(Integer)
    nb_collaborateurs: Mapped[int | None] = mapped_column(Integer)
    a_service_travaux: Mapped[bool] = mapped_column(Boolean, default=False)
    note_google: Mapped[float | None] = mapped_column(Float)
    note_trustpilot: Mapped[float | None] = mapped_column(Float)
    scraping_job_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("scraping_jobs.id")
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    agence = relationship("Agence", back_populates="snapshots")
    scraping_job = relationship("ScrapingJob")
