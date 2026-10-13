"""Reservation lifecycle: hold period, passenger limits, pay-to-confirm, boarding."""

import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import select, update

from app.core.clock import local_now
from app.core.config import settings
from app.models import Depart, DepartStatus, Reservation
from tests.helpers import API, book, bookable_departure, free_place_ids, open_caisse_for, pay


def new_passenger(client) -> dict[str, str]:
    email = f"test-{uuid.uuid4().hex[:10]}@cooperative.com"
    password = "Passager123!"
    response = client.post(f"{API}/auth/register", json={
        "name": "Test", "first_name": "Passager", "email": email, "telephone": "+261 34 00 000 00", "password": password,
    })
    assert response.status_code in (200, 201), response.text
    token = client.post(f"{API}/auth/login", json={"email": email, "password": password}).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_hold_period_is_set_by_the_server(client, db):
    passenger = new_passenger(client)
    depart = bookable_departure(db)
    response = book(client, passenger, depart.id, free_place_ids(db, depart.id, 1), date_expiration="2099-01-01T00:00:00Z")
    assert response.status_code == 201, response.text
    expiration = datetime.fromisoformat(response.json()["date_expiration"])
    expected = datetime.now(timezone.utc) + timedelta(minutes=settings.reservation_hold_minutes)
    assert abs((expiration - expected).total_seconds()) < 60


def test_passenger_cannot_confirm_own_reservation(client, db):
    passenger = new_passenger(client)
    depart = bookable_departure(db)
    reservation = book(client, passenger, depart.id, free_place_ids(db, depart.id, 1)).json()
    response = client.post(f"{API}/reservations/{reservation['id']}/confirm", headers=passenger)
    assert response.status_code == 403


def test_passenger_pending_reservations_are_capped(client, db):
    passenger = new_passenger(client)
    depart = bookable_departure(db, min_free=settings.passenger_max_pending_reservations + 1)
    seats = free_place_ids(db, depart.id, settings.passenger_max_pending_reservations + 1)
    for seat in seats[:-1]:
        assert book(client, passenger, depart.id, [seat]).status_code == 201
    assert book(client, passenger, depart.id, [seats[-1]]).status_code == 409


def test_passenger_seats_per_booking_are_capped(client, db):
    passenger = new_passenger(client)
    count = settings.passenger_max_seats_per_reservation + 1
    depart = bookable_departure(db, min_free=count)
    assert book(client, passenger, depart.id, free_place_ids(db, depart.id, count)).status_code == 422


def test_paying_a_pending_reservation_issues_its_tickets(client, db, login):
    passenger = new_passenger(client)
    cashier = login("responsable.gare1@cooperative.com")
    depart = bookable_departure(db, min_free=2)
    reservation = book(client, passenger, depart.id, free_place_ids(db, depart.id, 2)).json()
    assert reservation["statut"] == "EN_ATTENTE"
    response = pay(client, cashier, reservation, open_caisse_for(db, depart).id)
    assert response.status_code in (200, 201), response.text
    paid = client.get(f"{API}/reservations/{reservation['id']}", headers=passenger).json()
    assert paid["statut"] == "PAYEE"
    assert all(place["billet"] and place["billet"]["statut"] == "VALIDE" for place in paid["places"])


def test_payment_refused_after_hold_period(client, db, login):
    passenger = new_passenger(client)
    cashier = login("responsable.gare1@cooperative.com")
    depart = bookable_departure(db)
    reservation = book(client, passenger, depart.id, free_place_ids(db, depart.id, 1)).json()
    db.execute(update(Reservation).where(Reservation.id == reservation["id"]).values(date_expiration=datetime.now(timezone.utc) - timedelta(minutes=1)))
    db.commit()
    response = pay(client, cashier, reservation, open_caisse_for(db, depart).id)
    assert response.status_code == 409
    assert client.get(f"{API}/reservations/{reservation['id']}", headers=passenger).json()["statut"] == "EXPIREE"


def test_every_passenger_of_a_reservation_can_board(client, db, login):
    """I-B04: the second ticket of a paid two-seat reservation used to be refused."""
    passenger = new_passenger(client)
    agent = login("responsable.gare1@cooperative.com")
    depart = bookable_departure(db, min_free=2)
    # Boarding happens on the day of the departure.
    db.execute(update(Depart).where(Depart.id == depart.id).values(date_depart=local_now().date(), heure_depart=(local_now() + timedelta(hours=1)).time().replace(microsecond=0)))
    db.commit()
    reservation = book(client, passenger, depart.id, free_place_ids(db, depart.id, 2)).json()
    assert pay(client, agent, reservation, open_caisse_for(db, depart).id).status_code in (200, 201)
    tickets = [place["billet"]["numero_billet"] for place in client.get(f"{API}/reservations/{reservation['id']}", headers=passenger).json()["places"]]

    first = client.post(f"{API}/embarquement/controle", headers=agent, json={"code": tickets[0], "id_depart": depart.id}).json()
    assert first["statut"] == "VALIDE", first
    assert client.get(f"{API}/reservations/{reservation['id']}", headers=passenger).json()["statut"] == "PAYEE"

    second = client.post(f"{API}/embarquement/controle", headers=agent, json={"code": tickets[1], "id_depart": depart.id}).json()
    assert second["statut"] == "VALIDE", second
    assert client.get(f"{API}/reservations/{reservation['id']}", headers=passenger).json()["statut"] == "EMBARQUEE"

    again = client.post(f"{API}/embarquement/controle", headers=agent, json={"code": tickets[0], "id_depart": depart.id}).json()
    assert again["statut"] == "REFUSE"


def test_booking_refused_once_departure_time_has_passed(client, db):
    """I-B06: a scheduled departure whose time is over no longer takes bookings."""
    passenger = new_passenger(client)
    depart = bookable_departure(db)
    past = local_now() - timedelta(minutes=30)
    db.execute(update(Depart).where(Depart.id == depart.id).values(date_depart=past.date(), heure_depart=past.time().replace(microsecond=0), statut=DepartStatus.PROGRAMME))
    db.commit()
    response = book(client, passenger, depart.id, free_place_ids(db, depart.id, 1))
    assert response.status_code == 422


def test_passenger_cannot_read_someone_elses_reservation(client, db, login):
    owner = new_passenger(client)
    other = new_passenger(client)
    depart = bookable_departure(db)
    reservation = book(client, owner, depart.id, free_place_ids(db, depart.id, 1)).json()
    assert client.get(f"{API}/reservations/{reservation['id']}", headers=other).status_code == 404
    db.rollback()
    assert db.scalar(select(Reservation.id_user).where(Reservation.id == reservation["id"])) is not None
