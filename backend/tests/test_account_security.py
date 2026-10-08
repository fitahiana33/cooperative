"""Password changes end sessions, password policy, upload content checks, database refusals."""

import io

from sqlalchemy import select

from app.models import Vehicule
from app.models.user import UserRole
from tests.helpers import API
from tests.test_scopes import PASSWORD, create_user


def test_password_change_ends_existing_sessions(client, db, admin_headers):
    """I-S06."""
    user = create_user(db, UserRole.PASSAGER)
    tokens = client.post(f"{API}/auth/login", json={"email": user.email, "password": PASSWORD}).json()
    old = {"Authorization": f"Bearer {tokens['access_token']}"}
    assert client.get(f"{API}/auth/me", headers=old).status_code == 200

    assert client.put(f"{API}/users/{user.id}", headers=admin_headers, json={"password": "Nouveau123"}).status_code == 200
    assert client.get(f"{API}/auth/me", headers=old).status_code == 401
    assert client.post(f"{API}/auth/refresh", json={"refresh_token": tokens["refresh_token"]}).status_code == 401
    fresh = client.post(f"{API}/auth/login", json={"email": user.email, "password": "Nouveau123"}).json()
    assert client.get(f"{API}/auth/me", headers={"Authorization": f"Bearer {fresh['access_token']}"}).status_code == 200


def test_weak_passwords_are_refused_at_registration(client):
    for weak in ("abcdefgh", "12345678", "Ab1"):
        response = client.post(f"{API}/auth/register", json={"name": "W", "first_name": "P", "email": "weak.pw@cooperative.com", "password": weak})
        assert response.status_code == 422, weak


def test_upload_content_must_match_extension(client, db, admin_headers):
    """I-S08: a script renamed to .pdf is refused."""
    vehicle_id = db.scalar(select(Vehicule.id).limit(1))
    fake = client.post(
        f"{API}/vehicules/{vehicle_id}/documents/upload", headers=admin_headers,
        data={"type_document": "ASSURANCE"}, files={"file": ("assurance.pdf", io.BytesIO(b"#!/bin/sh\necho pwned"), "application/pdf")},
    )
    assert fake.status_code == 400
    real = client.post(
        f"{API}/vehicules/{vehicle_id}/documents/upload", headers=admin_headers,
        data={"type_document": "ASSURANCE"}, files={"file": ("assurance.pdf", io.BytesIO(b"%PDF-1.4\n%test\n"), "application/pdf")},
    )
    assert real.status_code == 201, real.text
