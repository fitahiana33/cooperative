from datetime import datetime
from decimal import Decimal
from enum import StrEnum

from sqlalchemy import BigInteger, CheckConstraint, DateTime, ForeignKey, Identity, Index, Numeric, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ReservationStatus(StrEnum):
    EN_ATTENTE = "EN_ATTENTE"
    CONFIRMEE = "CONFIRMEE"
    PAYEE = "PAYEE"
    ANNULEE = "ANNULEE"
    EXPIREE = "EXPIREE"
    EMBARQUEE = "EMBARQUEE"
    TERMINEE = "TERMINEE"


class Reservation(Base):
    __tablename__ = "reservations"
    __table_args__ = (
        CheckConstraint("statut IN ('EN_ATTENTE', 'CONFIRMEE', 'PAYEE', 'ANNULEE', 'EXPIREE', 'EMBARQUEE', 'TERMINEE')", name="ck_reservation_statut"),
        CheckConstraint("montant_total >= 0", name="ck_reservation_montant"),
        Index("idx_reservations_depart", "id_depart"),
        Index("idx_reservations_user", "id_user"),
        Index("idx_reservations_statut", "statut"),
        Index("idx_reservations_expiration", "date_expiration"),
    )

    id: Mapped[int] = mapped_column("id_reservation", BigInteger, Identity(always=True), primary_key=True)
    numero_reservation: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)
    id_depart: Mapped[int] = mapped_column(ForeignKey("departs.id_depart", ondelete="RESTRICT"), nullable=False)
    id_user: Mapped[int] = mapped_column(ForeignKey("users.id_user", ondelete="RESTRICT"), nullable=False)
    montant_total: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0, server_default="0", nullable=False)
    statut: Mapped[str] = mapped_column(String(20), default=ReservationStatus.EN_ATTENTE, server_default=ReservationStatus.EN_ATTENTE, nullable=False)
    date_expiration: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    depart = relationship("Depart", back_populates="reservations")
    places = relationship("ReservationPlace", back_populates="reservation", cascade="all, delete-orphan", passive_deletes=True)


class ReservationPlace(Base):
    __tablename__ = "reservation_places"
    __table_args__ = (
        UniqueConstraint("id_reservation", "id_depart_place", name="uq_reservation_place"),
        Index("idx_reservation_places_reservation", "id_reservation"),
        Index("idx_reservation_places_place", "id_depart_place"),
    )

    id: Mapped[int] = mapped_column("id_reservation_place", BigInteger, Identity(always=True), primary_key=True)
    id_reservation: Mapped[int] = mapped_column(ForeignKey("reservations.id_reservation", ondelete="CASCADE"), nullable=False)
    id_depart_place: Mapped[int] = mapped_column(ForeignKey("depart_places.id_depart_place", ondelete="RESTRICT"), nullable=False)
    nom_passager: Mapped[str] = mapped_column(String(150), nullable=False)
    telephone_passager: Mapped[str | None] = mapped_column(String(30))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    reservation = relationship("Reservation", back_populates="places")
    depart_place = relationship("DepartPlace")
    billet = relationship("Billet", back_populates="reservation_place", uselist=False)

