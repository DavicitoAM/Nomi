import asyncio
import hashlib
import json
from concurrent.futures import ThreadPoolExecutor, TimeoutError
from threading import Barrier, Event
from uuid import uuid4

import pytest
from conftest import register
from fastapi.testclient import TestClient
from sqlalchemy import text
from test_core import contact, create, pay, setup_commitment

from app.core.database import engine
from app.core.request_limits import RequestLimits
from app.main import app
from app.maintenance import cleanup
from app.modules.audit.infrastructure.repository import AuditRepository
from app.modules.commitments.infrastructure.repository import CommitmentRepository
from app.modules.contacts.infrastructure.repository import ContactRepository
from app.shared.uow import EffectsRepository


def cancel(client, c, key=None):
    return client.post(
        f"/api/v1/commitments/{c['id']}/cancel",
        json={"expected_version": c["version"]},
        headers={"Idempotency-Key": str(key or uuid4())},
    )


@pytest.mark.parametrize("includes_null_notes", [False, True])
def test_create_replays_persisted_pre_upgrade_requests(client, includes_null_notes):
    register(client)
    contact_id, key = contact(client), str(uuid4())
    created = create(client, contact_id, key).json()
    payload = {
        "contact_id": contact_id,
        "direction": "receivable",
        "original_amount_minor": 1000000,
        "currency_code": "MXN",
        "concept": None,
        "due_date": None,
    }
    if includes_null_notes:
        payload["notes"] = None
    digest = hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    with engine.begin() as db:
        db.execute(
            text(
                "UPDATE idempotency_records SET request_hash=:hash, "
                "response=response::jsonb - 'notes' WHERE idempotency_key=:key"
            ),
            {"hash": digest, "key": key},
        )
    replay = create(client, contact_id, key, notes=None)
    assert replay.status_code == 201 and replay.json() == created
    assert (
        create(client, contact_id, key, notes="A different request").json()["code"]
        == "IDEMPOTENCY_KEY_CONFLICT"
    )
    with engine.connect() as db:
        assert db.scalar(text("SELECT count(*) FROM commitments")) == 1


def test_contact_lifecycle_preserves_finance_and_summary(client):
    c = setup_commitment(client)
    pay(client, c["id"])
    path = f"/api/v1/contacts/{c['contact_id']}"
    detail = client.get(path).json()
    assert detail["summary"] == {
        "receivable_balance_minor": "750000",
        "payable_balance_minor": "0",
        "active_commitments": 1,
    }
    changed = client.patch(
        path,
        json={
            "expected_updated_at": detail["updated_at"],
            "name": "Juan actualizado",
            "notes": "Información descriptiva",
        },
    )
    assert changed.status_code == 200
    assert (
        client.patch(
            path, json={"expected_updated_at": detail["updated_at"], "name": "Old"}
        ).status_code
        == 409
    )
    body = {"expected_updated_at": changed.json()["updated_at"]}
    first = client.post(path + "/archive", json=body)
    assert first.status_code == 200 and first.json()["archived_at"]
    assert client.post(path + "/archive", json=body).json() == first.json()
    assert not client.get("/api/v1/contacts").json()["items"]
    assert (
        len(client.get("/api/v1/contacts?status=archived&search=actualizado").json()["items"]) == 1
    )
    assert create(client, c["contact_id"]).json()["code"] == "CONTACT_ARCHIVED"
    assert client.get(path).json()["summary"] == detail["summary"]
    restored = client.post(
        path + "/restore", json={"expected_updated_at": first.json()["updated_at"]}
    )
    assert restored.status_code == 200 and restored.json()["archived_at"] is None
    assert create(client, c["contact_id"]).status_code == 201
    history = client.get(f"/api/v1/commitments/{c['id']}/transactions").json()["items"]
    assert len(history) == 1
    with engine.connect() as db:
        assert (
            db.scalar(text("SELECT count(*) FROM audit_events WHERE action='contact.archived'"))
            == 1
        )


def test_cancel_replay_preserves_balance_and_excludes_dashboard(client):
    c = setup_commitment(client)
    c = pay(client, c["id"]).json()["commitment"]
    key = uuid4()
    response = cancel(client, c, key)
    assert response.status_code == 200
    result = response.json()
    assert (result["balance_minor"], result["version"], result["lifecycle_status"]) == (
        750000,
        3,
        "cancelled",
    )
    assert cancel(client, c, key).json() == result
    assert cancel(client, {**c, "version": 3}, key).json()["code"] == "IDEMPOTENCY_KEY_CONFLICT"
    assert cancel(client, result).json()["code"] == "COMMITMENT_NOT_OPEN"
    assert pay(client, c["id"], version=3).status_code == 422
    assert client.get("/api/v1/dashboard/summary").json()["receivable_balance_minor"] == "0"
    assert (
        client.get(f"/api/v1/contacts/{c['contact_id']}").json()["summary"]["active_commitments"]
        == 0
    )
    assert len(client.get(f"/api/v1/commitments/{c['id']}/transactions").json()["items"]) == 1


def test_paid_cannot_cancel_and_closed_can_edit_descriptions(client):
    c = setup_commitment(client)
    c = pay(client, c["id"], amount=1000000).json()["commitment"]
    assert cancel(client, c).status_code == 409
    path = f"/api/v1/commitments/{c['id']}"
    response = client.patch(
        path,
        json={
            "expected_version": c["version"],
            "concept": "Corregido",
            "notes": "Nota",
            "due_date": "2026-11-01",
        },
    )
    assert response.status_code == 200
    assert response.json()["balance_minor"] == 0 and response.json()["lifecycle_status"] == "paid"
    assert response.json()["notes"] == "Nota"
    assert (
        client.patch(path, json={"expected_version": c["version"], "concept": "Old"}).status_code
        == 409
    )
    for field, value in [
        ("original_amount_minor", 1),
        ("balance_minor", 1),
        ("direction", "payable"),
        ("contact_id", str(uuid4())),
        ("currency_code", "USD"),
    ]:
        assert client.patch(path, json={"expected_version": 3, field: value}).status_code == 422


def test_new_routes_deny_other_workspace_and_null_name(client):
    c = setup_commitment(client)
    with TestClient(app, headers={"Origin": "http://localhost:3000"}) as other:
        register(other, "other@example.com")
        assert cancel(other, c).status_code == 404
        assert (
            other.patch(
                f"/api/v1/commitments/{c['id']}", json={"expected_version": 1, "notes": "X"}
            ).status_code
            == 404
        )
        path = f"/api/v1/contacts/{c['contact_id']}"
        version = client.get(path).json()["updated_at"]
        assert other.get(path).status_code == 404
        assert (
            other.patch(path, json={"expected_updated_at": version, "name": "X"}).status_code == 404
        )
        for action in ("archive", "restore"):
            assert (
                other.post(path + "/" + action, json={"expected_updated_at": version}).status_code
                == 404
            )
        assert (
            client.patch(path, json={"expected_updated_at": version, "name": None}).status_code
            == 422
        )


@pytest.mark.parametrize(
    "repository,method", [(AuditRepository, "record"), (EffectsRepository, "emit")]
)
@pytest.mark.parametrize("operation", ["cancel", "archive", "edit"])
def test_lifecycle_rollback(client, monkeypatch, repository, method, operation):
    c = setup_commitment(client)

    def fail(*args, **kwargs):
        raise RuntimeError("Injected failure")

    monkeypatch.setattr(repository, method, fail)
    if operation == "cancel":
        response = cancel(client, c)
    elif operation == "edit":
        response = client.patch(
            f"/api/v1/commitments/{c['id']}", json={"expected_version": 1, "concept": "X"}
        )
    else:
        path = f"/api/v1/contacts/{c['contact_id']}"
        version = client.get(path).json()["updated_at"]
        response = client.post(path + "/archive", json={"expected_updated_at": version})
    assert response.status_code == 500
    current = client.get(f"/api/v1/commitments/{c['id']}").json()
    assert current["version"] == 1 and current["lifecycle_status"] == "open"
    assert client.get(f"/api/v1/contacts/{c['contact_id']}").json()["archived_at"] is None


def test_cancel_payment_race_has_one_commit(client, monkeypatch):
    c = setup_commitment(client)
    barrier = Barrier(2)
    original = CommitmentRepository.get

    def synchronized(*args, **kwargs):
        result = original(*args, **kwargs)
        barrier.wait(timeout=10)
        return result

    monkeypatch.setattr(CommitmentRepository, "get", synchronized)

    def request(kind):
        with TestClient(app, headers=dict(client.headers), cookies=client.cookies) as concurrent:
            return cancel(concurrent, c) if kind == "cancel" else pay(concurrent, c["id"])

    with ThreadPoolExecutor(max_workers=2) as pool:
        responses = list(pool.map(request, ["cancel", "pay"]))
    assert sum(r.status_code in (200, 201) for r in responses) == 1
    assert sum(r.status_code == 409 for r in responses) == 1


@pytest.mark.parametrize("first", ["archive", "create"])
def test_contact_archive_and_creation_serialize(client, monkeypatch, first):
    register(client)
    contact_id = contact(client)
    path = f"/api/v1/contacts/{contact_id}"
    version = client.get(path).json()["updated_at"]
    locked, release, second_started = Event(), Event(), Event()
    method = "archive" if first == "archive" else "require_active"
    original = getattr(ContactRepository, method)

    def hold_lock(*args, **kwargs):
        result = original(*args, **kwargs)
        locked.set()
        assert release.wait(10)
        return result

    monkeypatch.setattr(ContactRepository, method, hold_lock)

    def request(kind, second=False):
        with TestClient(app, headers=dict(client.headers), cookies=client.cookies) as concurrent:
            if second:
                second_started.set()
            if kind == "archive":
                return concurrent.post(path + "/archive", json={"expected_updated_at": version})
            return create(concurrent, contact_id)

    with ThreadPoolExecutor(max_workers=2) as pool:
        winner = pool.submit(request, first)
        try:
            assert locked.wait(10)
            loser = pool.submit(request, "create" if first == "archive" else "archive", True)
            assert second_started.wait(5)
            with pytest.raises(TimeoutError):
                loser.result(timeout=0.2)
        finally:
            release.set()
        assert winner.result(timeout=10).status_code in (200, 201)
        following = loser.result(timeout=10)
    if first == "archive":
        assert following.json()["code"] == "CONTACT_ARCHIVED"
    else:
        assert following.status_code == 200
    with engine.connect() as db:
        assert db.scalar(text("SELECT count(*) FROM commitments")) == (first == "create")


@pytest.mark.parametrize(
    "chunks,headers,expected",
    [
        ([b"a" * 10000, b"b" * 10000], [], 413),
        ([b"{}"], [(b"content-length", b"1")], 400),
        ([b"{}"], [(b"content-encoding", b"gzip")], 415),
        ([b"{}"], [(b"content-length", b"2"), (b"content-length", b"2")], 400),
        ([b"{", b"}"], [], 200),
    ],
)
def test_actual_body_limit_before_app(chunks, headers, expected):
    async def exercise():
        messages, called = [], []
        pending = list(chunks)

        async def receive():
            return {"type": "http.request", "body": pending.pop(0), "more_body": bool(pending)}

        async def send(message):
            messages.append(message)

        async def downstream(scope, receive, send):
            called.append(True)
            assert (await receive())["body"] == b"{}"
            await send({"type": "http.response.start", "status": 200, "headers": []})

        await RequestLimits(downstream)(
            {"type": "http", "method": "POST", "path": "/api/v1/contacts", "headers": headers},
            receive,
            send,
        )
        assert messages[0]["status"] == expected
        assert bool(called) == (expected == 200)

    asyncio.run(exercise())


def test_slow_body_times_out_before_app():
    async def exercise():
        messages = []

        async def receive():
            await asyncio.sleep(1)

        async def send(message):
            messages.append(message)

        async def downstream(*args):
            pytest.fail("Slow request reached application")

        await RequestLimits(downstream, timeout=0.01)(
            {"type": "http", "method": "POST", "path": "/", "headers": []}, receive, send
        )
        assert messages[0]["status"] == 408

    asyncio.run(exercise())


def test_export_is_scoped_complete_and_without_credentials(client):
    c = setup_commitment(client)
    pay(client, c["id"])
    with TestClient(app, headers={"Origin": "http://localhost:3000"}) as other:
        register(other, "private-other@example.com")
        other.post("/api/v1/contacts", json={"name": "OTHER PRIVATE CONTACT"})
    response = client.post("/api/v1/exports/workspace", json={})
    assert response.status_code == 200
    assert response.headers["content-disposition"].startswith("attachment;")
    result = response.json()
    assert result["format_version"] == "nomi-core-0.1"
    assert len(result["contacts"]) == len(result["commitments"]) == len(result["transactions"]) == 1
    assert result["transactions"][0]["commitment_id"] == c["id"]
    for forbidden in (
        "password_hash",
        "token_hash",
        "delivery_secret",
        "sessions",
        "PRIVATE CONTACT",
        "private-other",
    ):
        assert forbidden not in response.text
    assert (
        client.post(
            "/api/v1/exports/workspace", json={}, headers={"X-CSRF-Token": "bad"}
        ).status_code
        == 403
    )


def test_export_limit_is_explicit_and_not_silent_truncation(client, monkeypatch):
    from app.modules.reporting.application import export

    c = setup_commitment(client)
    pay(client, c["id"])
    monkeypatch.setattr(export, "MAX_EXPORT_ROWS", 2)
    assert (
        client.post("/api/v1/exports/workspace", json={}).json()["code"] == "EXPORT_LIMIT_EXCEEDED"
    )
    monkeypatch.setattr(export, "MAX_EXPORT_ROWS", 10000)
    monkeypatch.setattr(export, "MAX_EXPORT_BYTES", 10)
    assert (
        client.post("/api/v1/exports/workspace", json={}).json()["code"] == "EXPORT_LIMIT_EXCEEDED"
    )
    with engine.connect() as db:
        assert (
            db.scalar(text("SELECT count(*) FROM audit_events WHERE action='workspace.exported'"))
            == 0
        )


def test_export_explains_reversal_in_both_directions(client):
    c = setup_commitment(client)
    payment = pay(client, c["id"]).json()["transaction"]
    reversal = client.post(
        f"/api/v1/transactions/{payment['id']}/reverse",
        json={"expected_version": 2},
        headers={"Idempotency-Key": str(uuid4())},
    )
    assert reversal.status_code == 201, reversal.text
    data = client.post("/api/v1/exports/workspace", json={}).json()
    movements = {row["id"]: row for row in data["transactions"]}
    reversal_id = reversal.json()["transaction"]["id"]
    assert movements[payment["id"]]["reversed_by_transaction_id"] == reversal_id
    assert movements[reversal_id]["reversal_of_transaction_id"] == payment["id"]
    assert data["commitments"][0]["balance_minor"] == c["original_amount_minor"]


def test_export_uses_one_consistent_snapshot(client, monkeypatch):
    c = setup_commitment(client)
    original = CommitmentRepository.list

    def pay_after_read(*args, **kwargs):
        result = original(*args, **kwargs)
        with TestClient(app, headers=dict(client.headers), cookies=client.cookies) as other:
            assert pay(other, c["id"]).status_code == 201
        return result

    monkeypatch.setattr(CommitmentRepository, "list", pay_after_read)
    result = client.post("/api/v1/exports/workspace", json={})
    assert result.status_code == 200
    assert result.json()["commitments"][0]["balance_minor"] == 1000000
    assert not result.json()["transactions"]
    assert client.get(f"/api/v1/commitments/{c['id']}").json()["balance_minor"] == 750000


def test_cleanup_is_dry_by_default_and_preserves_financial_records(client):
    c = setup_commitment(client)
    pay(client, c["id"])
    with engine.begin() as db:
        db.execute(
            text(
                "UPDATE sessions SET created_at=now()-interval '50 days', expires_at=now()-interval '40 days'"
            )
        )
        db.execute(
            text(
                "UPDATE email_verification_tokens SET created_at=now()-interval '15 days', expires_at=now()-interval '10 days'"
            )
        )
        before = {
            table: db.scalar(text(f"SELECT count(*) FROM {table}"))
            for table in (
                "users",
                "contacts",
                "commitments",
                "transactions",
                "audit_events",
                "outbox_events",
                "idempotency_records",
            )
        }
    dry = cleanup()
    assert dry["mode"] == "dry-run" and dry["tables"]["sessions"] == {"eligible": 1, "removed": 0}
    with engine.connect() as db:
        assert db.scalar(text("SELECT count(*) FROM sessions")) == 1
    applied = cleanup(True)
    assert applied["tables"]["sessions"]["removed"] == 1
    assert applied["tables"]["email_verification_tokens"]["removed"] == 1
    assert cleanup(True)["tables"]["sessions"]["removed"] == 0
    with engine.connect() as db:
        for table, count in before.items():
            assert db.scalar(text(f"SELECT count(*) FROM {table}")) == count
        assert db.scalar(text("SELECT balance_minor FROM commitments")) == 750000


def test_cleanup_keeps_valid_sessions_and_unexpired_tokens(client):
    register(client)
    result = cleanup(True)
    assert all(table["removed"] == 0 for table in result["tables"].values())
    assert client.get("/api/v1/me").status_code == 200
