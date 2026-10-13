"""API used by the passenger app: trip search, seat layout, profile, notifications."""

from datetime import timedelta

from sqlalchemy import select, update

from app.core.clock import local_now, local_today
from app.models import Depart, DepartStatus, Destination, Itineraire, Notification
from tests.helpers import API
from tests.test_reservations import new_passenger


def test_search_by_origin_destination_and_date(client, db):
    passenger = new_passenger(client)
    origin = db.scalar(select(Destination.id).where(Destination.nom == "Antananarivo"))
    arrival = db.scalar(select(Destination.id).where(Destination.nom == "Toamasina"))
    # Vehicles have random rest days in the seed: pick a day that has this trip.
    day = db.scalar(
        select(Depart.date_depart).join(Itineraire, Itineraire.id == Depart.id_itineraire)
        .where(Itineraire.id_destination_depart == origin, Itineraire.id_destination_arrivee == arrival, Depart.date_depart > local_today())
        .order_by(Depart.date_depart).limit(1)
    )
    response = client.get(f"{API}/departs", headers=passenger, params={
        "id_destination_depart": origin, "id_destination_arrivee": arrival, "date_from": day.isoformat(), "date_to": day.isoformat(), "page_size": 50,
    })
    assert response.status_code == 200
    items = response.json()["items"]
    assert items, "expected departures Antananarivo → Toamasina"
    assert all(item["itineraire"]["destination_depart"]["nom"] == "Antananarivo" and item["itineraire"]["destination_arrivee"]["nom"] == "Toamasina" for item in items)
    assert all(item["date_depart"] == day.isoformat() for item in items)


def test_free_text_search_matches_city_names(client, login):
    """I-B24: searching "Toamasina" used to return nothing (only the status was searched)."""
    response = client.get(f"{API}/departs", headers=login("responsable.gare1@cooperative.com"), params={"search": "Toamasina", "page_size": 100})
    items = response.json()["items"]
    assert items
    assert all("Toamasina" in (item["itineraire"]["destination_depart"]["nom"], item["itineraire"]["destination_arrivee"]["nom"]) for item in items)


def test_reservable_filter_hides_closed_full_and_past_departures(client, db):
    passenger = new_passenger(client)
    full = db.scalar(select(Depart).where(Depart.statut == DepartStatus.PROGRAMME, Depart.date_depart > local_today()).order_by(Depart.id))
    full.places_reservees = full.nombre_places
    past = local_now() - timedelta(hours=1)
    gone = db.scalar(select(Depart).where(Depart.statut == DepartStatus.PROGRAMME, Depart.id != full.id, Depart.date_depart > local_today()).order_by(Depart.id.desc()))
    db.execute(update(Depart).where(Depart.id == gone.id).values(date_depart=past.date(), heure_depart=past.time().replace(microsecond=0)))
    db.commit()
    items = client.get(f"{API}/departs", headers=passenger, params={"reservable": True, "page_size": 100, "date_from": (local_today() - timedelta(days=1)).isoformat()}).json()["items"]
    ids = {item["id"] for item in items}
    assert full.id not in ids and gone.id not in ids
    assert all(item["statut"] in {"PROGRAMME", "EMBARQUEMENT", "RETARDE"} and item["places_disponibles"] > 0 for item in items)


def test_departure_exposes_seat_layout(client, login):
    item = client.get(f"{API}/departs?page_size=1", headers=login("passager04@cooperative.com")).json()["items"][0]
    assert {"places_avant", "places_par_rangee"} <= set(item["vehicule"])


def test_passenger_updates_own_profile(client):
    passenger = new_passenger(client)
    response = client.put(f"{API}/users/me", headers=passenger, json={"telephone": "+261 34 55 555 55", "address": "Lot II A Analakely"})
    assert response.status_code == 200, response.text
    assert response.json()["telephone"] == "+261 34 55 555 55"
    assert client.get(f"{API}/auth/me", headers=passenger).json()["address"] == "Lot II A Analakely"


def test_profile_update_cannot_change_role_or_email(client):
    passenger = new_passenger(client)
    before = client.get(f"{API}/auth/me", headers=passenger).json()
    client.put(f"{API}/users/me", headers=passenger, json={"email": "hijack@cooperative.com", "role": "admin", "is_active": False})
    after = client.get(f"{API}/auth/me", headers=passenger).json()
    assert after["email"] == before["email"] and after["role"] == before["role"] and after["is_active"] is True


def test_password_change_requires_current_password(client):
    passenger = new_passenger(client)
    assert client.post(f"{API}/users/me/password", headers=passenger, json={"current_password": "wrong", "new_password": "Nouveau123"}).status_code == 403
    assert client.post(f"{API}/users/me/password", headers=passenger, json={"current_password": "Passager123!", "new_password": "Nouveau123"}).status_code == 204
    # The session used for the change is closed like every other one.
    assert client.get(f"{API}/auth/me", headers=passenger).status_code == 401


def test_mark_all_notifications_read(client, db, login):
    headers = login("passager06@cooperative.com")
    unread_before = client.get(f"{API}/notifications?unread_only=true", headers=headers).json()["total"]
    assert unread_before > 0
    assert client.patch(f"{API}/notifications/read-all", headers=headers).json()["updated"] == unread_before
    assert client.get(f"{API}/notifications?unread_only=true", headers=headers).json()["total"] == 0
    assert db.scalar(select(Notification.id).limit(1)) is not None
