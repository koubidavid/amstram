from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class Agence(Base):
    __tablename__ = "agences"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    nom: Mapped[str] = mapped_column(String(255))
    siren: Mapped[str | None] = mapped_column(String(9))
    groupe: Mapped[str | None] = mapped_column(String(255))
    nb_coproprietes: Mapped[int | None] = mapped_column(Integer)
    nb_arretes_peril: Mapped[int | None] = mapped_column(Integer)
    adresse: Mapped[str | None] = mapped_column(String(500))
    ville: Mapped[str | None] = mapped_column(String(100))
    region: Mapped[str | None] = mapped_column(String(100))
    code_postal: Mapped[str | None] = mapped_column(String(10))
    site_web: Mapped[str | None] = mapped_column(String(500))
    nb_lots_geres: Mapped[int | None] = mapped_column(Integer)
    nb_collaborateurs: Mapped[int | None] = mapped_column(Integer)
    a_service_travaux: Mapped[bool] = mapped_column(Boolean, default=False)
    note_google: Mapped[float | None] = mapped_column(Float)
    nb_avis_google: Mapped[int | None] = mapped_column(Integer)
    note_trustpilot: Mapped[float | None] = mapped_column(Float)
    nb_avis_trustpilot: Mapped[int | None] = mapped_column(Integer)
    derniere_maj: Mapped[datetime | None] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Pappers data
    dirigeant_nom: Mapped[str | None] = mapped_column(String(255))
    dirigeant_qualite: Mapped[str | None] = mapped_column(String(100))
    chiffre_affaires: Mapped[int | None] = mapped_column(Integer)
    resultat_net: Mapped[int | None] = mapped_column(Integer)
    date_creation: Mapped[str | None] = mapped_column(String(20))
    forme_juridique: Mapped[str | None] = mapped_column(String(100))
    effectif_precise: Mapped[str | None] = mapped_column(String(100))

    # Commercial tracking
    statut_commercial: Mapped[str | None] = mapped_column(String(50), default="nouveau")
    notes_commercial: Mapped[str | None] = mapped_column(Text)

    offres = relationship("OffreEmploi", back_populates="agence")
    avis = relationship("Avis", back_populates="agence")
    insights = relationship("Insight", back_populates="agence")
    snapshots = relationship("AgenceSnapshot", back_populates="agence")
