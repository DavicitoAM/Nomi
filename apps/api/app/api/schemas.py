from datetime import UTC, date, datetime
from typing import Annotated, Generic, Literal, TypeVar
from uuid import UUID

from pydantic import (
    AwareDatetime,
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    StringConstraints,
    field_validator,
)

from app.modules.commitments.domain import MAX_MONEY


class Input(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class RegisterInput(Input):
    display_name: str = Field(min_length=1, max_length=120)
    email: EmailStr
    password: Annotated[
        str, StringConstraints(strip_whitespace=False, min_length=12, max_length=128)
    ]

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value):
        return value.lower()


class LoginInput(Input):
    email: EmailStr
    password: Annotated[
        str, StringConstraints(strip_whitespace=False, min_length=1, max_length=128)
    ]

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value):
        return value.lower()


class UserOut(BaseModel):
    id: UUID
    display_name: str
    email: str
    email_verified: bool


class WorkspaceOut(BaseModel):
    id: UUID
    name: str
    currency_code: str
    timezone: str


class MembershipOut(BaseModel):
    role: Literal["owner", "member"]


class ProfileOut(BaseModel):
    user: UserOut
    workspace: WorkspaceOut
    membership: MembershipOut


class ContactInput(Input):
    name: str = Field(min_length=1, max_length=160)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=40)


class ContactOut(BaseModel):
    id: UUID
    name: str
    email: str | None
    phone: str | None


class CommitmentInput(Input):
    contact_id: UUID
    direction: Literal["receivable", "payable"]
    original_amount_minor: int = Field(gt=0, le=MAX_MONEY, strict=True)
    currency_code: str = Field(pattern="^[A-Z]{3}$")
    concept: str | None = Field(default=None, max_length=160)
    due_date: date | None = None


class CommitmentOut(BaseModel):
    id: UUID
    contact_id: UUID
    direction: Literal["receivable", "payable"]
    original_amount_minor: int
    balance_minor: int
    currency_code: str
    concept: str | None
    due_date: date | None
    lifecycle_status: Literal["open", "paid", "cancelled"]
    version: int
    payment_state: Literal["pending", "partial", "paid"]
    timing_state: Literal["no_due_date", "upcoming", "due_soon", "overdue"] | None


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

    @field_validator("occurred_at", "created_at")
    @classmethod
    def utc_instant(cls, value):
        return value.astimezone(UTC)


class PaymentOut(BaseModel):
    transaction: TransactionOut
    commitment: CommitmentOut


class DashboardOut(BaseModel):
    currency_code: str
    receivable_balance_minor: int
    payable_balance_minor: int
    overdue_balance_minor: int
    due_soon_balance_minor: int
    active_commitments: int


T = TypeVar("T")


class Page(BaseModel, Generic[T]):
    items: list[T]
    next_cursor: UUID | None


class Problem(BaseModel):
    type: str
    title: str
    status: int
    detail: str
    instance: str
    code: str
    request_id: str
