from __future__ import annotations

import enum
import uuid
from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class TypePoste(str, enum.Enum):
    gestionnaire_locatif = "gestionnaire_locatif"
    assistant_gestion_locative = "assistant_gestion_locative"
    gestionnaire_copropriete = "gestionnaire_copropriete"
    assistant_copropriete = "assistant_copropriete"
    autre = "autre"


class OffreEmploi(Base):
    __tablename__ = "offres"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    agence_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("agences.id"))
    titre: Mapped[str] = mapped_column(String(500))
    description: Mapped[str | None] = mapped_column(Text)
    type_poste: Mapped[TypePoste] = mapped_column(Enum(TypePoste))
    url_source: Mapped[str | None] = mapped_column(String(1000))
    date_publication: Mapped[date | None] = mapped_column(Date)
    date_scrappee: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    agence = relationship("Agence", back_populates="offres")
