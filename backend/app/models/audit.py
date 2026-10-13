from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, Identity, Index, JSON, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class AuditLog(Base):
    """Immutable business audit trail (actor, action and before/after values)."""

    __tablename__ = "audit_logs"
    __table_args__ = (
        Index("idx_audit_logs_actor", "id_user"),
        Index("idx_audit_logs_entity", "entity_type", "entity_id"),
        Index("idx_audit_logs_created", "created_at"),
    )

    id: Mapped[int] = mapped_column("id_audit_log", BigInteger, Identity(always=True), primary_key=True)
    id_user: Mapped[int | None] = mapped_column(ForeignKey("users.id_user", ondelete="SET NULL"))
    action: Mapped[str] = mapped_column(String(80), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(80), nullable=False)
    entity_id: Mapped[str | None] = mapped_column(String(80))
    before_data: Mapped[dict | None] = mapped_column(JSON)
    after_data: Mapped[dict | None] = mapped_column(JSON)
    description: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    user = relationship("User")
