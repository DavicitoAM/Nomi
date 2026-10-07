"""Add descriptive notes and contact modification timestamp without rewriting history."""

import sqlalchemy as sa
from alembic import op

revision = "4eb83021fb32"
down_revision = "3da72910ea21"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("contacts", sa.Column("notes", sa.String(2000), nullable=True))
    op.add_column("contacts", sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True))
    op.execute("UPDATE contacts SET updated_at=created_at")
    op.alter_column("contacts", "updated_at", nullable=False)
    op.add_column("commitments", sa.Column("notes", sa.String(2000), nullable=True))


def downgrade():
    op.drop_column("commitments", "notes")
    op.drop_column("contacts", "updated_at")
    op.drop_column("contacts", "notes")
