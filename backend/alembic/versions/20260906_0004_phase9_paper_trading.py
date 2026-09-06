"""add Phase 9 paper trading sessions and typed event journal

Revision ID: 20260906_0004
Revises: 20260905_0003
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "20260906_0004"
down_revision: str | None = "20260905_0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

MONEY = sa.Numeric(78, 38)


def upgrade() -> None:
    op.create_table(
        "paper_trading_sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("provider_type", sa.String(32), nullable=False),
        sa.Column("dataset_id", sa.String(128), nullable=False),
        sa.Column("symbol", sa.String(32), nullable=False),
        sa.Column("strategy_type", sa.String(64), nullable=False),
        sa.Column("strategy_parameters", postgresql.JSONB(), nullable=False),
        sa.Column("initial_cash", MONEY, nullable=False),
        sa.Column("default_order_quantity", MONEY, nullable=False),
        sa.Column("risk", postgresql.JSONB(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True)),
        sa.Column("stopped_at", sa.DateTime(timezone=True)),
        sa.Column("error_message", sa.Text()),
        sa.Column("client_request_id", sa.String(255), unique=True),
        sa.Column("request_hash", sa.String(64)),
        sa.CheckConstraint(
            "status IN ('CREATED','STARTING','RUNNING','STOPPING',"
            "'STOPPED','FAILED','INTERRUPTED')",
            name="ck_paper_sessions_status",
        ),
        sa.CheckConstraint(
            "(client_request_id IS NULL) = (request_hash IS NULL)",
            name="ck_paper_sessions_idempotency_pair",
        ),
    )
    op.create_index("ix_paper_sessions_status", "paper_trading_sessions", ["status"])
    op.create_index("ix_paper_sessions_created_at", "paper_trading_sessions", ["created_at"])
    op.create_table(
        "paper_trading_events",
        sa.Column(
            "session_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("paper_trading_sessions.id", ondelete="RESTRICT"),
            primary_key=True,
        ),
        sa.Column("sequence", sa.Integer(), primary_key=True),
        sa.Column("event_type", sa.String(64), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("payload", postgresql.JSONB(), nullable=False),
    )
    op.create_index(
        "ix_paper_events_session_type",
        "paper_trading_events",
        ["session_id", "event_type"],
    )
    op.create_index(
        "ix_paper_events_session_time",
        "paper_trading_events",
        ["session_id", "occurred_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_paper_events_session_time", table_name="paper_trading_events")
    op.drop_index("ix_paper_events_session_type", table_name="paper_trading_events")
    op.drop_table("paper_trading_events")
    op.drop_index("ix_paper_sessions_created_at", table_name="paper_trading_sessions")
    op.drop_index("ix_paper_sessions_status", table_name="paper_trading_sessions")
    op.drop_table("paper_trading_sessions")
