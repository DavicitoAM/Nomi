"""Financial and security regressions discovered while closing the first slice."""

import ast
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import pytest
from sqlalchemy import text
from test_core import setup_commitment

from app.core.database import engine
from app.modules.commitments.domain.entities import Commitment
from app.shared.errors import DomainError


def test_module_dependency_boundaries():
    modules = Path(__file__).parents[1] / "app/modules"
    for path in modules.rglob("*.py"):
        relative = path.relative_to(modules)
        if len(relative.parts) < 3:
            continue
        owner, layer = relative.parts[:2]
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            imports = (
                [node.module or ""]
                if isinstance(node, ast.ImportFrom)
                else ([item.name for item in node.names] if isinstance(node, ast.Import) else [])
            )
            for imported in imports:
                if layer in ("domain", "application"):
                    assert not any(
                        part in imported.split(".") for part in ("infrastructure", "api")
                    ), (relative, imported)
                    assert not imported.startswith(("sqlalchemy", "fastapi", "pydantic")), (
                        relative,
                        imported,
                    )
                if imported.startswith("app.modules.") and ".infrastructure" in imported:
                    assert imported.split(".")[2] == owner, (relative, imported)


def valid_commitment():
    return Commitment(uuid4(), uuid4(), uuid4(), "receivable", 10000, 10000, "MXN", None, None)


@pytest.mark.parametrize(
    "changes",
    [
        {"original_amount_minor": True},
        {"original_amount_minor": 10.5},
        {"balance_minor": -1},
        {"balance_minor": 10001},
        {"balance_minor": False},
        {"version": True},
        {"version": 0},
        {"direction": "other"},
        {"currency_code": "mxn"},
        {"lifecycle_status": "paid"},
        {"lifecycle_status": "overdue"},
        {"balance_minor": 0},
    ],
)
def test_domain_rejects_invalid_financial_state(changes):
    with pytest.raises(DomainError):
        replace(valid_commitment(), **changes)


@pytest.mark.parametrize("amount", [True, 1.5, 0, -1])
def test_domain_rejects_non_positive_integer_payment(amount):
    with pytest.raises(DomainError):
        valid_commitment().pay(amount, 1)


def test_password_spaces_are_significant(client):
    password = "  meaningful spaces  "
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "spaces@example.com",
            "display_name": "Spaces",
            "password": password,
        },
    )
    assert response.status_code == 201
    client.cookies.clear()
    assert (
        client.post(
            "/api/v1/auth/login",
            json={
                "email": "spaces@example.com",
                "password": password.strip(),
            },
        ).status_code
        == 401
    )
    assert (
        client.post(
            "/api/v1/auth/login",
            json={
                "email": "spaces@example.com",
                "password": password,
            },
        ).status_code
        == 200
    )


def test_equivalent_timezone_retries_have_same_effect(client):
    commitment = setup_commitment(client)
    url = f"/api/v1/commitments/{commitment['id']}/transactions"
    headers = {"Idempotency-Key": str(uuid4())}
    body = {
        "amount_minor": 250000,
        "expected_version": 1,
        "occurred_at": "2026-10-06T12:00:00-06:00",
    }
    first = client.post(url, headers=headers, json=body)
    assert first.status_code == 201
    body["occurred_at"] = "2026-10-06T18:00:00Z"
    retry = client.post(url, headers=headers, json=body)
    assert retry.status_code == 201 and retry.json() == first.json()
    assert datetime.fromisoformat(first.json()["transaction"]["occurred_at"]) == datetime(
        2026, 10, 6, 18, tzinfo=UTC
    )
    with engine.connect() as db:
        assert db.scalar(text("SELECT count(*) FROM transactions")) == 1


def test_naive_payment_time_is_rejected(client):
    commitment = setup_commitment(client)
    response = client.post(
        f"/api/v1/commitments/{commitment['id']}/transactions",
        headers={"Idempotency-Key": str(uuid4())},
        json={"amount_minor": 250000, "expected_version": 1, "occurred_at": "2026-10-06T12:00:00"},
    )
    assert response.status_code == 422
    assert client.get(f"/api/v1/commitments/{commitment['id']}").json()["balance_minor"] == 1000000
