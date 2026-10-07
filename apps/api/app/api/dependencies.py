from typing import Annotated
from uuid import UUID

from fastapi import Depends, Header, Query

from app.api.security import auth_context
from app.shared.context import Context

Auth = Annotated[Context, Depends(auth_context)]
Key = Annotated[UUID, Header(alias="Idempotency-Key")]
Cursor = Annotated[UUID | None, Query()]
Limit = Annotated[int, Query(ge=1, le=100)]
