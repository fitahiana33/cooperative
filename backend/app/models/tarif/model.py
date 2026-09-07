from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import BigInteger, Boolean, CheckConstraint, Date, DateTime, ForeignKey, Identity, Index, Numeric, String, func, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Tarif(Base):
    __tablename__ = "tarifs"
    __table_args__ = (
        CheckConstraint("prix > 0", name="ck_tarif_prix_positif"),
        CheckConstraint("date_fin IS NULL OR date_fin >= date_debut", name="ck_tarif_dates"),
        Index("idx_tarifs_itineraire", "id_itineraire"),
        Index("idx_tarifs_cooperative", "id_cooperative"),
        Index("idx_tarifs_active", "is_active"),
        Index("idx_tarifs_dates", "date_debut", "date_fin"),
        Index("uq_active_tarif_general", "id_itineraire", unique=True, postgresql_where=text("is_active = TRUE AND id_cooperative IS NULL")),
        Index("uq_active_tarif_cooperative", "id_itineraire", "id_cooperative", unique=True, postgresql_where=text("is_active = TRUE AND id_cooperative IS NOT NULL")),
    )

    id: Mapped[int] = mapped_column("id_tarif", BigInteger, Identity(always=True), primary_key=True)
    id_itineraire: Mapped[int] = mapped_column(ForeignKey("itineraires.id_itineraire", ondelete="CASCADE"), nullable=False)
    id_cooperative: Mapped[int | None] = mapped_column(ForeignKey("cooperatives.id_cooperative", ondelete="CASCADE"))
    prix: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    devise: Mapped[str] = mapped_column(String(10), default="MGA", nullable=False)
    date_debut: Mapped[date] = mapped_column(Date, server_default=func.current_date(), nullable=False)
    date_fin: Mapped[date | None] = mapped_column(Date)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    itineraire = relationship("Itineraire", back_populates="tarifs")
    cooperative = relationship("Cooperative")
