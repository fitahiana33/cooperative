"""Operational regressions: inventory, deposits, callbacks and actual trip lifecycle."""

import hashlib
import hmac
import json
import time
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy import select, update

from app.core.config import settings
from app.models import Billet, Depart, DepartPlace, DepartPlaceStatus, DepartStatus, Paiement, PaiementStatus, Reservation, ReservationStatus
from app.services.reservation import ReservationService
from tests.helpers import API, book, bookable_departure, free_place_ids, open_caisse_for, pay
from tests.test_reservations import new_passenger
from tests.test_scopes import create_user, headers_for

CASHIER = "admin@cooperative.com"


def pending_booking(client, db, *, seats=1):
    passenger = new_passenger(client)
    # Keep this regression suite independent of the original tests' shared
    # day+2 inventory. Prefer other seeded days and never assume infinite seats.
    departure = None
    for days_ahead in range(3, 9):
        try:
            departure = bookable_departure(db, min_free=seats + 1, days_ahead=days_ahead)
            break
        except AssertionError:
            continue
    assert departure is not None, "Aucun départ disponible pour préparer le scénario de régression."
    response = book(client, passenger, departure.id, free_place_ids(db, departure.id, seats))
    assert response.status_code == 201, response.text
    return passenger, departure, response.json()


def pending_payment(db, reservation, *, amount=None):
    payment = Paiement(id_reservation=reservation["id"], montant=amount or Decimal(reservation["montant_total"]) / 4,
                       methode="MOBILE_MONEY", statut=PaiementStatus.EN_ATTENTE, fournisseur="papi",
                       notification_token="local-test-notification-token", reference_paiement=f"TEST-{uuid4().hex}",
                       cle_idempotence=f"TEST-{uuid4().hex}")
    db.add(payment)
    db.commit()
    return payment


def callback(client, monkeypatch, payment, *, status="SUCCESS", amount=None):
    monkeypatch.setattr(settings, "online_payment_enabled", True)
    monkeypatch.setattr(settings, "payment_provider", "papi")
    monkeypatch.setattr(settings, "papi_signing_secret", "local-test-signing-secret")
    payload = {"merchantPaymentReference": payment.reference_paiement, "notificationToken": payment.notification_token,
               "paymentStatus": status, "amount": str(payment.montant if amount is None else amount)}
    raw = json.dumps(payload).encode()
    stamp = str(int(time.time()))
    signature = hmac.new(settings.papi_signing_secret.encode(), stamp.encode() + b"." + raw, hashlib.sha256).hexdigest()
    return client.post(f"{API}/paiements/webhooks/papi", content=raw,
                       headers={"X-Papi-Signature": f"t={stamp},v1={signature}", "Content-Type": "application/json"})


def test_public_seat_map_endpoint_and_blocked_capacity(client, db, admin_headers):
    departure = bookable_departure(db)
    free = free_place_ids(db, departure.id, 1)[0]
    old_count = departure.places_disponibles
    assert client.patch(f"{API}/depart-places/{free}", headers=admin_headers, json={"statut": "BLOQUEE"}).status_code == 200
    try:
        response = client.get(f"{API}/reservations/public/departs/{departure.id}/places")
        assert response.status_code == 200
        assert next(p for p in response.json() if p["id"] == free)["statut"] == "BLOQUEE"
        offer = client.get(f"{API}/departs/public/{departure.id}").json()
        assert offer["places_disponibles"] == old_count - 1
        result = client.get(f"{API}/departs/public/programme", params={"date_from": departure.date_depart, "date_to": departure.date_depart, "passagers": old_count})
        assert departure.id not in {p["id"] for p in result.json()["items"]}
    finally:
        db.execute(update(DepartPlace).where(DepartPlace.id == free).values(statut="DISPONIBLE"))
        db.commit()


def test_expired_reservation_cannot_be_extended_by_editing(client, db):
    passenger, departure, reservation = pending_booking(client, db)
    db.execute(update(Reservation).where(Reservation.id == reservation["id"]).values(date_expiration=datetime.now(timezone.utc) - timedelta(minutes=1)))
    db.commit()
    response = client.patch(f"{API}/reservations/{reservation['id']}", headers=passenger, json={
        "id_depart": departure.id, "places": [{"id_depart_place": reservation["places"][0]["id_depart_place"], "nom_passager": "Voyageur"}],
    })
    assert response.status_code == 409
    db.expire_all()
    assert db.get(Reservation, reservation["id"]).statut == ReservationStatus.EXPIREE


def test_deposit_then_cash_balance_and_duplicate_settlement(client, db, login, monkeypatch):
    passenger, departure, reservation = pending_booking(client, db)
    payment = pending_payment(db, reservation)
    assert callback(client, monkeypatch, payment).status_code == 200
    cashier = login(CASHIER)
    balance = Decimal(reservation["montant_total"]) - payment.montant
    desk = open_caisse_for(db, departure)
    result = client.post(f"{API}/paiements", headers=cashier, json={"id_reservation": reservation["id"], "id_caisse": desk.id, "montant": str(balance)})
    assert result.status_code == 201, result.text
    duplicate = client.post(f"{API}/paiements", headers=cashier, json={"id_reservation": reservation["id"], "id_caisse": desk.id, "montant": str(balance)})
    assert duplicate.status_code == 409
    db.expire_all()
    receipts = list(db.scalars(select(Paiement).where(Paiement.id_reservation == reservation["id"], Paiement.statut == PaiementStatus.VALIDE)))
    assert sum(p.montant for p in receipts) == Decimal(reservation["montant_total"])
    assert len(receipts) == 2


@pytest.mark.parametrize("terminal", ["EXPIREE", "ANNULEE"])
def test_late_callback_does_not_reclaim_resold_seat(client, db, login, monkeypatch, terminal):
    _, departure, reservation = pending_booking(client, db)
    payment = pending_payment(db, reservation)
    db.execute(update(Reservation).where(Reservation.id == reservation["id"]).values(statut=terminal))
    db.commit()
    seat = reservation["places"][0]["id_depart_place"]
    other = new_passenger(client)
    replacement = book(client, other, departure.id, [seat])
    assert replacement.status_code == 201, replacement.text
    result = callback(client, monkeypatch, payment)
    assert result.status_code == 200, result.text
    db.expire_all()
    assert db.get(Reservation, reservation["id"]).statut == terminal
    assert db.get(Paiement, payment.id).remboursement_demande_le is not None
    assert db.get(DepartPlace, seat).statut == DepartPlaceStatus.RESERVEE
    # Refund of the former passenger must leave the new passenger's seat alone.
    response = client.post(f"{API}/paiements/{payment.id}/rembourser", headers=login(CASHIER), params={"id_caisse": open_caisse_for(db, departure).id})
    assert response.status_code == 200, response.text
    db.expire_all()
    assert db.get(DepartPlace, seat).statut == DepartPlaceStatus.RESERVEE
    assert db.get(Reservation, replacement.json()["id"]).statut == ReservationStatus.EN_ATTENTE
    assert callback(client, monkeypatch, payment).json()["idempotent"] is True


def test_callback_after_hold_deadline_records_refund_without_issuing_ticket(client, db, monkeypatch):
    _, _, reservation = pending_booking(client, db)
    payment = pending_payment(db, reservation)
    db.execute(update(Reservation).where(Reservation.id == reservation["id"]).values(date_expiration=datetime.now(timezone.utc) - timedelta(minutes=1)))
    db.commit()
    assert callback(client, monkeypatch, payment).status_code == 200
    db.expire_all()
    assert db.get(Reservation, reservation["id"]).statut == ReservationStatus.EXPIREE
    assert db.get(Paiement, payment.id).remboursement_demande_le is not None
    detail = ReservationService(db)._get(reservation["id"])
    assert all(p.billet is None for p in detail.places)


def test_bad_callback_amount_is_a_validation_error(client, db, monkeypatch):
    _, _, reservation = pending_booking(client, db)
    payment = pending_payment(db, reservation)
    assert callback(client, monkeypatch, payment, amount="not-a-number").status_code == 422
    assert callback(client, monkeypatch, payment, amount="NaN").status_code == 422


def test_existing_payment_blocks_reservation_repricing(client, db):
    passenger, departure, reservation = pending_booking(client, db)
    pending_payment(db, reservation)
    response = client.patch(f"{API}/reservations/{reservation['id']}", headers=passenger, json={
        "id_depart": departure.id, "places": [{"id_depart_place": reservation["places"][0]["id_depart_place"], "nom_passager": "Autre nom"}],
    })
    assert response.status_code == 409


def test_future_trip_cannot_be_marked_as_physically_departed(client, db, admin_headers):
    departure = bookable_departure(db)
    response = client.patch(f"{API}/departs/{departure.id}/status", headers=admin_headers, json={"statut": "PARTI"})
    assert response.status_code == 409


@pytest.mark.parametrize("resource", ["gare", "cooperative", "vehicle", "driver"])
def test_deactivation_requires_resolving_planned_departures(db, resource):
    from fastapi import HTTPException
    from app.services.gare.service import GareService
    from app.services.cooperative.service import CooperativeService
    from app.services.vehicule.service import VehiculeService
    from app.services.chauffeur.service import ChauffeurService
    departure = bookable_departure(db)
    actions = {
        "gare": lambda: GareService(db).toggle_gare(departure.id_gare),
        "cooperative": lambda: CooperativeService(db).toggle_cooperative(departure.id_cooperative),
        "vehicle": lambda: VehiculeService(db).toggle_vehicule(departure.id_vehicule),
        "driver": lambda: ChauffeurService(db).toggle_chauffeur(departure.id_chauffeur),
    }
    with pytest.raises(HTTPException) as error:
        actions[resource]()
    assert error.value.status_code == 409


def test_repair_can_restore_vehicle_state_and_availability_together(db):
    from app.models import Vehicule
    from app.services.vehicule.service import VehiculeService
    departure = bookable_departure(db)
    vehicle = Vehicule(id_modele=departure.vehicule.id_modele, id_cooperative=departure.id_cooperative,
                       immatriculation=f"TEST-{uuid4().hex[:8]}", nombre_places=12, etat="HORS_SERVICE", disponibilite=False)
    db.add(vehicle)
    db.commit()
    repaired = VehiculeService(db).update_vehicule(vehicle.id, etat="BON_ETAT", disponibilite=True)
    assert repaired.etat == "BON_ETAT" and repaired.disponibilite is True


def test_station_agent_cannot_handle_other_station_of_same_cooperative(client, db):
    from app.models import Gare, GareAgent, GareCooperative
    from app.models.user import UserRole
    _, departure, reservation = pending_booking(client, db)
    station = Gare(nom=f"Gare-test-{uuid4().hex[:8]}", ville="Antananarivo", adresse="Test local", is_active=True)
    db.add(station)
    db.flush()
    db.add(GareCooperative(id_gare=station.id, id_cooperative=departure.id_cooperative, is_active=True))
    agent = create_user(db, UserRole.AGENT_GARE)
    db.add(GareAgent(id_gare=station.id, id_user=agent.id))
    db.commit()
    headers = headers_for(client, agent)
    listing = client.get(f"{API}/reservations", headers=headers)
    assert listing.status_code == 200
    assert reservation["id"] not in {item["id"] for item in listing.json()["items"]}
    assert client.get(f"{API}/reservations/{reservation['id']}", headers=headers).status_code == 404
    assert client.get(f"{API}/departs/{departure.id}/passagers", headers=headers).status_code == 403
    response = book(client, headers, departure.id, free_place_ids(db, departure.id, 1))
    assert response.status_code == 403, response.text


def test_paid_amount_and_balance_are_exposed_to_passenger(client, db, monkeypatch):
    passenger, _, reservation = pending_booking(client, db)
    payment = pending_payment(db, reservation)
    assert callback(client, monkeypatch, payment).status_code == 200
    detail = client.get(f"{API}/reservations/{reservation['id']}", headers=passenger).json()
    assert Decimal(detail["montant_paye"]) == payment.montant
    assert Decimal(detail["montant_restant"]) == Decimal(detail["montant_total"]) - payment.montant


def test_partial_group_boarding_prevents_cancellation_and_refund(client, db, login, monkeypatch):
    from app.core.clock import local_now
    fixed = local_now().replace(hour=10, minute=0, second=0, microsecond=0)
    monkeypatch.setattr("app.services.reservation.service.local_now", lambda: fixed)
    _, departure, reservation = pending_booking(client, db, seats=2)
    db.execute(update(Depart).where(Depart.id == departure.id).values(date_depart=fixed.date(), heure_depart=fixed.time().replace(hour=12)))
    db.commit()
    cashier = login(CASHIER)
    desk = open_caisse_for(db, departure)
    assert pay(client, cashier, reservation, desk.id).status_code == 201
    detail = ReservationService(db)._get(reservation["id"])
    first_ticket = detail.places[0].billet.numero_billet
    assert client.post(f"{API}/embarquement/controle", headers=cashier, json={"code": first_ticket, "id_depart": departure.id}).json()["statut"] == "VALIDE"
    assert client.post(f"{API}/reservations/{reservation['id']}/cancel", headers=cashier).status_code == 409
    payment = db.scalar(select(Paiement).where(Paiement.id_reservation == reservation["id"], Paiement.statut == "VALIDE"))
    assert client.post(f"{API}/paiements/{payment.id}/rembourser", headers=cashier, params={"id_caisse": desk.id}).status_code == 409


def test_unsettled_deposit_cannot_board(client, db, login, monkeypatch):
    from app.core.clock import local_now
    fixed = local_now().replace(hour=10, minute=0, second=0, microsecond=0)
    monkeypatch.setattr("app.services.reservation.service.local_now", lambda: fixed)
    _, departure, reservation = pending_booking(client, db)
    payment = pending_payment(db, reservation)
    assert callback(client, monkeypatch, payment).status_code == 200
    db.execute(update(Depart).where(Depart.id == departure.id).values(date_depart=fixed.date(), heure_depart=fixed.time().replace(hour=12)))
    db.commit()
    detail = ReservationService(db)._get(reservation["id"])
    response = client.post(f"{API}/embarquement/controle", headers=login(CASHIER), json={"code": detail.places[0].billet.numero_billet, "id_depart": departure.id})
    assert response.status_code == 200
    assert response.json()["statut"] == "REFUSE" and "solde" in response.json()["motif_refus"]


def unused_driver_and_vehicle(db):
    from app.core.clock import local_today
    from app.models import Chauffeur, Vehicule
    from app.models.user import UserRole
    departure = bookable_departure(db)
    user = create_user(db, UserRole.CHAUFFEUR)
    driver = Chauffeur(id_user=user.id, id_cooperative=departure.id_cooperative, numero_permis=f"TEST-{uuid4().hex[:12]}",
                       categorie_permis="D", date_expiration_permis=local_today() + timedelta(days=365), disponibilite=True, is_active=True)
    vehicle = Vehicule(id_modele=departure.vehicule.id_modele, id_cooperative=departure.id_cooperative,
                       immatriculation=f"TEST-{uuid4().hex[:8]}", nombre_places=departure.nombre_places, disponibilite=True, is_active=True)
    db.add_all([driver, vehicle])
    db.commit()
    return driver, vehicle, departure


def test_future_assignment_can_be_used_to_plan_future_trip(db):
    from app.services.chauffeur.service import ChauffeurService
    from app.services.depart.service import DepartService
    driver, vehicle, base = unused_driver_and_vehicle(db)
    assignment = ChauffeurService(db).assign_to_vehicule(driver.id, vehicle.id, base.date_depart, base.date_depart + timedelta(days=5))
    assert assignment.is_active is False and assignment.is_cancelled is False
    departure = DepartService(db).create_depart(id_itineraire=base.id_itineraire, id_cooperative=base.id_cooperative, id_gare=base.id_gare,
                                              id_vehicule=vehicle.id, id_chauffeur=driver.id, id_tarif=base.id_tarif,
                                              date_depart=base.date_depart, heure_depart=base.heure_depart, nombre_places=base.nombre_places)
    assert departure.id_chauffeur == driver.id


def test_cancelled_future_assignment_is_not_reactivated_by_scheduler(db, monkeypatch):
    from app.core.clock import local_today
    from app.services.chauffeur.service import ChauffeurService
    driver, vehicle, _ = unused_driver_and_vehicle(db)
    start = local_today() + timedelta(days=3)
    service = ChauffeurService(db)
    service.assign_to_vehicule(driver.id, vehicle.id, start, start + timedelta(days=4))
    assignment = service.update_assignment(driver.id, vehicle.id, start, is_active=False)
    assert assignment.is_cancelled is True
    monkeypatch.setattr("app.services.chauffeur.service.local_today", lambda: start)
    service._synchronize_scheduled_assignments()
    db.refresh(assignment)
    assert assignment.is_active is False


def test_cash_refund_is_applied_once_under_concurrent_requests(client, db, login):
    from concurrent.futures import ThreadPoolExecutor
    _, departure, reservation = pending_booking(client, db)
    headers = login(CASHIER)
    desk = open_caisse_for(db, departure)
    paid = pay(client, headers, reservation, desk.id)
    assert paid.status_code == 201
    payment_id = paid.json()["id"]
    desk_id = desk.id
    db.rollback()
    def refund_once():
        return client.post(f"{API}/paiements/{payment_id}/rembourser", headers=headers, params={"id_caisse": desk_id}).status_code
    with ThreadPoolExecutor(max_workers=2) as pool:
        statuses = list(pool.map(lambda _: refund_once(), range(2)))
    assert sorted(statuses) == [200, 409]
    from app.models import OperationCaisse
    operations = list(db.scalars(select(OperationCaisse).where(OperationCaisse.id_paiement == payment_id, OperationCaisse.type_operation == "DEPENSE")))
    assert len(operations) == 1


def test_refunding_late_extra_payment_preserves_fully_paid_booking(client, db, login, monkeypatch):
    _, departure, reservation = pending_booking(client, db)
    headers = login(CASHIER)
    desk = open_caisse_for(db, departure)
    assert pay(client, headers, reservation, desk.id).status_code == 201
    extra = pending_payment(db, reservation)
    assert callback(client, monkeypatch, extra).status_code == 200
    db.expire_all()
    assert db.get(Paiement, extra.id).remboursement_demande_le is not None
    result = client.post(f"{API}/paiements/{extra.id}/rembourser", headers=headers, params={"id_caisse": desk.id})
    assert result.status_code == 200, result.text
    db.expire_all()
    detail = ReservationService(db)._get(reservation["id"])
    assert detail.statut == ReservationStatus.PAYEE
    assert all(p.billet.statut == "VALIDE" and p.depart_place.statut == "RESERVEE" for p in detail.places)


def test_administrator_can_sell_at_counter(client, db, admin_headers):
    departure = bookable_departure(db)
    response = client.post(f"{API}/reservations/guichet", headers=admin_headers, json={
        "id_depart": departure.id,
        "places": [{"id_depart_place": free_place_ids(db, departure.id, 1)[0], "nom_passager": "Client du guichet"}],
        "id_caisse": open_caisse_for(db, departure).id,
    })
    assert response.status_code == 201, response.text
    assert response.json()["statut"] == ReservationStatus.PAYEE


def test_driver_does_not_see_bookings_of_another_driver(client, db):
    from app.models import CooperativeMember
    _, _, reservation = pending_booking(client, db)
    driver, _, base = unused_driver_and_vehicle(db)
    db.add(CooperativeMember(id_user=driver.id_user, id_cooperative=base.id_cooperative, fonction="CHAUFFEUR", is_active=True))
    db.commit()
    headers = headers_for(client, driver.user)
    response = client.get(f"{API}/reservations", headers=headers)
    assert response.status_code == 200
    assert reservation["id"] not in {row["id"] for row in response.json()["items"]}
    assert client.get(f"{API}/reservations/{reservation['id']}", headers=headers).status_code == 404


def test_unknown_trip_duration_cannot_be_replaced_by_arbitrary_hour(db):
    from fastapi import HTTPException
    from app.services.depart.service import DepartService
    driver, vehicle, base = unused_driver_and_vehicle(db)
    route = base.itineraire
    duration = route.duree_estimee_minutes
    route.duree_estimee_minutes = None
    db.commit()
    try:
        with pytest.raises(HTTPException) as error:
            DepartService(db).create_depart(id_itineraire=base.id_itineraire, id_cooperative=base.id_cooperative, id_gare=base.id_gare,
                                           id_vehicule=vehicle.id, id_chauffeur=driver.id, id_tarif=base.id_tarif,
                                           date_depart=base.date_depart, heure_depart=base.heure_depart, nombre_places=base.nombre_places)
        assert error.value.status_code == 422 and "durée" in error.value.detail
    finally:
        route.duree_estimee_minutes = duration
        db.commit()


def test_cash_expense_cannot_overdraw_drawer(client, db, admin_headers):
    from app.models import Gare
    station = Gare(nom=f"Caisse-test-{uuid4().hex[:8]}", ville="Antananarivo", adresse="Test local", is_active=True)
    db.add(station)
    db.commit()
    opened = client.post(f"{API}/caisses", headers=admin_headers, json={"id_gare": station.id, "montant_ouverture": 100})
    assert opened.status_code == 201, opened.text
    response = client.post(f"{API}/caisses/{opened.json()['id']}/operations", headers=admin_headers,
                           json={"type_operation": "DEPENSE", "montant": "101", "description": "Dépense excessive"})
    assert response.status_code == 409


def test_cancelled_paid_booking_has_refund_due_and_no_balance_to_collect(client, db, login):
    passenger, departure, reservation = pending_booking(client, db)
    assert pay(client, login(CASHIER), reservation, open_caisse_for(db, departure).id).status_code == 201
    cancelled = client.post(f"{API}/reservations/{reservation['id']}/cancel", headers=passenger)
    assert cancelled.status_code == 200
    result = cancelled.json()
    assert Decimal(result["montant_paye"]) == Decimal(reservation["montant_total"])
    assert Decimal(result["montant_a_rembourser"]) == Decimal(reservation["montant_total"])
    assert Decimal(result["montant_restant"]) == 0


def test_payment_link_is_idempotent_and_seat_hold_covers_its_validity(client, db, monkeypatch):
    from app.services.finance.service import FinanceService
    _, _, reservation = pending_booking(client, db)
    monkeypatch.setattr(settings, "online_payment_enabled", True)
    monkeypatch.setattr(settings, "payment_provider", "papi")
    monkeypatch.setattr(settings, "papi_valid_duration_hours", 1)
    calls = []
    def make_link(**kwargs):
        calls.append(kwargs)
        return {"paymentLink": "https://example.invalid/test-payment", "notificationToken": "local-test-token"}
    monkeypatch.setattr(FinanceService, "_create_papi_link", staticmethod(make_link))
    key = f"TEST-{uuid4().hex}"
    arguments = dict(reservation_id=reservation["id"], amount=Decimal(reservation["montant_total"]), idempotency_key=key,
                     user_id=reservation["id_user"], client_name="Voyageur test", payer_phone="0340011122", payer_email=None, provider="MVOLA")
    before = datetime.now(timezone.utc)
    first = FinanceService(db).create_papi_payment(**arguments)
    second = FinanceService(db).create_papi_payment(**arguments)
    assert first["id_paiement"] == second["id_paiement"]
    assert len(calls) == 1
    assert calls[0]["payer_phone"] == "0340011122"
    db.expire_all()
    assert db.get(Reservation, reservation["id"]).date_expiration >= before + timedelta(hours=1)
    _, _, other = pending_booking(client, db)
    arguments.update(reservation_id=other["id"], user_id=other["id_user"])
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as error:
        FinanceService(db).create_papi_payment(**arguments)
    assert error.value.status_code == 409
