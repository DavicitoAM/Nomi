from dataclasses import asdict
from uuid import uuid4
from zoneinfo import ZoneInfo

from app.modules.commitments.domain.entities import MAX_MONEY, Commitment
from app.shared.context import now
from app.shared.errors import DomainError
from app.shared.ports import UnitOfWork


def present(commitment, timezone):
    value = asdict(commitment)
    value.pop("workspace_id")
    return {
        **value,
        "payment_state": commitment.payment_state,
        "timing_state": commitment.timing_state(now().astimezone(ZoneInfo(timezone)).date()),
    }


def list_commitments(uow: UnitOfWork, context, cursor, limit, filter="all", search=""):
    with uow:
        ids = uow.contacts.search_ids(context.workspace_id, search) if search else ()
        today = now().astimezone(ZoneInfo(context.timezone)).date()
        rows, next_cursor = uow.commitments.list(
            context.workspace_id,
            cursor,
            limit,
            filter=filter,
            search=search,
            contact_ids=ids,
            today=today,
        )
        names = uow.contacts.names(context.workspace_id, [row.contact_id for row in rows])
        return {
            "items": [
                {**present(row, context.timezone), "contact_name": names[row.contact_id]}
                for row in rows
            ],
            "next_cursor": next_cursor,
        }


def create_commitment(
    uow: UnitOfWork,
    context,
    key,
    contact_id,
    direction,
    original_amount_minor,
    currency_code,
    concept=None,
    due_date=None,
    notes=None,
):
    if not 0 < original_amount_minor <= MAX_MONEY:
        raise DomainError("INVALID_AMOUNT", "El monto está fuera del rango permitido.")
    if currency_code != context.currency:
        raise DomainError("CURRENCY_MISMATCH", "Usa la moneda de tu espacio.")
    if direction not in ("receivable", "payable"):
        raise DomainError("INVALID_DIRECTION", "Dirección inválida.")
    command = dict(
        contact_id=contact_id,
        direction=direction,
        original_amount_minor=original_amount_minor,
        currency_code=currency_code,
        concept=concept,
        due_date=due_date,
        notes=notes,
    )
    with uow:
        # Adding an optional field must not invalidate durable pre-upgrade requests.
        payload = {k: v for k, v in command.items() if k != "notes" or v is not None}
        record_id, previous = uow.effects.reserve(
            context,
            "CreateCommitment",
            key,
            payload,
            compatible_payloads=(command,) if notes is None else (),
        )
        if previous is not None:
            return previous
        uow.contacts.require_active(context.workspace_id, contact_id)
        commitment = Commitment(
            id=uuid4(),
            workspace_id=context.workspace_id,
            balance_minor=original_amount_minor,
            **command,
        )
        uow.commitments.create(commitment)
        uow.audit.record(
            context.workspace_id, context.user_id, "commitment.created", "commitment", commitment.id
        )
        uow.effects.emit(context.workspace_id, "CommitmentCreated", commitment.id)
        response = present(commitment, context.timezone)
        uow.effects.complete(record_id, response, "commitment", commitment.id)
        uow.commit()
        return response


def revise_commitment(
    uow: UnitOfWork,
    context,
    commitment_id,
    expected_version,
    *,
    changes=None,
    cancel=False,
    key=None,
):
    changes = changes or {}
    with uow:
        commitment = uow.commitments.get(context.workspace_id, commitment_id)
        if cancel:
            record_id, previous = uow.effects.reserve(
                context,
                "CancelCommitment",
                key,
                {
                    "commitment_id": commitment_id,
                    "expected_version": expected_version,
                },
            )
            if previous is not None:
                return previous
        revised = commitment.revise(expected_version, cancel=cancel, **changes)
        uow.commitments.save_revision(revised, expected_version)
        uow.audit.record(
            context.workspace_id,
            context.user_id,
            "commitment.cancelled" if cancel else "commitment.updated",
            "commitment",
            commitment_id,
        )
        uow.effects.emit(
            context.workspace_id,
            "CommitmentCancelled" if cancel else "CommitmentUpdated",
            commitment_id,
        )
        response = present(revised, context.timezone)
        if cancel:
            uow.effects.complete(record_id, response, "commitment", commitment_id, status=200)
        uow.commit()
        return response
