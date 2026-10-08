"""Single source of "now" and "today" for business rules.

The server runs in UTC while the station operates in local time
(Madagascar, UTC+3). Calendar dates (departure dates, "today" on the
dashboard, boarding checks) must be computed in the configured local
timezone, otherwise everything between 00:00 and 03:00 lands on the
previous day.
"""

from datetime import date, datetime, time, timezone
from functools import lru_cache
from zoneinfo import ZoneInfo

from app.core.config import settings


@lru_cache
def local_timezone() -> ZoneInfo:
    return ZoneInfo(settings.timezone)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def local_now() -> datetime:
    return datetime.now(local_timezone())


def local_today() -> date:
    return local_now().date()


def local_date(moment: datetime) -> date:
    """Calendar date of an instant, as seen at the station."""
    return moment.astimezone(local_timezone()).date()


def local_moment(day: date, at: time) -> datetime:
    """Aware datetime for a local calendar date and wall-clock time (e.g. a departure)."""
    return datetime.combine(day, at, local_timezone())
