from datetime import datetime
from decimal import Decimal
from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, Numeric, func
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base


class BookingSettings(Base):
    __tablename__ = "booking_settings"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    deposit_percentage: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    booking_close_minutes: Mapped[int] = mapped_column(
        Integer, nullable=False, default=10, server_default="10"
    )
    updated_by: Mapped[int | None] = mapped_column(
        ForeignKey("users.id_user", ondelete="SET NULL")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    __table_args__ = (
        CheckConstraint("id = 1", name="ck_booking_settings_singleton"),
        CheckConstraint(
            "deposit_percentage > 0 AND deposit_percentage <= 100",
            name="ck_booking_settings_percentage",
        ),
        CheckConstraint(
            "booking_close_minutes >= 0 AND booking_close_minutes <= 180",
            name="ck_booking_settings_close_minutes",
        ),
    )
