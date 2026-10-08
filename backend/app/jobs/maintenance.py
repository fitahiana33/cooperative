"""Periodic maintenance that keeps business data current without user action.

Run every minute by the in-process scheduler (``app.jobs.scheduler``) or once
from the command line (``python -m app.jobs.maintenance``), e.g. from cron.
"""

import logging
from datetime import timedelta

from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from app.core.clock import utc_now
from app.models.authentication import RevokedToken
from app.models.billet import Billet, BilletStatus
from app.models.depart import Depart, DepartStatus
from app.models.reservation import Reservation, ReservationPlace, ReservationStatus
from app.services.chauffeur.service import ChauffeurService
from app.services.tarif.service import activate_scheduled_tarifs

logger = logging.getLogger("cooperative.jobs")

# Arbitrary constant shared by every API process: only one runs the job at a time.
MAINTENANCE_LOCK_ID = 640_217


def expire_reservations(db: Session) -> int:
    """Expire unpaid reservations whose hold period is over; the trigger frees their seats."""
    expired_ids = list(db.scalars(
        update(Reservation)
        .where(Reservation.statut == ReservationStatus.EN_ATTENTE, Reservation.date_expiration <= utc_now())
        .values(statut=ReservationStatus.EXPIREE, updated_at=utc_now())
        .returning(Reservation.id)
    ))
    if expired_ids:
        db.execute(
            update(Billet)
            .where(Billet.statut == BilletStatus.VALIDE, Billet.id_reservation_place.in_(
                select(ReservationPlace.id).where(ReservationPlace.id_reservation.in_(expired_ids))
            ))
            .values(statut=BilletStatus.ANNULE, updated_at=utc_now())
        )
    db.commit()
    return len(expired_ids)


def close_finished_departures(db: Session) -> int:
    """Close the reservations of finished departures; unused tickets expire (no-shows)."""
    finished = select(Depart.id).where(Depart.statut == DepartStatus.TERMINE)
    reservation_ids = select(Reservation.id).where(
        Reservation.id_depart.in_(finished),
        Reservation.statut.in_([ReservationStatus.CONFIRMEE, ReservationStatus.PAYEE, ReservationStatus.EMBARQUEE]),
    )
    db.execute(
        update(Billet)
        .where(Billet.statut == BilletStatus.VALIDE, Billet.id_reservation_place.in_(
            select(ReservationPlace.id).where(ReservationPlace.id_reservation.in_(reservation_ids))
        ))
        .values(statut=BilletStatus.EXPIRE, updated_at=utc_now())
    )
    closed = db.execute(
        update(Reservation)
        .where(Reservation.id.in_(reservation_ids))
        .values(statut=ReservationStatus.TERMINEE, updated_at=utc_now())
    ).rowcount or 0
    db.commit()
    return closed


def purge_revoked_tokens(db: Session) -> int:
    """Revoked tokens are useless once they would have expired anyway."""
    deleted = db.execute(
        RevokedToken.__table__.delete().where(RevokedToken.expires_at < utc_now() - timedelta(days=1))
    ).rowcount or 0
    db.commit()
    return deleted


def run_maintenance(db: Session) -> dict[str, int]:
    result = {
        "reservations_expirees": expire_reservations(db),
        "reservations_terminees": close_finished_departures(db),
        "jetons_purges": purge_revoked_tokens(db),
        "tarifs_actives": activate_scheduled_tarifs(db),
    }
    ChauffeurService(db).synchronize()
    return result


def run_with_lock(db: Session) -> dict[str, int] | None:
    """Run the maintenance unless another process is already running it."""
    acquired = db.scalar(select(func.pg_try_advisory_lock(MAINTENANCE_LOCK_ID)))
    if not acquired:
        return None
    try:
        return run_maintenance(db)
    finally:
        db.execute(select(func.pg_advisory_unlock(MAINTENANCE_LOCK_ID)))
        db.commit()


if __name__ == "__main__":
    from app.db.session import SessionLocal

    logging.basicConfig(level=logging.INFO)
    with SessionLocal() as session:
        print(run_with_lock(session))
