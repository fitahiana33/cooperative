"""Test setup: a dedicated PostgreSQL database, migrated and filled with demo data.

The tests run against a real PostgreSQL database because the business rules
rely on triggers (seat locking, counters, boarding). The database is derived
from DATABASE_URL (`<name>_test`) unless TEST_DATABASE_URL is set; it is
recreated at the start of every test session.
"""

import os
import random
from pathlib import Path
from sqlalchemy.engine import make_url
from tests.database_safety import schema_test_url, temporary_test_schema
from uuid import uuid4

# Configure the application before anything imports app.core.config.
_base_url = os.environ.get("DATABASE_URL", "")
TEST_DATABASE_SCHEMA = os.environ.get("TEST_DATABASE_SCHEMA", "")
if TEST_DATABASE_SCHEMA == "auto":
    TEST_DATABASE_SCHEMA = "qa_validation_" + uuid4().hex[:20]
TEST_DATABASE_URL = os.environ.get("TEST_DATABASE_URL") or (
    make_url(_base_url).set(database=(make_url(_base_url).database or "") + "_test").render_as_string(hide_password=False) if _base_url else ""
)
if TEST_DATABASE_SCHEMA:
    TEST_DATABASE_URL = schema_test_url(_base_url, TEST_DATABASE_SCHEMA)
os.environ["DATABASE_URL"] = TEST_DATABASE_URL
os.environ["ENVIRONMENT"] = "test"
os.environ["SCHEDULER_ENABLED"] = "false"
os.environ["NOTIFICATION_EMAIL_ENABLED"] = "false"
os.environ.setdefault("UPLOADS_DIR", str(Path(__file__).resolve().parents[2] / "build" / "test-uploads"))

import psycopg  # noqa: E402
import pytest  # noqa: E402
from alembic import command  # noqa: E402
from alembic.config import Config  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

DEMO_PASSWORD = "Demo123!"


def _recreate_database() -> None:
    from tests.database_safety import validate_test_database_urls
    from psycopg import sql
    admin_url, name = validate_test_database_urls(TEST_DATABASE_URL, _base_url)
    with psycopg.connect(admin_url, autocommit=True) as conn:
        conn.execute(sql.SQL('DROP DATABASE IF EXISTS {} WITH (FORCE)').format(sql.Identifier(name)))
        conn.execute(sql.SQL('CREATE DATABASE {}').format(sql.Identifier(name)))


@pytest.fixture(scope="session", autouse=True)
def database(request):
    assert TEST_DATABASE_URL, "DATABASE_URL ou TEST_DATABASE_URL doit être défini pour les tests."
    if TEST_DATABASE_SCHEMA:
        schema_context = temporary_test_schema(_base_url, TEST_DATABASE_SCHEMA)
        schema_context.__enter__()
        request.addfinalizer(lambda: schema_context.__exit__(None, None, None))
        connection_url = make_url(_base_url).set(drivername="postgresql").render_as_string(hide_password=False)
        with psycopg.connect(connection_url, autocommit=True) as connection:
            connection.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto WITH SCHEMA public")
            connection.execute("CREATE EXTENSION IF NOT EXISTS btree_gist WITH SCHEMA public")
    else:
        _recreate_database()
    backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    alembic_config = Config(os.path.join(backend_dir, "alembic.ini"))
    alembic_config.set_main_option("script_location", os.path.join(backend_dir, "migrations"))
    if TEST_DATABASE_SCHEMA:
        alembic_config.attributes["version_table_schema"] = TEST_DATABASE_SCHEMA
    command.upgrade(alembic_config, "head")

    from app.db.seed import seed_default_admin
    from app.db.seed_dev import DemoSeeder
    from app.db.session import SessionLocal

    with SessionLocal() as db:
        seed_default_admin(db)
        DemoSeeder(db, random.Random(2026), write_qr=False).run()
        db.commit()
    yield
    if TEST_DATABASE_SCHEMA:
        from app.db.session import engine
        engine.dispose()



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

    def _login(email: str, password: str | None = None) -> dict[str, str]:
        from app.core.config import settings
        if password is None:
            password = settings.default_admin_password if email == settings.default_admin_email else DEMO_PASSWORD
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
