"""Persist mandatory partial-share-surrender audit records."""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "20260913_0009"
down_revision = "20260913_0008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "backtest_portfolio_snapshots",
        sa.Column(
            "partial_surrender_audits",
            postgresql.JSONB(),
            nullable=False,
            server_default="[]",
        ),
    )


def downgrade() -> None:
    op.drop_column("backtest_portfolio_snapshots", "partial_surrender_audits")
