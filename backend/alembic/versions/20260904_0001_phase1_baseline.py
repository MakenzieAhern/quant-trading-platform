"""Create the Phase 1 schema baseline."""

from collections.abc import Sequence

revision: str = "20260904_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Domain tables are introduced with their bounded contexts in later phases."""


def downgrade() -> None:
    """The baseline contains no schema objects."""
