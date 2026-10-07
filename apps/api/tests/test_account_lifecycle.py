import json
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier, Lock
from uuid import UUID

import pytest
from conftest import register
from fastapi.testclient import TestClient
from sqlalchemy import select, text
from test_core import pay, setup_commitment

from app.core.config import settings
from app.core.database import engine, session_factory
from app.main import app
from app.modules.audit.infrastructure.repository import AuditRepository
from app.modules.identity.application.mail import process_next_mail
from app.modules.identity.infrastructure.mail_transport import MailTransport
from app.modules.identity.infrastructure.models import (
    EmailVerificationTokenRow,
    PasswordResetTokenRow,
)
from app.modules.identity.infrastructure.repository import digest
from app.modules.identity.infrastructure.token_cipher import delivery_cipher
from app.shared.uow import EffectsRepository, SqlUnitOfWork


def latest_token(purpose="verify"):
    model = EmailVerificationTokenRow if purpose == "verify" else PasswordResetTokenRow
    with session_factory() as db:
        row = db.scalar(select(model).order_by(model.created_at.desc()).limit(1))
        return delivery_cipher().decrypt(row.delivery_secret.encode()).decode()


def forgot(client, email="david@example.com"):
    return client.post("/api/v1/auth/password/forgot", json={"email": email})


def verify(client, token):
    return client.post("/api/v1/auth/email/verify", json={"token": token})


def reset(client, token, password="new-secure-password"):
    return client.post("/api/v1/auth/password/reset", json={"token": token, "password": password})


def login(client, password="new-secure-password"):
    return client.post(
        "/api/v1/auth/login", json={"email": "david@example.com", "password": password}
    )


class RecordingMail:
    def __init__(self):
        self.messages = []
        self.lock = Lock()

    def send(self, event_id, message):
        with self.lock:
            self.messages.append((event_id, message))


def test_verification_persists_and_enables_protected_workspace(client, monkeypatch):
    profile = register(client)
    token = latest_token()
    monkeypatch.setattr(settings(), "environment", "production")
    assert client.get("/api/v1/dashboard/summary").status_code == 403
    assert verify(client, token).status_code == 200
    engine.dispose()
    assert client.get("/api/v1/me").json()["user"]["email_verified"] is True
    assert client.get("/api/v1/dashboard/summary").status_code == 200
    assert verify(client, token).json()["code"] == "ACCOUNT_LINK_INVALID"
    with session_factory() as db:
        row = db.scalar(select(EmailVerificationTokenRow))
        assert row.user_id == UUID(profile["user"]["id"])
        assert row.token_hash == digest(token) and row.used_at and row.delivery_secret is None
        assert db.scalar(text("SELECT email_verified_at IS NOT NULL FROM users"))


@pytest.mark.parametrize("purpose", ["verify", "reset"])
def test_expired_link_cannot_change_account(client, purpose):
    register(client)
    if purpose == "reset":
        assert forgot(client).status_code == 202
    token = latest_token(purpose)
    table = "email_verification_tokens" if purpose == "verify" else "password_reset_tokens"
    with engine.begin() as db:
        db.execute(
            text(
                f"UPDATE {table} SET created_at=now()-interval '2 days', expires_at=now()-interval '1 minute'"
            )
        )
    response = verify(client, token) if purpose == "verify" else reset(client, token)
    assert response.status_code == 400
    assert login(client, "a-long-test-password").status_code == 200


def test_resend_invalidates_previous_link_and_respects_cooldown(client):
    register(client)
    old = latest_token()
    assert client.post("/api/v1/auth/email/resend").status_code == 202
    with engine.begin() as db:
        assert db.scalar(text("SELECT count(*) FROM email_verification_tokens")) == 1
        db.execute(
            text("UPDATE email_verification_tokens SET created_at=now()-interval '2 minutes'")
        )
    assert client.post("/api/v1/auth/email/resend").status_code == 202
    new = latest_token()
    assert new != old
    assert verify(client, old).status_code == 400
    assert verify(client, new).status_code == 200


def test_reset_revokes_all_sessions_and_preserves_money(client):
    commitment = setup_commitment(client)
    assert pay(client, commitment["id"]).status_code == 201
    assert verify(client, latest_token()).status_code == 200
    with TestClient(app, headers={"Origin": "http://localhost:3000"}) as other:
        assert login(other, "a-long-test-password").status_code == 200
        assert forgot(client).status_code == 202
        token = latest_token("reset")
        assert reset(client, token).status_code == 200
        assert client.get("/api/v1/me").status_code == 401
        assert other.get("/api/v1/me").status_code == 401
    assert reset(client, token).status_code == 400
    assert login(client, "a-long-test-password").status_code == 401
    assert login(client).status_code == 200
    engine.dispose()
    assert client.get(f"/api/v1/commitments/{commitment['id']}").json()["balance_minor"] == 750000
    assert client.get("/api/v1/dashboard/summary").json()["receivable_balance_minor"] == "750000"
    with engine.connect() as db:
        assert db.scalar(text("SELECT count(*) FROM transactions")) == 1
        assert db.scalar(text("SELECT count(*) FROM workspaces")) == 1
        assert (
            db.scalar(text("SELECT count(*) FROM audit_events WHERE action='user.password_reset'"))
            == 1
        )
        assert (
            db.scalar(text("SELECT count(*) FROM outbox_events WHERE event_type='PasswordChanged'"))
            == 1
        )


def test_forgot_is_generic_and_does_not_expose_secret(client):
    register(client)
    absent = forgot(client, "absent@example.com")
    present = forgot(client)
    repeated = forgot(client)
    with engine.begin() as db:
        assert db.scalar(text("SELECT count(*) FROM password_reset_tokens")) == 1
        db.execute(text("UPDATE users SET status='disabled'"))
    disabled = forgot(client)
    assert all(
        r.status_code == 202 and r.json() == absent.json() for r in (present, repeated, disabled)
    )
    token = latest_token("reset")
    assert token not in present.text
    assert reset(client, token).status_code == 400


def test_token_purpose_and_new_password_validation(client):
    register(client)
    verification = latest_token()
    forgot(client)
    reset_token = latest_token("reset")
    assert reset(client, verification).status_code == 400
    assert verify(client, reset_token).status_code == 400
    response = reset(client, reset_token, "short")
    assert response.status_code == 422 and reset_token not in response.text
    assert reset(client, reset_token, "  long-password-with-spaces  ").status_code == 200
    assert login(client, "long-password-with-spaces").status_code == 401
    assert login(client, "  long-password-with-spaces  ").status_code == 200


@pytest.mark.parametrize("purpose", ["verify", "reset"])
def test_same_token_race_has_one_commit(client, purpose):
    register(client)
    if purpose == "reset":
        forgot(client)
    token = latest_token(purpose)
    barrier = Barrier(2)

    def execute(_):
        with TestClient(app, headers={"Origin": "http://localhost:3000"}) as parallel:
            barrier.wait(timeout=10)
            return verify(parallel, token) if purpose == "verify" else reset(parallel, token)

    with ThreadPoolExecutor(2) as pool:
        results = list(pool.map(execute, range(2)))
    assert sorted(r.status_code for r in results) == [200, 400]


def test_login_reset_race_never_leaves_an_old_password_session(client):
    register(client)
    forgot(client)
    token = latest_token("reset")
    barrier = Barrier(2)

    def old_login():
        with TestClient(app, headers={"Origin": "http://localhost:3000"}) as other:
            barrier.wait(timeout=10)
            result = login(other, "a-long-test-password")
            return result.status_code, dict(other.cookies)

    def change():
        with TestClient(app, headers={"Origin": "http://localhost:3000"}) as other:
            barrier.wait(timeout=10)
            return reset(other, token).status_code

    with ThreadPoolExecutor(2) as pool:
        a, b = pool.submit(old_login), pool.submit(change)
        status, cookies = a.result()
        assert b.result() == 200 and status in (200, 401)
    with TestClient(app, cookies=cookies) as old:
        assert old.get("/api/v1/me").status_code == 401


@pytest.mark.parametrize(
    "purpose,repository,method",
    [
        ("verify", AuditRepository, "record"),
        ("reset", AuditRepository, "record"),
        ("reset", EffectsRepository, "emit"),
    ],
)
def test_link_consumption_rolls_back_with_critical_effect(
    client, monkeypatch, purpose, repository, method
):
    register(client)
    if purpose == "reset":
        forgot(client)
    token = latest_token(purpose)

    def fail(*args, **kwargs):
        raise RuntimeError("Injected failure")

    with monkeypatch.context() as patch:
        patch.setattr(repository, method, fail)
        response = verify(client, token) if purpose == "verify" else reset(client, token)
        assert response.status_code == 500
    assert client.get("/api/v1/me").status_code == 200
    assert login(client, "a-long-test-password").status_code == 200
    response = verify(client, token) if purpose == "verify" else reset(client, token)
    assert response.status_code == 200


def test_request_failure_does_not_leave_token_without_outbox(client, monkeypatch):
    register(client)

    def fail(*args, **kwargs):
        raise RuntimeError("Injected failure")

    monkeypatch.setattr(EffectsRepository, "emit", fail)
    assert forgot(client).status_code == 500
    with engine.connect() as db:
        assert db.scalar(text("SELECT count(*) FROM password_reset_tokens")) == 0


def test_worker_failure_then_retry_persists_and_does_not_touch_finance(client):
    commitment = setup_commitment(client)
    pay(client, commitment["id"])

    class FailedMail:
        def send(self, *_):
            raise OSError("private-provider-message")

    assert process_next_mail(SqlUnitOfWork(), FailedMail())
    with engine.begin() as db:
        assert (
            db.scalar(
                text(
                    "SELECT last_error_code FROM outbox_events WHERE event_type='EmailVerificationRequested'"
                )
            )
            == "MAIL_DELIVERY_FAILED"
        )
        assert db.scalar(text("SELECT balance_minor FROM commitments")) == 750000
        db.execute(
            text(
                "UPDATE outbox_events SET available_at=now() WHERE event_type='EmailVerificationRequested'"
            )
        )
    engine.dispose()
    sender = RecordingMail()
    assert process_next_mail(SqlUnitOfWork(), sender)
    assert len(sender.messages) == 1
    with engine.connect() as db:
        assert db.scalar(
            text(
                "SELECT processed_at IS NOT NULL FROM outbox_events WHERE event_type='EmailVerificationRequested'"
            )
        )
        assert db.scalar(text("SELECT delivery_secret FROM email_verification_tokens")) is None
    assert verify(client, sender.messages[0][1]["token"]).status_code == 200


def test_concurrent_workers_claim_once(client):
    register(client)
    sender, barrier = RecordingMail(), Barrier(2)

    def execute(_):
        barrier.wait(timeout=10)
        return process_next_mail(SqlUnitOfWork(), sender)

    with ThreadPoolExecutor(2) as pool:
        results = list(pool.map(execute, range(2)))
    assert sorted(results) == [False, True]
    assert len(sender.messages) == 1


def test_process_crash_after_delivery_recovers_same_message(client, monkeypatch, tmp_path):
    register(client)
    monkeypatch.setattr(settings(), "mailbox_dir", tmp_path)

    class Crash(BaseException):
        pass

    class CrashAfterDelivery:
        def send(self, event_id, message):
            MailTransport().send(event_id, message)
            raise Crash()

    with pytest.raises(Crash):
        process_next_mail(SqlUnitOfWork(), CrashAfterDelivery())
    assert not process_next_mail(SqlUnitOfWork(), MailTransport())  # lease still held
    original = json.loads(next(tmp_path.glob("*.json")).read_text(encoding="utf-8"))
    with engine.begin() as db:
        db.execute(text("UPDATE outbox_events SET available_at=now()"))
    environment = {**os.environ, "MAILBOX_DIR": str(tmp_path)}
    result = subprocess.run(
        [sys.executable, "-m", "app.worker", "--once"],
        env=environment,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, "worker subprocess failed"
    assert len(list(tmp_path.glob("*.json"))) == 1
    assert json.loads(next(tmp_path.glob("*.json")).read_text(encoding="utf-8")) == original
    assert original["recipient"] not in result.stdout and original["link"] not in result.stdout
    with engine.connect() as db:
        assert db.scalar(
            text(
                "SELECT processed_at IS NOT NULL FROM outbox_events WHERE event_type='EmailVerificationRequested'"
            )
        )


def test_mail_never_retries_forever_and_operator_can_requeue(client, monkeypatch, tmp_path):
    register(client)
    with engine.begin() as db:
        db.execute(text("UPDATE outbox_events SET attempts=8"))
    assert not process_next_mail(SqlUnitOfWork(), RecordingMail())
    result = subprocess.run(
        [sys.executable, "-m", "app.worker", "--once", "--retry-failed"],
        env={**os.environ, "MAILBOX_DIR": str(tmp_path)},
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0
    assert len(list(tmp_path.glob("*.json"))) == 1


def test_legacy_registration_event_is_prepared_durably(client):
    profile = register(client)
    with engine.begin() as db:
        db.execute(text("DELETE FROM email_verification_tokens"))
        db.execute(
            text(
                "UPDATE outbox_events SET payload=jsonb_build_object('resource_id', CAST(:user_id AS text))"
            ),
            {"user_id": profile["user"]["id"]},
        )
    mail = RecordingMail()
    assert process_next_mail(SqlUnitOfWork(), mail)
    assert verify(client, mail.messages[0][1]["token"]).status_code == 200


def test_csrf_origin_and_rate_limit_on_account_routes(client):
    register(client)
    assert (
        client.post("/api/v1/auth/email/resend", headers={"X-CSRF-Token": "bad"}).status_code == 403
    )
    assert (
        client.post(
            "/api/v1/auth/password/forgot",
            headers={"Origin": "https://other.example"},
            json={"email": "david@example.com"},
        ).status_code
        == 403
    )
    for _ in range(20):
        assert forgot(client, "absent@example.com").status_code == 202
    assert forgot(client).status_code == 429


def test_account_and_financial_state_survive_fresh_api_process(client):
    commitment = setup_commitment(client)
    pay(client, commitment["id"])
    forgot(client)
    token = latest_token("reset")
    code = """
import json, sys
from fastapi.testclient import TestClient
from app.main import app
from app.core.database import engine
assert engine.url.database == "nomi_test"
with TestClient(app, headers={"Origin":"http://localhost:3000"}) as client:
    result = client.post("/api/v1/auth/password/reset", json=json.load(sys.stdin))
    print(result.status_code)
"""
    child = subprocess.run(
        [sys.executable, "-c", code],
        input=json.dumps({"token": token, "password": "fresh-process-password"}),
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert child.returncode == 0 and child.stdout.strip() == "200"
    assert client.get("/api/v1/me").status_code == 401
    assert login(client, "fresh-process-password").status_code == 200
    engine.dispose()
    assert client.get(f"/api/v1/commitments/{commitment['id']}").json()["balance_minor"] == 750000
    assert reset(client, token).status_code == 400


def test_additive_migration_preserves_existing_users_and_finance(client):
    from alembic import command
    from alembic.config import Config

    c = setup_commitment(client)
    pay(client, c["id"])
    assert engine.url.database == "nomi_test"
    with engine.connect() as db:
        before = list(db.execute(text("SELECT id, password_hash, status, created_at FROM users")))
        balance = list(db.execute(text("SELECT id, balance_minor, version FROM commitments")))
    # Only the disposable database: reproduce the old schema containing financial data.
    command.downgrade(Config("alembic.ini"), "8c328338b737")
    command.upgrade(Config("alembic.ini"), "head")
    with engine.connect() as db:
        assert (
            list(db.execute(text("SELECT id, password_hash, status, created_at FROM users")))
            == before
        )
        assert (
            list(db.execute(text("SELECT id, balance_minor, version FROM commitments"))) == balance
        )
        assert db.scalar(text("SELECT count(*) FROM transactions")) == 1
        assert db.scalar(text("SELECT bool_and(updated_at=created_at) FROM users"))
    assert login(client, "a-long-test-password").status_code == 200


def test_worker_skips_expired_or_consumed_links(client):
    register(client)
    verify(client, latest_token())
    sender = RecordingMail()
    assert process_next_mail(SqlUnitOfWork(), sender)
    assert sender.messages == []

    forgot(client)
    with engine.begin() as db:
        db.execute(
            text(
                "UPDATE password_reset_tokens SET created_at=now()-interval '2 days', expires_at=now()-interval '1 minute'"
            )
        )
    assert process_next_mail(SqlUnitOfWork(), sender)
    assert sender.messages == []


def test_expired_secrets_are_cleared_even_for_exhausted_mail(client):
    register(client)
    with engine.begin() as db:
        db.execute(
            text(
                "UPDATE email_verification_tokens SET created_at=now()-interval '2 days', expires_at=now()-interval '1 minute'"
            )
        )
        db.execute(text("UPDATE outbox_events SET attempts=8"))
    assert not process_next_mail(SqlUnitOfWork(), RecordingMail())
    with engine.connect() as db:
        assert db.scalar(text("SELECT delivery_secret FROM email_verification_tokens")) is None


def test_smtp_uses_tls_and_stable_message_id(monkeypatch):
    import ssl
    from uuid import uuid4

    from app.modules.identity.infrastructure import mail_transport

    calls, messages = [], []

    class SMTP:
        def __init__(self, host, port, timeout):
            assert host == "smtp.example.com" and port == 587 and timeout == 10

        def __enter__(self):
            return self

        def __exit__(self, *_):
            pass

        def ehlo(self):
            calls.append("ehlo")

        def starttls(self, context):
            assert context.verify_mode == ssl.CERT_REQUIRED and context.check_hostname
            calls.append("tls")

        def send_message(self, message):
            assert "tls" in calls
            messages.append(message)

    monkeypatch.setattr(mail_transport.smtplib, "SMTP", SMTP)
    monkeypatch.setattr(settings(), "mail_backend", "smtp")
    monkeypatch.setattr(settings(), "smtp_host", "smtp.example.com")
    event_id = str(uuid4())
    message = {
        "recipient": "synthetic@example.com",
        "purpose": "changed",
        "token": None,
        "expires_at": None,
    }
    MailTransport().send(event_id, message)
    MailTransport().send(event_id, message)
    assert len(messages) == 2
    assert messages[0]["Message-ID"] == messages[1]["Message-ID"]
