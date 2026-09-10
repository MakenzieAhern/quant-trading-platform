from datetime import date
from enum import StrEnum
from itertools import pairwise

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.domain.common import NonNegativeDecimal, PositiveDecimal
from app.domain.markets.identifiers import Board, Exchange, Market, SecurityId
from app.domain.trading import OrderSide, OrderType


class PriceLimitModel(StrEnum):
    PERCENT_FROM_PREVIOUS_CLOSE = "PERCENT_FROM_PREVIOUS_CLOSE"
    NONE = "NONE"


class DailySecurityStatus(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    security_id: SecurityId
    trading_date: date
    is_st: bool
    is_suspended: bool
    is_one_price_limit: bool = False
    delisting_period_start: date | None = None
    source_version: str = Field(min_length=1)

    @model_validator(mode="after")
    def validate_delisting_period(self) -> "DailySecurityStatus":
        if (
            self.delisting_period_start is not None
            and self.delisting_period_start > self.trading_date
        ):
            raise ValueError("delisting period cannot start after status date")
        return self


class TransactionCostSchedule(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    commission_rate: NonNegativeDecimal
    minimum_commission: NonNegativeDecimal
    sell_stamp_duty_rate: NonNegativeDecimal
    transfer_fee_rate: NonNegativeDecimal
    valid_from: date
    valid_to: date | None = None
    source_version: str = Field(min_length=1)


class TradingRuleSet(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    rule_set_id: str = Field(min_length=1)
    market: Market = Market.CN_A
    exchange: Exchange | None = None
    board: Board | None = None
    security_id: SecurityId | None = None
    valid_from: date
    valid_to: date | None = None
    buy_lot_size: int = Field(gt=0)
    minimum_buy_quantity: int | None = Field(default=None, gt=0)
    buy_quantity_increment: int | None = Field(default=None, gt=0)
    minimum_tick: PositiveDecimal
    price_limit_rate: NonNegativeDecimal | None
    st_price_limit_rate: NonNegativeDecimal | None = None
    ipo_no_limit_sessions: int = Field(default=0, ge=0)
    conservative_no_fill_listing_sessions: int = Field(default=0, ge=0)
    odd_lot_sell_only: bool = True
    permitted_order_types: frozenset[OrderType] = frozenset({OrderType.MARKET})
    t_plus_one_sale: bool = True
    conservative_no_fill: bool = False
    cost_schedule: TransactionCostSchedule
    source: str = Field(min_length=1)
    source_publication_date: date
    provenance_note: str = Field(min_length=1)
    source_version: str = Field(min_length=1)

    @model_validator(mode="after")
    def validate_range(self) -> "TradingRuleSet":
        if self.valid_to is not None and self.valid_to < self.valid_from:
            raise ValueError("valid_to must not precede valid_from")
        if self.cost_schedule.valid_from > self.valid_from:
            raise ValueError("cost schedule must be effective by rule start")
        return self

    def applies_on(self, trading_date: date) -> bool:
        return self.valid_from <= trading_date and (
            self.valid_to is None or trading_date <= self.valid_to
        )


class TradingRuleVersion(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    version: str = Field(min_length=1)
    rules: tuple[TradingRuleSet, ...]

    @model_validator(mode="after")
    def validate_ranges(self) -> "TradingRuleVersion":
        by_scope: dict[tuple[object, ...], list[TradingRuleSet]] = {}
        for rule in self.rules:
            scope = (rule.market, rule.exchange, rule.board, str(rule.security_id))
            by_scope.setdefault(scope, []).append(rule)
        for scoped_rules in by_scope.values():
            ordered = sorted(scoped_rules, key=lambda item: item.valid_from)
            for previous, current in pairwise(ordered):
                if previous.valid_to is None or current.valid_from <= previous.valid_to:
                    raise ValueError("rule effective-date ranges must not overlap within a scope")
        return self


class ResolvedTradingRules(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    security_id: SecurityId
    trading_date: date
    buy_lot_size: int
    minimum_buy_quantity: int
    buy_quantity_increment: int
    odd_lot_sell_only: bool
    minimum_tick: PositiveDecimal
    price_limit_model: PriceLimitModel
    price_limit_rate: NonNegativeDecimal | None
    suspended: bool
    executable: bool
    t_plus_one_sale: bool
    permitted_order_types: frozenset[OrderType]
    cost_schedule: TransactionCostSchedule
    rule_source_version: str


class TradingRuleResolver:
    """Resolves effective rules with explicit security/status/IPO/board precedence."""

    def __init__(self, version: TradingRuleVersion) -> None:
        self._version = version

    def resolve(
        self,
        *,
        security_id: SecurityId,
        market: Market,
        exchange: Exchange,
        board: Board,
        trading_date: date,
        side: OrderSide,
        order_type: OrderType,
        security_status: DailySecurityStatus,
        listing_age_sessions: int,
    ) -> ResolvedTradingRules:
        if (
            security_status.security_id != security_id
            or security_status.trading_date != trading_date
        ):
            raise ValueError("SECURITY_STATUS_IDENTITY_MISMATCH")
        if listing_age_sessions < 0:
            raise ValueError("INVALID_LISTING_AGE")
        candidates = [
            rule
            for rule in self._version.rules
            if rule.market is market
            and rule.applies_on(trading_date)
            and (rule.exchange is None or rule.exchange is exchange)
            and (rule.board is None or rule.board is board)
            and (rule.security_id is None or rule.security_id == security_id)
        ]
        if not candidates:
            raise LookupError("RULE_VERSION_NOT_FOUND")
        selected = max(candidates, key=_precedence)
        limit_rate = selected.price_limit_rate
        if security_status.delisting_period_start is not None:
            # Only the pilot regime is audited; do not project it onto older transitions.
            if not date(2023, 1, 1) <= trading_date <= date(2024, 7, 31):
                raise LookupError("DELISTING_RULE_OUTSIDE_AUDITED_PERIOD")
            if trading_date == security_status.delisting_period_start:
                limit_rate = None
        elif listing_age_sessions < selected.ipo_no_limit_sessions:
            limit_rate = None
        elif security_status.is_st and selected.st_price_limit_rate is not None:
            limit_rate = selected.st_price_limit_rate
        executable = (
            not security_status.is_suspended
            and not security_status.is_one_price_limit
            and not selected.conservative_no_fill
            and listing_age_sessions >= selected.conservative_no_fill_listing_sessions
            and order_type in selected.permitted_order_types
        )
        return ResolvedTradingRules(
            security_id=security_id,
            trading_date=trading_date,
            buy_lot_size=selected.buy_lot_size,
            minimum_buy_quantity=selected.minimum_buy_quantity or selected.buy_lot_size,
            buy_quantity_increment=selected.buy_quantity_increment or selected.buy_lot_size,
            odd_lot_sell_only=selected.odd_lot_sell_only,
            minimum_tick=selected.minimum_tick,
            price_limit_model=(
                PriceLimitModel.NONE
                if limit_rate is None
                else PriceLimitModel.PERCENT_FROM_PREVIOUS_CLOSE
            ),
            price_limit_rate=limit_rate,
            suspended=security_status.is_suspended,
            executable=executable,
            t_plus_one_sale=selected.t_plus_one_sale and side is OrderSide.SELL,
            permitted_order_types=selected.permitted_order_types,
            cost_schedule=selected.cost_schedule,
            rule_source_version=f"{self._version.version}:{selected.source_version}",
        )


def _precedence(rule: TradingRuleSet) -> tuple[int, int, int]:
    return (
        1 if rule.security_id is not None else 0,
        1 if rule.board is not None else 0,
        1 if rule.exchange is not None else 0,
    )


def is_locked_one_price_bar(
    *,
    raw_open: PositiveDecimal,
    raw_high: PositiveDecimal,
    raw_low: PositiveDecimal,
    raw_close: PositiveDecimal,
    pre_close: PositiveDecimal | None,
    rules: ResolvedTradingRules,
) -> bool:
    """Conservatively identify daily price-limit locks without claiming liquidity."""
    if rules.price_limit_rate is None or pre_close is None:
        return False
    if len({raw_open, raw_high, raw_low, raw_close}) != 1:
        return False
    move = abs(raw_close - pre_close) / pre_close
    rounding_tolerance = rules.minimum_tick / pre_close
    return move + rounding_tolerance >= rules.price_limit_rate
