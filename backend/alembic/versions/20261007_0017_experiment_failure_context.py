"""Persist observed personal-experiment failure context separately from results."""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "20261007_0017"
down_revision = "20260924_0016"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("product_research_jobs", sa.Column("error_context", postgresql.JSONB()))


def downgrade() -> None:
    op.drop_column("product_research_jobs", "error_context")
