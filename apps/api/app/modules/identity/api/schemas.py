from typing import Annotated
from uuid import UUID

from pydantic import (
    BaseModel,
    EmailStr,
    Field,
    StringConstraints,
    field_validator,
)

from app.api.schemas import Input
from app.modules.workspaces.api.schemas import MembershipOut, WorkspaceOut


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


class ProfileOut(BaseModel):
    user: UserOut
    workspace: WorkspaceOut
    membership: MembershipOut
    can_operate: bool


class EmailInput(Input):
    email: EmailStr

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value):
        return value.lower()


class TokenInput(Input):
    token: str = Field(min_length=43, max_length=43, pattern=r"^[A-Za-z0-9_-]+$")


class ResetPasswordInput(TokenInput):
    password: Annotated[
        str, StringConstraints(strip_whitespace=False, min_length=12, max_length=128)
    ]


class MessageOut(BaseModel):
    message: str
