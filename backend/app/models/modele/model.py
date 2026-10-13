from datetime import datetime
from sqlalchemy import BigInteger, Integer, Boolean, DateTime, ForeignKey, Index, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base

class Modele(Base):
    __tablename__ = "modeles"
    __table_args__ = (UniqueConstraint("id_marque", "nom", name="uq_modele_marque_nom"), Index("idx_modeles_marque", "id_marque"))
    id: Mapped[int] = mapped_column("id_modele", BigInteger, primary_key=True)
    id_marque: Mapped[int] = mapped_column(ForeignKey("marques.id_marque", ondelete="RESTRICT"), nullable=False)
    nom: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    # Seat map: seats beside the driver, then rows of `places_par_rangee` with a middle aisle.
    places_avant: Mapped[int] = mapped_column(Integer, default=2, server_default="2", nullable=False)
    places_par_rangee: Mapped[int] = mapped_column(Integer, default=4, server_default="4", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    marque = relationship("Marque", back_populates="modeles")
    vehicules = relationship("Vehicule", back_populates="modele", passive_deletes=True)
