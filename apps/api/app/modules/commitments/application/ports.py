from datetime import date
from typing import Protocol, Sequence
from uuid import UUID

from app.modules.commitments.domain.entities import Commitment


class Commitments(Protocol):
    def create(self, commitment: Commitment) -> None: ...
    def get(self, workspace_id: UUID, commitment_id: UUID) -> Commitment: ...
    # Shared financial CAS for payments and reversals; never an arbitrary balance setter.
    def save_payment(self, commitment: Commitment, expected_version: int) -> None: ...
    def save_revision(self, commitment: Commitment, expected_version: int) -> None: ...
    def contact_summary(self, workspace_id: UUID, contact_id: UUID) -> dict: ...
    def list(
        self,
        workspace_id: UUID,
        cursor: UUID | None,
        limit: int,
        *,
        filter: str = "all",
        search: str = "",
        contact_ids: Sequence[UUID] = (),
        today: date | None = None,
    ) -> tuple[list[Commitment], str | None]: ...
    def summary(self, workspace_id: UUID, today: date) -> dict[str, int]: ...
