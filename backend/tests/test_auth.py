import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.db.session import get_db
from app.main import app

SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


def setup_function():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def test_auth_full_flow():
    client = TestClient(app)

    # 1. Register a passenger user
    reg_resp = client.post(
        "/api/v1/auth/register",
        json={
            "name": "Rasoa",
            "first_name": "Marie",
            "email": "rasoa@example.com",
            "telephone": "0341234567",
            "address": "Antananarivo",
            "password": "Password123!",
        },
    )
    assert reg_resp.status_code == 201, reg_resp.text
    reg_data = reg_resp.json()
    assert "access_token" in reg_data
    assert "refresh_token" in reg_data
    assert reg_data["user"]["role"] == "passenger"
    assert reg_data["user"]["email"] == "rasoa@example.com"

    access_token = reg_data["access_token"]
    refresh_token = reg_data["refresh_token"]

    # 2. Get current user profile (/auth/me)
    me_resp = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert me_resp.status_code == 200
    assert me_resp.json()["email"] == "rasoa@example.com"

    # 3. RBAC test: Passenger trying to list all users should get 403 Forbidden
    users_resp = client.get(
        "/api/v1/users",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert users_resp.status_code == 403

    # 4. Refresh token
    refresh_resp = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert refresh_resp.status_code == 200
    new_data = refresh_resp.json()
    assert "access_token" in new_data
    assert new_data["access_token"] != access_token

    # 5. Login with credentials
    login_resp = client.post(
        "/api/v1/auth/login",
        json={
            "email": "rasoa@example.com",
            "password": "Password123!",
        },
    )
    assert login_resp.status_code == 200
    assert "access_token" in login_resp.json()

    # 6. Forgot password & reset password flow
    forgot_resp = client.post(
        "/api/v1/auth/forgot-password",
        json={"email": "rasoa@example.com"},
    )
    assert forgot_resp.status_code == 200

    # Create a valid reset token directly using token service
    from app.services.authentication.token import create_password_reset_token

    reset_token = create_password_reset_token("rasoa@example.com")

    reset_resp = client.post(
        "/api/v1/auth/reset-password",
        json={
            "token": reset_token,
            "new_password": "NewSecretPassword123!",
        },
    )
    assert reset_resp.status_code == 200

    # Verify login with new password works
    new_login_resp = client.post(
        "/api/v1/auth/login",
        json={
            "email": "rasoa@example.com",
            "password": "NewSecretPassword123!",
        },
    )
    assert new_login_resp.status_code == 200

    print("ALL BACKEND AUTH TESTS PASSED SUCCESSFULLY!")


if __name__ == "__main__":
    setup_function()
    test_auth_full_flow()
