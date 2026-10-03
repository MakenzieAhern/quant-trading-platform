from datetime import date, datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.research.models import ResearchPeriodKind


class ApiModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ResearchErrorResponse(ApiModel):
    code: str
    message: str
    details: dict[str, Any] = Field(default_factory=dict)
    request_id: str


class MarketResponse(ApiModel):
    market_id: str
    exchanges: tuple[str, ...]
    boards: tuple[str, ...]


class DatasetResponse(ApiModel):
    dataset_id: str
    current_dataset_quality: str | None = None
    provider: str
    provider_version: str
    retrieval_timestamp: datetime
    coverage_start: date
    coverage_end: date
    security_count: int
    canonical_sha256: str
    rule_version: str
    adjustment_method: str
    readiness_status: str
    frozen: bool
    manifest: dict[str, Any] | None = None


class StrategyResponse(ApiModel):
    strategy_id: str
    version: str
    name_en: str
    name_zh: str
    factor_formulas: tuple[str, ...]
    frozen_configuration: dict[str, Any]
    configuration_hash: str


class CreateResearchRunRequest(ApiModel):
    dataset_id: str = Field(pattern=r"^[a-z0-9][a-z0-9._-]{2,127}$")
    strategy_id: str
    benchmark_id: str = "CSI300"
    period_kind: ResearchPeriodKind


class ResearchRunResponse(ApiModel):
    run_id: UUID
    current_dataset_quality: str | None = None
    status: str
    period_kind: ResearchPeriodKind
    git_commit: str
    dataset_id: str
    dataset_checksum: str
    provider: str
    provider_version: str
    market_rule_version: str
    strategy_id: str
    strategy_config_hash: str
    transaction_cost_config: dict[str, Any]
    benchmark_id: str
    benchmark_version: str
    temporal_split_hash: str
    random_seed: int
    created_at: datetime
    started_at: datetime | None
    completed_at: datetime | None
    failure_code: str | None
    diagnostics: dict[str, Any]


class MetricResponse(ApiModel):
    period_kind: ResearchPeriodKind
    metric_name: str
    value: str | None


class PointResponse(ApiModel):
    sequence: int
    trading_date: date
    value: str


class MonthlyReturnResponse(ApiModel):
    month: date
    value: str | None


class RollingMetricResponse(ApiModel):
    trading_date: date
    metric_name: str
    value: str | None


class RebalanceResponse(ApiModel):
    sequence: int
    trading_date: date
    turnover: str
    transaction_cost: str


class HoldingResponse(ApiModel):
    sequence: int
    trading_date: date
    security_id: str
    quantity: str
    weight: str
    market_value: str


class TradeResponse(ApiModel):
    sequence: int
    order_id: UUID
    security_id: str
    side: str
    quantity: str
    price: str
    transaction_cost: str
    timestamp: datetime


class ResearchPage[PageItem](ApiModel):
    items: list[PageItem]
    limit: int
    offset: int
    total: int
