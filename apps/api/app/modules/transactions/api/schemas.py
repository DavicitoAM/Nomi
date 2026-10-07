from datetime import UTC, datetime
from typing import Literal
from uuid import UUID

from pydantic import (
    AwareDatetime,
    BaseModel,
    Field,
    field_validator,
)

from app.api.schemas import Input
from app.modules.commitments.api.schemas import CommitmentOut
from app.modules.commitments.domain.entities import MAX_MONEY


class PaymentInput(Input):
    type: Literal["payment"] = "payment"
    amount_minor: int = Field(gt=0, le=MAX_MONEY, strict=True)
    expected_version: int = Field(ge=1, le=2147483646, strict=True)
    occurred_at: AwareDatetime
    note: str | None = Field(default=None, max_length=500)

    @field_validator("occurred_at")
    @classmethod
    def utc_instant(cls, value):
        return value.astimezone(UTC)


class TransactionOut(BaseModel):
    id: UUID
    type: Literal["payment", "reversal"]
    amount_minor: int
    currency_code: str
    occurred_at: datetime
    created_at: datetime
    note: str | None
    reversal_of_transaction_id: UUID | None = None
    reversed_by_transaction_id: UUID | None = None

    @field_validator("occurred_at", "created_at")
    @classmethod
    def utc_instant(cls, value):
        return value.astimezone(UTC)


class PaymentOut(BaseModel):
    transaction: TransactionOut
    commitment: CommitmentOut


class ReversalInput(Input):
    expected_version: int = Field(ge=1, le=2147483646, strict=True)
    note: str | None = Field(default=None, max_length=500)
