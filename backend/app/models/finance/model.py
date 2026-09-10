from datetime import datetime
from decimal import Decimal
from enum import StrEnum

from sqlalchemy import BigInteger, CheckConstraint, DateTime, ForeignKey, Identity, Index, Numeric, String, Text, func, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class PaiementMethode(StrEnum):
    ESPECES = "ESPECES"
    MOBILE_MONEY = "MOBILE_MONEY"
    CARTE = "CARTE"
    VIREMENT = "VIREMENT"
    AUTRE = "AUTRE"


class PaiementStatus(StrEnum):
    EN_ATTENTE = "EN_ATTENTE"
    VALIDE = "VALIDE"
    ECHOUE = "ECHOUE"
    REMBOURSE = "REMBOURSE"


class CaisseStatus(StrEnum):
    OUVERTE = "OUVERTE"
    CLOTUREE = "CLOTUREE"


class OperationType(StrEnum):
    RECETTE = "RECETTE"
    DEPENSE = "DEPENSE"
    COMMISSION = "COMMISSION"


class Paiement(Base):
    __tablename__ = "paiements"
    __table_args__ = (
        CheckConstraint("montant > 0", name="ck_paiement_montant"),
        CheckConstraint("methode IN ('ESPECES', 'MOBILE_MONEY', 'CARTE', 'VIREMENT', 'AUTRE')", name="ck_paiement_methode"),
        CheckConstraint("statut IN ('EN_ATTENTE', 'VALIDE', 'ECHOUE', 'REMBOURSE')", name="ck_paiement_statut"),
        Index("idx_paiements_reservation", "id_reservation"),
        Index("idx_paiements_statut", "statut"),
        Index("idx_paiements_agent", "id_agent"),
        Index("idx_paiements_date", "date_paiement"),
    )

    id: Mapped[int] = mapped_column("id_paiement", BigInteger, Identity(always=True), primary_key=True)
    id_reservation: Mapped[int] = mapped_column(ForeignKey("reservations.id_reservation", ondelete="RESTRICT"), nullable=False)
    montant: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    methode: Mapped[str] = mapped_column(String(30), default=PaiementMethode.ESPECES, server_default=PaiementMethode.ESPECES, nullable=False)
    reference_paiement: Mapped[str | None] = mapped_column(String(100))
    statut: Mapped[str] = mapped_column(String(20), default=PaiementStatus.EN_ATTENTE, server_default=PaiementStatus.EN_ATTENTE, nullable=False)
    date_paiement: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    id_agent: Mapped[int | None] = mapped_column(ForeignKey("users.id_user", ondelete="SET NULL"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    reservation = relationship("Reservation")


class Caisse(Base):
    __tablename__ = "caisses"
    __table_args__ = (
        CheckConstraint("statut IN ('OUVERTE', 'CLOTUREE')", name="ck_caisse_statut"),
        CheckConstraint("montant_ouverture >= 0 AND (montant_cloture IS NULL OR montant_cloture >= 0)", name="ck_caisse_montants"),
        CheckConstraint("(statut = 'OUVERTE' AND date_cloture IS NULL) OR (statut = 'CLOTUREE' AND date_cloture IS NOT NULL)", name="ck_caisse_cloture_coherente"),
        Index("idx_caisses_gare", "id_gare"),
        Index("idx_caisses_agent", "id_agent"),
        Index("idx_caisses_statut", "statut"),
        Index("uq_caisse_ouverte_gare", "id_gare", unique=True, postgresql_where=text("statut = 'OUVERTE'")),
    )

    id: Mapped[int] = mapped_column("id_caisse", BigInteger, Identity(always=True), primary_key=True)
    id_gare: Mapped[int] = mapped_column(ForeignKey("gares.id_gare", ondelete="RESTRICT"), nullable=False)
    id_agent: Mapped[int] = mapped_column(ForeignKey("users.id_user", ondelete="RESTRICT"), nullable=False)
    date_ouverture: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    montant_ouverture: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0, server_default="0", nullable=False)
    date_cloture: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    montant_cloture: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    statut: Mapped[str] = mapped_column(String(20), default=CaisseStatus.OUVERTE, server_default=CaisseStatus.OUVERTE, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    operations = relationship("OperationCaisse", back_populates="caisse", cascade="all, delete-orphan", passive_deletes=True)


class OperationCaisse(Base):
    __tablename__ = "operations_caisse"
    __table_args__ = (
        CheckConstraint("montant > 0", name="ck_operation_montant"),
        CheckConstraint("type_operation IN ('RECETTE', 'DEPENSE', 'COMMISSION')", name="ck_operation_type"),
        Index("idx_operations_caisse_caisse", "id_caisse"),
        Index("idx_operations_caisse_type", "type_operation"),
        Index("idx_operations_caisse_cooperative", "id_cooperative"),
        Index("idx_operations_caisse_date", "date_operation"),
    )

    id: Mapped[int] = mapped_column("id_operation", BigInteger, Identity(always=True), primary_key=True)
    id_caisse: Mapped[int] = mapped_column(ForeignKey("caisses.id_caisse", ondelete="CASCADE"), nullable=False)
    type_operation: Mapped[str] = mapped_column(String(20), nullable=False)
    montant: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    id_paiement: Mapped[int | None] = mapped_column(ForeignKey("paiements.id_paiement", ondelete="SET NULL"))
    id_cooperative: Mapped[int | None] = mapped_column(ForeignKey("cooperatives.id_cooperative", ondelete="SET NULL"))
    description: Mapped[str | None] = mapped_column(String(255))
    date_operation: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    caisse = relationship("Caisse", back_populates="operations")

