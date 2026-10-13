"""Configuration guards, password reset, data reset, private files."""

import pytest
from pydantic import ValidationError
from sqlalchemy import select

from app.core.config import Settings, settings
from app.models import Billet
from tests.helpers import API

STRONG_SECRET = "s" * 48


def make_settings(**overrides) -> Settings:
    values = dict(
        app_name="test", environment="production", database_url=settings.database_url, secret_key=STRONG_SECRET,
        api_v1_prefix="/api/v1", allowed_origins=[], jwt_algorithm="HS256",
        default_admin_email="admin@cooperative.com", default_admin_password="Xk9-strong-Pass",
    )
    values.update(overrides)
    return Settings(_env_file=None, **values)


def test_production_refuses_sample_secret_key():
    with pytest.raises(ValidationError):
        make_settings(secret_key="change-me-in-development")


def test_production_refuses_default_admin_password():
    with pytest.raises(ValidationError):
        make_settings(default_admin_password="Admin123!")


def test_production_refuses_debug_reset_link():
    with pytest.raises(ValidationError):
        make_settings(debug_return_reset_url=True)


def test_production_accepts_strong_values():
    assert make_settings().environment == "production"


def test_development_tolerates_sample_values():
    assert make_settings(environment="development", secret_key="change-me", default_admin_password="Admin123!").is_development


def test_forgot_password_never_returns_the_link(client):
    response = client.post(f"{API}/auth/forgot-password", json={"email": settings.default_admin_email})
    assert response.status_code == 200
    assert not response.json().get("reset_url")


def test_data_reset_requires_the_admin_password(client, admin_headers):
    assert client.post(f"{API}/system/reset-business-data", headers=admin_headers, json={}).status_code == 422
    assert client.post(f"{API}/system/reset-business-data", headers=admin_headers, json={"password": "wrong"}).status_code == 403


def test_data_reset_is_admin_only(client, login):
    response = client.post(f"{API}/system/reset-business-data", headers=login("responsable.gare1@cooperative.com"), json={"password": "Demo123!"})
    assert response.status_code == 403


def test_uploads_are_not_served_statically(client):
    assert client.get("/uploads/qr_codes/anything.png").status_code == 404
    assert client.get("/uploads/vehicules/anything.pdf").status_code == 404


def test_ticket_qr_requires_authentication_and_ownership(client, db, login):
    billet = db.scalar(select(Billet).limit(1))
    owner_id = billet.reservation_place.reservation.id_user
    from app.models import User

    owner = db.get(User, owner_id)
    assert client.get(f"{API}/billets/{billet.id}/qr.png").status_code == 401
    if owner.email.startswith("passager"):
        response = client.get(f"{API}/billets/{billet.id}/qr.png", headers=login(owner.email))
        assert response.status_code == 200 and response.content[:4] == b"\x89PNG"
    stranger = "passager25@cooperative.com" if owner.email != "passager25@cooperative.com" else "passager24@cooperative.com"
    assert client.get(f"{API}/billets/{billet.id}/qr.png", headers=login(stranger)).status_code == 404
    staff = client.get(f"{API}/billets/{billet.id}/qr.png", headers=login("responsable.gare1@cooperative.com"))
    assert staff.status_code == 200
