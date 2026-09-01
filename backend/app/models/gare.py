from datetime import datetime
from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Numeric, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base

class Gare(Base):
    __tablename__ = "gares"
    id: Mapped[int] = mapped_column("id_gare", BigInteger, primary_key=True)
    nom: Mapped[str] = mapped_column(String(150), nullable=False); adresse: Mapped[str] = mapped_column(String(255), nullable=False); ville: Mapped[str] = mapped_column(String(100), nullable=False)
    region: Mapped[str | None] = mapped_column(String(100)); telephone: Mapped[str | None] = mapped_column(String(30)); email: Mapped[str | None] = mapped_column(String(150)); description: Mapped[str | None] = mapped_column(Text)
    latitude: Mapped[float | None] = mapped_column(Numeric(10, 7)); longitude: Mapped[float | None] = mapped_column(Numeric(10, 7)); is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False); updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    quais = relationship("Quai", back_populates="gare", cascade="all, delete-orphan"); zones = relationship("Zone", back_populates="gare", cascade="all, delete-orphan"); cooperatives = relationship("GareCooperative", back_populates="gare", cascade="all, delete-orphan")

class Quai(Base):
    __tablename__ = "quais"; __table_args__ = (UniqueConstraint("id_gare", "numero"),)
    id: Mapped[int] = mapped_column("id_quai", BigInteger, primary_key=True); id_gare: Mapped[int] = mapped_column(ForeignKey("gares.id_gare", ondelete="CASCADE"), nullable=False); numero: Mapped[str] = mapped_column(String(50), nullable=False)
    nom: Mapped[str | None] = mapped_column(String(100)); description: Mapped[str | None] = mapped_column(Text); is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False); updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False); gare = relationship("Gare", back_populates="quais")

class Zone(Base):
    __tablename__ = "zones"
    id: Mapped[int] = mapped_column("id_zone", BigInteger, primary_key=True); id_gare: Mapped[int] = mapped_column(ForeignKey("gares.id_gare", ondelete="CASCADE"), nullable=False); nom: Mapped[str] = mapped_column(String(100), nullable=False)
    type_zone: Mapped[str | None] = mapped_column(String(50)); description: Mapped[str | None] = mapped_column(Text); is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False); updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False); gare = relationship("Gare", back_populates="zones"); emplacements = relationship("Emplacement", back_populates="zone", cascade="all, delete-orphan")

class Emplacement(Base):
    __tablename__ = "emplacements"; __table_args__ = (UniqueConstraint("id_zone", "code"),)
    id: Mapped[int] = mapped_column("id_emplacement", BigInteger, primary_key=True); id_zone: Mapped[int] = mapped_column(ForeignKey("zones.id_zone", ondelete="CASCADE"), nullable=False); code: Mapped[str] = mapped_column(String(50), nullable=False)
    nom: Mapped[str | None] = mapped_column(String(100)); type_emplacement: Mapped[str | None] = mapped_column(String(50)); description: Mapped[str | None] = mapped_column(Text); is_available: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False); is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False); updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False); zone = relationship("Zone", back_populates="emplacements")
