from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, date, datetime, timedelta
from threading import Barrier
from uuid import UUID, uuid4

import pytest
from conftest import register
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from app.core.database import engine
from app.main import app
from app.modules.audit.repository import AuditRepository
from app.modules.commitments.domain import Commitment
from app.modules.commitments.repository import CommitmentRepository
from app.modules.workspaces.repository import WorkspaceRepository
from app.shared.errors import DomainError
from app.shared.uow import EffectsRepository


def contact(client, name="Juan Pérez"):
    response = client.post("/api/v1/contacts", json={"name": name})
    assert response.status_code == 201, response.text
    return response.json()["id"]


def create(client, contact_id, key=None, amount=1000000, **extra):
    return client.post(
        "/api/v1/commitments",
        headers={"Idempotency-Key": str(key or uuid4())},
        json={
            "contact_id": contact_id,
            "direction": "receivable",
            "original_amount_minor": amount,
            "currency_code": "MXN",
            **extra,
        },
    )


def pay(client, commitment_id, amount=250000, version=1, key=None):
    return client.post(
        f"/api/v1/commitments/{commitment_id}/transactions",
        headers={"Idempotency-Key": str(key or uuid4())},
        json={
            "amount_minor": amount,
            "expected_version": version,
            "occurred_at": "2026-10-02T17:00:00Z",
            "note": "Transferencia",
        },
    )


def setup_commitment(client):
    register(client)
    result = create(client, contact(client))
    assert result.status_code == 201
    return result.json()


def test_full_vertical_slice(client):
    profile = register(client)
    assert profile["membership"]["role"] == "owner"
    assert profile["workspace"]["currency_code"] == "MXN"
    assert client.get("/api/v1/dashboard/summary").json()["active_commitments"] == 0
    created = create(client, contact(client)).json()
    assert created["version"] == 1 and created["balance_minor"] == 1000000
    response = pay(client, created["id"])
    assert response.status_code == 201, response.text
    updated = response.json()["commitment"]
    assert (updated["balance_minor"], updated["version"], updated["payment_state"]) == (
        750000,
        2,
        "partial",
    )
    dashboard = client.get("/api/v1/dashboard/summary").json()
    assert dashboard["receivable_balance_minor"] == 750000
    history = client.get(f"/api/v1/commitments/{created['id']}/transactions").json()["items"]
    assert (
        created["original_amount_minor"] - sum(t["amount_minor"] for t in history)
        == updated["balance_minor"]
    )
    with engine.connect() as db:
        assert (
            db.scalar(
                text(
                    "SELECT count(*) FROM audit_events WHERE action = 'transaction.payment_registered'"
                )
            )
            == 1
        )
        assert (
            db.scalar(
                text("SELECT count(*) FROM outbox_events WHERE event_type = 'PaymentRegistered'")
            )
            == 1
        )


def test_duplicate_create_and_replay_snapshot(client):
    register(client)
    cid, key = contact(client), uuid4()
    first = create(client, cid, key)
    assert create(client, cid, key).json() == first.json()
    pay(client, first.json()["id"])
    assert create(client, cid, key).json() == first.json()
    conflict = create(client, cid, key, amount=500000)
    assert conflict.status_code == 409
    assert conflict.json()["code"] == "IDEMPOTENCY_KEY_CONFLICT"


def test_payment_replay_after_later_payment(client):
    commitment = setup_commitment(client)
    key = uuid4()
    first = pay(client, commitment["id"], key=key)
    assert first.status_code == 201
    assert pay(client, commitment["id"], version=2).status_code == 201
    assert pay(client, commitment["id"], key=key).json() == first.json()
    assert pay(client, commitment["id"], key=key, amount=1).status_code == 409
    assert client.get(f"/api/v1/commitments/{commitment['id']}").json()["balance_minor"] == 500000


@pytest.mark.parametrize("amount", [0, -1, 1000001, 1.5, True])
def test_invalid_payments_leave_balance_unchanged(client, amount):
    commitment = setup_commitment(client)
    assert pay(client, commitment["id"], amount=amount).status_code == 422
    assert client.get(f"/api/v1/commitments/{commitment['id']}").json()["balance_minor"] == 1000000


def test_full_payment_excluded_and_paid_rejects_payment(client):
    commitment = setup_commitment(client)
    paid = pay(client, commitment["id"], amount=1000000).json()["commitment"]
    assert paid["lifecycle_status"] == "paid"
    assert paid["timing_state"] is None
    assert client.get("/api/v1/dashboard/summary").json()["active_commitments"] == 0
    assert (
        pay(client, commitment["id"], amount=1, version=2).json()["code"] == "COMMITMENT_NOT_OPEN"
    )


def test_workspace_isolation_and_untrusted_authority(client):
    commitment = setup_commitment(client)
    with TestClient(app, headers={"Origin": "http://localhost:3000"}) as other:
        register(other, "other@example.com")
        assert other.get(f"/api/v1/commitments/{commitment['id']}").status_code == 404
        assert other.get(f"/api/v1/commitments/{commitment['id']}/transactions").status_code == 404
        assert pay(other, commitment["id"]).status_code == 404
        assert create(other, commitment["contact_id"]).status_code == 404
        assert other.get("/api/v1/dashboard/summary").json()["active_commitments"] == 0
        assert (
            other.post(
                "/api/v1/contacts", json={"name": "X", "workspace_id": commitment["id"]}
            ).status_code
            == 422
        )


def test_auth_csrf_revocation_and_cookie_flags(client):
    assert client.get("/api/v1/me").status_code == 401
    register(client)
    old_token = client.cookies["nomi_session"]
    assert (
        client.post(
            "/api/v1/contacts", headers={"X-CSRF-Token": "wrong"}, json={"name": "X"}
        ).status_code
        == 403
    )
    assert (
        client.post(
            "/api/v1/contacts", headers={"Origin": "https://evil.example"}, json={"name": "X"}
        ).status_code
        == 403
    )
    assert client.post("/api/v1/auth/logout").status_code == 204
    client.cookies.set("nomi_session", old_token)
    assert client.get("/api/v1/me").status_code == 401
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "DAVID@example.com", "password": "a-long-test-password"},
    )
    assert response.status_code == 200
    assert "HttpOnly" in response.headers.get_list("set-cookie")[0]
    assert "SameSite=lax" in response.headers.get_list("set-cookie")[0]


def test_expired_session(client):
    register(client)
    with engine.begin() as db:
        db.execute(text("UPDATE sessions SET expires_at = now() - interval '1 minute'"))
    assert client.get("/api/v1/me").status_code == 401


@pytest.mark.parametrize(
    "repository,method", [(AuditRepository, "record"), (EffectsRepository, "emit")]
)
def test_payment_rollback_when_critical_effect_fails(client, monkeypatch, repository, method):
    commitment = setup_commitment(client)
    with engine.connect() as db:
        before = db.scalar(text("SELECT count(*) FROM idempotency_records"))

    def fail(*args, **kwargs):
        raise RuntimeError("Injected failure")

    monkeypatch.setattr(repository, method, fail)
    assert pay(client, commitment["id"]).status_code == 500
    with engine.connect() as db:
        assert db.scalar(text("SELECT count(*) FROM transactions")) == 0
        assert db.scalar(text("SELECT balance_minor FROM commitments")) == 1000000
        assert db.scalar(text("SELECT version FROM commitments")) == 1
        assert db.scalar(text("SELECT count(*) FROM idempotency_records")) == before


def test_registration_rollback(client, monkeypatch):
    def fail(*args, **kwargs):
        raise RuntimeError("Injected failure")

    monkeypatch.setattr(WorkspaceRepository, "create_personal", fail)
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "test@example.com",
            "display_name": "Test",
            "password": "a-long-test-password",
        },
    )
    assert response.status_code == 500
    with engine.connect() as db:
        assert db.scalar(text("SELECT count(*) FROM users")) == 0


def test_concurrent_payments_only_one_wins(client, monkeypatch):
    commitment = setup_commitment(client)
    barrier = Barrier(2)
    original = CommitmentRepository.save_payment

    def synchronized(self, commitment, expected_version):
        barrier.wait(timeout=10)
        return original(self, commitment, expected_version)

    monkeypatch.setattr(CommitmentRepository, "save_payment", synchronized)

    def execute(amount):
        with TestClient(
            app, headers=dict(client.headers), cookies=dict(client.cookies)
        ) as parallel:
            return pay(parallel, commitment["id"], amount=amount)

    with ThreadPoolExecutor(2) as pool:
        results = list(pool.map(execute, [700000, 500000]))
    assert sorted(result.status_code for result in results) == [201, 409]
    with engine.connect() as db:
        assert db.scalar(text("SELECT count(*) FROM transactions")) == 1
        assert db.scalar(text("SELECT version FROM commitments")) == 2
        assert db.scalar(text("SELECT balance_minor FROM commitments")) in (300000, 500000)


def test_concurrent_identical_key_has_one_effect(client):
    commitment = setup_commitment(client)
    key, barrier = uuid4(), Barrier(2)

    def execute(_):
        with TestClient(
            app, headers=dict(client.headers), cookies=dict(client.cookies)
        ) as parallel:
            barrier.wait(timeout=10)
            return pay(parallel, commitment["id"], key=key)

    with ThreadPoolExecutor(2) as pool:
        results = list(pool.map(execute, range(2)))
    assert [r.status_code for r in results] == [201, 201]
    assert results[0].json() == results[1].json()
    with engine.connect() as db:
        assert db.scalar(text("SELECT count(*) FROM transactions")) == 1


def test_contact_duplicates_allowed_archived_contact_rejected(client):
    register(client)
    first, second = contact(client), contact(client)
    assert first != second
    with engine.begin() as db:
        db.execute(
            text("UPDATE contacts SET archived_at = now() WHERE id = :id"), {"id": UUID(first)}
        )
    assert create(client, first).json()["code"] == "CONTACT_ARCHIVED"


def test_currency_mismatch_and_missing_idempotency(client):
    register(client)
    cid = contact(client)
    assert create(client, cid, currency_code="USD").json()["code"] == "CURRENCY_MISMATCH"
    response = client.post(
        "/api/v1/commitments",
        json={
            "contact_id": cid,
            "direction": "receivable",
            "original_amount_minor": 100,
            "currency_code": "MXN",
        },
    )
    assert response.status_code == 422


def test_dashboard_timezone_and_exclusions(client, monkeypatch):
    from app.modules.reporting import application

    monkeypatch.setattr(application, "now", lambda: datetime(2026, 10, 3, 2, 0, tzinfo=UTC))
    register(client)
    cid = contact(client)
    # In Mexico City it is still October 2: due today is not overdue.
    create(client, cid, amount=100, due_date="2026-10-02")
    create(client, cid, amount=200, due_date="2026-10-01", direction="payable")
    create(client, cid, amount=300)
    cancelled = create(client, cid, amount=400).json()
    with engine.begin() as db:
        db.execute(
            text("UPDATE commitments SET lifecycle_status='cancelled' WHERE id=:id"),
            {"id": UUID(cancelled["id"])},
        )
    summary = client.get("/api/v1/dashboard/summary").json()
    assert summary == {
        "currency_code": "MXN",
        "receivable_balance_minor": 400,
        "payable_balance_minor": 200,
        "overdue_balance_minor": 200,
        "due_soon_balance_minor": 100,
        "active_commitments": 3,
    }


def test_postgresql_constraints(client):
    setup_commitment(client)
    for statement in (
        "UPDATE commitments SET balance_minor=-1",
        "UPDATE commitments SET balance_minor=1000001",
        "UPDATE commitments SET version=0",
        "UPDATE commitments SET lifecycle_status='paid'",
    ):
        with pytest.raises(IntegrityError), engine.begin() as db:
            db.execute(text(statement))


def test_cursor_pagination_and_contract(client):
    register(client)
    for name in ("Ana", "Juan", "Sara"):
        contact(client, name)
    first = client.get("/api/v1/contacts?limit=2").json()
    second = client.get(f"/api/v1/contacts?limit=2&cursor={first['next_cursor']}").json()
    assert len(first["items"]) == 2 and len(second["items"]) == 1
    assert not ({c["id"] for c in first["items"]} & {c["id"] for c in second["items"]})
    assert second["next_cursor"] is None
    assert client.get("/api/v1/contacts?limit=1000").status_code == 422
    assert client.get("/openapi.json").json()["openapi"].startswith("3.1")


def test_invalid_input_does_not_echo_password(client):
    secret = "SECRET-THAT-MUST-NOT-LEAK"
    response = client.post(
        "/api/v1/auth/register", json={"email": "invalid", "display_name": "D", "password": secret}
    )
    assert response.status_code == 422
    assert secret not in response.text
    assert response.headers["content-type"] == "application/problem+json"
    assert response.headers["x-request-id"] == response.json()["request_id"]


def test_domain_states_and_balance_property():
    today = date(2026, 10, 2)
    base = dict(
        id=uuid4(),
        workspace_id=uuid4(),
        contact_id=uuid4(),
        direction="receivable",
        currency_code="MXN",
        concept=None,
        due_date=today,
    )
    for original in (1, 2, 100, 1000000):
        for amount in {1, original, max(1, original // 2)}:
            c = Commitment(**base, original_amount_minor=original, balance_minor=original)
            paid = c.pay(amount, 1)
            assert 0 <= paid.balance_minor <= original
            assert paid.balance_minor + amount == original
            assert paid.version == 2
    for days, state in ((-1, "overdue"), (0, "due_soon"), (7, "due_soon"), (8, "upcoming")):
        c = Commitment(
            **{**base, "due_date": today + timedelta(days=days)},
            original_amount_minor=100,
            balance_minor=100,
        )
        assert c.timing_state(today) == state
    with pytest.raises(DomainError, match="saldo cambió"):
        c.pay(1, 99)
