from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from uuid import UUID

from app.domain.analytics import EquityPoint, PerformanceMetrics
from app.domain.risk import RiskConfig, RiskDecision
from app.domain.trading import Fill, Order, Signal


class BacktestRunStatus(StrEnum):
    CREATED = "CREATED"
    RUNNING = "RUNNING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"


ALLOWED_TRANSITIONS = {
    BacktestRunStatus.CREATED: frozenset({BacktestRunStatus.RUNNING}),
    BacktestRunStatus.RUNNING: frozenset({BacktestRunStatus.SUCCEEDED, BacktestRunStatus.FAILED}),
    BacktestRunStatus.SUCCEEDED: frozenset(),
    BacktestRunStatus.FAILED: frozenset(),
}


def require_transition(current: BacktestRunStatus, target: BacktestRunStatus) -> None:
    if target not in ALLOWED_TRANSITIONS[current]:
        raise ValueError(f"invalid backtest state transition: {current} -> {target}")


@dataclass(frozen=True, slots=True)
class CreateBacktestCommand:
    dataset_id: str
    symbol: str
    strategy_type: str
    strategy_parameters: dict[str, object]
    initial_cash: Decimal
    default_order_quantity: Decimal
    risk: RiskConfig
    start: datetime | None = None
    end: datetime | None = None
    client_request_id: str | None = None


@dataclass(frozen=True, slots=True)
class BacktestRun:
    id: UUID
    status: BacktestRunStatus
    strategy_id: str
    strategy_type: str
    strategy_parameters: dict[str, object]
    symbol: str
    dataset_id: str
    created_at: datetime
    started_at: datetime | None
    completed_at: datetime | None
    initial_cash: Decimal
    default_order_quantity: Decimal
    risk: dict[str, object]
    start: datetime | None
    end: datetime | None
    error_message: str | None
    client_request_id: str | None
    request_hash: str | None


@dataclass(frozen=True, slots=True)
class ResultSummary:
    metrics: PerformanceMetrics
    signal_count: int
    proposal_count: int
    risk_decision_count: int
    risk_rejection_count: int
    order_count: int
    fill_count: int
    snapshot_count: int
    start_time: datetime | None
    end_time: datetime | None


@dataclass(frozen=True, slots=True)
class Page[ItemT]:
    items: tuple[ItemT, ...]
    limit: int
    offset: int
    total: int


BacktestEvent = Signal | RiskDecision | Order | Fill | EquityPoint
