from datetime import date, datetime
from sqlalchemy import BigInteger, Boolean, Date, DateTime, ForeignKey, Index, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base

class Chauffeur(Base):
    __tablename__ = "chauffeurs"
    __table_args__ = (
        Index("idx_chauffeurs_user", "id_user"),
        Index("idx_chauffeurs_cooperative", "id_cooperative"),
        Index("idx_chauffeurs_disponibilite", "disponibilite"),
        Index("idx_chauffeurs_expiration_permis", "date_expiration_permis"),
    )
    id: Mapped[int] = mapped_column("id_chauffeur", BigInteger, primary_key=True)
    id_user: Mapped[int] = mapped_column(ForeignKey("users.id_user", ondelete="RESTRICT"), unique=True, nullable=False)
    id_cooperative: Mapped[int] = mapped_column(ForeignKey("cooperatives.id_cooperative", ondelete="RESTRICT"), nullable=False)
    numero_permis: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    categorie_permis: Mapped[str] = mapped_column(String(20), nullable=False)
    date_expiration_permis: Mapped[date] = mapped_column(Date, nullable=False)
    disponibilite: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    user = relationship("User")
    cooperative = relationship("Cooperative", back_populates="chauffeurs")
    vehicules_assignments = relationship("VehiculeChauffeur", back_populates="chauffeur", passive_deletes=True)

    @property
    def permis_expire(self) -> bool:
        return self.date_expiration_permis < date.today()

    @property
    def vehicule_actuel(self):
        for assignment in self.vehicules_assignments:
            if assignment.is_active:
                return assignment.vehicule
        return None
