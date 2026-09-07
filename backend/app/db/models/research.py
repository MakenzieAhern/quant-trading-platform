from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
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

FINANCIAL = Numeric(78, 38)
RUN_FK = "research_runs.id"
DATASET_FK = "research_datasets.dataset_id"


class MarketModel(Base):
    __tablename__ = "markets"

    market_id: Mapped[str] = mapped_column(String(32), primary_key=True)
    name_en: Mapped[str] = mapped_column(String(128), nullable=False)
    name_zh: Mapped[str] = mapped_column(String(128), nullable=False)


class ExchangeModel(Base):
    __tablename__ = "exchanges"

    exchange_id: Mapped[str] = mapped_column(String(32), primary_key=True)
    market_id: Mapped[str] = mapped_column(
        String(32), ForeignKey("markets.market_id", ondelete="RESTRICT"), nullable=False
    )
    name_en: Mapped[str] = mapped_column(String(128), nullable=False)
    name_zh: Mapped[str] = mapped_column(String(128), nullable=False)


class BoardModel(Base):
    __tablename__ = "boards"

    board_id: Mapped[str] = mapped_column(String(32), primary_key=True)
    exchange_id: Mapped[str] = mapped_column(
        String(32), ForeignKey("exchanges.exchange_id", ondelete="RESTRICT"), nullable=False
    )
    name_en: Mapped[str] = mapped_column(String(128), nullable=False)
    name_zh: Mapped[str] = mapped_column(String(128), nullable=False)


class SecurityModel(Base):
    __tablename__ = "securities"
    __table_args__ = (Index("ix_securities_exchange_symbol", "exchange_id", "symbol"),)

    security_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    exchange_id: Mapped[str] = mapped_column(
        String(32), ForeignKey("exchanges.exchange_id", ondelete="RESTRICT"), nullable=False
    )
    symbol: Mapped[str] = mapped_column(String(16), nullable=False)
    name: Mapped[str] = mapped_column(String(256), nullable=False)


class SecurityListingPeriodModel(Base):
    __tablename__ = "security_listing_periods"

    security_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("securities.security_id", ondelete="RESTRICT"), primary_key=True
    )
    valid_from: Mapped[date] = mapped_column(Date, primary_key=True)
    valid_to: Mapped[date | None] = mapped_column(Date)
    board_id: Mapped[str] = mapped_column(
        String(32), ForeignKey("boards.board_id", ondelete="RESTRICT"), nullable=False
    )
    effective_symbol: Mapped[str] = mapped_column(String(16), nullable=False)


class TradingSessionModel(Base):
    __tablename__ = "trading_sessions"

    market_id: Mapped[str] = mapped_column(
        String(32), ForeignKey("markets.market_id", ondelete="RESTRICT"), primary_key=True
    )
    session_date: Mapped[date] = mapped_column(Date, primary_key=True)
    is_open: Mapped[bool] = mapped_column(Boolean, nullable=False)
    source_version: Mapped[str] = mapped_column(String(128), nullable=False)


class SecurityDailyStatusModel(Base):
    __tablename__ = "security_daily_status"

    security_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("securities.security_id", ondelete="RESTRICT"), primary_key=True
    )
    trading_date: Mapped[date] = mapped_column(Date, primary_key=True)
    is_st: Mapped[bool] = mapped_column(Boolean, nullable=False)
    is_suspended: Mapped[bool] = mapped_column(Boolean, nullable=False)
    is_one_price_limit: Mapped[bool] = mapped_column(Boolean, nullable=False)
    source_version: Mapped[str] = mapped_column(String(128), nullable=False)


class CorporateActionModel(Base):
    __tablename__ = "corporate_actions"

    action_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    security_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("securities.security_id", ondelete="RESTRICT"), nullable=False
    )
    action_type: Mapped[str] = mapped_column(String(32), nullable=False)
    announcement_date: Mapped[date] = mapped_column(Date, nullable=False)
    ex_date: Mapped[date] = mapped_column(Date, nullable=False)
    cash_per_share: Mapped[Decimal] = mapped_column(FINANCIAL, nullable=False)
    share_ratio: Mapped[Decimal] = mapped_column(FINANCIAL, nullable=False)
    source_version: Mapped[str] = mapped_column(String(128), nullable=False)


class MarketRuleSetModel(Base):
    __tablename__ = "market_rule_sets"

    rule_set_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    market_id: Mapped[str] = mapped_column(
        String(32), ForeignKey("markets.market_id", ondelete="RESTRICT"), nullable=False
    )
    description: Mapped[str] = mapped_column(Text, nullable=False)


class MarketRuleVersionModel(Base):
    __tablename__ = "market_rule_versions"

    rule_version_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    rule_set_id: Mapped[str] = mapped_column(
        String(128),
        ForeignKey("market_rule_sets.rule_set_id", ondelete="RESTRICT"),
        nullable=False,
    )
    valid_from: Mapped[date] = mapped_column(Date, nullable=False)
    valid_to: Mapped[date | None] = mapped_column(Date)
    rules: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    provenance: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)


class ResearchDatasetModel(Base):
    __tablename__ = "research_datasets"

    dataset_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    provider: Mapped[str] = mapped_column(String(64), nullable=False)
    provider_version: Mapped[str] = mapped_column(String(64), nullable=False)
    retrieval_timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    coverage_start: Mapped[date] = mapped_column(Date, nullable=False)
    coverage_end: Mapped[date] = mapped_column(Date, nullable=False)
    security_count: Mapped[int] = mapped_column(Integer, nullable=False)
    canonical_sha256: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    rule_version: Mapped[str] = mapped_column(String(128), nullable=False)
    adjustment_method: Mapped[str] = mapped_column(String(64), nullable=False)
    manifest: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    readiness_status: Mapped[str] = mapped_column(String(16), nullable=False)
    frozen: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)


class ResearchDatasetFileModel(Base):
    __tablename__ = "research_dataset_files"

    dataset_id: Mapped[str] = mapped_column(
        String(128), ForeignKey(DATASET_FK, ondelete="RESTRICT"), primary_key=True
    )
    relative_path: Mapped[str] = mapped_column(String(512), primary_key=True)
    media_type: Mapped[str] = mapped_column(String(128), nullable=False)
    sha256: Mapped[str] = mapped_column(String(64), nullable=False)


class ResearchDatasetPartitionModel(Base):
    __tablename__ = "research_dataset_partitions"

    dataset_id: Mapped[str] = mapped_column(
        String(128), ForeignKey(DATASET_FK, ondelete="RESTRICT"), primary_key=True
    )
    partition_key: Mapped[str] = mapped_column(String(256), primary_key=True)
    relative_path: Mapped[str] = mapped_column(String(512), nullable=False)
    row_count: Mapped[int] = mapped_column(Integer, nullable=False)
    sha256: Mapped[str] = mapped_column(String(64), nullable=False)


class BenchmarkMembershipModel(Base):
    __tablename__ = "benchmark_memberships"

    dataset_id: Mapped[str] = mapped_column(
        String(128), ForeignKey(DATASET_FK, ondelete="RESTRICT"), primary_key=True
    )
    benchmark_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    security_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    valid_from: Mapped[date] = mapped_column(Date, primary_key=True)
    valid_to: Mapped[date | None] = mapped_column(Date)


class ResearchRunModel(Base):
    __tablename__ = "research_runs"
    __table_args__ = (
        Index("ix_research_runs_status_created", "status", "created_at"),
        UniqueConstraint(
            "dataset_id", "strategy_config_hash", "temporal_split_hash", "period_kind"
        ),
    )

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    status: Mapped[str] = mapped_column(String(24), nullable=False)
    period_kind: Mapped[str] = mapped_column(String(24), nullable=False)
    git_commit: Mapped[str] = mapped_column(String(40), nullable=False)
    dataset_id: Mapped[str] = mapped_column(
        String(128), ForeignKey(DATASET_FK, ondelete="RESTRICT"), nullable=False
    )
    dataset_checksum: Mapped[str] = mapped_column(String(64), nullable=False)
    provider: Mapped[str] = mapped_column(String(64), nullable=False)
    provider_version: Mapped[str] = mapped_column(String(64), nullable=False)
    market_rule_version: Mapped[str] = mapped_column(String(128), nullable=False)
    strategy_id: Mapped[str] = mapped_column(String(128), nullable=False)
    strategy_config_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    strategy_config: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    transaction_cost_config: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    benchmark_id: Mapped[str] = mapped_column(String(64), nullable=False)
    benchmark_version: Mapped[str] = mapped_column(String(128), nullable=False)
    temporal_split_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    temporal_split: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    random_seed: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    failure_code: Mapped[str | None] = mapped_column(String(64))
    diagnostics: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)


class ResearchPeriodModel(Base):
    __tablename__ = "research_periods"

    run_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey(RUN_FK, ondelete="RESTRICT"), primary_key=True
    )
    period_kind: Mapped[str] = mapped_column(String(24), primary_key=True)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)


class ResearchMetricModel(Base):
    __tablename__ = "research_metrics"

    run_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey(RUN_FK, ondelete="RESTRICT"), primary_key=True
    )
    period_kind: Mapped[str] = mapped_column(String(24), primary_key=True)
    metric_name: Mapped[str] = mapped_column(String(64), primary_key=True)
    value: Mapped[Decimal | None] = mapped_column(FINANCIAL)


class _ResearchPointBase:
    run_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey(RUN_FK, ondelete="RESTRICT"), primary_key=True
    )
    sequence: Mapped[int] = mapped_column(Integer, primary_key=True)
    trading_date: Mapped[date] = mapped_column(Date, nullable=False)
    value: Mapped[Decimal] = mapped_column(FINANCIAL, nullable=False)


class ResearchEquityPointModel(_ResearchPointBase, Base):
    __tablename__ = "research_equity_points"


class ResearchBenchmarkPointModel(_ResearchPointBase, Base):
    __tablename__ = "research_benchmark_points"


class ResearchDrawdownPointModel(_ResearchPointBase, Base):
    __tablename__ = "research_drawdown_points"


class ResearchRebalanceModel(Base):
    __tablename__ = "research_rebalances"

    run_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey(RUN_FK, ondelete="RESTRICT"), primary_key=True
    )
    sequence: Mapped[int] = mapped_column(Integer, primary_key=True)
    trading_date: Mapped[date] = mapped_column(Date, nullable=False)
    turnover: Mapped[Decimal] = mapped_column(FINANCIAL, nullable=False)
    transaction_cost: Mapped[Decimal] = mapped_column(FINANCIAL, nullable=False)


class ResearchFactorScoreModel(Base):
    __tablename__ = "research_factor_scores"
    __table_args__ = (UniqueConstraint("run_id", "trading_date", "security_id"),)

    run_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey(RUN_FK, ondelete="RESTRICT"), primary_key=True
    )
    sequence: Mapped[int] = mapped_column(Integer, primary_key=True)
    trading_date: Mapped[date] = mapped_column(Date, nullable=False)
    security_id: Mapped[str] = mapped_column(String(64), nullable=False)
    mom_12_1: Mapped[Decimal] = mapped_column(FINANCIAL, nullable=False)
    trend_120: Mapped[Decimal] = mapped_column(FINANCIAL, nullable=False)
    low_vol: Mapped[Decimal] = mapped_column(FINANCIAL, nullable=False)
    alpha_score: Mapped[Decimal] = mapped_column(FINANCIAL, nullable=False)


class ResearchHoldingModel(Base):
    __tablename__ = "research_holdings"
    __table_args__ = (UniqueConstraint("run_id", "trading_date", "security_id"),)

    run_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey(RUN_FK, ondelete="RESTRICT"), primary_key=True
    )
    sequence: Mapped[int] = mapped_column(Integer, primary_key=True)
    trading_date: Mapped[date] = mapped_column(Date, nullable=False)
    security_id: Mapped[str] = mapped_column(String(64), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(FINANCIAL, nullable=False)
    weight: Mapped[Decimal] = mapped_column(FINANCIAL, nullable=False)
    market_value: Mapped[Decimal] = mapped_column(FINANCIAL, nullable=False)


class ResearchTradeModel(Base):
    __tablename__ = "research_trades"

    run_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey(RUN_FK, ondelete="RESTRICT"), primary_key=True
    )
    sequence: Mapped[int] = mapped_column(Integer, primary_key=True)
    order_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    security_id: Mapped[str] = mapped_column(String(64), nullable=False)
    side: Mapped[str] = mapped_column(String(8), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(FINANCIAL, nullable=False)
    price: Mapped[Decimal] = mapped_column(FINANCIAL, nullable=False)
    transaction_cost: Mapped[Decimal] = mapped_column(FINANCIAL, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class ResearchMonthlyReturnModel(Base):
    __tablename__ = "research_monthly_returns"

    run_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey(RUN_FK, ondelete="RESTRICT"), primary_key=True
    )
    month: Mapped[date] = mapped_column(Date, primary_key=True)
    value: Mapped[Decimal | None] = mapped_column(FINANCIAL)


class ResearchRollingMetricModel(Base):
    __tablename__ = "research_rolling_metrics"

    run_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey(RUN_FK, ondelete="RESTRICT"), primary_key=True
    )
    trading_date: Mapped[date] = mapped_column(Date, primary_key=True)
    metric_name: Mapped[str] = mapped_column(String(64), primary_key=True)
    value: Mapped[Decimal | None] = mapped_column(FINANCIAL)
