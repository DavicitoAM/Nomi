from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from uuid import uuid4

import pytest
from conftest import register
from fastapi.testclient import TestClient
from sqlalchemy import text
from test_core import contact, create, pay, setup_commitment

from app.core.config import settings
from app.core.database import engine
from app.main import app
from app.modules.audit.infrastructure.repository import AuditRepository
from app.modules.commitments.infrastructure.repository import CommitmentRepository
from app.shared.uow import EffectsRepository


def reverse(client, payment_id, version=2, key=None, **extra):
    return client.post(
        f"/api/v1/transactions/{payment_id}/reverse",
        headers={"Idempotency-Key": str(key or uuid4())},
        json={"expected_version": version, **extra},
    )


@pytest.mark.parametrize("amount", [1, 250000, 1000000])
def test_reverse_restores_balance_and_dashboard(client, amount):
    c = setup_commitment(client)
    p = pay(client, c["id"], amount=amount).json()["transaction"]
    response = reverse(client, p["id"], note="Corrección")
    assert response.status_code == 201, response.text
    result = response.json()
    assert result["commitment"]["balance_minor"] == 1000000
    assert result["commitment"]["lifecycle_status"] == "open"
    assert result["commitment"]["version"] == 3
    assert result["transaction"]["amount_minor"] == amount
    assert result["transaction"]["reversal_of_transaction_id"] == p["id"]
    assert client.get("/api/v1/dashboard/summary").json()["receivable_balance_minor"] == "1000000"
    history = client.get(f"/api/v1/commitments/{c['id']}/transactions?limit=1").json()
    assert history["items"][0]["id"] == p["id"]
    assert history["items"][0]["reversed_by_transaction_id"] == result["transaction"]["id"]
    page2 = client.get(
        f"/api/v1/commitments/{c['id']}/transactions?cursor={history['next_cursor']}"
    ).json()
    assert page2["items"][0]["type"] == "reversal"
    with engine.connect() as db:
        assert (
            db.scalar(
                text(
                    "SELECT count(*) FROM audit_events WHERE action='transaction.payment_reversed'"
                )
            )
            == 1
        )
        assert (
            db.scalar(text("SELECT count(*) FROM outbox_events WHERE event_type='PaymentReversed'"))
            == 1
        )


def test_reverse_retry_and_conflicts(client):
    c = setup_commitment(client)
    p = pay(client, c["id"]).json()["transaction"]
    key = uuid4()
    first = reverse(client, p["id"], key=key)
    assert first.status_code == 201
    assert pay(client, c["id"], amount=100, version=3).status_code == 201
    assert reverse(client, p["id"], key=key).json() == first.json()
    assert (
        reverse(client, p["id"], key=key, note="different").json()["code"]
        == "IDEMPOTENCY_KEY_CONFLICT"
    )
    assert reverse(client, p["id"], version=4).json()["code"] == "PAYMENT_ALREADY_REVERSED"
    assert (
        reverse(client, first.json()["transaction"]["id"], version=4).json()["code"]
        == "NOT_A_PAYMENT"
    )


def test_reverse_cancelled_and_stale_version(client):
    c = setup_commitment(client)
    p = pay(client, c["id"]).json()["transaction"]
    assert reverse(client, p["id"], version=1).json()["code"] == "VERSION_CONFLICT"
    with engine.begin() as db:
        db.execute(text("UPDATE commitments SET lifecycle_status='cancelled'"))
    assert reverse(client, p["id"]).json()["code"] == "COMMITMENT_CANCELLED"
    with engine.connect() as db:
        assert db.scalar(text("SELECT balance_minor FROM commitments")) == 750000


def test_reverse_authorization_and_cursor_scope(client):
    c = setup_commitment(client)
    p = pay(client, c["id"]).json()["transaction"]
    with TestClient(app, headers={"Origin": "http://localhost:3000"}) as other:
        assert reverse(other, p["id"]).status_code == 401
        register(other, "other@example.com")
        assert reverse(other, p["id"]).json()["code"] == "TRANSACTION_NOT_FOUND"
        assert reverse(other, uuid4()).json()["code"] == "TRANSACTION_NOT_FOUND"
    client.headers["X-CSRF-Token"] = "invalid"
    assert reverse(client, p["id"]).status_code == 403
    assert (
        client.get(f"/api/v1/commitments/{c['id']}/transactions?cursor={uuid4()}").status_code
        == 422
    )


@pytest.mark.parametrize(
    "extra",
    [
        {"amount_minor": 1},
        {"currency_code": "USD"},
        {"expected_version": True},
        {"expected_version": 0},
        {"note": "x" * 501},
    ],
)
def test_reverse_rejects_untrusted_values(client, extra):
    c = setup_commitment(client)
    p = pay(client, c["id"]).json()["transaction"]
    assert reverse(client, p["id"], **extra).status_code == 422


@pytest.mark.parametrize(
    "repository,method", [(AuditRepository, "record"), (EffectsRepository, "emit")]
)
def test_reverse_rolls_back_all_effects(client, monkeypatch, repository, method):
    c = setup_commitment(client)
    p = pay(client, c["id"]).json()["transaction"]
    key = uuid4()

    def fail(*args, **kwargs):
        raise RuntimeError("Injected failure")

    with monkeypatch.context() as patch:
        patch.setattr(repository, method, fail)
        assert reverse(client, p["id"], key=key).status_code == 500
    with engine.connect() as db:
        assert db.scalar(text("SELECT count(*) FROM transactions")) == 1
        assert db.scalar(text("SELECT balance_minor FROM commitments")) == 750000
        assert db.scalar(text("SELECT version FROM commitments")) == 2
        assert (
            db.scalar(
                text("SELECT count(*) FROM idempotency_records WHERE operation='ReversePayment'")
            )
            == 0
        )
    assert reverse(client, p["id"], key=key).status_code == 201


@pytest.mark.parametrize("race", ["reverse", "payment", "same_key"])
def test_reverse_concurrency(client, monkeypatch, race):
    c = setup_commitment(client)
    p = pay(client, c["id"]).json()["transaction"]
    barrier, key = Barrier(2), uuid4()
    original = CommitmentRepository.save_payment
    if race != "same_key":

        def synchronized(self, value, version):
            barrier.wait(timeout=10)
            return original(self, value, version)

        monkeypatch.setattr(CommitmentRepository, "save_payment", synchronized)

    def execute(index):
        with TestClient(
            app, headers=dict(client.headers), cookies=dict(client.cookies)
        ) as parallel:
            if race == "same_key":
                barrier.wait(timeout=10)
            if race == "payment" and index == 1:
                return pay(parallel, c["id"], amount=100, version=2)
            return reverse(parallel, p["id"], key=key if race == "same_key" else None)

    with ThreadPoolExecutor(2) as pool:
        results = list(pool.map(execute, range(2)))
    assert sorted(r.status_code for r in results) == (
        [201, 201] if race == "same_key" else [201, 409]
    )
    if race == "same_key":
        assert results[0].json() == results[1].json()
    with engine.connect() as db:
        assert db.scalar(text("SELECT count(*) FROM transactions")) == 2
        assert db.scalar(text("SELECT version FROM commitments")) == 3
        assert db.scalar(text("SELECT balance_minor FROM commitments")) in (1000000, 749900)


def test_large_aggregate_is_exact_decimal_string(client):
    c = setup_commitment(client)
    with engine.begin() as db:
        db.execute(
            text("""
            INSERT INTO commitments
            (id, workspace_id, contact_id, direction, original_amount_minor, balance_minor,
             currency_code, lifecycle_status, version, created_at, updated_at)
            SELECT gen_random_uuid(), workspace_id, contact_id, direction, 9000000000000,
                   9000000000000, currency_code, 'open', 1, now(), now()
            FROM commitments CROSS JOIN generate_series(1, 1002) WHERE id=:id
        """),
            {"id": c["id"]},
        )
    assert client.get("/api/v1/dashboard/summary").json()["receivable_balance_minor"] == str(
        1002 * 9000000000000 + 1000000
    )


def test_unverified_account_is_blocked_outside_development(client, monkeypatch):
    register(client)
    monkeypatch.setattr(settings(), "environment", "production")
    assert client.get("/api/v1/me").status_code == 200
    assert client.get("/api/v1/dashboard/summary").json()["code"] == "EMAIL_NOT_VERIFIED"
    assert client.post("/api/v1/contacts", json={"name": "Juan"}).status_code == 403
    with engine.begin() as db:
        db.execute(text("UPDATE users SET status='active'"))
    assert client.get("/api/v1/dashboard/summary").status_code == 200
    assert client.post("/api/v1/auth/logout").status_code == 204


def test_search_filters_and_contact_names_are_scoped_server_side(client):
    from datetime import timedelta
    from zoneinfo import ZoneInfo

    from app.shared.context import now

    register(client)
    today = now().astimezone(ZoneInfo("America/Mexico_City")).date()
    ids = []
    for name in ("Ana", "Juan", "Sara"):
        ids.append(
            create(
                client,
                contact(client, name),
                concept="Consulta",
                due_date=(today - timedelta(days=1)).isoformat(),
            ).json()["id"]
        )
    first = client.get("/api/v1/commitments?limit=1").json()
    second = client.get(f"/api/v1/commitments?limit=1&cursor={first['next_cursor']}").json()
    target = second["items"][0]
    result = client.get(f"/api/v1/commitments?limit=1&search={target['contact_name']}").json()
    assert result["items"][0]["id"] == target["id"]
    assert result["items"][0]["contact_name"] == target["contact_name"]
    assert len(client.get("/api/v1/commitments?filter=overdue").json()["items"]) == 3
    assert client.get("/api/v1/commitments?filter=due_soon").json()["items"] == []
    assert client.get("/api/v1/commitments?filter=payable").json()["items"] == []
    assert client.get("/api/v1/commitments?search=%25").json()["items"] == []
    assert client.get("/api/v1/commitments?filter=invalid").status_code == 422
    assert pay(client, ids[0], amount=1000000).status_code == 201
    assert len(client.get("/api/v1/commitments?filter=overdue").json()["items"]) == 2
    with TestClient(app, headers={"Origin": "http://localhost:3000"}) as other:
        register(other, "other@example.com")
        assert other.get("/api/v1/commitments?search=Consulta").json()["items"] == []
