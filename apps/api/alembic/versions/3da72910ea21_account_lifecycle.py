"""Durable account links and mail delivery retries (additive)."""

import sqlalchemy as sa
from alembic import op

revision = "3da72910ea21"
down_revision = "8c328338b737"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "users", sa.Column("email_verified_at", sa.DateTime(timezone=True), nullable=True)
    )
    op.add_column("users", sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True))
    op.execute("UPDATE users SET updated_at=created_at")
    op.alter_column("users", "updated_at", nullable=False)
    op.add_column(
        "outbox_events",
        sa.Column(
            "available_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.add_column("outbox_events", sa.Column("last_error_code", sa.String(40), nullable=True))
    for table, index in (
        ("email_verification_tokens", "ix_verification_user_created"),
        ("password_reset_tokens", "ix_reset_user_created"),
    ):
        op.create_table(
            table,
            sa.Column("id", sa.Uuid(), primary_key=True),
            sa.Column(
                "user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False
            ),
            sa.Column("token_hash", sa.String(64), nullable=False, unique=True),
            sa.Column("delivery_secret", sa.String(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
            sa.CheckConstraint("expires_at > created_at"),
        )
        op.create_index(index, table, ["user_id", "created_at"])


def downgrade():
    op.drop_table("password_reset_tokens")
    op.drop_table("email_verification_tokens")
    op.drop_column("outbox_events", "last_error_code")
    op.drop_column("outbox_events", "available_at")
    op.drop_column("users", "updated_at")
    op.drop_column("users", "email_verified_at")
