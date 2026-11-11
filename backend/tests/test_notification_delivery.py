"""SMTP is simulated: these tests never send external email."""
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import select

from app.core.config import settings
from app.models import Reservation, User
from app.models.user import UserRole
from app.services.notification import NotificationService
from app.services.notification import delivery
from tests.helpers import API
from tests.test_reliability import public_payload
from tests.test_scopes import create_user


@pytest.fixture
def smtp(monkeypatch):
    captured = []
    monkeypatch.setattr(settings, "notification_email_enabled", True)
    monkeypatch.setattr(settings, "smtp_host", "smtp.example.test")
    monkeypatch.setattr(settings, "smtp_from", "notifications@example.com")
    monkeypatch.setattr(settings, "smtp_username", None)
    monkeypatch.setattr(settings, "smtp_use_ssl", False)
    monkeypatch.setattr(settings, "smtp_use_tls", True)

    class FakeSMTP:
        def __init__(self, host, port, timeout):
            assert host == "smtp.example.test" and timeout == 10

        def __enter__(self):
            return self

        def __exit__(self, *_):
            pass

        def starttls(self):
            pass

        def send_message(self, message):
            captured.append(message)

    monkeypatch.setattr(delivery.smtplib, "SMTP", FakeSMTP)
    # Accidentally selecting SSL must also stay inside the simulated transport.
    monkeypatch.setattr(delivery.smtplib, "SMTP_SSL", FakeSMTP)
    return captured


def add_notification(db, user, **kwargs):
    item = NotificationService.add(db, user_id=user.id, type_notification="RAPPEL_DEPART",
        titre="Rappel de départ", message="Votre départ est prévu demain à 08:00.", **kwargs)
    db.commit()
    return item


def test_delivery_sends_only_title_and_message_and_does_not_repeat(db, smtp, monkeypatch):
    user = create_user(db, UserRole.PASSAGER)
    monkeypatch.setattr(settings, "notification_email_enabled", False)
    historical = add_notification(db, user)
    monkeypatch.setattr(settings, "notification_email_enabled", True)
    item = add_notification(db, user)
    assert delivery.deliver_notifications(db) == 1
    assert len(smtp) == 1
    message = smtp[0]
    assert str(message["To"]) == user.email
    assert str(message["Subject"]) == item.titre
    assert message.get_content().strip() == item.message
    assert not message.is_multipart() and list(message.iter_attachments()) == []
    assert message["Message-ID"] == f"<notification-{item.id}@example.com>"
    assert item.delivery_status == "DELIVERED" and item.delivered_at
    assert historical.delivery_status == "IN_APP"
    assert delivery.deliver_notifications(db) == 0 and len(smtp) == 1


@pytest.mark.parametrize("disabled", ["notification_email_enabled", "smtp_host"])
def test_disabled_delivery_stays_in_app(db, smtp, monkeypatch, disabled):
    monkeypatch.setattr(settings, disabled, False if disabled == "notification_email_enabled" else None)
    item = add_notification(db, create_user(db, UserRole.PASSAGER))
    assert delivery.deliver_notifications(db) == 0
    assert item.canal == "IN_APP" and item.delivery_status == "IN_APP"
    assert item.delivery_attempts == 0 and smtp == []


def test_transport_failure_is_retried_later_and_stops_after_five_attempts(db, smtp, monkeypatch):
    def unavailable(*_):
        raise OSError("Private transport detail must not be stored")

    monkeypatch.setattr(delivery, "_send", unavailable)
    item = add_notification(db, create_user(db, UserRole.PASSAGER))
    for attempt in range(1, 6):
        assert delivery.deliver_notifications(db) == 0
        assert item.delivery_attempts == attempt
        assert item.delivery_error == "Transport email indisponible."
        assert item.delivery_status == ("FAILED" if attempt == 5 else "RETRY")
        assert item.next_attempt_at > datetime.now(timezone.utc)
        assert delivery.deliver_notifications(db) == 0
        assert item.delivery_attempts == attempt
        item.next_attempt_at = datetime.now(timezone.utc) - timedelta(seconds=1)
        db.commit()
    assert delivery.deliver_notifications(db) == 0 and item.delivery_attempts == 5
    assert item.delivered_at is None and smtp == []


def test_guest_delivery_uses_only_the_email_entered_for_its_reservation(client, db, smtp):
    payload = public_payload(db, email_reservataire="voyageur@example.com")
    response = client.post(f"{API}/reservations/public", json=payload)
    assert response.status_code == 201, response.text
    reservation = db.scalar(select(Reservation).where(Reservation.id == response.json()["reservation"]["id"]))
    guest = db.get(User, reservation.id_user)
    assert not guest.is_active and guest.email.endswith("@guest.cooperative.local")
    item = add_notification(db, guest, reservation_id=reservation.id)
    assert delivery.deliver_notifications(db) == 1
    assert str(smtp[0]["To"]) == payload["email_reservataire"]
    assert item.delivery_status == "DELIVERED"


def test_inactive_account_and_invalid_address_are_not_sent(db, smtp):
    user = create_user(db, UserRole.PASSAGER)
    user.is_active = False
    skipped = add_notification(db, user)
    assert delivery.deliver_notifications(db) == 0
    assert skipped.delivery_status == "IN_APP" and skipped.delivery_attempts == 0
    user.is_active = True
    user.email = "invalid-address"
    invalid = add_notification(db, user)
    assert delivery.deliver_notifications(db) == 0
    assert invalid.delivery_status == "FAILED" and invalid.delivery_attempts == 1
    assert smtp == []
