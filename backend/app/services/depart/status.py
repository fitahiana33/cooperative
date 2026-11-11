"""Automatic, conservative state transitions for operational departures."""

from datetime import timedelta

from sqlalchemy import and_, or_, update
from sqlalchemy.orm import Session

from app.core.clock import local_now
from app.models.depart import Depart, DepartStatus


def mark_overdue_departures(db: Session, *, commit: bool = True) -> int:
    """Flag a missed scheduled departure without pretending it actually left.

    ``PARTI`` is an operational fact recorded by the driver/staff pointage.  If
    its planned time has elapsed with no pointage, the honest status is
    ``RETARDE`` so an operator can reschedule, cancel or point it as departed.
    """
    now = local_now()
    overdue = or_(
        Depart.date_depart < now.date(),
        and_(
            Depart.date_depart == now.date(),
            Depart.heure_depart <= now.time().replace(tzinfo=None),
        ),
    )
    result = db.execute(
        update(Depart)
        .where(
            Depart.statut.in_([DepartStatus.PROGRAMME, DepartStatus.EMBARQUEMENT]),
            overdue,
        )
        .values(statut=DepartStatus.RETARDE)
    )
    changed = result.rowcount or 0
    if changed and commit:
        db.commit()
    return changed


def booking_deadline(depart: Depart, close_minutes: int):
    """Return the station-local deadline for creating a new reservation."""
    from app.core.clock import local_moment

    return local_moment(depart.date_depart, depart.heure_depart) - timedelta(
        minutes=close_minutes
    )


def booking_is_open(depart: Depart, close_minutes: int) -> bool:
    """A delay needs a new planned time before sales can reopen."""
    return (
        depart.statut == DepartStatus.PROGRAMME
        and local_now() < booking_deadline(depart, close_minutes)
    )
