"""Allow a durable pause state for local simulated sessions."""

from alembic import op

revision = "20260923_0015"
down_revision = "20260922_0014"
branch_labels = None
depends_on = None

OLD = "status IN ('CREATED','STARTING','RUNNING','STOPPING','STOPPED','FAILED','INTERRUPTED')"
NEW = (
    "status IN ('CREATED','STARTING','RUNNING','PAUSING','PAUSED',"
    "'STOPPING','STOPPED','FAILED','INTERRUPTED')"
)


def upgrade() -> None:
    op.drop_constraint("ck_paper_sessions_status", "paper_trading_sessions", type_="check")
    op.create_check_constraint("ck_paper_sessions_status", "paper_trading_sessions", NEW)


def downgrade() -> None:
    op.drop_constraint("ck_paper_sessions_status", "paper_trading_sessions", type_="check")
    op.create_check_constraint("ck_paper_sessions_status", "paper_trading_sessions", OLD)
