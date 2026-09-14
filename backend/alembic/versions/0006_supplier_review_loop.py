"""Add supplier submission and change-request workflow.

Revision ID: 0006_supplier_review_loop
Revises: 0005_phase_three_compliance
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0006_supplier_review_loop"
down_revision: str | None = "0005_phase_three_compliance"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # PostgreSQL enums cannot add several values in a single ALTER statement.
    op.execute("ALTER TYPE supplier_status ADD VALUE IF NOT EXISTS 'SUBMITTED'")
    op.execute("ALTER TYPE supplier_status ADD VALUE IF NOT EXISTS 'UNDER_REVIEW'")
    op.execute("ALTER TYPE supplier_status ADD VALUE IF NOT EXISTS 'CHANGES_REQUESTED'")
    op.execute("ALTER TYPE supplier_status ADD VALUE IF NOT EXISTS 'RESUBMITTED'")
    op.add_column(
        "suppliers",
        sa.Column("review_round", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column("suppliers", sa.Column("change_request", sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column("suppliers", "change_request")
    op.drop_column("suppliers", "review_round")
    # Enum values are intentionally retained. Removing PostgreSQL enum values
    # requires rebuilding the type and can invalidate existing rows.
