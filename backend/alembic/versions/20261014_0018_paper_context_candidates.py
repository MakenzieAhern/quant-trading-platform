"""Preserve candidate daily-context arrivals independently of execution admission."""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "20261014_0018"
down_revision = "20261007_0017"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "product_paper_context_candidates",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("eligibility_sha256", sa.String(64), nullable=False),
        sa.Column("trading_date", sa.Date(), nullable=False),
        sa.Column("candidate_sha256", sa.String(64), nullable=False, unique=True),
        sa.Column("observation_sha256", sa.String(64), nullable=False),
        sa.Column("source_id", sa.String(128), nullable=False),
        sa.Column("parser_version", sa.String(128), nullable=False),
        sa.Column("source_published_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("first_observed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "registered_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("clock_timestamp()"),
        ),
    )
    op.create_index(
        "ix_paper_context_day",
        "product_paper_context_candidates",
        ["eligibility_sha256", "trading_date"],
    )
    op.execute(
        "CREATE TRIGGER immutable_evidence BEFORE UPDATE OR DELETE ON "
        "product_paper_context_candidates FOR EACH ROW "
        "EXECUTE FUNCTION product_market_append_only()"
    )


def downgrade() -> None:
    # Only this new candidate index is removed; immutable private files are retained.
    op.drop_table("product_paper_context_candidates")
