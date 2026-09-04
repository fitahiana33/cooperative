from datetime import datetime
from sqlalchemy import BigInteger, Boolean, DateTime, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base

class Marque(Base):
    __tablename__ = "marques"
    id: Mapped[int] = mapped_column("id_marque", BigInteger, primary_key=True)
    nom: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    modeles = relationship("Modele", back_populates="marque", passive_deletes=True)
