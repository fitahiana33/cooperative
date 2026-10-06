from datetime import datetime
from enum import StrEnum

from sqlalchemy import BigInteger, CheckConstraint, DateTime, ForeignKey, Identity, Index, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class DepartPlaceStatus(StrEnum):
    DISPONIBLE = "DISPONIBLE"
    RESERVEE = "RESERVEE"
    BLOQUEE = "BLOQUEE"
    OCCUPEE = "OCCUPEE"


class DepartPlace(Base):
    __tablename__ = "depart_places"
    __table_args__ = (
        UniqueConstraint("id_depart", "numero_place", name="uq_depart_place_numero"),
        CheckConstraint("numero_place > 0", name="ck_depart_place_numero"),
        CheckConstraint("statut IN ('DISPONIBLE', 'RESERVEE', 'BLOQUEE', 'OCCUPEE')", name="ck_depart_place_statut"),
        Index("idx_depart_places_depart", "id_depart"),
        Index("idx_depart_places_statut", "statut"),
    )

    id: Mapped[int] = mapped_column("id_depart_place", BigInteger, Identity(always=True), primary_key=True)
    id_depart: Mapped[int] = mapped_column(ForeignKey("departs.id_depart", ondelete="CASCADE"), nullable=False)
    numero_place: Mapped[int] = mapped_column(Integer, nullable=False)
    statut: Mapped[str] = mapped_column(String(20), default=DepartPlaceStatus.DISPONIBLE, server_default=DepartPlaceStatus.DISPONIBLE, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    depart = relationship("Depart", back_populates="places")

