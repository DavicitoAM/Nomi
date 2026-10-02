from datetime import date, datetime
from uuid import UUID

from sqlalchemy import BigInteger, CheckConstraint, DateTime, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class CommitmentRow(Base):
    __tablename__ = "commitments"
    __table_args__ = (
        CheckConstraint("direction IN ('receivable','payable')"),
        CheckConstraint("original_amount_minor > 0"),
        CheckConstraint("balance_minor >= 0 AND balance_minor <= original_amount_minor"),
        CheckConstraint("currency_code ~ '^[A-Z]{3}$'"),
        CheckConstraint("version >= 1"),
        CheckConstraint(
            "(lifecycle_status = 'open' AND balance_minor > 0) OR (lifecycle_status = 'paid' AND balance_minor = 0) OR (lifecycle_status = 'cancelled' AND balance_minor >= 0)"
        ),
        Index("ix_commitments_dashboard", "workspace_id", "lifecycle_status", "due_date"),
        Index("ix_commitments_contact", "workspace_id", "contact_id", "created_at"),
    )
    id: Mapped[UUID] = mapped_column(primary_key=True)
    workspace_id: Mapped[UUID] = mapped_column(ForeignKey("workspaces.id", ondelete="RESTRICT"))
    contact_id: Mapped[UUID] = mapped_column(ForeignKey("contacts.id", ondelete="RESTRICT"))
    direction: Mapped[str] = mapped_column(String(16))
    original_amount_minor: Mapped[int] = mapped_column(BigInteger)
    balance_minor: Mapped[int] = mapped_column(BigInteger)
    currency_code: Mapped[str] = mapped_column(String(3))
    concept: Mapped[str | None] = mapped_column(String(160))
    due_date: Mapped[date | None]
    lifecycle_status: Mapped[str] = mapped_column(String(16))
    version: Mapped[int] = mapped_column(default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
