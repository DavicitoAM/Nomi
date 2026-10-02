from dataclasses import asdict

from sqlalchemy import select, update

from app.modules.commitments.domain import Commitment
from app.modules.commitments.models import CommitmentRow
from app.shared.context import now
from app.shared.errors import DomainError


def entity(row):
    return Commitment(**{field: getattr(row, field) for field in Commitment.__dataclass_fields__})


class CommitmentRepository:
    def __init__(self, db):
        self.db = db

    def create(self, commitment):
        self.db.add(CommitmentRow(**asdict(commitment), created_at=now(), updated_at=now()))
        self.db.flush()

    def get(self, workspace_id, commitment_id):
        row = self.db.scalar(
            select(CommitmentRow).where(
                CommitmentRow.id == commitment_id,
                CommitmentRow.workspace_id == workspace_id,
                CommitmentRow.deleted_at.is_(None),
            )
        )
        if row is None:
            raise DomainError("COMMITMENT_NOT_FOUND", "No encontramos ese pendiente.", 404)
        return entity(row)

    def save_payment(self, commitment, expected_version):
        result = self.db.execute(
            update(CommitmentRow)
            .where(
                CommitmentRow.id == commitment.id,
                CommitmentRow.workspace_id == commitment.workspace_id,
                CommitmentRow.version == expected_version,
                CommitmentRow.deleted_at.is_(None),
            )
            .values(
                balance_minor=commitment.balance_minor,
                lifecycle_status=commitment.lifecycle_status,
                version=commitment.version,
                updated_at=now(),
            )
        )
        if result.rowcount != 1:
            raise DomainError(
                "VERSION_CONFLICT", "El saldo cambió. Revisa y confirma de nuevo.", 409
            )

    def list(self, workspace_id, cursor, limit):
        query = select(CommitmentRow).where(
            CommitmentRow.workspace_id == workspace_id, CommitmentRow.deleted_at.is_(None)
        )
        if cursor:
            query = query.where(CommitmentRow.id > cursor)
        rows = list(self.db.scalars(query.order_by(CommitmentRow.id).limit(limit + 1)))
        return [entity(row) for row in rows[:limit]], str(rows[limit - 1].id) if len(
            rows
        ) > limit else None

    def summary(self, workspace_id, today):
        # Explicit read port owned by commitments; reporting does not import its ORM model.
        from datetime import timedelta

        from sqlalchemy import func

        scope = (
            CommitmentRow.workspace_id == workspace_id,
            CommitmentRow.lifecycle_status == "open",
            CommitmentRow.deleted_at.is_(None),
        )
        balance = CommitmentRow.balance_minor
        query = select(
            func.coalesce(func.sum(balance).filter(CommitmentRow.direction == "receivable"), 0),
            func.coalesce(func.sum(balance).filter(CommitmentRow.direction == "payable"), 0),
            func.coalesce(func.sum(balance).filter(CommitmentRow.due_date < today), 0),
            func.coalesce(
                func.sum(balance).filter(
                    CommitmentRow.due_date.between(today, today + timedelta(days=7))
                ),
                0,
            ),
            func.count(),
        ).where(*scope)
        row = self.db.execute(query).one()
        return dict(
            zip(
                (
                    "receivable_balance_minor",
                    "payable_balance_minor",
                    "overdue_balance_minor",
                    "due_soon_balance_minor",
                    "active_commitments",
                ),
                map(int, row),
            )
        )
