from datetime import date, datetime
from sqlalchemy import BigInteger, Boolean, Date, DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base

class Chauffeur(Base):
    __tablename__ = "chauffeurs"
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
    vehicules_assignments = relationship("VehiculeChauffeur", back_populates="chauffeur", cascade="all, delete-orphan")
