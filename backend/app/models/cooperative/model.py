from datetime import date, datetime
from sqlalchemy import BigInteger, Boolean, Date, DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base

class Cooperative(Base):
    __tablename__ = "cooperatives"
    id: Mapped[int] = mapped_column("id_cooperative", BigInteger, primary_key=True)
    nom: Mapped[str] = mapped_column(String(150), nullable=False)
    sigle: Mapped[str | None] = mapped_column(String(50))
    numero_agrement: Mapped[str | None] = mapped_column(String(100))
    adresse: Mapped[str | None] = mapped_column(String(255))
    ville: Mapped[str | None] = mapped_column(String(100))
    telephone: Mapped[str | None] = mapped_column(String(30))
    email: Mapped[str | None] = mapped_column(String(150))
    description: Mapped[str | None] = mapped_column(Text)
    responsable_id: Mapped[int | None] = mapped_column(ForeignKey("users.id_user", ondelete="SET NULL"))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    responsable = relationship("User")
    gares = relationship("GareCooperative", back_populates="cooperative", cascade="all, delete-orphan")
    members = relationship("CooperativeMember", back_populates="cooperative", cascade="all, delete-orphan")
    vehicules = relationship("Vehicule", back_populates="cooperative")
    chauffeurs = relationship("Chauffeur", back_populates="cooperative")


class GareCooperative(Base):
    __tablename__ = "gare_cooperatives"
    id_gare: Mapped[int] = mapped_column(ForeignKey("gares.id_gare", ondelete="CASCADE"), primary_key=True)
    id_cooperative: Mapped[int] = mapped_column(ForeignKey("cooperatives.id_cooperative", ondelete="CASCADE"), primary_key=True)
    date_debut: Mapped[date | None] = mapped_column(Date)
    date_fin: Mapped[date | None] = mapped_column(Date)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    gare = relationship("Gare", back_populates="cooperatives")
    cooperative = relationship("Cooperative", back_populates="gares")


class CooperativeMember(Base):
    __tablename__ = "cooperative_members"
    id_cooperative: Mapped[int] = mapped_column(ForeignKey("cooperatives.id_cooperative", ondelete="CASCADE"), primary_key=True)
    id_user: Mapped[int] = mapped_column(ForeignKey("users.id_user", ondelete="CASCADE"), primary_key=True)
    fonction: Mapped[str | None] = mapped_column(String(100))
    date_adhesion: Mapped[date | None] = mapped_column(Date)
    date_fin: Mapped[date | None] = mapped_column(Date)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    cooperative = relationship("Cooperative", back_populates="members")
    user = relationship("User", back_populates="cooperatives")
