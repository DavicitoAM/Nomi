from datetime import date
from typing import Literal
from uuid import UUID

from pydantic import (
    BaseModel,
    Field,
)

from app.api.schemas import Input
from app.modules.commitments.domain.entities import MAX_MONEY


class CommitmentInput(Input):
    contact_id: UUID
    direction: Literal["receivable", "payable"]
    original_amount_minor: int = Field(gt=0, le=MAX_MONEY, strict=True)
    currency_code: str = Field(pattern="^[A-Z]{3}$")
    concept: str | None = Field(default=None, max_length=160)
    due_date: date | None = None
    notes: str | None = Field(default=None, max_length=2000)


class CommitmentVersion(Input):
    expected_version: int = Field(ge=1, le=2147483646, strict=True)


class CommitmentEdit(CommitmentVersion):
    concept: str | None = Field(default=None, max_length=160)
    notes: str | None = Field(default=None, max_length=2000)
    due_date: date | None = None


class CommitmentOut(BaseModel):
    id: UUID
    contact_id: UUID
    direction: Literal["receivable", "payable"]
    original_amount_minor: int
    balance_minor: int
    currency_code: str
    concept: str | None
    notes: str | None = None
    due_date: date | None
    lifecycle_status: Literal["open", "paid", "cancelled"]
    version: int
    payment_state: Literal["pending", "partial", "paid"]
    timing_state: Literal["no_due_date", "upcoming", "due_soon", "overdue"] | None


class CommitmentListOut(CommitmentOut):
    contact_name: str
