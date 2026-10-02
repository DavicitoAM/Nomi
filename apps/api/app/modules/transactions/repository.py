from uuid import uuid4

from sqlalchemy import select

from app.modules.transactions.models import TransactionRow
from app.shared.context import now


def transaction_data(row):
    return {
        "id": str(row.id),
        "type": row.type,
        "amount_minor": row.amount_minor,
        "currency_code": row.currency_code,
        "occurred_at": row.occurred_at.isoformat(),
        "created_at": row.created_at.isoformat(),
        "note": row.note,
    }


class TransactionRepository:
    def __init__(self, db):
        self.db = db

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
        query = select(TransactionRow).where(
            TransactionRow.commitment_id == authorized_commitment.id
        )
        if cursor:
            query = query.where(TransactionRow.id > cursor)
        rows = list(self.db.scalars(query.order_by(TransactionRow.id).limit(limit + 1)))
        return {
            "items": [transaction_data(r) for r in rows[:limit]],
            "next_cursor": str(rows[limit - 1].id) if len(rows) > limit else None,
        }
