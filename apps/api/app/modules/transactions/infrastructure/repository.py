from uuid import uuid4

from sqlalchemy import select, tuple_
from sqlalchemy.orm import aliased

from app.modules.transactions.infrastructure.models import TransactionRow
from app.shared.context import now
from app.shared.errors import DomainError


def transaction_data(row):
    return {
        "id": str(row.id),
        "type": row.type,
        "amount_minor": row.amount_minor,
        "currency_code": row.currency_code,
        "occurred_at": row.occurred_at.isoformat(),
        "created_at": row.created_at.isoformat(),
        "note": row.note,
        "reversal_of_transaction_id": str(row.reversal_of_transaction_id)
        if row.reversal_of_transaction_id
        else None,
        "reversed_by_transaction_id": None,
    }


class TransactionRepository:
    def __init__(self, db):
        self.db = db

    def original(self, transaction_id):
        row = self.db.get(TransactionRow, transaction_id)
        if row is None:
            raise DomainError("TRANSACTION_NOT_FOUND", "No encontramos ese movimiento.", 404)
        return {**transaction_data(row), "commitment_id": row.commitment_id}

    def export_for_commitments(self, authorized_ids, limit):
        rows = list(
            self.db.scalars(
                select(TransactionRow)
                .where(TransactionRow.commitment_id.in_(authorized_ids))
                .order_by(TransactionRow.created_at, TransactionRow.id)
                .limit(limit)
            )
        )
        reversals = {
            row.reversal_of_transaction_id: str(row.id)
            for row in rows
            if row.reversal_of_transaction_id is not None
        }
        return [
            {
                **transaction_data(row),
                "commitment_id": str(row.commitment_id),
                "reversed_by_transaction_id": reversals.get(row.id),
            }
            for row in rows
        ]

    def is_reversed(self, transaction_id):
        return (
            self.db.scalar(
                select(TransactionRow.id).where(
                    TransactionRow.reversal_of_transaction_id == transaction_id
                )
            )
            is not None
        )

    def reversal(self, commitment, original, note, user_id):
        from uuid import UUID

        row = TransactionRow(
            id=uuid4(),
            commitment_id=commitment.id,
            type="reversal",
            amount_minor=original["amount_minor"],
            currency_code=original["currency_code"],
            occurred_at=now(),
            created_at=now(),
            note=note,
            created_by=user_id,
            reversal_of_transaction_id=UUID(original["id"]),
        )
        self.db.add(row)
        self.db.flush()
        return transaction_data(row)

    def payment(self, commitment, amount, occurred_at, note, user_id):
        row = TransactionRow(
            id=uuid4(),
            commitment_id=commitment.id,
            type="payment",
            amount_minor=amount,
            currency_code=commitment.currency_code,
            occurred_at=occurred_at,
            note=note,
            created_by=user_id,
            created_at=now(),
        )
        self.db.add(row)
        self.db.flush()
        return transaction_data(row)

    def history(self, authorized_commitment, cursor, limit):
        # Only called with a commitment obtained through the scoped commitment port.
        reversed_row = aliased(TransactionRow)
        query = (
            select(TransactionRow, reversed_row.id)
            .outerjoin(reversed_row, reversed_row.reversal_of_transaction_id == TransactionRow.id)
            .where(TransactionRow.commitment_id == authorized_commitment.id)
        )
        if cursor:
            anchor = self.db.scalar(
                select(TransactionRow).where(
                    TransactionRow.id == cursor,
                    TransactionRow.commitment_id == authorized_commitment.id,
                )
            )
            if anchor is None:
                raise DomainError("INVALID_CURSOR", "El cursor no pertenece a este historial.")
            query = query.where(
                tuple_(TransactionRow.created_at, TransactionRow.id)
                > tuple_(anchor.created_at, anchor.id)
            )
        rows = list(
            self.db.execute(
                query.order_by(TransactionRow.created_at, TransactionRow.id).limit(limit + 1)
            )
        )
        return {
            "items": [
                {
                    **transaction_data(row),
                    "reversed_by_transaction_id": str(reversal_id) if reversal_id else None,
                }
                for row, reversal_id in rows[:limit]
            ],
            "next_cursor": str(rows[limit - 1][0].id) if len(rows) > limit else None,
        }
