from datetime import datetime
from enum import StrEnum

from sqlalchemy import BigInteger, Boolean, CheckConstraint, DateTime, ForeignKey, Identity, Index, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class NotificationType(StrEnum):
    CONFIRMATION_RESERVATION = "CONFIRMATION_RESERVATION"
    CONFIRMATION_PAIEMENT = "CONFIRMATION_PAIEMENT"
    RAPPEL_DEPART = "RAPPEL_DEPART"
    RETARD = "RETARD"
    ANNULATION = "ANNULATION"
    MODIFICATION_HORAIRE = "MODIFICATION_HORAIRE"
    CONFIRMATION_EMBARQUEMENT = "CONFIRMATION_EMBARQUEMENT"
    EXPIRATION_DOCUMENT = "EXPIRATION_DOCUMENT"
    MODIFICATION_RESERVATION = "MODIFICATION_RESERVATION"


class NotificationChannel(StrEnum):
    IN_APP = "IN_APP"
    PUSH = "PUSH"
    SMS = "SMS"
    EMAIL = "EMAIL"


class Notification(Base):
    __tablename__ = "notifications"
    __table_args__ = (
        CheckConstraint("canal IN ('IN_APP', 'PUSH', 'SMS', 'EMAIL')", name="ck_notification_canal"),
        CheckConstraint("type_notification IN ('CONFIRMATION_RESERVATION', 'CONFIRMATION_PAIEMENT', 'RAPPEL_DEPART', 'RETARD', 'ANNULATION', 'MODIFICATION_HORAIRE', 'CONFIRMATION_EMBARQUEMENT', 'EXPIRATION_DOCUMENT', 'MODIFICATION_RESERVATION')", name="ck_notification_type"),
        Index("idx_notifications_user", "id_user"),
        Index("idx_notifications_type", "type_notification"),
        Index("idx_notifications_lue", "est_lue"),
        Index("idx_notifications_date_envoi", "date_envoi"),
        Index("idx_notifications_delivery", "delivery_status", "next_attempt_at"),
    )

    id: Mapped[int] = mapped_column("id_notification", BigInteger, Identity(always=True), primary_key=True)
    id_user: Mapped[int] = mapped_column(ForeignKey("users.id_user", ondelete="CASCADE"), nullable=False)
    type_notification: Mapped[str] = mapped_column(String(50), nullable=False)
    titre: Mapped[str] = mapped_column(String(150), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    id_reservation: Mapped[int | None] = mapped_column(ForeignKey("reservations.id_reservation", ondelete="CASCADE"))
    id_depart: Mapped[int | None] = mapped_column(ForeignKey("departs.id_depart", ondelete="CASCADE"))
    canal: Mapped[str] = mapped_column(String(20), default=NotificationChannel.IN_APP, server_default=NotificationChannel.IN_APP, nullable=False)
    est_lue: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false", nullable=False)
    delivery_status: Mapped[str] = mapped_column(String(20), default="IN_APP", server_default="IN_APP", nullable=False)
    delivery_attempts: Mapped[int] = mapped_column(Integer, default=0, server_default="0", nullable=False)
    next_attempt_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    delivery_error: Mapped[str | None] = mapped_column(String(255))
    date_envoi: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    date_lecture: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    user = relationship("User")

