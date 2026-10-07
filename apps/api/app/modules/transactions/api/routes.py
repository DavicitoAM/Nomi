from uuid import UUID

from fastapi import APIRouter

from app.api.dependencies import Auth, Cursor, Key, Limit
from app.api.schemas import Page
from app.modules.transactions.api.schemas import (
    PaymentInput,
    PaymentOut,
    ReversalInput,
    TransactionOut,
)
from app.modules.transactions.application.use_cases import register_payment, reverse_payment
from app.shared.uow import SqlUnitOfWork

router = APIRouter()


@router.post("/transactions/{transaction_id}/reverse", response_model=PaymentOut, status_code=201)
def reverse(transaction_id: UUID, body: ReversalInput, context: Auth, key: Key):
    return reverse_payment(SqlUnitOfWork(), context, key, transaction_id, **body.model_dump())


@router.post(
    "/commitments/{commitment_id}/transactions", response_model=PaymentOut, status_code=201
)
def pay(commitment_id: UUID, body: PaymentInput, context: Auth, key: Key):
    return register_payment(SqlUnitOfWork(), context, key, commitment_id, **body.model_dump())


@router.get("/commitments/{commitment_id}/transactions", response_model=Page[TransactionOut])
def history(commitment_id: UUID, context: Auth, cursor: Cursor = None, limit: Limit = 30):
    with SqlUnitOfWork() as uow:
        commitment = uow.commitments.get(context.workspace_id, commitment_id)
        return uow.transactions.history(commitment, cursor, limit)
