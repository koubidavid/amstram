from __future__ import annotations

import enum
import uuid
from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, Enum, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class SourceAvis(str, enum.Enum):
    google = "google"
    trustpilot = "trustpilot"


class Avis(Base):
    __tablename__ = "avis"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    agence_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("agences.id"))
    source: Mapped[SourceAvis] = mapped_column(Enum(SourceAvis))
    note: Mapped[float] = mapped_column(Float)
    texte: Mapped[str | None] = mapped_column(Text)
    mentionne_travaux: Mapped[bool] = mapped_column(Boolean, default=False)
    mentionne_reactivite: Mapped[bool] = mapped_column(Boolean, default=False)
    date_avis: Mapped[date | None] = mapped_column(Date)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    agence = relationship("Agence", back_populates="avis")
