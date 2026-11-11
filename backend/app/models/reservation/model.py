from datetime import datetime
from decimal import Decimal
from enum import StrEnum

from sqlalchemy import BigInteger, CheckConstraint, DateTime, ForeignKey, Identity, Index, Numeric, String, UniqueConstraint, func, select
from sqlalchemy.orm import Mapped, column_property, mapped_column, relationship

from app.db.base import Base
from app.models.finance import Paiement, PaiementStatus


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
        CheckConstraint("taux_acompte IS NULL OR (taux_acompte > 0 AND taux_acompte <= 1)", name="ck_reservations_taux_acompte"),
        CheckConstraint("plancher_acompte IS NULL OR plancher_acompte >= 0", name="ck_reservations_plancher_acompte"),
        Index("idx_reservations_depart", "id_depart"),
        Index("idx_reservations_user", "id_user"),
        Index("idx_reservations_statut", "statut"),
        Index("idx_reservations_expiration", "date_expiration"),
        UniqueConstraint("commande_hash", name="uq_reservations_commande_hash"),
    )

    id: Mapped[int] = mapped_column("id_reservation", BigInteger, Identity(always=True), primary_key=True)
    numero_reservation: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)
    id_depart: Mapped[int] = mapped_column(ForeignKey("departs.id_depart", ondelete="RESTRICT"), nullable=False)
    id_user: Mapped[int] = mapped_column(ForeignKey("users.id_user", ondelete="RESTRICT"), nullable=False)
    montant_total: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0, server_default="0", nullable=False)
    taux_acompte: Mapped[Decimal | None] = mapped_column(Numeric(5, 4))
    plancher_acompte: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    statut: Mapped[str] = mapped_column(String(20), default=ReservationStatus.EN_ATTENTE, server_default=ReservationStatus.EN_ATTENTE, nullable=False)
    date_expiration: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    nom_reservataire: Mapped[str | None] = mapped_column(String(150))
    telephone_reservataire: Mapped[str | None] = mapped_column(String(30))
    email_reservataire: Mapped[str | None] = mapped_column(String(150))
    acces_public_hash: Mapped[str | None] = mapped_column(String(64), unique=True)
    commande_hash: Mapped[str | None] = mapped_column(String(64))
    commande_payload_hash: Mapped[str | None] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    depart = relationship("Depart", back_populates="reservations")
    places = relationship("ReservationPlace", back_populates="reservation", cascade="all, delete-orphan", passive_deletes=True)

    montant_paye = column_property(
        select(func.coalesce(func.sum(Paiement.montant), 0))
        .where(Paiement.id_reservation == id, Paiement.statut == PaiementStatus.VALIDE)
        .correlate_except(Paiement).scalar_subquery()
    )
    montant_a_rembourser = column_property(
        select(func.coalesce(func.sum(Paiement.montant), 0))
        .where(Paiement.id_reservation == id, Paiement.statut == PaiementStatus.VALIDE,
               Paiement.remboursement_demande_le.is_not(None))
        .correlate_except(Paiement).scalar_subquery()
    )

    montant_rembourse = column_property(
        select(func.coalesce(func.sum(Paiement.montant), 0)).where(Paiement.id_reservation == id,
            Paiement.statut == PaiementStatus.REMBOURSE).correlate_except(Paiement).scalar_subquery()
    )

    @property
    def montant_restant(self) -> Decimal:
        if self.statut in {ReservationStatus.ANNULEE, ReservationStatus.EXPIREE}:
            return Decimal("0")
        return max(Decimal("0"), Decimal(self.montant_total) - Decimal(self.montant_paye or 0))

    @property
    def etat_paiement(self) -> str:
        if self.montant_a_rembourser:
            return "A_REMBOURSER"
        if self.montant_paye and self.montant_restant == 0:
            return "REGLE"
        return "ACOMPTE_RECU" if self.montant_paye else "REMBOURSE" if self.montant_rembourse else "NON_REGLE"

    @property
    def date_limite_annulation(self):
        from app.core.clock import local_moment
        from app.core.config import settings
        from datetime import timedelta
        if not self.depart:
            return None
        return local_moment(self.depart.date_depart, self.depart.heure_depart) - timedelta(minutes=settings.cancellation_deadline_minutes)

    @property
    def peut_annuler(self) -> bool:
        from app.core.clock import local_now
        if self.statut not in {"EN_ATTENTE", "CONFIRMEE", "PAYEE"} or self.depart.statut in {"PARTI", "TERMINE"}:
            return False
        if any(place.billet and place.billet.statut == "UTILISE" for place in self.places):
            return False
        if self.statut == "EN_ATTENTE" and self.date_expiration and self.date_expiration <= datetime.now(self.date_expiration.tzinfo):
            return False
        return not self.montant_paye or self.depart.statut == "ANNULE" or local_now() <= self.date_limite_annulation

    @property
    def peut_payer(self) -> bool:
        from app.core.config import settings
        return (settings.online_payment_enabled and settings.payment_provider.lower() == "papi"
                and self.statut in {"EN_ATTENTE", "CONFIRMEE", "PAYEE"} and self.montant_restant > 0
                and self.depart.statut not in {"PARTI", "TERMINE", "ANNULE"}
                and not (self.date_expiration and self.statut == "EN_ATTENTE" and self.date_expiration <= datetime.now(self.date_expiration.tzinfo)))

    @property
    def minimum_a_payer(self):
        from app.services.booking_policy import minimum_deposit
        return self.montant_restant if self.montant_paye else minimum_deposit(self.montant_total, rate=self.taux_acompte, floor=self.plancher_acompte)


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

