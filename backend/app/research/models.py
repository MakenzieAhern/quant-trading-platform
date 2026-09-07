from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from enum import StrEnum

from app.data.providers.research import DailyBarRecord, SecurityStatusRecord
from app.domain.markets import SecurityId


class ResearchPeriodKind(StrEnum):
    DEVELOPMENT = "DEVELOPMENT"
    VALIDATION = "VALIDATION"
    OUT_OF_SAMPLE = "OUT_OF_SAMPLE"
    FULL_PERIOD = "FULL_PERIOD"


@dataclass(frozen=True, slots=True)
class AdjustedClosePoint:
    trading_date: date
    adjusted_close: Decimal


@dataclass(frozen=True, slots=True)
class FactorValues:
    security_id: SecurityId
    as_of: date
    mom_12_1: Decimal
    trend_120: Decimal
    vol20: Decimal

    @property
    def low_vol(self) -> Decimal:
        return -self.vol20


@dataclass(frozen=True, slots=True)
class ScoredSecurity:
    security_id: SecurityId
    alpha_score: Decimal
    mom_12_1_z: Decimal
    trend_120_z: Decimal
    low_vol_z: Decimal


@dataclass(frozen=True, slots=True)
class CrossSectionResult:
    scores: tuple[ScoredSecurity, ...]
    unavailable_factors: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class TargetPosition:
    security_id: SecurityId
    target_weight: Decimal
    quantity: Decimal
    reference_price: Decimal


@dataclass(frozen=True, slots=True)
class PortfolioTarget:
    positions: tuple[TargetPosition, ...]
    residual_cash: Decimal


@dataclass(frozen=True, slots=True)
class ResearchSession:
    trading_date: date
    bars: tuple[DailyBarRecord, ...]
    statuses: tuple[SecurityStatusRecord, ...]
    buy_lot_sizes: tuple[tuple[SecurityId, int], ...]

    def __post_init__(self) -> None:
        if any(bar.trading_date != self.trading_date for bar in self.bars):
            raise ValueError("all bars must belong to the research session")
        if len({str(bar.security_id) for bar in self.bars}) != len(self.bars):
            raise ValueError("research session contains duplicate bars")
        if any(status.status.trading_date != self.trading_date for status in self.statuses):
            raise ValueError("all statuses must belong to the research session")
