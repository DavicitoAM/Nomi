from datetime import datetime
from uuid import UUID

from sqlalchemy import BigInteger, CheckConstraint, DateTime, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class TransactionRow(Base):
    __tablename__ = "transactions"
    __table_args__ = (
        CheckConstraint("amount_minor > 0"),
        CheckConstraint("currency_code ~ '^[A-Z]{3}$'"),
        CheckConstraint(
            "(type = 'payment' AND reversal_of_transaction_id IS NULL) OR (type = 'reversal' AND reversal_of_transaction_id IS NOT NULL)"
        ),
        Index("ix_transactions_history", "commitment_id", "occurred_at", "created_at"),
    )
    id: Mapped[UUID] = mapped_column(primary_key=True)
    commitment_id: Mapped[UUID] = mapped_column(ForeignKey("commitments.id", ondelete="RESTRICT"))
    type: Mapped[str] = mapped_column(String(16))
    amount_minor: Mapped[int] = mapped_column(BigInteger)
    currency_code: Mapped[str] = mapped_column(String(3))
    note: Mapped[str | None] = mapped_column(String(500))
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_by: Mapped[UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    reversal_of_transaction_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("transactions.id", ondelete="RESTRICT"), unique=True
    )
