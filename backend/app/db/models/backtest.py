from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base

MONEY = Numeric(78, 38)
RUN_FK = "backtest_runs.id"


class BacktestRunModel(Base):
    __tablename__ = "backtest_runs"
    __table_args__ = (
        Index("ix_backtest_runs_status", "status"),
        Index("ix_backtest_runs_created_at", "created_at"),
        CheckConstraint(
            "status IN ('CREATED', 'RUNNING', 'SUCCEEDED', 'FAILED')",
            name="ck_backtest_runs_status",
        ),
        CheckConstraint(
            "(client_request_id IS NULL) = (request_hash IS NULL)",
            name="ck_backtest_runs_idempotency_pair",
        ),
    )

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    status: Mapped[str] = mapped_column(String(16), nullable=False)
    strategy_id: Mapped[str] = mapped_column(String(128), nullable=False)
    symbol: Mapped[str] = mapped_column(String(32), nullable=False)
    dataset_id: Mapped[str] = mapped_column(String(128), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    config: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text)
    client_request_id: Mapped[str | None] = mapped_column(String(255), unique=True)
    request_hash: Mapped[str | None] = mapped_column(String(64))


class BacktestSignalModel(Base):
    __tablename__ = "backtest_signals"

    run_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey(RUN_FK, ondelete="RESTRICT"), primary_key=True
    )
    sequence: Mapped[int] = mapped_column(Integer, primary_key=True)
    strategy_id: Mapped[str] = mapped_column(String(128), nullable=False)
    symbol: Mapped[str] = mapped_column(String(32), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    signal_type: Mapped[str] = mapped_column(String(16), nullable=False)


class BacktestOrderProposalModel(Base):
    __tablename__ = "backtest_order_proposals"
    __table_args__ = (UniqueConstraint("run_id", "proposal_id"),)

    run_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey(RUN_FK, ondelete="RESTRICT"), primary_key=True
    )
    sequence: Mapped[int] = mapped_column(Integer, primary_key=True)
    proposal_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    strategy_id: Mapped[str] = mapped_column(String(128), nullable=False)
    symbol: Mapped[str] = mapped_column(String(32), nullable=False)
    side: Mapped[str] = mapped_column(String(8), nullable=False)
    order_type: Mapped[str] = mapped_column(String(16), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(MONEY, nullable=False)
    signal_timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class BacktestRiskDecisionModel(Base):
    __tablename__ = "backtest_risk_decisions"
    __table_args__ = (
        UniqueConstraint("run_id", "proposal_id"),
        ForeignKeyConstraint(
            ("run_id", "proposal_id"),
            ("backtest_order_proposals.run_id", "backtest_order_proposals.proposal_id"),
            ondelete="RESTRICT",
        ),
    )

    run_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey(RUN_FK, ondelete="RESTRICT"), primary_key=True
    )
    sequence: Mapped[int] = mapped_column(Integer, primary_key=True)
    proposal_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    approved: Mapped[bool] = mapped_column(Boolean, nullable=False)
    reason_code: Mapped[str] = mapped_column(String(64), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    diagnostics: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)


class BacktestOrderModel(Base):
    __tablename__ = "backtest_orders"
    __table_args__ = (
        UniqueConstraint("run_id", "order_id"),
        UniqueConstraint("run_id", "proposal_id"),
        ForeignKeyConstraint(
            ("run_id", "proposal_id"),
            ("backtest_order_proposals.run_id", "backtest_order_proposals.proposal_id"),
            ondelete="RESTRICT",
        ),
    )

    run_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey(RUN_FK, ondelete="RESTRICT"), primary_key=True
    )
    sequence: Mapped[int] = mapped_column(Integer, primary_key=True)
    order_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    proposal_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True))
    strategy_id: Mapped[str] = mapped_column(String(128), nullable=False)
    symbol: Mapped[str] = mapped_column(String(32), nullable=False)
    side: Mapped[str] = mapped_column(String(8), nullable=False)
    order_type: Mapped[str] = mapped_column(String(16), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(MONEY, nullable=False)
    price: Mapped[Decimal | None] = mapped_column(MONEY)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    accepted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class BacktestFillModel(Base):
    __tablename__ = "backtest_fills"
    __table_args__ = (
        UniqueConstraint("run_id", "order_id"),
        Index("ix_backtest_fills_run_timestamp", "run_id", "timestamp"),
        ForeignKeyConstraint(
            ("run_id", "order_id"),
            ("backtest_orders.run_id", "backtest_orders.order_id"),
            ondelete="RESTRICT",
        ),
    )

    run_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey(RUN_FK, ondelete="RESTRICT"), primary_key=True
    )
    sequence: Mapped[int] = mapped_column(Integer, primary_key=True)
    order_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    strategy_id: Mapped[str] = mapped_column(String(128), nullable=False)
    symbol: Mapped[str] = mapped_column(String(32), nullable=False)
    side: Mapped[str] = mapped_column(String(8), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(MONEY, nullable=False)
    price: Mapped[Decimal] = mapped_column(MONEY, nullable=False)
    commission: Mapped[Decimal] = mapped_column(MONEY, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class BacktestPortfolioSnapshotModel(Base):
    __tablename__ = "backtest_portfolio_snapshots"
    __table_args__ = (Index("ix_backtest_snapshots_run_sequence", "run_id", "sequence"),)

    run_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey(RUN_FK, ondelete="RESTRICT"), primary_key=True
    )
    sequence: Mapped[int] = mapped_column(Integer, primary_key=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    cash: Mapped[Decimal] = mapped_column(MONEY, nullable=False)
    market_value: Mapped[Decimal] = mapped_column(MONEY, nullable=False)
    equity: Mapped[Decimal] = mapped_column(MONEY, nullable=False)
    realized_pnl: Mapped[Decimal] = mapped_column(MONEY, nullable=False)
    unrealized_pnl: Mapped[Decimal] = mapped_column(MONEY, nullable=False)
    cumulative_commission: Mapped[Decimal] = mapped_column(MONEY, nullable=False)
    drawdown: Mapped[Decimal] = mapped_column(MONEY, nullable=False)
    positions: Mapped[list[dict[str, str]]] = mapped_column(JSONB, nullable=False)
    pending_demergers: Mapped[list[dict[str, object]]] = mapped_column(
        JSONB, nullable=False, default=list, server_default="[]"
    )
    pending_mergers: Mapped[list[dict[str, object]]] = mapped_column(
        JSONB, nullable=False, default=list, server_default="[]"
    )
    merger_rounding_audits: Mapped[list[dict[str, object]]] = mapped_column(
        JSONB, nullable=False, default=list, server_default="[]"
    )


class BacktestMetricsModel(Base):
    __tablename__ = "backtest_metrics"
    __table_args__ = (
        CheckConstraint("number_of_fills >= 0", name="ck_backtest_metrics_fill_count"),
    )

    run_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey(RUN_FK, ondelete="RESTRICT"), primary_key=True
    )
    initial_equity: Mapped[Decimal] = mapped_column(MONEY, nullable=False)
    final_equity: Mapped[Decimal] = mapped_column(MONEY, nullable=False)
    total_return: Mapped[Decimal] = mapped_column(MONEY, nullable=False)
    cagr: Mapped[Decimal | None] = mapped_column(MONEY)
    max_drawdown: Mapped[Decimal] = mapped_column(MONEY, nullable=False)
    sharpe_ratio: Mapped[Decimal | None] = mapped_column(MONEY)
    sortino_ratio: Mapped[Decimal | None] = mapped_column(MONEY)
    total_commission: Mapped[Decimal] = mapped_column(MONEY, nullable=False)
    number_of_fills: Mapped[int] = mapped_column(Integer, nullable=False)


class BacktestRiskReservationModel(Base):
    __tablename__ = "backtest_risk_reservations"
    __table_args__ = (
        UniqueConstraint("run_id", "proposal_id"),
        UniqueConstraint("run_id", "order_id"),
        ForeignKeyConstraint(
            ("run_id", "proposal_id"),
            ("backtest_order_proposals.run_id", "backtest_order_proposals.proposal_id"),
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ("run_id", "order_id"),
            ("backtest_orders.run_id", "backtest_orders.order_id"),
            ondelete="RESTRICT",
        ),
    )

    run_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey(RUN_FK, ondelete="RESTRICT"), primary_key=True
    )
    sequence: Mapped[int] = mapped_column(Integer, primary_key=True)
    proposal_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    order_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    symbol: Mapped[str] = mapped_column(String(32), nullable=False)
    signed_quantity: Mapped[Decimal] = mapped_column(MONEY, nullable=False)
    cash_delta: Mapped[Decimal] = mapped_column(MONEY, nullable=False)
    buying_power_consumed: Mapped[Decimal] = mapped_column(MONEY, nullable=False)
