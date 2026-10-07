import base64
import os

# Tests operate exclusively on a dedicated disposable database, never the app database.
os.environ["DATABASE_URL"] = os.getenv(
    "TEST_DATABASE_URL", "postgresql+psycopg://nomi:nomi_local@127.0.0.1:54329/nomi_test"
)
os.environ["APP_ORIGIN"] = "http://localhost:3000"
os.environ["COOKIE_SECURE"] = "false"
os.environ["ENVIRONMENT"] = "development"
os.environ["ACCOUNT_MAIL_KEY"] = base64.urlsafe_b64encode(os.urandom(32)).decode()
os.environ["MAIL_BACKEND"] = "file"

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.core.database import engine
from app.main import app, attempts


@pytest.fixture(scope="session", autouse=True)
def migrated_database():
    if engine.url.database != "nomi_test":
        raise RuntimeError("Tests require the dedicated nomi_test database")
    command.upgrade(Config("alembic.ini"), "head")
    yield
    engine.dispose()


@pytest.fixture(autouse=True)
def clean_database(migrated_database):
    with engine.begin() as db:
        db.execute(
            text(
                "TRUNCATE transactions, commitments, contacts, audit_events, outbox_events, "
                "idempotency_records, sessions, memberships, workspaces, users, "
                "email_verification_tokens, password_reset_tokens"
            )
        )
    attempts.clear()


@pytest.fixture
def client():
    with TestClient(app, headers={"Origin": "http://localhost:3000"}) as value:
        yield value


def register(client, email="david@example.com"):
    response = client.post(
        "/api/v1/auth/register",
        json={"email": email, "display_name": "David", "password": "a-long-test-password"},
    )
    assert response.status_code == 201, response.text
    client.headers["X-CSRF-Token"] = client.cookies["nomi_csrf"]
    return response.json()
