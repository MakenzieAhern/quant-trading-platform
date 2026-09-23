from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from uuid import UUID

from app.domain.risk import RiskConfig


class PaperSessionConcurrencyError(RuntimeError):
    """Raised when an atomic lifecycle transition loses a concurrent race."""


class PaperSessionStatus(StrEnum):
    CREATED = "CREATED"
    STARTING = "STARTING"
    RUNNING = "RUNNING"
    PAUSING = "PAUSING"
    PAUSED = "PAUSED"
    STOPPING = "STOPPING"
    STOPPED = "STOPPED"
    FAILED = "FAILED"
    INTERRUPTED = "INTERRUPTED"


ALLOWED_TRANSITIONS: dict[PaperSessionStatus, frozenset[PaperSessionStatus]] = {
    PaperSessionStatus.CREATED: frozenset(
        {PaperSessionStatus.STARTING, PaperSessionStatus.STOPPED}
    ),
    PaperSessionStatus.STARTING: frozenset(
        {
            PaperSessionStatus.RUNNING,
            PaperSessionStatus.PAUSING,
            PaperSessionStatus.STOPPING,
            PaperSessionStatus.FAILED,
            PaperSessionStatus.INTERRUPTED,
        }
    ),
    PaperSessionStatus.RUNNING: frozenset(
        {
            PaperSessionStatus.PAUSING,
            PaperSessionStatus.STOPPING,
            PaperSessionStatus.STOPPED,
            PaperSessionStatus.FAILED,
            PaperSessionStatus.INTERRUPTED,
        }
    ),
    PaperSessionStatus.PAUSING: frozenset(
        {
            PaperSessionStatus.PAUSED,
            PaperSessionStatus.STOPPING,
            PaperSessionStatus.FAILED,
            PaperSessionStatus.INTERRUPTED,
        }
    ),
    PaperSessionStatus.PAUSED: frozenset({PaperSessionStatus.STARTING, PaperSessionStatus.STOPPED}),
    PaperSessionStatus.STOPPING: frozenset(
        {
            PaperSessionStatus.STOPPED,
            PaperSessionStatus.FAILED,
            PaperSessionStatus.INTERRUPTED,
        }
    ),
    PaperSessionStatus.STOPPED: frozenset(),
    PaperSessionStatus.FAILED: frozenset(),
    PaperSessionStatus.INTERRUPTED: frozenset(),
}


def require_transition(current: PaperSessionStatus, target: PaperSessionStatus) -> None:
    if target not in ALLOWED_TRANSITIONS[current]:
        raise ValueError(f"invalid paper session transition: {current} -> {target}")


@dataclass(frozen=True, slots=True)
class CreatePaperSessionCommand:
    provider_type: str
    dataset_id: str
    symbol: str
    strategy_type: str
    strategy_parameters: dict[str, object]
    initial_cash: Decimal
    default_order_quantity: Decimal
    risk: RiskConfig
    client_request_id: str | None = None


@dataclass(frozen=True, slots=True)
class PaperSession:
    id: UUID
    status: PaperSessionStatus
    provider_type: str
    dataset_id: str
    symbol: str
    strategy_type: str
    strategy_parameters: dict[str, object]
    initial_cash: Decimal
    default_order_quantity: Decimal
    risk: dict[str, object]
    created_at: datetime
    started_at: datetime | None
    stopped_at: datetime | None
    error_message: str | None
    client_request_id: str | None
    request_hash: str | None


@dataclass(frozen=True, slots=True)
class PaperEventRecord:
    session_id: UUID
    sequence: int
    event_type: str
    occurred_at: datetime
    payload: dict[str, object]
