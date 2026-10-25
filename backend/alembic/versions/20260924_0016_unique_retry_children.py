"""Keep each failed product task bound to one durable retry child."""

from alembic import op

revision = "20260924_0016"
down_revision = "20260923_0015"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_unique_constraint(
        "uq_product_research_retry_of", "product_research_jobs", ["retry_of"]
    )
    op.create_unique_constraint(
        "uq_product_market_update_retry_of", "product_market_update_jobs", ["retry_of"]
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_product_market_update_retry_of", "product_market_update_jobs", type_="unique"
    )
    op.drop_constraint("uq_product_research_retry_of", "product_research_jobs", type_="unique")
