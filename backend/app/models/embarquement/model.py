from datetime import datetime
from enum import StrEnum

from sqlalchemy import BigInteger, CheckConstraint, DateTime, ForeignKey, Identity, Index, String, Text, func, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class EmbarquementStatus(StrEnum):
    VALIDE = "VALIDE"
    REFUSE = "REFUSE"


class Embarquement(Base):
    __tablename__ = "embarquements"
    __table_args__ = (
        CheckConstraint("statut IN ('VALIDE', 'REFUSE')", name="ck_embarquement_statut"),
        CheckConstraint("(statut = 'REFUSE' AND motif_refus IS NOT NULL) OR statut = 'VALIDE'", name="ck_embarquement_motif_refus"),
        Index("idx_embarquements_billet", "id_billet"),
        Index("idx_embarquements_agent", "id_agent"),
        Index("idx_embarquements_statut", "statut"),
        Index("idx_embarquements_date", "date_heure_embarquement"),
        Index("uq_embarquement_valide_billet", "id_billet", unique=True, postgresql_where=text("statut = 'VALIDE'")),
    )

    id: Mapped[int] = mapped_column("id_embarquement", BigInteger, Identity(always=True), primary_key=True)
    id_billet: Mapped[int] = mapped_column(ForeignKey("billets.id_billet", ondelete="RESTRICT"), nullable=False)
    id_agent: Mapped[int] = mapped_column(ForeignKey("users.id_user", ondelete="RESTRICT"), nullable=False)
    date_heure_embarquement: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    statut: Mapped[str] = mapped_column(String(20), default=EmbarquementStatus.VALIDE, server_default=EmbarquementStatus.VALIDE, nullable=False)
    motif_refus: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    billet = relationship("Billet")
