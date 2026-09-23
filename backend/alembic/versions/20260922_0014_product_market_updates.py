"""Independent user-triggered EOD candidates and append-only source receipts."""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "20260922_0014"
down_revision = "20260922_0013"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "product_market_update_jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("request_key", sa.String(128), nullable=False, unique=True),
        sa.Column("configuration", postgresql.JSONB(), nullable=False),
        sa.Column("configuration_sha256", sa.String(64), nullable=False),
        sa.Column("master_snapshot", postgresql.JSONB(), nullable=False),
        sa.Column("status", sa.String(24), nullable=False),
        sa.Column("phase", sa.String(32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True)),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.Column("cancel_requested", sa.Boolean(), nullable=False),
        sa.Column("completed_requests", sa.Integer(), nullable=False),
        sa.Column("total_requests", sa.Integer()),
        sa.Column("error_code", sa.String(64)),
        sa.Column("summary", postgresql.JSONB()),
        sa.Column(
            "retry_of",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("product_market_update_jobs.id", ondelete="RESTRICT"),
        ),
        sa.Column("attempt", sa.Integer(), nullable=False),
    )
    op.create_index(
        "ix_market_update_status_created", "product_market_update_jobs", ["status", "created_at"]
    )
    op.create_table(
        "product_market_receipts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "job_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("product_market_update_jobs.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("security_id", sa.String(32), nullable=False),
        sa.Column("received_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("manifest_sha256", sa.String(64), nullable=False),
        sa.Column("evidence", postgresql.JSONB(), nullable=False),
    )
    op.create_index("ix_product_market_receipts_job_id", "product_market_receipts", ["job_id"])
    op.create_table(
        "product_market_observations",
        sa.Column("provider", sa.String(64), primary_key=True),
        sa.Column("security_id", sa.String(32), primary_key=True),
        sa.Column("trading_date", sa.Date(), primary_key=True),
        sa.Column(
            "receipt_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("product_market_receipts.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("payload", postgresql.JSONB(), nullable=False),
    )
    op.execute("""
        CREATE FUNCTION product_market_append_only() RETURNS trigger LANGUAGE plpgsql AS $$
        BEGIN RAISE EXCEPTION 'Product market evidence is append only'; END; $$
    """)
    for table in ("product_market_receipts", "product_market_observations"):
        op.execute(
            f"CREATE TRIGGER immutable_evidence BEFORE UPDATE OR DELETE ON {table} "
            "FOR EACH ROW EXECUTE FUNCTION product_market_append_only()"
        )


def downgrade() -> None:
    op.drop_table("product_market_observations")
    op.drop_table("product_market_receipts")
    op.drop_table("product_market_update_jobs")
    op.execute("DROP FUNCTION product_market_append_only()")
