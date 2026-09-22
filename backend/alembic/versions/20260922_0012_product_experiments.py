"""Isolated durable self-service experiments; formal research is unchanged."""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "20260922_0012"
down_revision = "20260913_0011"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "product_research_jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("status", sa.String(24), nullable=False),
        sa.Column("mode", sa.String(32), nullable=False),
        sa.Column("dataset_id", sa.String(128), nullable=False),
        sa.Column("dataset_sha256", sa.String(64), nullable=False),
        sa.Column("configuration", postgresql.JSONB(), nullable=False),
        sa.Column("configuration_sha256", sa.String(64), nullable=False),
        sa.Column("request_key", sa.String(128), nullable=False, unique=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True)),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.Column("phase", sa.String(32), nullable=False),
        sa.Column("completed_sessions", sa.Integer(), nullable=False),
        sa.Column("total_sessions", sa.Integer()),
        sa.Column("cancel_requested", sa.Boolean(), nullable=False),
        sa.Column("error_code", sa.String(64)),
        sa.Column(
            "retry_of",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("product_research_jobs.id", ondelete="RESTRICT"),
        ),
        sa.Column("attempt", sa.Integer(), nullable=False),
        sa.Column("summary", postgresql.JSONB()),
    )
    op.create_index(
        "ix_product_jobs_status_created", "product_research_jobs", ["status", "created_at"]
    )
    op.create_table(
        "product_research_rows",
        sa.Column(
            "job_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("product_research_jobs.id", ondelete="RESTRICT"),
            primary_key=True,
        ),
        sa.Column("collection", sa.String(32), primary_key=True),
        sa.Column("sequence", sa.Integer(), primary_key=True),
        sa.Column("payload", postgresql.JSONB(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("product_research_rows")
    op.drop_index("ix_product_jobs_status_created", table_name="product_research_jobs")
    op.drop_table("product_research_jobs")
