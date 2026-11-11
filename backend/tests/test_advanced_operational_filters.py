"""Cross-module filters must narrow records without bypassing user scopes."""

from sqlalchemy import select

from app.models import Billet, Depart, Reservation, ReservationPlace
from tests.helpers import API


def _sample(db):
    row = db.execute(
        select(Reservation, Depart)
        .join(Depart, Depart.id == Reservation.id_depart)
        .join(ReservationPlace, ReservationPlace.id_reservation == Reservation.id)
        .join(Billet, Billet.id_reservation_place == ReservationPlace.id)
        .where(Depart.id_gare.is_not(None))
        .limit(1)
    ).first()
    assert row is not None
    return row


def test_reservations_can_be_filtered_by_operational_dimensions(client, db, login):
    reservation, depart = _sample(db)
    response = client.get(
        f"{API}/reservations",
        headers=login("admin@cooperative.com"),
        params={
            "page_size": 100,
            "id_cooperative": depart.id_cooperative,
            "id_gare": depart.id_gare,
            "id_itineraire": depart.id_itineraire,
            "id_depart": depart.id,
            "date_from": depart.date_depart.isoformat(),
            "date_to": depart.date_depart.isoformat(),
        },
    )
    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["total"] >= 1
    assert {item["id_depart"] for item in payload["items"]} == {depart.id}
    assert reservation.id in {item["id"] for item in payload["items"]}


def test_tickets_can_be_filtered_by_operational_dimensions(client, db, login):
    _, depart = _sample(db)
    response = client.get(
        f"{API}/billets",
        headers=login("admin@cooperative.com"),
        params={
            "page_size": 100,
            "id_cooperative": depart.id_cooperative,
            "id_gare": depart.id_gare,
            "id_itineraire": depart.id_itineraire,
            "id_depart": depart.id,
            "date_from": depart.date_depart.isoformat(),
            "date_to": depart.date_depart.isoformat(),
        },
    )
    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["total"] >= 1
    assert {item["id_depart"] for item in payload["items"]} == {depart.id}
