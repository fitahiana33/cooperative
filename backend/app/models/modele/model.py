from datetime import datetime
from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base

class Modele(Base):
    __tablename__ = "modeles"
    __table_args__ = (UniqueConstraint("id_marque", "nom", name="uq_modele_marque_nom"),)
    id: Mapped[int] = mapped_column("id_modele", BigInteger, primary_key=True)
    id_marque: Mapped[int] = mapped_column(ForeignKey("marques.id_marque", ondelete="RESTRICT"), nullable=False)
    nom: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    marque = relationship("Marque", back_populates="modeles")
    vehicules = relationship("Vehicule", back_populates="modele")
