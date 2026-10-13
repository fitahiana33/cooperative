"""Test setup: a dedicated PostgreSQL database, migrated and filled with demo data.

The tests run against a real PostgreSQL database because the business rules
rely on triggers (seat locking, counters, boarding). The database is derived
from DATABASE_URL (`<name>_test`) unless TEST_DATABASE_URL is set; it is
recreated at the start of every test session.
"""

import os
import random

# Configure the application before anything imports app.core.config.
_base_url = os.environ.get("DATABASE_URL", "")
TEST_DATABASE_URL = os.environ.get("TEST_DATABASE_URL") or (
    _base_url.rsplit("/", 1)[0] + "/" + _base_url.rsplit("/", 1)[1].split("?")[0] + "_test" if _base_url else ""
)
os.environ["DATABASE_URL"] = TEST_DATABASE_URL
os.environ["ENVIRONMENT"] = "test"
os.environ["SCHEDULER_ENABLED"] = "false"
os.environ.setdefault("UPLOADS_DIR", "/tmp/cooperative-test-uploads")

import psycopg  # noqa: E402
import pytest  # noqa: E402
from alembic import command  # noqa: E402
from alembic.config import Config  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

DEMO_PASSWORD = "Demo123!"


def _recreate_database() -> None:
    admin_url = TEST_DATABASE_URL.replace("postgresql+psycopg://", "postgresql://").rsplit("/", 1)[0] + "/postgres"
    name = TEST_DATABASE_URL.rsplit("/", 1)[1]
    with psycopg.connect(admin_url, autocommit=True) as conn:
        conn.execute(f'DROP DATABASE IF EXISTS "{name}" WITH (FORCE)')
        conn.execute(f'CREATE DATABASE "{name}"')


@pytest.fixture(scope="session", autouse=True)
def database():
    assert TEST_DATABASE_URL, "DATABASE_URL ou TEST_DATABASE_URL doit être défini pour les tests."
    _recreate_database()
    backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    alembic_config = Config(os.path.join(backend_dir, "alembic.ini"))
    alembic_config.set_main_option("script_location", os.path.join(backend_dir, "migrations"))
    command.upgrade(alembic_config, "head")

    from app.db.seed import seed_default_admin
    from app.db.seed_dev import DemoSeeder
    from app.db.session import SessionLocal

    with SessionLocal() as db:
        seed_default_admin(db)
        DemoSeeder(db, random.Random(2026), write_qr=False).run()
        db.commit()
    yield


@pytest.fixture(scope="session")
def client(database):
    from app.main import app

    # Many accounts log in during the suite; the per-IP login limit is not under test here.
    app.state.limiter.enabled = False
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture()
def db():
    from app.db.session import SessionLocal

    with SessionLocal() as session:
        yield session


@pytest.fixture(scope="session")
def login(client):
    tokens: dict[str, str] = {}

    def _login(email: str, password: str = DEMO_PASSWORD) -> dict[str, str]:
        key = f"{email}:{password}"
        if key not in tokens:
            response = client.post("/api/v1/auth/login", json={"email": email, "password": password})
            assert response.status_code == 200, response.text
            tokens[key] = response.json()["access_token"]
        return {"Authorization": f"Bearer {tokens[key]}"}

    return _login


@pytest.fixture(scope="session")
def admin_headers(login):
    from app.core.config import settings

    return login(settings.default_admin_email, settings.default_admin_password)
