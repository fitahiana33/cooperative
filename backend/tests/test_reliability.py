"""Recovery and isolation checks against PostgreSQL; no real provider calls."""
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from types import SimpleNamespace
from uuid import uuid4
import csv
import io

import pytest
from fastapi import HTTPException
from sqlalchemy import func, select

from app.core.config import settings
from app.core.clock import local_today
from app.models import Depart, Gare, GareAgent, OperationCaisse, Paiement, Reservation, User
from app.models.user import UserRole
from app.services.booking_policy import minimum_deposit
from app.services.finance import FinanceService
from app.services.reservation import ReservationService
from app.services.reports import ReportService
from tests.database_safety import validate_test_database_urls as validate_database
from tests.helpers import API, bookable_departure, free_place_ids, open_caisse_for, pay
from tests.test_operational_integrity import pending_booking, callback
from tests.test_scopes import create_user, headers_for


@pytest.mark.parametrize("target,application", [
    ("postgresql+psycopg://user@localhost/production", ""),
    ("postgresql+psycopg://user@localhost/app_test", "postgresql+psycopg://other@localhost/app_test"),
    ("sqlite:///app_test", ""),
])
def test_destructive_setup_rejects_unsafe_targets(target, application):
    with pytest.raises(RuntimeError):
        validate_database(target, application)


def public_payload(db, **overrides):
    departure = bookable_departure(db, days_ahead=6)
    payload = dict(cle_idempotence=uuid4().hex, id_depart=departure.id,
        places=[{"id_depart_place": free_place_ids(db, departure.id, 1)[0], "nom_passager": "Voyageur test"}],
        nom_reservataire="Voyageur test", telephone_reservataire="034" + str(uuid4().int)[:7],
        montant_avance=int(minimum_deposit(Decimal(departure.tarif.prix))), fournisseur="MVOLA")
    payload.update(overrides)
    return payload


def test_public_creation_is_recoverable_without_contacting_provider(client, db, monkeypatch):
    def forbidden(**kwargs):
        raise AssertionError("Creating the reservation must not contact the provider")
    monkeypatch.setattr(FinanceService, "_create_papi_link", staticmethod(forbidden))
    payload = public_payload(db)
    first = client.post(f"{API}/reservations/public", json=payload)
    second = client.post(f"{API}/reservations/public", json=payload)
    assert first.status_code == second.status_code == 201
    assert first.json()["reservation"]["id"] == second.json()["reservation"]["id"]
    assert first.json()["access_token"] == second.json()["access_token"]
    assert first.json()["payment"] is None
    payload["nom_reservataire"] = "Autre personne"
    assert client.post(f"{API}/reservations/public", json=payload).status_code == 409


def test_guest_seat_and_pending_limits_use_the_server_policy(client, db, monkeypatch):
    monkeypatch.setattr(settings, "passenger_max_seats_per_reservation", 1)
    payload = public_payload(db)
    seats = free_place_ids(db, payload["id_depart"], 2)
    excessive = {**payload, "places": [{"id_depart_place": seat, "nom_passager": "Test"} for seat in seats]}
    assert client.post(f"{API}/reservations/public", json=excessive).status_code == 422
    monkeypatch.setattr(settings, "passenger_max_pending_reservations", 1)
    assert client.post(f"{API}/reservations/public", json=payload).status_code == 201
    other = public_payload(db, telephone_reservataire=payload["telephone_reservataire"])
    assert client.post(f"{API}/reservations/public", json=other).status_code == 409


def test_unknown_provider_outcome_is_recoverable_and_callback_sets_collection_date(client, db, monkeypatch):
    _, _, reservation = pending_booking(client, db)
    monkeypatch.setattr(settings, "online_payment_enabled", True)
    monkeypatch.setattr(settings, "payment_provider", "papi")
    calls = []
    def timeout(**kwargs):
        calls.append(kwargs)
        raise HTTPException(502, "Simulated lost response")
    monkeypatch.setattr(FinanceService, "_create_papi_link", staticmethod(timeout))
    args = dict(reservation_id=reservation["id"], amount=minimum_deposit(Decimal(reservation["montant_total"])),
        idempotency_key=uuid4().hex, user_id=reservation["id_user"], client_name="Test", payer_phone=None, payer_email=None, provider="MVOLA")
    service = FinanceService(db)
    first = service.create_papi_payment(**args)
    second = service.create_papi_payment(**{**args, "idempotency_key": uuid4().hex})
    assert first["verification_requise"] and first["checkout_url"] is None
    assert second["id_paiement"] == first["id_paiement"] and len(calls) == 1
    payment = db.get(Paiement, first["id_paiement"])
    payment.date_paiement = datetime.now(timezone.utc) - timedelta(days=2)
    db.commit()
    signed_event = SimpleNamespace(reference_paiement=payment.reference_paiement, notification_token="recovered-token", montant=payment.montant)
    assert callback(client, monkeypatch, signed_event).status_code == 200
    db.expire_all()
    payment = db.get(Paiement, first["id_paiement"])
    assert payment.statut == "VALIDE" and not payment.verification_requise
    assert payment.date_validation.astimezone(timezone.utc).date() == datetime.now(timezone.utc).date()
    assert payment.date_paiement == payment.date_validation


def test_station_manager_is_scoped_and_can_be_assigned_by_administrator(client, db, admin_headers):
    manager = create_user(db, UserRole.RESPONSABLE_GARE)
    headers = headers_for(client, manager)
    assert client.get(f"{API}/departs", headers=headers).json()["total"] == 0
    station = db.scalar(select(Gare).where(Gare.ville == "Toamasina"))
    assert client.post(f"{API}/gares/{station.id}/agents/{manager.id}", headers=admin_headers).status_code == 200
    result = client.get(f"{API}/departs", headers=headers).json()
    assert result["total"] > 0 and all(row["id_gare"] == station.id for row in result["items"])
    other = db.scalar(select(Gare.id).where(Gare.id != station.id))
    assert client.get(f"{API}/gares/{other}", headers=headers).status_code == 404


def test_payments_are_restricted_to_the_agents_station(client, db, login):
    response = client.get(f"{API}/paiements", headers=login("agent.toamasina@cooperative.com"), params={"page_size": 100})
    assert response.status_code == 200
    gare_id = db.scalar(select(Gare.id).where(Gare.ville == "Toamasina"))
    for payment in response.json()["items"]:
        reservation = db.get(Reservation, payment["id_reservation"])
        assert reservation.depart.id_gare == gare_id


def test_external_refund_keeps_cash_untouched_and_preserves_both_financial_events(client, db, admin_headers):
    _, departure, reservation = pending_booking(client, db)
    assert pay(client, admin_headers, reservation, open_caisse_for(db, departure).id).status_code == 201
    payment = db.scalar(select(Paiement).where(Paiement.id_reservation == reservation["id"]))
    count_before = db.scalar(select(func.count()).select_from(OperationCaisse))
    response = client.post(f"{API}/paiements/{payment.id}/rembourser", headers=admin_headers,
        json={"methode": "MOBILE_MONEY", "reference": "EXTERNAL-" + uuid4().hex})
    assert response.status_code == 200, response.text
    assert response.json()["methode_remboursement"] == "MOBILE_MONEY"
    assert response.json()["date_remboursement"]
    db.expire_all()
    assert db.scalar(select(func.count()).select_from(OperationCaisse)) == count_before
    rows = ReportService(db).rows(report_type="financial", date_from=local_today(), date_to=local_today())
    entries = [row for row in rows if row["reservation"] == reservation["numero_reservation"]]
    assert {row["operation"] for row in entries} == {"ENCAISSEMENT", "REMBOURSEMENT"}
    assert sum(row["montant"] for row in entries) == 0


def test_statistics_rejects_unbounded_ranges(client, admin_headers):
    assert client.get(f"{API}/statistiques", headers=admin_headers,
        params={"date_from": "2000-01-01", "date_to": "2030-01-01"}).status_code == 422


def test_public_station_directory_paginates_without_duplicates(client):
    first = client.get(f"{API}/gares/public", params={"page_size": 1}).json()
    second = client.get(f"{API}/gares/public", params={"page_size": 1, "page": 2}).json()
    assert first["total"] > 1 and first["total"] == second["total"]
    assert len(first["items"]) == len(second["items"]) == 1
    assert first["items"][0]["id"] != second["items"][0]["id"]


def test_reservation_csv_exports_more_than_one_thousand_rows(client, admin_headers, monkeypatch):
    def export(**kwargs):
        assert kwargs["for_export"] is True
        return (SimpleNamespace(numero_reservation=f"EXPORT-{index}", id_depart=1, depart=None,
            places=[], montant_total=Decimal("1000"), statut="ANNULEE") for index in range(1050))
    monkeypatch.setattr(ReservationService, "list_reservations", lambda self, **kwargs: export(**kwargs))
    response = client.get(f"{API}/reservations/export.csv", headers=admin_headers)
    assert response.status_code == 200
    rows = list(csv.reader(io.StringIO(response.text)))
    assert len(rows) == 1051 and rows[-1][0] == "EXPORT-1049"


def test_pdf_preserves_french_text_and_last_long_cell():
    pdf = ReportService.pdf_bytes("État des recettes", [{"référence": "Départ " + "long " * 200 + "FIN-CELLULE"}])
    assert b"/WinAnsiEncoding" in pdf and b"FIN-" in pdf and b"CELLULE" in pdf
    assert pdf.endswith(b"%%EOF\n")


def test_public_retries_are_serialized_under_concurrent_requests(client, db):
    from concurrent.futures import ThreadPoolExecutor
    payload = public_payload(db)
    db.rollback()
    with ThreadPoolExecutor(max_workers=2) as executor:
        responses = list(executor.map(lambda _: client.post(f"{API}/reservations/public", json=payload), range(2)))
    assert [response.status_code for response in responses] == [201, 201]
    assert responses[0].json()["reservation"]["id"] == responses[1].json()["reservation"]["id"]
    assert responses[0].json()["access_token"] == responses[1].json()["access_token"]


def test_incident_journal_is_scoped_and_resolution_does_not_change_the_trip(client, db, admin_headers, login):
    departure = bookable_departure(db, days_ahead=7)
    old_status = departure.statut
    first = client.post(f"{API}/departs/{departure.id}/incidents", headers=admin_headers,
        json={"type": "PANNE", "description": "Contrôle du véhicule demandé avant le départ."})
    assert first.status_code == 201
    incident = first.json()[-1]
    endpoint = f"{API}/departs/{departure.id}/incidents/{incident['id']}/resolution"
    assert client.post(endpoint, headers=admin_headers, json={"description": "Contrôle effectué, véhicule remis en service."}).status_code == 200
    assert client.post(endpoint, headers=admin_headers, json={"description": "Seconde résolution refusée."}).status_code == 409
    db.expire_all()
    assert db.get(Depart, departure.id).statut == old_status
    assert client.get(f"{API}/departs/{departure.id}/incidents", headers=login("passager02@cooperative.com")).status_code == 403


def test_migration_upgrades_existing_schema_and_can_be_reapplied(monkeypatch):
    from pathlib import Path
    from alembic import command
    from alembic.config import Config
    from sqlalchemy import create_engine, inspect
    from tests.database_safety import temporary_test_schema, test_schema_from_url

    with temporary_test_schema(settings.database_url) as target:
        monkeypatch.setattr(settings, "database_url", target)
        root = Path(__file__).resolve().parents[1]
        config = Config(str(root / "alembic.ini"))
        config.set_main_option("script_location", str(root / "migrations"))
        config.attributes["version_table_schema"] = test_schema_from_url(target)
        command.upgrade(config, "0039_surplus_refunds")
        command.upgrade(config, "head")
        command.downgrade(config, "0039_surplus_refunds")
        command.upgrade(config, "head")
        engine = create_engine(target)
        try:
            inspector = inspect(engine)
            assert "commande_hash" in {column["name"] for column in inspector.get_columns("reservations")}
            assert any(constraint["column_names"] == ["commande_hash"] for constraint in inspector.get_unique_constraints("reservations"))
            assert "date_validation" in {column["name"] for column in inspector.get_columns("paiements")}
        finally:
            engine.dispose()

