"""Independent local watchlist; archive and formal research remain read-only."""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "20260922_0013"
down_revision = "20260922_0012"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "product_watchlist",
        sa.Column("dataset_id", sa.String(128), primary_key=True),
        sa.Column("security_id", sa.String(32), primary_key=True),
        sa.Column("dataset_sha256", sa.String(64), nullable=False),
        sa.Column("security", postgresql.JSONB(), nullable=False),
        sa.Column("added_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("product_watchlist")
