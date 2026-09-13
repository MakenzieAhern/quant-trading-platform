"""Persist pending whole-share mergers and audit-only fractional materiality."""

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

from alembic import op

revision = "20260913_0007"
down_revision = "20260913_0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    for name in ("pending_mergers", "merger_rounding_audits"):
        op.add_column(
            "backtest_portfolio_snapshots",
            sa.Column(name, JSONB(), nullable=False, server_default="[]"),
        )


def downgrade() -> None:
    for name in ("merger_rounding_audits", "pending_mergers"):
        op.drop_column("backtest_portfolio_snapshots", name)
