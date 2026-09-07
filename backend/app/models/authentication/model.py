from datetime import datetime

from sqlalchemy import DateTime, Index, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class RevokedToken(Base):
    __tablename__ = "revoked_tokens"
    __table_args__ = (Index("idx_revoked_tokens_expires_at", "expires_at"),)

    jti: Mapped[str] = mapped_column(String(64), primary_key=True)
    token_type: Mapped[str] = mapped_column(String(20), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
