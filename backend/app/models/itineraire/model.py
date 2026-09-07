from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import BigInteger, Boolean, CheckConstraint, Date, DateTime, ForeignKey, Identity, Index, Integer, Numeric, Text, UniqueConstraint, func, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Itineraire(Base):
    __tablename__ = "itineraires"
    __table_args__ = (
        CheckConstraint("id_destination_depart <> id_destination_arrivee", name="ck_itineraire_destinations_differentes"),
        CheckConstraint("distance_km IS NULL OR distance_km > 0", name="ck_itineraire_distance_positive"),
        CheckConstraint("duree_estimee_minutes IS NULL OR duree_estimee_minutes > 0", name="ck_itineraire_duree_positive"),
        UniqueConstraint("id_destination_depart", "id_destination_arrivee", name="uq_itineraire_depart_arrivee"),
        Index("idx_itineraires_depart", "id_destination_depart"),
        Index("idx_itineraires_arrivee", "id_destination_arrivee"),
        Index("idx_itineraires_active", "is_active"),
    )

    id: Mapped[int] = mapped_column("id_itineraire", BigInteger, Identity(always=True), primary_key=True)
    id_destination_depart: Mapped[int] = mapped_column(ForeignKey("destinations.id_destination", ondelete="RESTRICT"), nullable=False)
    id_destination_arrivee: Mapped[int] = mapped_column(ForeignKey("destinations.id_destination", ondelete="RESTRICT"), nullable=False)
    distance_km: Mapped[Decimal | None] = mapped_column(Numeric(8, 2))
    duree_estimee_minutes: Mapped[int | None] = mapped_column(Integer)
    description: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    destination_depart = relationship("Destination", foreign_keys=[id_destination_depart], back_populates="itineraires_depart")
    destination_arrivee = relationship("Destination", foreign_keys=[id_destination_arrivee], back_populates="itineraires_arrivee")
    cooperatives = relationship("ItineraireCooperative", back_populates="itineraire", passive_deletes=True)
    tarifs = relationship("Tarif", back_populates="itineraire", passive_deletes=True)


class ItineraireCooperative(Base):
    __tablename__ = "itineraire_cooperatives"
    __table_args__ = (
        CheckConstraint("date_fin IS NULL OR date_fin >= date_debut", name="ck_itineraire_cooperative_dates"),
        Index("idx_itineraire_cooperatives_itineraire", "id_itineraire"),
        Index("idx_itineraire_cooperatives_cooperative", "id_cooperative"),
        Index("idx_itineraire_cooperatives_active", "is_active"),
        Index("uq_active_itineraire_cooperative", "id_itineraire", "id_cooperative", unique=True, postgresql_where=text("is_active = TRUE")),
    )

    id_itineraire: Mapped[int] = mapped_column(ForeignKey("itineraires.id_itineraire", ondelete="CASCADE"), primary_key=True)
    id_cooperative: Mapped[int] = mapped_column(ForeignKey("cooperatives.id_cooperative", ondelete="CASCADE"), primary_key=True)
    date_debut: Mapped[date] = mapped_column(Date, server_default=func.current_date(), nullable=False)
    date_fin: Mapped[date | None] = mapped_column(Date)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    itineraire = relationship("Itineraire", back_populates="cooperatives")
    cooperative = relationship("Cooperative")
