from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from enum import StrEnum

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
