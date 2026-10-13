"""Seed keeps administrator changes; business dates follow the station's timezone."""

from datetime import date, datetime, time, timezone

from sqlalchemy import select

from app.core.clock import local_date, local_moment
from app.db.seed import seed_default_admin
from app.models import Permission, Role
from app.models.user import UserRole


def test_seed_keeps_a_deactivated_role(db):
    role = db.scalar(select(Role).where(Role.libelle == UserRole.CHAUFFEUR))
    role.is_active = False
    db.commit()
    try:
        seed_default_admin(db)
        db.expire_all()
        assert db.scalar(select(Role.is_active).where(Role.libelle == UserRole.CHAUFFEUR)) is False
    finally:
        role = db.scalar(select(Role).where(Role.libelle == UserRole.CHAUFFEUR))
        role.is_active = True
        db.commit()


def test_seed_keeps_a_removed_permission(db):
    role = db.scalar(select(Role).where(Role.libelle == UserRole.AGENT_GARE))
    permission = db.scalar(select(Permission).where(Permission.code == "TARIF_READ"))
    role.permissions.remove(permission)
    db.commit()
    try:
        seed_default_admin(db)
        db.expire_all()
        role = db.scalar(select(Role).where(Role.libelle == UserRole.AGENT_GARE))
        assert "TARIF_READ" not in {item.code for item in role.permissions}
    finally:
        role.permissions.append(db.scalar(select(Permission).where(Permission.code == "TARIF_READ")))
        db.commit()


def test_passengers_cannot_confirm_reservations(db):
    role = db.scalar(select(Role).where(Role.libelle == UserRole.PASSAGER))
    assert "RESERVATION_UPDATE" not in {item.code for item in role.permissions}


def test_local_date_uses_station_time():
    # 22:30 UTC on 8 October is already 9 October in Antananarivo (UTC+3).
    assert local_date(datetime(2026, 10, 8, 22, 30, tzinfo=timezone.utc)) == date(2026, 10, 9)
    assert local_date(datetime(2026, 10, 8, 20, 59, tzinfo=timezone.utc)) == date(2026, 10, 8)


def test_local_moment_is_timezone_aware():
    moment = local_moment(date(2026, 10, 9), time(1, 30))
    assert moment.astimezone(timezone.utc) == datetime(2026, 10, 8, 22, 30, tzinfo=timezone.utc)
