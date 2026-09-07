from datetime import date, datetime
from sqlalchemy import BigInteger, Boolean, CheckConstraint, Date, DateTime, ForeignKey, Index, Integer, String, Text, func, text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base

class Vehicule(Base):
    __tablename__ = "vehicules"
    __table_args__ = (
        CheckConstraint("chevaux IS NULL OR chevaux > 0", name="ck_vehicule_chevaux"),
        CheckConstraint("nombre_places > 0", name="ck_vehicule_nombre_places"),
        CheckConstraint("etat IN ('BON_ETAT', 'MOYEN', 'A_REPARER', 'HORS_SERVICE')", name="ck_vehicule_etat"),
        Index("idx_vehicules_modele", "id_modele"),
        Index("idx_vehicules_cooperative", "id_cooperative"),
        Index("idx_vehicules_immatriculation", "immatriculation"),
        Index("idx_vehicules_disponibilite", "disponibilite"),
        Index("idx_vehicules_etat", "etat"),
    )

    id: Mapped[int] = mapped_column("id_vehicule", BigInteger, primary_key=True)
    id_modele: Mapped[int] = mapped_column(ForeignKey("modeles.id_modele", ondelete="RESTRICT"), nullable=False)
    id_cooperative: Mapped[int] = mapped_column(ForeignKey("cooperatives.id_cooperative", ondelete="RESTRICT"), nullable=False)
    immatriculation: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)
    chevaux: Mapped[int | None] = mapped_column(Integer)
    nombre_places: Mapped[int] = mapped_column(Integer, nullable=False)
    disponibilite: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    etat: Mapped[str] = mapped_column(String(50), default="BON_ETAT", nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    modele = relationship("Modele", back_populates="vehicules")
    cooperative = relationship("Cooperative", back_populates="vehicules")
    documents = relationship("VehiculeDocument", back_populates="vehicule", passive_deletes=True)
    chauffeurs_assignments = relationship("VehiculeChauffeur", back_populates="vehicule", passive_deletes=True)


class VehiculeDocument(Base):
    __tablename__ = "vehicule_documents"
    __table_args__ = (
        CheckConstraint("type_document IN ('CARTE_GRISE', 'ASSURANCE', 'VISITE_TECHNIQUE', 'AUTRE_DOCUMENT')", name="ck_vehicule_document_type"),
        CheckConstraint("date_expiration IS NULL OR date_delivrance IS NULL OR date_expiration >= date_delivrance", name="ck_vehicule_document_dates"),
        Index("idx_vehicule_documents_vehicule", "id_vehicule"),
        Index("idx_vehicule_documents_type", "type_document"),
        Index("idx_vehicule_documents_expiration", "date_expiration"),
    )

    id: Mapped[int] = mapped_column("id_document", BigInteger, primary_key=True)
    id_vehicule: Mapped[int] = mapped_column(ForeignKey("vehicules.id_vehicule", ondelete="CASCADE"), nullable=False)
    type_document: Mapped[str] = mapped_column(String(50), nullable=False)
    numero_document: Mapped[str | None] = mapped_column(String(100))
    date_delivrance: Mapped[date | None] = mapped_column(Date)
    date_expiration: Mapped[date | None] = mapped_column(Date)
    fichier_path: Mapped[str | None] = mapped_column(String(500))
    is_valid: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    vehicule = relationship("Vehicule", back_populates="documents", passive_deletes=True)

    @property
    def is_expired(self) -> bool:
        return self.date_expiration is not None and self.date_expiration < date.today()


class VehiculeChauffeur(Base):
    __tablename__ = "vehicule_chauffeurs"
    __table_args__ = (
        CheckConstraint("date_fin IS NULL OR date_fin >= date_debut", name="ck_vehicule_chauffeur_dates"),
        Index(
            "uq_active_chauffeur_assignment",
            "id_chauffeur",
            unique=True,
            postgresql_where=text("is_active = TRUE"),
        ),
        Index(
            "uq_active_vehicle_assignment",
            "id_vehicule",
            unique=True,
            postgresql_where=text("is_active = TRUE"),
        ),
        Index("idx_vehicule_chauffeurs_vehicule", "id_vehicule"),
        Index("idx_vehicule_chauffeurs_chauffeur", "id_chauffeur"),
        Index("idx_vehicule_chauffeurs_active", "is_active"),
    )

    id_vehicule: Mapped[int] = mapped_column(ForeignKey("vehicules.id_vehicule", ondelete="RESTRICT"), primary_key=True)
    id_chauffeur: Mapped[int] = mapped_column(ForeignKey("chauffeurs.id_chauffeur", ondelete="RESTRICT"), primary_key=True)
    date_debut: Mapped[date] = mapped_column(Date, primary_key=True, server_default=func.current_date())
    date_fin: Mapped[date | None] = mapped_column(Date)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    vehicule = relationship("Vehicule", back_populates="chauffeurs_assignments", passive_deletes=True)
    chauffeur = relationship("Chauffeur", back_populates="vehicules_assignments", passive_deletes=True)
