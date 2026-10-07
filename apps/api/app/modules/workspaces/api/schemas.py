from typing import Literal
from uuid import UUID

from pydantic import (
    BaseModel,
)


class WorkspaceOut(BaseModel):
    id: UUID
    name: str
    currency_code: str
    timezone: str


class MembershipOut(BaseModel):
    role: Literal["owner", "member"]
