from datetime import date, datetime, time
from enum import StrEnum

from sqlalchemy import BigInteger, CheckConstraint, Date, DateTime, ForeignKey, Identity, Index, Integer, String, Time, func, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class DepartStatus(StrEnum):
    PROGRAMME = "PROGRAMME"
    EMBARQUEMENT = "EMBARQUEMENT"
    RETARDE = "RETARDE"
    PARTI = "PARTI"
    TERMINE = "TERMINE"
    ANNULE = "ANNULE"


class Depart(Base):
    __tablename__ = "departs"
    __table_args__ = (
        CheckConstraint(
            "statut IN ('PROGRAMME', 'EMBARQUEMENT', 'RETARDE', 'PARTI', 'TERMINE', 'ANNULE')",
            name="ck_departs_statut",
        ),
        CheckConstraint("nombre_places > 0", name="ck_departs_nombre_places"),
        CheckConstraint(
            "places_reservees >= 0 AND places_reservees <= nombre_places",
            name="ck_departs_places_reservees",
        ),
        Index("idx_departs_itineraire", "id_itineraire"),
        Index("idx_departs_cooperative", "id_cooperative"),
        Index("idx_departs_vehicule", "id_vehicule"),
        Index("idx_departs_chauffeur", "id_chauffeur"),
        Index("idx_departs_tarif", "id_tarif"),
        Index("idx_departs_date_heure", "date_depart", "heure_depart"),
        Index("idx_departs_statut", "statut"),
        Index(
            "uq_active_depart_vehicle_slot",
            "id_vehicule",
            "date_depart",
            "heure_depart",
            unique=True,
            postgresql_where=text("statut <> 'ANNULE'"),
        ),
        Index(
            "uq_active_depart_driver_slot",
            "id_chauffeur",
            "date_depart",
            "heure_depart",
            unique=True,
            postgresql_where=text("statut <> 'ANNULE'"),
        ),
    )

    id: Mapped[int] = mapped_column("id_depart", BigInteger, Identity(always=True), primary_key=True)
    id_itineraire: Mapped[int] = mapped_column(
        ForeignKey("itineraires.id_itineraire", ondelete="RESTRICT"), nullable=False
    )
    id_cooperative: Mapped[int] = mapped_column(
        ForeignKey("cooperatives.id_cooperative", ondelete="RESTRICT"), nullable=False
    )
    id_vehicule: Mapped[int] = mapped_column(
        ForeignKey("vehicules.id_vehicule", ondelete="RESTRICT"), nullable=False
    )
    id_chauffeur: Mapped[int] = mapped_column(
        ForeignKey("chauffeurs.id_chauffeur", ondelete="RESTRICT"), nullable=False
    )
    id_tarif: Mapped[int] = mapped_column(
        ForeignKey("tarifs.id_tarif", ondelete="RESTRICT"), nullable=False
    )
    date_depart: Mapped[date] = mapped_column(Date, nullable=False)
    heure_depart: Mapped[time] = mapped_column(Time, nullable=False)
    nombre_places: Mapped[int] = mapped_column(Integer, nullable=False)
    places_reservees: Mapped[int] = mapped_column(Integer, default=0, server_default="0", nullable=False)
    statut: Mapped[str] = mapped_column(String(20), default=DepartStatus.PROGRAMME, server_default=DepartStatus.PROGRAMME, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    itineraire = relationship("Itineraire", back_populates="departs")
    cooperative = relationship("Cooperative", back_populates="departs")
    vehicule = relationship("Vehicule", back_populates="departs")
    chauffeur = relationship("Chauffeur", back_populates="departs")
    tarif = relationship("Tarif", back_populates="departs")

    @property
    def places_disponibles(self) -> int:
        return max(self.nombre_places - self.places_reservees, 0)

    @property
    def taux_remplissage(self) -> float:
        if self.nombre_places <= 0:
            return 0.0
        return round((self.places_reservees / self.nombre_places) * 100, 2)
