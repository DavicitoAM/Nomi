from dataclasses import asdict
from uuid import uuid4
from zoneinfo import ZoneInfo

from app.modules.commitments.domain import MAX_MONEY, Commitment
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
    )
    with uow:
        record_id, previous = uow.effects.reserve(context, "CreateCommitment", key, command)
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
