"""phase 7 backtest persistence

Revision ID: 20260905_0002
Revises: 20260904_0001
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "20260905_0002"
down_revision: str | None = "20260904_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

money = sa.Numeric(78, 38)


def upgrade() -> None:
    op.create_table(
        "backtest_runs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("strategy_id", sa.String(128), nullable=False),
        sa.Column("symbol", sa.String(32), nullable=False),
        sa.Column("dataset_id", sa.String(128), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True)),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.Column("config", postgresql.JSONB(), nullable=False),
        sa.Column("error_message", sa.Text()),
        sa.Column("client_request_id", sa.String(255), unique=True),
        sa.Column("request_hash", sa.String(64)),
    )
    op.create_index("ix_backtest_runs_status", "backtest_runs", ["status"])
    op.create_index("ix_backtest_runs_created_at", "backtest_runs", ["created_at"])

    event_tables: list[tuple[str, list[sa.Column[object]], list[sa.SchemaItem]]] = [
        (
            "backtest_signals",
            [
                sa.Column("strategy_id", sa.String(128), nullable=False),
                sa.Column("symbol", sa.String(32), nullable=False),
                sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
                sa.Column("signal_type", sa.String(16), nullable=False),
            ],
            [],
        ),
        (
            "backtest_order_proposals",
            [
                sa.Column("proposal_id", postgresql.UUID(as_uuid=True), nullable=False),
                sa.Column("strategy_id", sa.String(128), nullable=False),
                sa.Column("symbol", sa.String(32), nullable=False),
                sa.Column("side", sa.String(8), nullable=False),
                sa.Column("order_type", sa.String(16), nullable=False),
                sa.Column("quantity", money, nullable=False),
                sa.Column("signal_timestamp", sa.DateTime(timezone=True), nullable=False),
            ],
            [sa.UniqueConstraint("run_id", "proposal_id")],
        ),
        (
            "backtest_risk_decisions",
            [
                sa.Column("proposal_id", postgresql.UUID(as_uuid=True), nullable=False),
                sa.Column("approved", sa.Boolean(), nullable=False),
                sa.Column("reason_code", sa.String(64), nullable=False),
                sa.Column("message", sa.Text(), nullable=False),
                sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
                sa.Column("diagnostics", postgresql.JSONB(), nullable=False),
            ],
            [],
        ),
        (
            "backtest_orders",
            [
                sa.Column("order_id", postgresql.UUID(as_uuid=True), nullable=False),
                sa.Column("proposal_id", postgresql.UUID(as_uuid=True)),
                sa.Column("strategy_id", sa.String(128), nullable=False),
                sa.Column("symbol", sa.String(32), nullable=False),
                sa.Column("side", sa.String(8), nullable=False),
                sa.Column("order_type", sa.String(16), nullable=False),
                sa.Column("quantity", money, nullable=False),
                sa.Column("price", money),
                sa.Column("status", sa.String(32), nullable=False),
                sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
                sa.Column("submitted_at", sa.DateTime(timezone=True)),
                sa.Column("accepted_at", sa.DateTime(timezone=True)),
            ],
            [sa.UniqueConstraint("run_id", "order_id")],
        ),
        (
            "backtest_fills",
            [
                sa.Column("order_id", postgresql.UUID(as_uuid=True), nullable=False),
                sa.Column("strategy_id", sa.String(128), nullable=False),
                sa.Column("symbol", sa.String(32), nullable=False),
                sa.Column("side", sa.String(8), nullable=False),
                sa.Column("quantity", money, nullable=False),
                sa.Column("price", money, nullable=False),
                sa.Column("commission", money, nullable=False),
                sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
            ],
            [sa.UniqueConstraint("run_id", "order_id")],
        ),
    ]
    for name, columns, constraints in event_tables:
        op.create_table(
            name,
            sa.Column(
                "run_id",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("backtest_runs.id", ondelete="CASCADE"),
                primary_key=True,
            ),
            sa.Column("sequence", sa.Integer(), primary_key=True),
            *columns,
            *constraints,
        )

    op.create_index("ix_backtest_fills_run_timestamp", "backtest_fills", ["run_id", "timestamp"])
    op.create_table(
        "backtest_portfolio_snapshots",
        sa.Column(
            "run_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("backtest_runs.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("sequence", sa.Integer(), primary_key=True),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("cash", money, nullable=False),
        sa.Column("market_value", money, nullable=False),
        sa.Column("equity", money, nullable=False),
        sa.Column("realized_pnl", money, nullable=False),
        sa.Column("unrealized_pnl", money, nullable=False),
        sa.Column("cumulative_commission", money, nullable=False),
        sa.Column("drawdown", money, nullable=False),
        sa.Column("positions", postgresql.JSONB(), nullable=False),
    )
    op.create_index(
        "ix_backtest_snapshots_run_sequence",
        "backtest_portfolio_snapshots",
        ["run_id", "sequence"],
    )
    op.create_table(
        "backtest_metrics",
        sa.Column(
            "run_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("backtest_runs.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("initial_equity", money, nullable=False),
        sa.Column("final_equity", money, nullable=False),
        sa.Column("total_return", money, nullable=False),
        sa.Column("cagr", money),
        sa.Column("max_drawdown", money, nullable=False),
        sa.Column("sharpe_ratio", money),
        sa.Column("sortino_ratio", money),
        sa.Column("total_commission", money, nullable=False),
        sa.Column("number_of_fills", sa.Integer(), nullable=False),
    )
    op.create_table(
        "backtest_risk_reservations",
        sa.Column(
            "run_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("backtest_runs.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("sequence", sa.Integer(), primary_key=True),
        sa.Column("proposal_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("order_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("symbol", sa.String(32), nullable=False),
        sa.Column("signed_quantity", money, nullable=False),
        sa.Column("cash_delta", money, nullable=False),
        sa.Column("buying_power_consumed", money, nullable=False),
        sa.UniqueConstraint("run_id", "proposal_id"),
    )


def downgrade() -> None:
    for table in (
        "backtest_risk_reservations",
        "backtest_metrics",
        "backtest_portfolio_snapshots",
        "backtest_fills",
        "backtest_orders",
        "backtest_risk_decisions",
        "backtest_order_proposals",
        "backtest_signals",
        "backtest_runs",
    ):
        op.drop_table(table)
