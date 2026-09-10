from datetime import datetime
from enum import StrEnum
from uuid import UUID, uuid4

from sqlalchemy import BigInteger, CheckConstraint, DateTime, ForeignKey, Identity, Index, String, UUID as SQLUUID, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class BilletStatus(StrEnum):
    VALIDE = "VALIDE"
    UTILISE = "UTILISE"
    ANNULE = "ANNULE"
    EXPIRE = "EXPIRE"


class Billet(Base):
    __tablename__ = "billets"
    __table_args__ = (
        CheckConstraint("statut IN ('VALIDE', 'UTILISE', 'ANNULE', 'EXPIRE')", name="ck_billet_statut"),
        Index("idx_billets_reservation_place", "id_reservation_place"),
        Index("idx_billets_statut", "statut"),
        Index("idx_billets_qr_code", "qr_code_uuid"),
    )

    id: Mapped[int] = mapped_column("id_billet", BigInteger, Identity(always=True), primary_key=True)
    numero_billet: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    id_reservation_place: Mapped[int] = mapped_column(ForeignKey("reservation_places.id_reservation_place", ondelete="RESTRICT"), unique=True, nullable=False)
    qr_code_uuid: Mapped[UUID] = mapped_column(SQLUUID(as_uuid=True), default=uuid4, server_default=func.gen_random_uuid(), unique=True, nullable=False)
    qr_code_path: Mapped[str | None] = mapped_column(String(500))
    statut: Mapped[str] = mapped_column(String(20), default=BilletStatus.VALIDE, server_default=BilletStatus.VALIDE, nullable=False)
    date_emission: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    date_utilisation: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    reservation_place = relationship("ReservationPlace", back_populates="billet")

