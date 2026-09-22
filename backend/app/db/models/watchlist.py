"""Local personal watchlist, independent from research/security authority tables."""

from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class WatchlistItemModel(Base):
    __tablename__ = "product_watchlist"

    dataset_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    security_id: Mapped[str] = mapped_column(String(32), primary_key=True)
    dataset_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    security: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    added_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
