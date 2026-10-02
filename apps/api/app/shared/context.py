from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID


def now() -> datetime:
    return datetime.now(UTC)


@dataclass(frozen=True)
class Context:
    user_id: UUID
    workspace_id: UUID
    currency: str
    timezone: str
    session_id: UUID
