from datetime import datetime
from typing import Literal, Protocol, TypedDict
from uuid import UUID

from app.modules.commitments.domain.entities import Commitment


class Movement(TypedDict):
    id: str
    type: Literal["payment", "reversal"]
    amount_minor: int
    currency_code: str
    occurred_at: str
    created_at: str
    note: str | None
    reversal_of_transaction_id: str | None
    reversed_by_transaction_id: str | None


class OriginalMovement(Movement):
    commitment_id: UUID


class History(TypedDict):
    items: list[Movement]
    next_cursor: str | None


class Transactions(Protocol):
    def export_for_commitments(self, authorized_ids: list[UUID], limit: int) -> list[dict]: ...
    def original(self, transaction_id: UUID) -> OriginalMovement: ...
    def is_reversed(self, transaction_id: UUID) -> bool: ...
    def payment(
        self,
        commitment: Commitment,
        amount: int,
        occurred_at: datetime,
        note: str | None,
        user_id: UUID,
    ) -> Movement: ...
    def reversal(
        self, commitment: Commitment, original: OriginalMovement, note: str | None, user_id: UUID
    ) -> Movement: ...
    def history(
        self, authorized_commitment: Commitment, cursor: UUID | None, limit: int
    ) -> History: ...
