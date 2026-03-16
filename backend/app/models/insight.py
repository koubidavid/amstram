from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, JSON, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class Insight(Base):
    __tablename__ = "insights"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    agence_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("agences.id"))
    score_besoin: Mapped[int] = mapped_column(Integer, default=0)
    signaux: Mapped[dict | None] = mapped_column(JSON)
    ratio_lots_collab: Mapped[float | None] = mapped_column(Float)
    turnover_score: Mapped[float | None] = mapped_column(Float)
    avis_negatifs_travaux: Mapped[int | None] = mapped_column(Integer)
    croissance_parc: Mapped[float | None] = mapped_column(Float)
    has_service_travaux: Mapped[bool] = mapped_column(Boolean, default=False)
    recommandation: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    agence = relationship("Agence", back_populates="insights")
