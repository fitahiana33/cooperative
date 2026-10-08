"""Departure scheduling, status notifications, boarding tied to a departure, fares."""

from datetime import timedelta

from sqlalchemy import select, update

from app.core.clock import local_now, local_today
from app.models import Depart, DepartStatus, Notification, Tarif, VehiculeChauffeur, VehiculeDocument
from app.services.tarif.service import activate_scheduled_tarifs
from tests.helpers import API, book, bookable_departure, free_place_ids, open_caisse_for, pay
from tests.test_reservations import new_passenger

MANAGER = "responsable.gare1@cooperative.com"


def schedule_payload(depart: Depart, *, day, at) -> dict:
    return {
        "id_itineraire": depart.id_itineraire, "id_cooperative": depart.id_cooperative,
        "id_vehicule": depart.id_vehicule, "id_chauffeur": depart.id_chauffeur, "id_tarif": depart.id_tarif,
        "date_depart": day.isoformat(), "heure_depart": at.strftime("%H:%M:%S"),
    }


def test_vehicle_cannot_be_scheduled_during_its_own_trip(client, db, login):
    """I-B15: the old check only refused the exact same hour."""
    depart = bookable_departure(db)
    five_minutes_later = (local_now().replace(hour=depart.heure_depart.hour, minute=depart.heure_depart.minute) + timedelta(minutes=5)).time()
    response = client.post(f"{API}/departs", headers=login(MANAGER), json=schedule_payload(depart, day=depart.date_depart, at=five_minutes_later))
    assert response.status_code == 409, response.text


def test_departure_refused_when_insurance_expires_before_it(client, db, login):
    depart = bookable_departure(db, days_ahead=4)
    document = VehiculeDocument(id_vehicule=depart.id_vehicule, type_document="ASSURANCE", numero_document="TEST-EXP",
                                date_delivrance=local_today() - timedelta(days=300), date_expiration=local_today() + timedelta(days=1))
    db.add(document)
    db.commit()
    try:
        target = local_today() + timedelta(days=6)
        response = client.post(f"{API}/departs", headers=login(MANAGER), json=schedule_payload(depart, day=target, at=depart.heure_depart))
        assert response.status_code == 422
        assert "assurance" in response.json()["detail"].lower()
    finally:
        db.delete(document)
        db.commit()


def test_delay_notifies_passengers(client, db, login):
    passenger = new_passenger(client)
    depart = bookable_departure(db)
    reservation = book(client, passenger, depart.id, free_place_ids(db, depart.id, 1)).json()
    response = client.patch(f"{API}/departs/{depart.id}/status", headers=login(MANAGER), json={"statut": "RETARDE"})
    assert response.status_code == 200, response.text
    assert db.scalar(select(Notification.id).where(Notification.id_reservation == reservation["id"], Notification.type_notification == "RETARD")) is not None


def test_schedule_change_notifies_passengers(client, db, login):
    passenger = new_passenger(client)
    depart = bookable_departure(db)
    reservation = book(client, passenger, depart.id, free_place_ids(db, depart.id, 1)).json()
    later = (local_now().replace(hour=depart.heure_depart.hour, minute=depart.heure_depart.minute) + timedelta(minutes=1)).time().replace(second=0, microsecond=0)
    response = client.put(f"{API}/departs/{depart.id}", headers=login(MANAGER), json={"heure_depart": later.strftime("%H:%M:%S")})
    assert response.status_code == 200, response.text
    assert db.scalar(select(Notification.id).where(Notification.id_reservation == reservation["id"], Notification.type_notification == "MODIFICATION_HORAIRE")) is not None


def test_reducing_seats_below_reserved_ones_is_a_clear_refusal(client, db, login):
    depart = bookable_departure(db)
    response = client.put(f"{API}/departs/{depart.id}", headers=login(MANAGER), json={"nombre_places": 1})
    assert response.status_code in (409, 422), response.text


def test_boarding_refuses_ticket_of_another_departure(client, db, login):
    """I-B09: only the date used to be checked."""
    agent = login(MANAGER)
    passenger = new_passenger(client)
    depart = bookable_departure(db)
    db.execute(update(Depart).where(Depart.id == depart.id).values(date_depart=local_today(), heure_depart=(local_now() + timedelta(hours=2)).time().replace(microsecond=0)))
    db.commit()
    reservation = book(client, passenger, depart.id, free_place_ids(db, depart.id, 1)).json()
    assert pay(client, agent, reservation, open_caisse_for(db, depart).id).status_code in (200, 201)
    ticket = client.get(f"{API}/reservations/{reservation['id']}", headers=passenger).json()["places"][0]["billet"]["numero_billet"]
    other = db.scalar(select(Depart.id).where(Depart.id != depart.id, Depart.date_depart == local_today()).limit(1))

    wrong = client.post(f"{API}/embarquement/controle", headers=agent, json={"code": ticket, "id_depart": other}).json()
    assert wrong["statut"] == "REFUSE" and "autre départ" in wrong["motif_refus"]
    right = client.post(f"{API}/embarquement/controle", headers=agent, json={"code": ticket, "id_depart": depart.id}).json()
    assert right["statut"] == "VALIDE"

    passengers = client.get(f"{API}/departs/{depart.id}/passagers", headers=agent).json()
    row = next(item for item in passengers if item["billet"] == ticket)
    assert row["embarque"] is True


def test_future_fare_version_keeps_current_fare_until_its_start(client, db, login, admin_headers):
    """I-B26: the current fare used to be deactivated at once."""
    current = db.scalar(select(Tarif).where(Tarif.is_active.is_(True), Tarif.id_cooperative.is_(None)).order_by(Tarif.id))
    start = local_today() + timedelta(days=5)
    response = client.put(f"{API}/tarifs/{current.id}", headers=admin_headers, json={"prix": str(current.prix + 5000), "date_debut": start.isoformat()})
    assert response.status_code == 200, response.text
    version = response.json()
    assert version["is_active"] is False and version["activation_programmee"] is True
    db.expire_all()
    assert db.get(Tarif, current.id).is_active is True

    # On the start date the scheduler switches over and moves later departures to the new fare.
    db.execute(update(Tarif).where(Tarif.id == version["id"]).values(date_debut=local_today()))
    db.execute(update(Tarif).where(Tarif.id == current.id).values(date_fin=local_today() - timedelta(days=1)))
    db.commit()
    later = db.scalar(select(Depart).where(Depart.id_tarif == current.id, Depart.statut == DepartStatus.PROGRAMME, Depart.date_depart >= local_today()).limit(1))
    activate_scheduled_tarifs(db)
    db.expire_all()
    assert db.get(Tarif, version["id"]).is_active is True
    assert db.get(Tarif, current.id).is_active is False
    if later is not None:
        assert db.get(Depart, later.id).id_tarif == version["id"]


def test_driver_reads_own_profile_and_vehicle(client, db, login):
    """I-B16."""
    headers = login("chauffeur01@cooperative.com")
    profile = client.get(f"{API}/chauffeurs/me", headers=headers)
    assert profile.status_code == 200, profile.text
    vehicle_id = db.scalar(select(VehiculeChauffeur.id_vehicule).where(VehiculeChauffeur.id_chauffeur == profile.json()["id"], VehiculeChauffeur.is_active.is_(True)))
    assert client.get(f"{API}/vehicules/{vehicle_id}", headers=headers).status_code == 200


def test_passenger_filters_departures_by_cooperative(client, db, login):
    """I-B17."""
    cooperative_id = db.scalar(select(Depart.id_cooperative).limit(1))
    response = client.get(f"{API}/departs?id_cooperative={cooperative_id}&page_size=50", headers=login("passager03@cooperative.com"))
    assert response.status_code == 200
    assert {item["id_cooperative"] for item in response.json()["items"]} == {cooperative_id}


def test_boarding_requires_a_departure(client, login):
    response = client.post(f"{API}/embarquement/controle", headers=login(MANAGER), json={"code": "TKT-UNKNOWN"})
    assert response.status_code == 422
