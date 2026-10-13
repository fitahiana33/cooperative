"""Scheduled maintenance: reservation expiry, finished departures, assignments, tokens."""

from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select, update

from app.core.clock import local_today
from app.jobs.maintenance import close_finished_departures, expire_reservations, purge_revoked_tokens, run_with_lock
from app.models import (
    Billet, BilletStatus, Depart, DepartPlace, DepartPlaceStatus, DepartStatus, Reservation, ReservationPlace,
    ReservationStatus, RevokedToken, VehiculeChauffeur,
)
from app.services.chauffeur.service import ChauffeurService


def test_unpaid_reservations_expire_and_free_their_seats(db):
    reservation = db.scalar(select(Reservation).where(Reservation.statut == ReservationStatus.EN_ATTENTE).limit(1))
    place_ids = [place.id_depart_place for place in reservation.places]
    reservation.date_expiration = datetime.now(timezone.utc) - timedelta(minutes=1)
    db.commit()

    assert expire_reservations(db) >= 1
    db.expire_all()
    assert db.get(Reservation, reservation.id).statut == ReservationStatus.EXPIREE
    statuses = set(db.scalars(select(DepartPlace.statut).where(DepartPlace.id.in_(place_ids))))
    assert statuses == {DepartPlaceStatus.DISPONIBLE}


def test_reservations_still_within_their_hold_period_are_kept(db):
    reservation = db.scalar(select(Reservation).where(Reservation.statut == ReservationStatus.EN_ATTENTE, Reservation.date_expiration > datetime.now(timezone.utc)).limit(1))
    expire_reservations(db)
    db.expire_all()
    assert db.get(Reservation, reservation.id).statut == ReservationStatus.EN_ATTENTE


def test_finished_departures_close_reservations_and_expire_unused_tickets(db):
    depart = db.scalar(select(Depart).where(Depart.statut == DepartStatus.PROGRAMME, Depart.date_depart > local_today()).order_by(Depart.id))
    paid = db.scalar(select(Reservation).where(Reservation.id_depart == depart.id, Reservation.statut == ReservationStatus.PAYEE).limit(1))
    if paid is None:
        paid = db.scalar(select(Reservation).join(Depart).where(Reservation.statut == ReservationStatus.PAYEE, Depart.statut == DepartStatus.PROGRAMME).limit(1))
        depart = db.get(Depart, paid.id_depart)
    depart.statut = DepartStatus.TERMINE
    db.commit()

    assert close_finished_departures(db) >= 1
    db.expire_all()
    assert db.get(Reservation, paid.id).statut == ReservationStatus.TERMINEE
    ticket_statuses = set(db.scalars(
        select(Billet.statut).join(ReservationPlace, ReservationPlace.id == Billet.id_reservation_place).where(ReservationPlace.id_reservation == paid.id)
    ))
    assert ticket_statuses == {BilletStatus.EXPIRE}


def test_assignments_past_their_end_date_are_closed(db):
    assignment = db.scalar(select(VehiculeChauffeur).where(VehiculeChauffeur.is_active.is_(True)).limit(1))
    db.execute(update(VehiculeChauffeur).where(
        VehiculeChauffeur.id_vehicule == assignment.id_vehicule, VehiculeChauffeur.id_chauffeur == assignment.id_chauffeur,
    ).values(date_fin=local_today() - timedelta(days=1)))
    db.commit()

    ChauffeurService(db).synchronize()
    db.expire_all()
    still_active = db.scalar(select(func.count()).select_from(VehiculeChauffeur).where(
        VehiculeChauffeur.id_vehicule == assignment.id_vehicule, VehiculeChauffeur.id_chauffeur == assignment.id_chauffeur, VehiculeChauffeur.is_active.is_(True),
    ))
    assert still_active == 0


def test_expired_revoked_tokens_are_purged(db):
    db.add(RevokedToken(jti="purge-me", token_type="refresh", expires_at=datetime.now(timezone.utc) - timedelta(days=3)))
    db.add(RevokedToken(jti="keep-me", token_type="refresh", expires_at=datetime.now(timezone.utc) + timedelta(days=3)))
    db.commit()
    purge_revoked_tokens(db)
    assert db.get(RevokedToken, "purge-me") is None
    assert db.get(RevokedToken, "keep-me") is not None


def test_maintenance_runs_once_at_a_time(db):
    from app.db.session import SessionLocal

    with SessionLocal() as other:
        assert other.scalar(select(func.pg_try_advisory_lock(640_217)))
        try:
            assert run_with_lock(db) is None
        finally:
            other.execute(select(func.pg_advisory_unlock(640_217)))
            other.commit()
    assert run_with_lock(db) is not None
