"""Preserve non-tradable conversion carrying state in portfolio snapshots."""

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

from alembic import op

revision = "20260913_0006"
down_revision = "2054636c61ed"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "backtest_portfolio_snapshots",
        sa.Column("pending_demergers", JSONB(), nullable=False, server_default="[]"),
    )


def downgrade() -> None:
    op.drop_column("backtest_portfolio_snapshots", "pending_demergers")
