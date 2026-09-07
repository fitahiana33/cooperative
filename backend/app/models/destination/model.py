from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, Identity, Index, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Destination(Base):
    __tablename__ = "destinations"
    __table_args__ = (
        UniqueConstraint("nom", name="uq_destinations_nom"),
        Index("idx_destinations_nom", "nom"),
        Index("idx_destinations_active", "is_active"),
    )

    id: Mapped[int] = mapped_column("id_destination", BigInteger, Identity(always=True), primary_key=True)
    nom: Mapped[str] = mapped_column(String(150), nullable=False)
    region: Mapped[str | None] = mapped_column(String(100))
    description: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    itineraires_depart = relationship(
        "Itineraire", foreign_keys="Itineraire.id_destination_depart",
        back_populates="destination_depart", passive_deletes=True,
    )
    itineraires_arrivee = relationship(
        "Itineraire", foreign_keys="Itineraire.id_destination_arrivee",
        back_populates="destination_arrivee", passive_deletes=True,
    )
