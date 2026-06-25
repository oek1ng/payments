"""Outbox retry columns.

Revision ID: 1869437e2a9a
Revises: 07ef33c004af
Create Date: 2026-06-25 09:40:25.249583

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "1869437e2a9a"
down_revision: str | Sequence[str] | None = "07ef33c004af"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("outbox", sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"))
    op.add_column(
        "outbox",
        sa.Column("last_attempt_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.execute("ALTER TYPE outbox_status ADD VALUE IF NOT EXISTS 'dead'")


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("outbox", "last_attempt_at")
    op.drop_column("outbox", "attempts")
