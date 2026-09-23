from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base

MONEY = Numeric(78, 38)


class PaperTradingSessionModel(Base):
    __tablename__ = "paper_trading_sessions"
    __table_args__ = (
        Index("ix_paper_sessions_status", "status"),
        Index("ix_paper_sessions_created_at", "created_at"),
        CheckConstraint(
            "status IN ('CREATED','STARTING','RUNNING','PAUSING','PAUSED','STOPPING',"
            "'STOPPED','FAILED','INTERRUPTED')",
            name="ck_paper_sessions_status",
        ),
        CheckConstraint(
            "(client_request_id IS NULL) = (request_hash IS NULL)",
            name="ck_paper_sessions_idempotency_pair",
        ),
    )

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    status: Mapped[str] = mapped_column(String(16), nullable=False)
    provider_type: Mapped[str] = mapped_column(String(32), nullable=False)
    dataset_id: Mapped[str] = mapped_column(String(128), nullable=False)
    symbol: Mapped[str] = mapped_column(String(32), nullable=False)
    strategy_type: Mapped[str] = mapped_column(String(64), nullable=False)
    strategy_parameters: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    initial_cash: Mapped[Decimal] = mapped_column(MONEY, nullable=False)
    default_order_quantity: Mapped[Decimal] = mapped_column(MONEY, nullable=False)
    risk: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    stopped_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    error_message: Mapped[str | None] = mapped_column(Text)
    client_request_id: Mapped[str | None] = mapped_column(String(255), unique=True)
    request_hash: Mapped[str | None] = mapped_column(String(64))


class PaperTradingEventModel(Base):
    __tablename__ = "paper_trading_events"
    __table_args__ = (
        Index("ix_paper_events_session_type", "session_id", "event_type"),
        Index("ix_paper_events_session_time", "session_id", "occurred_at"),
    )

    session_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("paper_trading_sessions.id", ondelete="RESTRICT"),
        primary_key=True,
    )
    sequence: Mapped[int] = mapped_column(Integer, primary_key=True)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
