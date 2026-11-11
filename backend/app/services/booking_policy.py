"""Authoritative booking policy shared by public, web and native clients."""

from decimal import Decimal, ROUND_CEILING
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.booking_settings import BookingSettings
from app.services.audit import AuditService


def minimum_deposit(total: Decimal, *, rate=None, floor=None) -> Decimal:
    total = Decimal(total)
    rate = Decimal(str(settings.deposit_rate)) if rate is None else Decimal(str(rate))
    floor = (
        Decimal(settings.minimum_deposit_amount)
        if floor is None
        else Decimal(str(floor))
    )
    return min(
        total, max(floor, (total * rate).quantize(Decimal("1"), rounding=ROUND_CEILING))
    )


def booking_policy(db: Session | None = None) -> dict:
    configuration = db.get(BookingSettings, 1) if db is not None else None
    rate = (
        configuration.deposit_percentage / Decimal(100)
        if configuration
        else Decimal(str(settings.deposit_rate))
    )
    close_minutes = (
        configuration.booking_close_minutes
        if configuration
        else settings.booking_close_minutes
    )
    return {
        "max_seats": settings.passenger_max_seats_per_reservation,
        "max_pending": settings.passenger_max_pending_reservations,
        "hold_minutes": settings.reservation_hold_minutes,
        "cancellation_deadline_minutes": settings.cancellation_deadline_minutes,
        "booking_close_minutes": close_minutes,
        "deposit_rate": float(rate),
        "minimum_deposit_amount": settings.minimum_deposit_amount,
        "online_payment_enabled": settings.online_payment_enabled
        and settings.payment_provider.lower() == "papi",
        "boarding_requires_full_payment": settings.boarding_requires_full_payment,
    }


class BookingSettingsService:
    def __init__(self, db: Session):
        self.db = db

    def read(self) -> dict:
        policy = booking_policy(self.db)
        row = self.db.get(BookingSettings, 1)
        return {
            "deposit_percentage": round(policy["deposit_rate"] * 100, 2),
            "minimum_deposit_amount": policy["minimum_deposit_amount"],
            "booking_close_minutes": policy["booking_close_minutes"],
            "updated_at": row.updated_at if row else None,
        }

    def update(
        self, percentage: Decimal, close_minutes: int | None = None, *, user_id: int
    ) -> dict:
        # Serialize even the first update, when the singleton does not exist yet.
        self.db.execute(select(func.pg_advisory_xact_lock(7420042)))
        before = self.read()
        close_minutes = (
            before["booking_close_minutes"]
            if close_minutes is None
            else close_minutes
        )
        row = self.db.get(BookingSettings, 1)
        if row is None:
            row = BookingSettings(
                id=1,
                deposit_percentage=percentage,
                booking_close_minutes=close_minutes,
                updated_by=user_id,
            )
            self.db.add(row)
        else:
            row.deposit_percentage = percentage
            row.booking_close_minutes = close_minutes
            row.updated_by = user_id
        AuditService(self.db).record(
            user_id=user_id,
            action="BOOKING_SETTINGS_UPDATE",
            entity_type="booking_settings",
            entity_id=1,
            before={
                "deposit_percentage": before["deposit_percentage"],
                "booking_close_minutes": before["booking_close_minutes"],
            },
            after={
                "deposit_percentage": percentage,
                "booking_close_minutes": close_minutes,
            },
        )
        self.db.commit()
        self.db.refresh(row)
        return self.read()
