from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from enum import StrEnum

from app.data.providers.research import (
    DailyBarRecord,
    FeatureOnlyDailyObservation,
    SecurityStatusRecord,
)
from app.domain.markets import CorporateAction, SecurityId
from app.domain.markets.consolidations import ShareConsolidationEvent
from app.domain.markets.demergers import DemergerEvent
from app.domain.markets.mergers import MergerEvent
from app.domain.markets.pass_through import RestructuringBonusPassThroughEvent
from app.domain.markets.rules import ResolvedTradingRules
from app.domain.markets.surrenders import MandatoryPartialShareSurrenderEvent


class ResearchPeriodKind(StrEnum):
    PILOT_SMOKE = "PILOT_SMOKE"
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
    feature_only_observations: tuple[FeatureOnlyDailyObservation, ...] = ()
    corporate_actions: tuple[CorporateAction, ...] = ()
    trading_rules: tuple[ResolvedTradingRules, ...] = ()
    demergers: tuple[DemergerEvent, ...] = ()
    mergers: tuple[MergerEvent, ...] = ()
    partial_surrenders: tuple[MandatoryPartialShareSurrenderEvent, ...] = ()
    surrender_holder_class: str | None = None
    surrender_holder_classes: tuple[tuple[SecurityId, str], ...] = ()
    pass_through_events: tuple[RestructuringBonusPassThroughEvent, ...] = ()
    consolidations: tuple[ShareConsolidationEvent, ...] = ()
    consolidation_holder_class: str | None = None
    unexplained_reference_adjustment_ids: tuple[SecurityId, ...] = ()

    def __post_init__(self) -> None:
        reference_ids = set(self.unexplained_reference_adjustment_ids)
        if len(reference_ids) != len(
            self.unexplained_reference_adjustment_ids
        ) or not reference_ids <= {bar.security_id for bar in self.bars}:
            raise ValueError("invalid reference adjustment identity")
        if any(bar.trading_date != self.trading_date for bar in self.bars):
            raise ValueError("all bars must belong to the research session")
        if len({str(bar.security_id) for bar in self.bars}) != len(self.bars):
            raise ValueError("research session contains duplicate bars")
        if any(
            observation.trading_date != self.trading_date
            for observation in self.feature_only_observations
        ):
            raise ValueError("all feature-only observations must belong to the research session")
        feature_ids = {observation.security_id for observation in self.feature_only_observations}
        if len(feature_ids) != len(self.feature_only_observations):
            raise ValueError("research session contains duplicate feature-only observations")
        if feature_ids & {bar.security_id for bar in self.bars}:
            raise ValueError("complete and feature-only observations must be disjoint")
        if any(status.status.trading_date != self.trading_date for status in self.statuses):
            raise ValueError("all statuses must belong to the research session")
        for values in (tuple(item.status for item in self.statuses), self.trading_rules):
            if len({item.security_id for item in values}) != len(values):
                raise ValueError("duplicate status or rule identity")
            if any(item.trading_date != self.trading_date for item in values):
                raise ValueError("rule/status session mismatch")
        if len({security_id for security_id, _ in self.surrender_holder_classes}) != len(
            self.surrender_holder_classes
        ):
            raise ValueError("duplicate surrender holder-class identity")
