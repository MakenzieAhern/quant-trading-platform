"""harden phase 7 audit integrity

Revision ID: 20260905_0003
Revises: 20260905_0002
"""

from collections.abc import Sequence

from alembic import op

revision: str = "20260905_0003"
down_revision: str | None = "20260905_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

CHILD_TABLES = (
    "backtest_signals",
    "backtest_order_proposals",
    "backtest_risk_decisions",
    "backtest_orders",
    "backtest_fills",
    "backtest_portfolio_snapshots",
    "backtest_metrics",
    "backtest_risk_reservations",
)


def _replace_run_foreign_keys(ondelete: str) -> None:
    for table in CHILD_TABLES:
        constraint = f"{table}_run_id_fkey"
        op.drop_constraint(constraint, table, type_="foreignkey")
        op.create_foreign_key(
            constraint,
            table,
            "backtest_runs",
            ["run_id"],
            ["id"],
            ondelete=ondelete,
        )


def upgrade() -> None:
    _replace_run_foreign_keys("RESTRICT")
    op.create_check_constraint(
        "ck_backtest_runs_status",
        "backtest_runs",
        "status IN ('CREATED', 'RUNNING', 'SUCCEEDED', 'FAILED')",
    )
    op.create_check_constraint(
        "ck_backtest_runs_idempotency_pair",
        "backtest_runs",
        "(client_request_id IS NULL) = (request_hash IS NULL)",
    )
    op.create_check_constraint(
        "ck_backtest_metrics_fill_count", "backtest_metrics", "number_of_fills >= 0"
    )
    op.create_unique_constraint(
        "uq_backtest_risk_decisions_run_proposal",
        "backtest_risk_decisions",
        ["run_id", "proposal_id"],
    )
    op.create_unique_constraint(
        "uq_backtest_orders_run_proposal",
        "backtest_orders",
        ["run_id", "proposal_id"],
    )
    op.create_unique_constraint(
        "uq_backtest_reservations_run_order",
        "backtest_risk_reservations",
        ["run_id", "order_id"],
    )
    op.create_foreign_key(
        "fk_backtest_decisions_proposal",
        "backtest_risk_decisions",
        "backtest_order_proposals",
        ["run_id", "proposal_id"],
        ["run_id", "proposal_id"],
        ondelete="RESTRICT",
    )
    op.create_foreign_key(
        "fk_backtest_orders_proposal",
        "backtest_orders",
        "backtest_order_proposals",
        ["run_id", "proposal_id"],
        ["run_id", "proposal_id"],
        ondelete="RESTRICT",
    )
    op.create_foreign_key(
        "fk_backtest_fills_order",
        "backtest_fills",
        "backtest_orders",
        ["run_id", "order_id"],
        ["run_id", "order_id"],
        ondelete="RESTRICT",
    )
    op.create_foreign_key(
        "fk_backtest_reservations_proposal",
        "backtest_risk_reservations",
        "backtest_order_proposals",
        ["run_id", "proposal_id"],
        ["run_id", "proposal_id"],
        ondelete="RESTRICT",
    )
    op.create_foreign_key(
        "fk_backtest_reservations_order",
        "backtest_risk_reservations",
        "backtest_orders",
        ["run_id", "order_id"],
        ["run_id", "order_id"],
        ondelete="RESTRICT",
    )


def downgrade() -> None:
    for constraint, table in (
        ("fk_backtest_reservations_order", "backtest_risk_reservations"),
        ("fk_backtest_reservations_proposal", "backtest_risk_reservations"),
        ("fk_backtest_fills_order", "backtest_fills"),
        ("fk_backtest_orders_proposal", "backtest_orders"),
        ("fk_backtest_decisions_proposal", "backtest_risk_decisions"),
    ):
        op.drop_constraint(constraint, table, type_="foreignkey")
    op.drop_constraint(
        "uq_backtest_reservations_run_order",
        "backtest_risk_reservations",
        type_="unique",
    )
    op.drop_constraint("uq_backtest_orders_run_proposal", "backtest_orders", type_="unique")
    op.drop_constraint(
        "uq_backtest_risk_decisions_run_proposal",
        "backtest_risk_decisions",
        type_="unique",
    )
    op.drop_constraint("ck_backtest_metrics_fill_count", "backtest_metrics", type_="check")
    op.drop_constraint("ck_backtest_runs_idempotency_pair", "backtest_runs", type_="check")
    op.drop_constraint("ck_backtest_runs_status", "backtest_runs", type_="check")
    _replace_run_foreign_keys("CASCADE")
