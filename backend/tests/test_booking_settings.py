from datetime import timedelta
from decimal import Decimal
from uuid import uuid4

from sqlalchemy import select

from app.core.clock import local_today
from app.models import AuditLog, Reservation
from app.models.user import UserRole
from app.services.booking_policy import minimum_deposit
from app.services.insights import DecisionSupportService
from tests.helpers import API
from tests.test_reliability import public_payload
from tests.test_scopes import create_user, headers_for


def test_settings_are_admin_only_and_percentages_are_bounded(client, db, admin_headers):
    user = create_user(db, UserRole.PASSAGER)
    headers = headers_for(client, user)
    for method in [client.get, client.put]:
        kwargs = {"json": {"deposit_percentage": 50}} if method == client.put else {}
        assert (
            method(
                f"{API}/system/booking-settings", headers=headers, **kwargs
            ).status_code
            == 403
        )
    for value in [0, -1, 100.01, 25.555]:
        assert (
            client.put(
                f"{API}/system/booking-settings",
                headers=admin_headers,
                json={"deposit_percentage": value},
            ).status_code
            == 422
        )


def test_deposit_changes_only_new_bookings_and_audits_actor(client, db, admin_headers):
    endpoint = f"{API}/system/booking-settings"
    original = client.get(endpoint, headers=admin_headers).json()["deposit_percentage"]
    try:
        assert (
            client.put(
                endpoint, headers=admin_headers, json={"deposit_percentage": 37.5}
            ).status_code
            == 200
        )
        assert client.get(f"{API}/reservations/policy").json()["deposit_rate"] == 0.375
        created = client.post(
            f"{API}/reservations/public", json=public_payload(db)
        ).json()
        assert "reservation" in created, created
        reservation = db.get(Reservation, created["reservation"]["id"])
        assert reservation.taux_acompte == Decimal(".3750")
        expected = minimum_deposit(
            reservation.montant_total,
            rate=Decimal(".375"),
            floor=reservation.plancher_acompte,
        )
        assert Decimal(str(created["acompte_minimum"])) == expected
        client.put(
            endpoint, headers=admin_headers, json={"deposit_percentage": 100}
        ).raise_for_status()
        db.expire_all()
        assert reservation.minimum_a_payer == expected
        assert client.get(f"{API}/reservations/policy").json()["deposit_rate"] == 1
        assert db.scalar(
            select(AuditLog).where(
                AuditLog.action == "BOOKING_SETTINGS_UPDATE",
                AuditLog.id_user.is_not(None),
            )
        )
    finally:
        client.put(
            endpoint, headers=admin_headers, json={"deposit_percentage": original}
        ).raise_for_status()


def test_insights_database_queries_respect_empty_scope(client, db, admin_headers):
    assert DecisionSupportService(db, gare_ids=set()).analyze()["previsions"] == []
    result = DecisionSupportService(db).analyze(cooperative_ids=set())
    assert result["anomalies"] == [] and result["recommandations"] == []
    response = client.get(f"{API}/aide-decision", headers=admin_headers)
    assert response.status_code == 200, response.text
    for r in response.json()["recommandations"]:
        assert r["departs_recommandes"] == sum(
            d["departs_supplementaires"] for d in r["jours"]
        )
        assert len(r["jours"]) == 7
    future = local_today() + timedelta(days=1)
    assert (
        client.get(
            f"{API}/aide-decision?date_reference={future}", headers=admin_headers
        ).status_code
        == 422
    )
