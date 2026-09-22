"""Separate corporate-action PnL from trading realizations."""

import sqlalchemy as sa

from alembic import op

revision = "20260913_0008"
down_revision = "20260913_0007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    for name in ("corporate_action_realized_pnl", "total_pnl"):
        op.add_column(
            "backtest_portfolio_snapshots",
            sa.Column(name, sa.Numeric(78, 38), nullable=False, server_default="0"),
        )
    op.execute(
        "UPDATE backtest_portfolio_snapshots s "
        "SET total_pnl = s.equity - (r.config->>'initial_cash')::numeric "
        "FROM backtest_runs r WHERE s.run_id = r.id"
    )


def downgrade() -> None:
    for name in ("total_pnl", "corporate_action_realized_pnl"):
        op.drop_column("backtest_portfolio_snapshots", name)
