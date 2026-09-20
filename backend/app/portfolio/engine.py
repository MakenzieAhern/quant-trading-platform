from datetime import date, datetime
from decimal import ROUND_CEILING, ROUND_FLOOR, ROUND_HALF_EVEN, Context, Decimal, localcontext
from typing import Any

from app.domain.market import Bar
from app.domain.markets import CorporateAction, CorporateActionType
from app.domain.markets.consolidations import ShareConsolidationEvent
from app.domain.markets.corporate_actions import require_supported_corporate_action
from app.domain.markets.demergers import (
    BasisAllocationMethod,
    DemergerEvent,
    accounting_symbol,
)
from app.domain.markets.mergers import MergerEvent
from app.domain.markets.pass_through import RestructuringBonusPassThroughEvent
from app.domain.markets.surrenders import (
    MandatoryPartialShareSurrenderEvent,
)
from app.domain.trading import (
    DemergerRoundingAudit,
    Fill,
    MergerRoundingAudit,
    OrderSide,
    PartialShareSurrenderAudit,
    PendingDemergerEntitlement,
    PendingMergerEntitlement,
    PortfolioSnapshot,
    Position,
    RestructuringBonusPassThroughAudit,
    RetainedBonusRoundingAudit,
    ShareConsolidationAudit,
)
from app.event import Event, EventBus, EventType

PORTFOLIO_CONTEXT = Context(prec=28, rounding=ROUND_HALF_EVEN)
ZERO = Decimal(0)
RIGHTS_ISSUE_POLICY = "CN_A_RIGHTS_ISSUE_POLICY_V1"
RIGHTS_ENTITLEMENT_POLICY = "NO_SUBSCRIPTION_NO_MONETIZATION_V1"
RIGHTS_ISSUE_PARTICIPATION = "DECLINE_SUBSCRIPTION"
RETAINED_BONUS_FRACTION_APPROVAL_SHA256 = (
    "26bf7dafd15bf2eca4476b2dfeaa09b5fc95ee90dbe2769637ae9a21bfa603e5"
)


class PortfolioError(ValueError):
    """Raised when portfolio events violate chronological or numeric contracts."""


class PortfolioEngine:
    """Record fills and completed-Bar marks without making trading decisions."""

    def __init__(self, event_bus: EventBus, initial_cash: Decimal) -> None:
        if not isinstance(initial_cash, Decimal):
            raise TypeError("initial_cash must be a Decimal instance")
        if not initial_cash.is_finite() or initial_cash <= ZERO:
            raise ValueError("initial_cash must be positive and finite")
        self._event_bus = event_bus
        self._initial_cash = initial_cash
        self._cash = initial_cash
        self._positions: dict[str, Position] = {}
        self._marks: dict[str, Decimal] = {}
        self._mark_dates: dict[str, date] = {}
        self._snapshots: list[PortfolioSnapshot] = []
        self._cumulative_commission = ZERO
        self._running_peak = initial_cash
        self._last_event_timestamp: datetime | None = None
        self._pending_demergers: dict[str, PendingDemergerEntitlement] = {}
        self._demerger_events: dict[str, DemergerEvent] = {}
        self._demerger_audits: dict[tuple[str, str], DemergerRoundingAudit] = {}
        self._retired_realized = ZERO
        self._corporate_action_realized = ZERO
        self._merger_events: dict[str, MergerEvent] = {}
        self._pending_mergers: dict[str, PendingMergerEntitlement] = {}
        self._merger_audits: dict[str, MergerRoundingAudit] = {}
        self._surrender_events: dict[tuple[str, date], str] = {}
        self._surrender_audits: list[PartialShareSurrenderAudit] = []
        self._consolidation_audits: dict[tuple[str, date], ShareConsolidationAudit] = {}
        self._pass_through_audits: dict[tuple[str, date], RestructuringBonusPassThroughAudit] = {}
        self._retained_bonus_audits: dict[str, RetainedBonusRoundingAudit] = {}
        self._event_bus.subscribe(EventType.ORDER_FILLED, self._on_fill)
        self._event_bus.subscribe(EventType.MARKET_DATA, self._on_market_data)

    @property
    def initial_cash(self) -> Decimal:
        return self._initial_cash

    @property
    def cash(self) -> Decimal:
        return self._cash

    @property
    def positions(self) -> tuple[Position, ...]:
        return tuple(self._positions[symbol] for symbol in sorted(self._positions))

    @property
    def snapshots(self) -> tuple[PortfolioSnapshot, ...]:
        return tuple(self._snapshots)

    @property
    def latest_snapshot(self) -> PortfolioSnapshot | None:
        return self._snapshots[-1] if self._snapshots else None

    @property
    def marks(self) -> dict[str, Decimal]:
        return {symbol: self._marks[symbol] for symbol in sorted(self._marks)}

    @property
    def cumulative_commission(self) -> Decimal:
        return self._cumulative_commission

    @property
    def pending_demergers(self) -> tuple[PendingDemergerEntitlement, ...]:
        return tuple(self._pending_demergers[k] for k in sorted(self._pending_demergers))

    @property
    def partial_surrender_audits(self) -> tuple[PartialShareSurrenderAudit, ...]:
        return tuple(
            sorted(self._surrender_audits, key=lambda a: (a.effective_date, str(a.security_id)))
        )

    @property
    def demerger_rounding_audits(self) -> tuple[DemergerRoundingAudit, ...]:
        return tuple(self._demerger_audits[k] for k in sorted(self._demerger_audits))

    @property
    def pass_through_audits(self) -> tuple[RestructuringBonusPassThroughAudit, ...]:
        return tuple(self._pass_through_audits[k] for k in sorted(self._pass_through_audits))

    @property
    def consolidation_audits(self) -> tuple[ShareConsolidationAudit, ...]:
        return tuple(self._consolidation_audits[k] for k in sorted(self._consolidation_audits))

    @property
    def retained_bonus_rounding_audits(self) -> tuple[RetainedBonusRoundingAudit, ...]:
        return tuple(self._retained_bonus_audits[k] for k in sorted(self._retained_bonus_audits))

    def apply_consolidation(
        self, event: ShareConsolidationEvent, timestamp: datetime, *, holder_class: str | None
    ) -> None:
        self._require_chronological(timestamp, "share consolidation")
        event.require_supported()
        if timestamp.date() != event.effective_date or holder_class != event.affected_holder_class:
            raise PortfolioError("CONSOLIDATION_BOUNDARY_OR_HOLDER_MISMATCH")
        symbol = accounting_symbol(event.security_id)
        key = (symbol, event.effective_date)
        if key in self._consolidation_audits:
            raise PortfolioError("duplicate share consolidation")
        current = self._positions.get(symbol)
        q = current.quantity if current else ZERO
        theoretical, whole = event.quantities(q)
        with localcontext(PORTFOLIO_CONTEXT):
            basis = (
                (
                    current.aggregate_cost_basis
                    if current.aggregate_cost_basis is not None
                    else q * current.average_price
                )
                if current
                else ZERO
            )
            retained = basis if whole else ZERO
            lost = basis - retained
            updated = None
            if current is not None:
                # Preserve carrying value through the non-trading unit conversion. This
                # is not a price observation; the next actual raw Bar replaces the mark.
                carrying = q * self._marks.get(symbol, current.market_price)
                mark = carrying / whole if whole else ZERO
                updated = Position(
                    symbol=symbol,
                    quantity=whole,
                    average_price=retained / whole if whole else ZERO,
                    aggregate_cost_basis=retained,
                    market_price=mark,
                    unrealized_pnl=carrying - retained if whole else ZERO,
                    realized_pnl=current.realized_pnl,
                )
            audit = ShareConsolidationAudit(
                event_checksum=event.event_checksum,
                security_id=str(event.security_id),
                effective_date=event.effective_date,
                original_quantity=q,
                theoretical_quantity=theoretical,
                new_quantity=whole,
                discarded_fraction=theoretical - whole,
                original_basis=basis,
                retained_basis=retained,
                basis_written_off=lost,
                fractional_treatment="EXACT"
                if theoretical == whole
                else (
                    "OFFICIAL_FLOOR"
                    if event.official_fraction_method == "FLOOR"
                    else "RESEARCH_FLOOR"
                ),
            )
        if updated is not None:
            self._positions[symbol] = updated
            self._marks.pop(symbol, None)
            self._mark_dates.pop(symbol, None)
        with localcontext(PORTFOLIO_CONTEXT):
            self._corporate_action_realized -= lost
        self._consolidation_audits[key] = audit
        self._last_event_timestamp = timestamp

    def apply_pass_through(
        self, event: RestructuringBonusPassThroughEvent, timestamp: datetime
    ) -> None:
        self._require_chronological(timestamp, "restructuring pass-through")
        event.require_supported()
        if timestamp.date() != event.effective_date:
            raise PortfolioError("pass-through session mismatch")
        symbol = accounting_symbol(event.security_id)
        key = (symbol, event.effective_date)
        if key in self._pass_through_audits:
            raise PortfolioError("duplicate restructuring pass-through")
        current = self._positions.get(symbol)
        q = current.quantity if current else ZERO
        if q < ZERO or q != q.to_integral_value():
            raise PortfolioError("pass-through requires whole long shares")
        with localcontext(PORTFOLIO_CONTEXT) as context:
            context.prec = max(
                context.prec,
                len(q.as_tuple().digits) + len(event.bonus_ratio.as_tuple().digits) + 1,
            )
            basis = (
                (
                    current.aggregate_cost_basis
                    if current.aggregate_cost_basis is not None
                    else q * current.average_price
                )
                if current
                else ZERO
            )
            audit = RestructuringBonusPassThroughAudit(
                event_checksum=event.event_checksum,
                security_id=str(event.security_id),
                effective_date=event.effective_date,
                temporary_registration_date=event.temporary_registration_date,
                transfer_date=event.transfer_date,
                transfer_recipient=event.transfer_recipient,
                original_quantity=q,
                original_basis=basis,
                bonus_ratio=event.bonus_ratio,
                temporary_bonus_quantity=q * event.bonus_ratio,
                convention_approval_sha256=event.convention_approval_sha256,
            )
        # Metadata only: do not touch positions, basis, cash, marks, PnL or execution.
        self._pass_through_audits[key] = audit
        self._last_event_timestamp = timestamp

    def apply_partial_surrender(
        self,
        event: MandatoryPartialShareSurrenderEvent,
        timestamp: datetime,
        *,
        holder_class: str | None,
    ) -> None:
        self._require_chronological(timestamp, "partial share surrender")
        event.require_supported()
        if timestamp.date() != event.application_date:
            raise PortfolioError("partial surrender session mismatch")
        if holder_class != event.affected_holder_class:
            raise PortfolioError("PARTIAL_SURRENDER_HOLDER_APPLICABILITY_UNVERIFIED")
        symbol = accounting_symbol(event.security_id)
        key = (symbol, timestamp.date())
        if key in self._surrender_events:
            raise PortfolioError("duplicate partial surrender")
        current = self._positions.get(symbol)
        audit = None
        updated = None
        if current is not None and current.quantity:
            with localcontext(PORTFOLIO_CONTEXT):
                q = current.quantity
                if q < ZERO or q != q.to_integral_value():
                    raise PortfolioError("partial surrender requires whole long shares")
                with localcontext(PORTFOLIO_CONTEXT) as quantity_context:
                    ratios = [
                        event.surrender_ratio,
                        *(band.surrender_ratio for band in event.quantity_bands),
                    ]
                    quantity_context.prec = max(
                        quantity_context.prec,
                        len(q.as_tuple().digits)
                        + max(len(ratio.as_tuple().digits) for ratio in ratios if ratio is not None)
                        + 1,
                    )
                    theoretical = event.theoretical_surrender(q)
                    lower = theoretical.to_integral_value(rounding=ROUND_FLOOR)
                    surrendered = (
                        lower
                        if event.quantity_rounding_rule == "OFFICIAL_FLOOR_SURRENDER"
                        else (
                            min(q, theoretical.to_integral_value(rounding=ROUND_CEILING))
                            if event.research_fraction_rule is not None
                            else theoretical
                        )
                    )
                    retained = q - surrendered
                # Issuer-level issuance rounding cannot define this holder-level transfer.
                if surrendered != surrendered.to_integral_value():
                    raise PortfolioError("PARTIAL_SURRENDER_FRACTIONAL_ALLOCATION_UNRESOLVED")
                basis = current.aggregate_cost_basis
                if basis is None:
                    basis = q * current.average_price
                retained_basis = basis * retained / q
                surrendered_basis = basis - retained_basis
                price = self._marks.get(symbol, current.market_price)
                average = basis / q
                if retained and retained_basis / retained != average:
                    raise PortfolioError("PARTIAL_SURRENDER_DECIMAL_INVARIANT_UNREPRESENTABLE")
                updated = Position(
                    symbol=symbol,
                    quantity=retained,
                    average_price=average if retained else ZERO,
                    aggregate_cost_basis=retained_basis,
                    market_price=price,
                    unrealized_pnl=retained * price - retained_basis,
                    realized_pnl=current.realized_pnl,
                )
                audit = PartialShareSurrenderAudit(
                    event_checksum=event.event_checksum,
                    security_id=str(event.security_id),
                    effective_date=timestamp.date(),
                    affected_holder_class=holder_class,
                    original_quantity=q,
                    surrendered_quantity=surrendered,
                    retained_quantity=retained,
                    original_basis=basis,
                    surrendered_basis=surrendered_basis,
                    retained_basis=retained_basis,
                    market_value_removed=surrendered * price,
                    historical_registry_date=event.effective_date,
                    research_boundary=(
                        "FIRST_POST_EVENT_TRADING_BOUNDARY_V1"
                        if event.research_effective_date
                        else None
                    ),
                    official_fraction_rule=(
                        "NOT_EVIDENCED"
                        if event.quantity_rounding_rule == "UNRESOLVED"
                        else event.quantity_rounding_rule
                    ),
                    research_fraction_rule=event.research_fraction_rule,
                    convention_approval_sha256=event.convention_approval_sha256,
                    theoretical_surrender=theoretical,
                    lower_surrender_bound=lower,
                    extra_shares_vs_floor=surrendered - lower,
                    estimated_value_difference=(surrendered - lower) * price,
                )
                realized = self._corporate_action_realized - surrendered_basis
        # No state changes until every account quantity/basis/provenance check passes.
        if updated is not None and audit is not None:
            self._positions[symbol] = updated
            self._corporate_action_realized = realized
            self._surrender_audits.append(audit)
        self._surrender_events[key] = event.event_checksum
        self._last_event_timestamp = timestamp

    def partial_surrender_materiality(self) -> dict[str, Any]:
        with localcontext(PORTFOLIO_CONTEXT):
            return {
                "events_total": len(self._surrender_events),
                "securities_with_partial_surrender": len({k[0] for k in self._surrender_events}),
                "position_occurrences": len(self._surrender_audits),
                "total_shares_surrendered": sum(
                    (a.surrendered_quantity for a in self._surrender_audits), ZERO
                ),
                "total_basis_written_off": sum(
                    (a.surrendered_basis for a in self._surrender_audits), ZERO
                ),
                "max_single_event_basis_write_off": max(
                    (a.surrendered_basis for a in self._surrender_audits), default=ZERO
                ),
                "events_with_compensation": 0,
                "fractional_surrender_cases": sum(
                    a.theoretical_surrender != a.lower_surrender_bound
                    for a in self._surrender_audits
                ),
                "zero_retained_cases": sum(
                    a.retained_quantity == ZERO for a in self._surrender_audits
                ),
                "max_extra_share_surrendered_vs_floor": max(
                    (a.extra_shares_vs_floor for a in self._surrender_audits), default=ZERO
                ),
                "max_estimated_economic_difference": max(
                    (a.estimated_value_difference for a in self._surrender_audits), default=ZERO
                ),
                "scope": "APPLIED_SUPPORTED_EVENTS_ONLY_NOT_FULL_SOURCE_INVENTORY",
            }

    def is_orderable(self, symbol: str, *, require_observed_unit_price: bool = True) -> bool:
        if require_observed_unit_price and any(
            event_symbol == symbol and self._mark_dates.get(symbol, date.min) < effective
            for event_symbol, effective in self._consolidation_audits
        ):
            return False
        if symbol in self._merger_events:
            return False
        if symbol in self._demerger_events:
            event = self._demerger_events[symbol]
            retained = any(accounting_symbol(s.security_id) == symbol for s in event.successors)
            if not retained:
                return False
        if self._last_event_timestamp is not None and any(
            symbol == accounting_symbol(e.successor_security)
            and self._last_event_timestamp.date() < e.successor_listing_date
            for e in self._merger_events.values()
        ):
            return False
        if self._last_event_timestamp is not None and any(
            symbol == accounting_symbol(s.security_id)
            and self._last_event_timestamp.date() < s.listing_date
            for e in self._demerger_events.values()
            for s in e.successors
        ):
            return False
        return not any(symbol == s for p in self.pending_demergers for s in p.successor_symbols)

    @property
    def pending_mergers(self) -> tuple[PendingMergerEntitlement, ...]:
        return tuple(self._pending_mergers[k] for k in sorted(self._pending_mergers))

    @property
    def merger_rounding_audits(self) -> tuple[MergerRoundingAudit, ...]:
        return tuple(self._merger_audits[k] for k in sorted(self._merger_audits))

    def merger_materiality(self) -> dict[str, int | Decimal | None]:
        """Observed account conversions only, never a full-dataset census or strategy metric."""
        audits = self.merger_rounding_audits
        values = [a.maximum_estimated_discarded_value for a in audits]
        bounds = [a.maximum_floor_ceil_value_difference for a in audits]
        zero_whole = [a for a in audits if a.whole_successor_quantity == ZERO]
        with localcontext(PORTFOLIO_CONTEXT):
            return {
                "zero_whole_share_events": len({a.event_checksum for a in zero_whole}),
                "zero_whole_share_position_occurrences": len(zero_whole),
                "total_basis_written_off": sum((a.basis_written_off for a in zero_whole), ZERO),
                "max_single_write_off": max(
                    (a.basis_written_off for a in zero_whole), default=ZERO
                ),
                "total_market_value_removed_at_events": sum(
                    (a.market_value_removed for a in zero_whole), ZERO
                ),
                "fractional_merger_events_total": sum(bool(a.fractional_remainder) for a in audits),
                "total_discarded_fractional_shares": sum(
                    (a.fractional_remainder for a in audits), ZERO
                ),
                "max_single_event_discarded_share_fraction": max(
                    (a.fractional_remainder for a in audits), default=ZERO
                ),
                "max_single_event_estimated_value": None
                if None in values
                else max((v for v in values if v is not None), default=ZERO),
                "aggregate_estimated_discarded_value": None
                if None in values
                else sum((v for v in values if v is not None), ZERO),
                "max_floor_ceil_value_difference": None
                if None in bounds
                else max((v for v in bounds if v is not None), default=ZERO),
                "aggregate_floor_ceil_value_difference": None
                if None in bounds
                else sum((v for v in bounds if v is not None), ZERO),
            }

    def recognize_merger(self, event: MergerEvent, session_date: date, timestamp: datetime) -> None:
        self._require_chronological(timestamp, "merger")
        event.require_supported()
        if session_date != event.effective_date:
            raise PortfolioError("merger must belong to its effective session")
        parent = accounting_symbol(event.parent_security)
        successor = accounting_symbol(event.successor_security)
        if parent in self._merger_events or parent in self._demerger_events:
            raise PortfolioError("duplicate mandatory conversion")
        current = self._positions.get(parent)
        pending, audit = None, None
        if current is not None and current.quantity:
            theoretical, whole, remainder = event.quantities(current.quantity)
            exact = event.theoretical_fraction(current.quantity)
            price = self._marks.get(parent)
            if price is None or self._mark_dates.get(parent) != event.parent_last_trading_date:
                raise PortfolioError("MERGER_PARENT_LAST_RAW_CLOSE_UNAVAILABLE")
            with localcontext(PORTFOLIO_CONTEXT):
                basis = current.aggregate_cost_basis
                if basis is None:
                    basis = current.quantity * current.average_price
                pending = (
                    PendingMergerEntitlement(
                        parent_symbol=parent,
                        successor_symbols=(successor,),
                        event_checksum=event.event_checksum,
                        parent_quantity=current.quantity,
                        aggregate_cost_basis=basis,
                        carrying_value=current.quantity * price,
                        whole_successor_quantity=whole,
                    )
                    if whole
                    else None
                )
                audit = MergerRoundingAudit(
                    event_checksum=event.event_checksum,
                    parent_symbol=parent,
                    successor_symbol=successor,
                    parent_quantity=current.quantity,
                    theoretical_successor_quantity=theoretical,
                    exact_theoretical_numerator=exact.numerator,
                    exact_theoretical_denominator=exact.denominator,
                    whole_successor_quantity=whole,
                    fractional_remainder=remainder,
                    floor_ceil_quantity_difference=Decimal(1) if remainder else ZERO,
                    zero_whole_share_policy=event.zero_whole_share_policy,
                    accounting_classification="CORPORATE_ACTION_FRACTIONAL_FORFEITURE_LOSS"
                    if not whole
                    else None,
                    basis_written_off=basis if not whole else ZERO,
                    market_value_removed=current.quantity * price if not whole else ZERO,
                )
        self._merger_events[parent] = event
        if pending is not None:
            self._pending_mergers[parent] = pending
        if audit is not None:
            self._merger_audits[parent] = audit
            with localcontext(PORTFOLIO_CONTEXT):
                self._corporate_action_realized -= audit.basis_written_off
        if current is not None:
            with localcontext(PORTFOLIO_CONTEXT):
                self._retired_realized += current.realized_pnl
        self._positions.pop(parent, None)
        self._marks.pop(parent, None)
        self._mark_dates.pop(parent, None)
        self._last_event_timestamp = timestamp

    def activate_mergers(
        self, session_date: date, raw_opens: dict[str, Decimal], timestamp: datetime
    ) -> None:
        self._require_chronological(timestamp, "merger activation")
        updates: dict[str, Position] = {}
        completed = []
        with localcontext(PORTFOLIO_CONTEXT):
            for parent, pending in sorted(self._pending_mergers.items()):
                event = self._merger_events[parent]
                if session_date < event.activation_date:
                    continue
                symbol = accounting_symbol(event.successor_security)
                price = raw_opens.get(symbol)
                if not isinstance(price, Decimal) or not price.is_finite() or price <= ZERO:
                    raise PortfolioError("MERGER_SUCCESSOR_RAW_PRICE_UNAVAILABLE")
                current = updates.get(symbol, self._positions.get(symbol))
                if current is not None and current.quantity < ZERO:
                    raise PortfolioError("merger policy is long-only")
                quantity = pending.whole_successor_quantity
                basis = pending.aggregate_cost_basis
                realized = ZERO
                if current is not None:
                    quantity += current.quantity
                    basis += (
                        current.aggregate_cost_basis
                        if current.aggregate_cost_basis is not None
                        else current.quantity * current.average_price
                    )
                    realized = current.realized_pnl
                updates[symbol] = Position(
                    symbol=symbol,
                    quantity=quantity,
                    average_price=basis / quantity,
                    aggregate_cost_basis=basis,
                    market_price=price,
                    unrealized_pnl=quantity * price - basis,
                    realized_pnl=realized,
                )
                completed.append(parent)
        self._positions.update(updates)
        self._marks.update({symbol: position.market_price for symbol, position in updates.items()})
        for parent in completed:
            del self._pending_mergers[parent]
        for symbol, price in sorted(raw_opens.items()):
            if isinstance(price, Decimal) and price.is_finite() and price > ZERO:
                self._observe_merger_price(symbol, price, session_date)
        self._last_event_timestamp = timestamp

    def _observe_merger_price(self, symbol: str, raw_price: Decimal, session_date: date) -> None:
        with localcontext(PORTFOLIO_CONTEXT):
            for parent, audit in self._merger_audits.items():
                if parent in self._pending_mergers or audit.successor_symbol != symbol:
                    continue
                if session_date < self._merger_events[parent].activation_date:
                    continue
                maximum = max(audit.maximum_observed_raw_price or raw_price, raw_price)
                self._merger_audits[parent] = audit.model_copy(
                    update={
                        "first_available_raw_price": audit.first_available_raw_price or raw_price,
                        "maximum_observed_raw_price": maximum,
                        "maximum_estimated_discarded_value": maximum * audit.fractional_remainder,
                        "maximum_floor_ceil_value_difference": maximum
                        * audit.floor_ceil_quantity_difference,
                    }
                )

    def recognize_demerger(
        self, event: DemergerEvent, session_date: date, timestamp: datetime
    ) -> None:
        self._require_chronological(timestamp, "demerger")
        event.require_supported()
        if session_date != event.application_date:
            raise PortfolioError("demerger must belong to its effective session")
        parent = accounting_symbol(event.parent_security)
        if parent in self._demerger_events or parent in self._merger_events:
            raise PortfolioError("duplicate demerger")
        current = self._positions.get(parent)
        if current is not None and current.quantity < ZERO:
            raise PortfolioError("demerger policy is long-only")
        pending = None
        if current is not None and current.quantity > ZERO:
            if (
                self._marks.get(parent) != event.parent_last_close
                or self._mark_dates.get(parent) != event.parent_last_trading_date
            ):
                raise PortfolioError("demerger parent last raw close mismatch")
            with localcontext(PORTFOLIO_CONTEXT):
                for successor in event.successors:
                    quantity = current.quantity * successor.conversion_ratio
                    if (
                        quantity != quantity.to_integral_value()
                        and event.research_fractional_method is None
                    ):
                        raise PortfolioError("DEMERGER_FRACTIONAL_QUANTITY_UNRESOLVED")
                basis = current.aggregate_cost_basis
                if basis is None:
                    basis = current.quantity * current.average_price
                pending = PendingDemergerEntitlement(
                    parent_symbol=parent,
                    successor_symbols=tuple(
                        sorted(accounting_symbol(s.security_id) for s in event.successors)
                    ),
                    event_checksum=event.event_checksum,
                    parent_quantity=current.quantity,
                    aggregate_cost_basis=basis,
                    carrying_value=current.quantity * event.parent_last_close,
                )
        self._demerger_events[parent] = event
        if pending is not None:
            self._pending_demergers[parent] = pending
        if current is not None:
            with localcontext(PORTFOLIO_CONTEXT):
                self._retired_realized += current.realized_pnl
        self._positions.pop(parent, None)
        self._marks.pop(parent, None)
        self._mark_dates.pop(parent, None)
        self._last_event_timestamp = timestamp

    def activate_demergers(
        self, session_date: date, raw_opens: dict[str, Decimal], timestamp: datetime
    ) -> None:
        self._require_chronological(timestamp, "demerger activation")
        updates: dict[str, Position] = {}
        audits: dict[tuple[str, str], DemergerRoundingAudit] = {}
        completed = []
        basis_written_off = ZERO
        with localcontext(PORTFOLIO_CONTEXT):
            for parent, pending in sorted(self._pending_demergers.items()):
                event = self._demerger_events[parent]
                successors = sorted(event.successors, key=lambda s: str(s.security_id))
                if session_date < successors[0].listing_date:
                    continue
                event.require_supported()
                if max(s.published_on for s in event.allocation_sources) >= session_date:
                    raise PortfolioError("demerger allocation evidence unavailable")
                weights = [
                    (
                        s.basis_allocation_weight or ZERO
                        if event.basis_allocation == BasisAllocationMethod.OFFICIAL_ASSET_ALLOCATION
                        else s.conversion_ratio * s.reference_value
                    )
                    for s in successors
                ]
                total = sum(weights, ZERO)
                remaining = pending.aggregate_cost_basis
                for index, (successor, weight) in enumerate(zip(successors, weights, strict=True)):
                    symbol = accounting_symbol(successor.security_id)
                    price = raw_opens.get(symbol)
                    if not isinstance(price, Decimal) or not price.is_finite() or price <= ZERO:
                        raise PortfolioError("DEMERGER_SUCCESSOR_RAW_PRICE_UNAVAILABLE")
                    if symbol in updates or symbol in self._positions:
                        raise PortfolioError("DEMERGER_EXISTING_SUCCESSOR_POSITION_UNSUPPORTED")
                    basis = (
                        remaining
                        if index == len(successors) - 1
                        else (pending.aggregate_cost_basis * weight / total)
                    )
                    remaining -= basis
                    theoretical = pending.parent_quantity * successor.conversion_ratio
                    quantity = (
                        theoretical.to_integral_value(rounding=ROUND_FLOOR)
                        if event.research_fractional_method is not None
                        else theoretical
                    )
                    if event.research_fractional_method is not None:
                        written_off = basis if not quantity else ZERO
                        audits[(parent, symbol)] = DemergerRoundingAudit(
                            event_checksum=event.event_checksum,
                            parent_symbol=parent,
                            successor_symbol=symbol,
                            parent_quantity=pending.parent_quantity,
                            theoretical_successor_quantity=theoretical,
                            whole_successor_quantity=quantity,
                            fractional_remainder=theoretical - quantity,
                            branch_basis=basis,
                            basis_transferred=basis - written_off,
                            basis_written_off=written_off,
                            official_fractional_method=event.official_fractional_method,
                            research_fractional_method=event.research_fractional_method,
                        )
                        basis_written_off += written_off
                    if quantity:
                        updates[symbol] = Position(
                            symbol=symbol,
                            quantity=quantity,
                            average_price=basis / quantity,
                            aggregate_cost_basis=basis,
                            market_price=price,
                            unrealized_pnl=quantity * price - basis,
                            realized_pnl=ZERO,
                        )
                assert remaining == ZERO
                completed.append(parent)
        # Validate every successor before publishing any ownership change.
        self._positions.update(updates)
        self._marks.update({s: p.market_price for s, p in updates.items()})
        self._demerger_audits.update(audits)
        self._corporate_action_realized -= basis_written_off
        for parent in completed:
            del self._pending_demergers[parent]
        self._last_event_timestamp = timestamp

    def apply_fill(self, fill: Fill) -> Position:
        self._require_chronological(fill.timestamp, "fill")
        self._reject_pass_through_trading(fill.symbol, fill.timestamp)
        if not self.is_orderable(fill.symbol):
            raise PortfolioError("CORPORATE_ACTION_NON_ORDERABLE")
        current = self._positions.get(fill.symbol)
        current_quantity = current.quantity if current is not None else ZERO
        current_average = current.average_price if current is not None else ZERO
        current_realized = current.realized_pnl if current is not None else ZERO
        signed_fill_quantity = fill.quantity if fill.side is OrderSide.BUY else -fill.quantity

        with localcontext(PORTFOLIO_CONTEXT):
            notional = fill.quantity * fill.price
            cash_change = -notional if fill.side is OrderSide.BUY else notional
            updated_cash = self._cash + cash_change - fill.commission
            updated_commission = self._cumulative_commission + fill.commission
            new_quantity = current_quantity + signed_fill_quantity
            new_average, realized_change = self._cost_basis_after_fill(
                current_quantity,
                current_average,
                signed_fill_quantity,
                fill.price,
            )
            aggregate_basis = None
            if current is not None and current.aggregate_cost_basis is not None:
                if new_quantity < ZERO:
                    raise PortfolioError("converted position cannot become short")
                if fill.side is OrderSide.BUY:
                    aggregate_basis = current.aggregate_cost_basis + notional
                else:
                    removed = (
                        current.aggregate_cost_basis
                        if new_quantity == ZERO
                        else (current.aggregate_cost_basis * fill.quantity / current_quantity)
                    )
                    aggregate_basis = current.aggregate_cost_basis - removed
                    realized_change = notional - removed
                new_average = aggregate_basis / new_quantity if new_quantity else ZERO
            realized = current_realized + realized_change
            mark = self._marks.get(fill.symbol, fill.price)
            unrealized = (
                (
                    new_quantity * mark - aggregate_basis
                    if aggregate_basis is not None
                    else new_quantity * (mark - new_average)
                )
                if new_quantity
                else ZERO
            )

        updated = Position(
            symbol=fill.symbol,
            quantity=new_quantity,
            average_price=new_average,
            market_price=mark,
            unrealized_pnl=unrealized,
            realized_pnl=realized,
            aggregate_cost_basis=aggregate_basis,
        )
        self._cash = updated_cash
        self._cumulative_commission = updated_commission
        self._positions[fill.symbol] = updated
        self._last_event_timestamp = fill.timestamp
        return updated

    def mark_to_market(self, bar: Bar, *, snapshot: bool = True) -> PortfolioSnapshot | None:
        self._require_chronological(bar.timestamp, "market data")
        self._reject_pass_through_trading(bar.symbol, bar.timestamp)
        if not self.is_orderable(bar.symbol, require_observed_unit_price=False):
            raise PortfolioError("pending or retired security cannot receive a market quote")

        self._marks[bar.symbol] = bar.close
        self._mark_dates[bar.symbol] = bar.timestamp.date()
        self._observe_merger_price(bar.symbol, bar.open, bar.timestamp.date())
        self._observe_merger_price(bar.symbol, bar.high, bar.timestamp.date())
        current = self._positions.get(bar.symbol)
        if current is not None:
            with localcontext(PORTFOLIO_CONTEXT):
                unrealized = current.quantity * (bar.close - current.average_price)
                if current.aggregate_cost_basis is not None:
                    unrealized = current.quantity * bar.close - current.aggregate_cost_basis
            self._positions[bar.symbol] = current.model_copy(
                update={"market_price": bar.close, "unrealized_pnl": unrealized}
            )

        return self.snapshot_at(bar.timestamp) if snapshot else None

    def compact_closed_positions(self) -> None:
        """Retain realized PnL while dropping zero-quantity research bookkeeping."""
        closed = tuple(
            symbol for symbol, position in self._positions.items() if not position.quantity
        )
        for symbol in closed:
            self._retired_realized += self._positions.pop(symbol).realized_pnl
            self._marks.pop(symbol, None)
            self._mark_dates.pop(symbol, None)

    def snapshot_at(self, timestamp: datetime) -> PortfolioSnapshot:
        self._require_chronological(timestamp, "snapshot")
        with localcontext(PORTFOLIO_CONTEXT):
            positions = self.positions
            market_value = sum(
                (position.quantity * position.market_price for position in positions), ZERO
            ) + sum(
                (p.carrying_value for p in (*self.pending_demergers, *self.pending_mergers)), ZERO
            )
            unrealized_pnl = sum((position.unrealized_pnl for position in positions), ZERO) + sum(
                (p.unrealized_pnl for p in (*self.pending_demergers, *self.pending_mergers)), ZERO
            )
            realized_pnl = sum(
                (position.realized_pnl for position in positions), self._retired_realized
            )
            equity = self._cash + market_value
            running_peak = max(self._running_peak, equity)
            drawdown = equity / running_peak - Decimal(1)
            total_pnl = equity - self._initial_cash

        snapshot = PortfolioSnapshot(
            timestamp=timestamp,
            cash=self._cash,
            positions=positions,
            market_value=market_value,
            equity=equity,
            realized_pnl=realized_pnl,
            unrealized_pnl=unrealized_pnl,
            cumulative_commission=self._cumulative_commission,
            drawdown=drawdown,
            pending_demergers=self.pending_demergers,
            pending_mergers=self.pending_mergers,
            merger_rounding_audits=self.merger_rounding_audits,
            demerger_rounding_audits=self.demerger_rounding_audits,
            corporate_action_realized_pnl=self._corporate_action_realized,
            total_pnl=total_pnl,
            partial_surrender_audits=self.partial_surrender_audits,
            pass_through_audits=self.pass_through_audits,
            consolidation_audits=self.consolidation_audits,
            retained_bonus_rounding_audits=self.retained_bonus_rounding_audits,
        )
        self._running_peak = running_peak
        self._last_event_timestamp = timestamp
        self._snapshots.append(snapshot)
        self._event_bus.publish(
            Event(EventType.PORTFOLIO_UPDATED, snapshot, occurred_at=snapshot.timestamp)
        )
        return snapshot

    def apply_corporate_action(
        self, symbol: str, action: CorporateAction, timestamp: datetime
    ) -> Position | None:
        """Apply only complete, economically reconstructable long-position events."""
        self._require_chronological(timestamp, "corporate action")
        try:
            require_supported_corporate_action(action)
        except ValueError as exc:
            raise PortfolioError(str(exc)) from exc
        current = self._positions.get(symbol)
        if action.action_type is CorporateActionType.RIGHTS_RELATED_EVENT:
            if current is not None and current.quantity < ZERO:
                raise PortfolioError("rights policy is long-only")
            # Decline subscription: no entitlement asset, cash, shares, orders or fills.
            self._last_event_timestamp = timestamp
            return current
        if current is None or current.quantity <= ZERO:
            return current
        if action.action_type is CorporateActionType.CASH_DIVIDEND:
            with localcontext(PORTFOLIO_CONTEXT):
                income = current.quantity * action.cash_per_share
                self._cash += income
                self._corporate_action_realized += income
            self._last_event_timestamp = timestamp
            return current
        if action.action_type in {
            CorporateActionType.STOCK_DIVIDEND,
            CorporateActionType.BONUS_SHARE,
        }:
            assert action.share_ratio is not None
            assert action.ex_date is not None
            if action.event_checksum in self._retained_bonus_audits:
                raise PortfolioError("duplicate retained bonus")
            with localcontext(PORTFOLIO_CONTEXT):
                basis = current.aggregate_cost_basis
                if basis is None:
                    basis = current.quantity * current.average_price
                theoretical = current.quantity * (Decimal(1) + action.share_ratio)
                quantity = theoretical.to_integral_value(rounding=ROUND_FLOOR)
                updated = current.model_copy(
                    update={
                        "quantity": quantity,
                        "average_price": basis / quantity,
                        "aggregate_cost_basis": basis,
                        "unrealized_pnl": quantity * current.market_price - basis,
                    }
                )
                self._retained_bonus_audits[action.event_checksum] = RetainedBonusRoundingAudit(
                    event_checksum=action.event_checksum,
                    security_id=str(action.security_id),
                    effective_date=action.ex_date,
                    original_quantity=current.quantity,
                    share_ratio=action.share_ratio,
                    theoretical_quantity=theoretical,
                    whole_quantity=quantity,
                    discarded_fraction=theoretical - quantity,
                    original_basis=basis,
                    retained_basis=basis,
                    fractional_treatment=(
                        "EXACT" if theoretical == quantity else "RESEARCH_FLOOR_NO_CASH"
                    ),
                    convention_approval_sha256=RETAINED_BONUS_FRACTION_APPROVAL_SHA256,
                )
            self._positions[symbol] = updated
            self._last_event_timestamp = timestamp
            return updated
        raise PortfolioError("unsupported corporate action type")

    def reset(self) -> None:
        self._cash = self._initial_cash
        self._positions.clear()
        self._marks.clear()
        self._mark_dates.clear()
        self._snapshots.clear()
        self._cumulative_commission = ZERO
        self._running_peak = self._initial_cash
        self._last_event_timestamp = None
        self._pending_demergers.clear()
        self._demerger_events.clear()
        self._demerger_audits.clear()
        self._retired_realized = ZERO
        self._corporate_action_realized = ZERO
        self._merger_events.clear()
        self._pending_mergers.clear()
        self._merger_audits.clear()
        self._surrender_events.clear()
        self._surrender_audits.clear()
        self._pass_through_audits.clear()
        self._consolidation_audits.clear()
        self._retained_bonus_audits.clear()

    def _reject_pass_through_trading(self, symbol: str, timestamp: datetime) -> None:
        for (event_symbol, _), audit in self._pass_through_audits.items():
            if (
                symbol == event_symbol
                and audit.temporary_registration_date <= timestamp.date() <= audit.transfer_date
            ):
                raise PortfolioError("PASS_THROUGH_TRADING_OBSERVATION_CONFLICT")

    def _require_chronological(self, timestamp: datetime, event_name: str) -> None:
        if self._last_event_timestamp is not None and timestamp < self._last_event_timestamp:
            raise PortfolioError(f"{event_name} cannot move portfolio time backwards")

    @staticmethod
    def _cost_basis_after_fill(
        current_quantity: Decimal,
        current_average: Decimal,
        signed_fill_quantity: Decimal,
        fill_price: Decimal,
    ) -> tuple[Decimal, Decimal]:
        if current_quantity == ZERO:
            return fill_price, ZERO
        if (current_quantity > ZERO) == (signed_fill_quantity > ZERO):
            new_quantity = current_quantity + signed_fill_quantity
            weighted_cost = (
                abs(current_quantity) * current_average + abs(signed_fill_quantity) * fill_price
            )
            return weighted_cost / abs(new_quantity), ZERO

        closing_quantity = min(abs(current_quantity), abs(signed_fill_quantity))
        if current_quantity > ZERO:
            realized = closing_quantity * (fill_price - current_average)
        else:
            realized = closing_quantity * (current_average - fill_price)
        new_quantity = current_quantity + signed_fill_quantity
        if new_quantity == ZERO:
            return ZERO, realized
        if (new_quantity > ZERO) != (current_quantity > ZERO):
            return fill_price, realized
        return current_average, realized

    def _on_fill(self, event: Event[Any]) -> None:
        if not isinstance(event.payload, Fill):
            raise TypeError("ORDER_FILLED event payload must be a Fill")
        self.apply_fill(event.payload)

    def _on_market_data(self, event: Event[Any]) -> None:
        if not isinstance(event.payload, Bar):
            raise TypeError("MARKET_DATA event payload must be a Bar")
        self.mark_to_market(event.payload)
