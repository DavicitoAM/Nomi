from datetime import UTC, datetime
from uuid import UUID

from pydantic import (
    AwareDatetime,
    BaseModel,
    EmailStr,
    Field,
    field_validator,
)

from app.api.schemas import Input


class ContactInput(Input):
    name: str = Field(min_length=1, max_length=160)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=40)
    notes: str | None = Field(default=None, max_length=2000)


class ContactVersion(Input):
    expected_updated_at: AwareDatetime


class ContactEdit(ContactVersion):
    name: str | None = Field(default=None, min_length=1, max_length=160)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=40)
    notes: str | None = Field(default=None, max_length=2000)

    @field_validator("name")
    @classmethod
    def non_null_name(cls, value):
        if value is None:
            raise ValueError("Name cannot be null")
        return value


class ContactOut(BaseModel):
    id: UUID
    name: str
    email: str | None
    phone: str | None
    notes: str | None
    archived_at: datetime | None
    updated_at: datetime

    @field_validator("archived_at", "updated_at")
    @classmethod
    def utc_instant(cls, value):
        return value.astimezone(UTC) if value else None


class ContactSummary(BaseModel):
    receivable_balance_minor: str
    payable_balance_minor: str
    active_commitments: int


class ContactDetail(ContactOut):
    summary: ContactSummary
