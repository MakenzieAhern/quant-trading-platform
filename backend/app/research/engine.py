from collections.abc import Iterable
from dataclasses import dataclass, replace
from datetime import UTC, date, datetime, time
from decimal import Decimal
from itertools import pairwise
from typing import Protocol
from uuid import NAMESPACE_URL, UUID, uuid5
from zoneinfo import ZoneInfo

from app.domain.market import Bar
from app.domain.markets.calendar import TradingCalendar
from app.domain.markets.consolidations import CONSOLIDATION_POLICY
from app.domain.markets.corporate_actions import (
    corporate_action_sort_key,
    require_supported_corporate_action,
    require_unambiguous_ordinary_distributions,
)
from app.domain.markets.mergers import MERGER_POLICY, ZERO_WHOLE_SHARE_POLICY
from app.domain.markets.pass_through import PASS_THROUGH_POLICY
from app.domain.markets.surrenders import (
    PARTIAL_SURRENDER_BOUNDARY_POLICY,
    PARTIAL_SURRENDER_FRACTION_POLICY,
    PARTIAL_SURRENDER_POLICY,
)
from app.domain.risk import OrderProposal, RiskConfig, RiskDecision, RiskReservation
from app.domain.trading import Fill, Order, OrderSide, OrderType, PortfolioSnapshot
from app.event import Event, EventBus, EventType
from app.execution import FixedBasisPointSlippage, OrderManager, SimulatedBroker
from app.execution.costs import CommissionModel, SlippageModel
from app.portfolio import PortfolioEngine
from app.research.execution_convention import VERSION, rejection_reason
from app.research.models import PortfolioTarget, ResearchSession
from app.risk import RiskEngine

ZERO = Decimal(0)


class UnexplainedReferenceAdjustment(ValueError):
    code = "UNEXPLAINED_HELD_REFERENCE_ADJUSTMENT"

    def __init__(self, trading_date: date, security_ids: tuple[str, ...]) -> None:
        super().__init__(self.code)
        self.trading_date = trading_date
        self.security_ids = security_ids


class ResearchStrategy(Protocol):
    strategy_id: str

    def target_for_completed_session(
        self, session: ResearchSession, available_equity: Decimal
    ) -> PortfolioTarget | None: ...

    def reset(self) -> None: ...


@dataclass(frozen=True, slots=True)
class ResearchExecutionResult:
    proposals: tuple[OrderProposal, ...]
    decisions: tuple[RiskDecision, ...]
    orders: tuple[Order, ...]
    fills: tuple[Fill, ...]
    snapshots: tuple[PortfolioSnapshot, ...]
    active_reservations: tuple[RiskReservation, ...]
    expired_order_ids: tuple[UUID, ...]
    execution_checks: tuple[tuple[UUID, str], ...]
    execution_convention: str = VERSION
    merger_policy: str = MERGER_POLICY
    zero_whole_share_policy: str = ZERO_WHOLE_SHARE_POLICY
    partial_surrender_policy: str = PARTIAL_SURRENDER_POLICY
    partial_surrender_fraction_policy: str = PARTIAL_SURRENDER_FRACTION_POLICY
    partial_surrender_boundary_policy: str = PARTIAL_SURRENDER_BOUNDARY_POLICY
    pass_through_policy: str = PASS_THROUGH_POLICY
    consolidation_policy: str = CONSOLIDATION_POLICY


@dataclass(frozen=True, slots=True)
class ResearchExecutionDelta:
    session: ResearchSession
    target: PortfolioTarget | None
    proposals: tuple[OrderProposal, ...]
    decisions: tuple[RiskDecision, ...]
    orders: tuple[Order, ...]
    fills: tuple[Fill, ...]
    snapshot: PortfolioSnapshot | None
    expired_order_ids: tuple[UUID, ...]
    execution_checks: tuple[tuple[UUID, str], ...]


class ResearchExecutionEngine:
    """Multi-security daily engine reusing the existing risk/OMS/broker/portfolio path."""

    def __init__(
        self,
        strategy: ResearchStrategy,
        *,
        initial_cash: Decimal,
        commission_model: CommissionModel,
        calendar: TradingCalendar,
        slippage_model: SlippageModel | None = None,
        risk_config: RiskConfig | None = None,
    ) -> None:
        self._strategy = strategy
        self._calendar = calendar
        dates = tuple(item.session_date for item in calendar.sessions if item.is_open)
        self._next_session = dict(pairwise(dates))
        self._calendar_dates = frozenset(dates)
        self._active_session: ResearchSession | None = None
        self._previous_date: date | None = None
        self._execution_checks: list[tuple[UUID, str]] = []
        if slippage_model is not None and slippage_model != FixedBasisPointSlippage():
            raise ValueError("V1 requires raw OPEN pricing and zero additional slippage")
        self._event_bus = EventBus()
        self._portfolio = PortfolioEngine(self._event_bus, initial_cash)
        self._broker = SimulatedBroker(
            self._event_bus,
            commission_model,
            slippage_model or FixedBasisPointSlippage(),
            limit_fill_eligible=self._fill_eligible,
        )
        self._oms = OrderManager(
            self._event_bus,
            self._broker,
            self._portfolio,
            RiskEngine(
                (risk_config or RiskConfig(enforce_buying_power=True)).model_copy(
                    update={"allow_limit_orders": True}
                )
            ),
            commission_model,
        )
        self._expired_order_ids: list[UUID] = []

    def next_accepted_session(self, trading_date: date) -> date | None:
        return self._next_session.get(trading_date)

    @property
    def calendar(self) -> TradingCalendar:
        return self._calendar

    @property
    def last_completed_session(self) -> date | None:
        return self._previous_date

    def extend_calendar(self, calendar: TradingCalendar) -> None:
        """Append already accepted dates; never reroute past targets or pending orders.

        Acceptance/provenance belongs to the application boundary. A future durable
        forward adapter must journal when each extension was applied and replay that
        timeline, not reconstruct old intents using the final expanded calendar.
        """
        calendar.require_extension_of(self._calendar)
        dates = tuple(item.session_date for item in calendar.sessions if item.is_open)
        next_session = dict(pairwise(dates))
        self._calendar = calendar
        self._next_session = next_session
        self._calendar_dates = frozenset(dates)

    def run(self, sessions: Iterable[ResearchSession]) -> ResearchExecutionResult:
        self.reset()
        for session in sessions:
            self.process_session(session)
        return self.finish()

    def process_session(self, session: ResearchSession) -> ResearchExecutionDelta:
        """Process one completed session without exposing any future session."""

        if self._previous_date is not None and session.trading_date <= self._previous_date:
            raise ValueError("research sessions must be strictly chronological")
        if session.trading_date not in self._calendar_dates:
            raise ValueError("session outside accepted calendar")
        if (
            self._previous_date is not None
            and self._next_session.get(self._previous_date) != session.trading_date
        ):
            raise ValueError("missing calendar session must be represented explicitly")
        require_unambiguous_ordinary_distributions(session.corporate_actions)
        held_symbols = {
            position.symbol for position in self._portfolio.positions if position.quantity != ZERO
        }
        unexplained_ids = tuple(
            sorted(
                str(identity)
                for identity in session.unexplained_reference_adjustment_ids
                if _domain_symbol(identity) in held_symbols
            )
        )
        if unexplained_ids:
            # Fail before today's accounting, fills, marks, strategy calls or progress.
            raise UnexplainedReferenceAdjustment(session.trading_date, unexplained_ids)
        proposal_count = len(self._oms.proposals)
        decision_count = len(self._oms.decisions)
        fill_count = len(self._broker.fills)
        expired_count = len(self._expired_order_ids)
        check_count = len(self._execution_checks)
        target = self._process_session(session)
        self._previous_date = session.trading_date
        proposals = self._oms.proposals[proposal_count:]
        fills = self._broker.fills[fill_count:]
        order_ids = (
            {item.proposal_id for item in proposals}
            | {item.order_id for item in fills}
            | set(self._expired_order_ids[expired_count:])
        )
        return ResearchExecutionDelta(
            session=session,
            target=target,
            proposals=proposals,
            decisions=self._oms.decisions[decision_count:],
            orders=tuple(item for item in self._oms.orders if item.id in order_ids),
            fills=fills,
            snapshot=self._portfolio.latest_snapshot,
            expired_order_ids=tuple(self._expired_order_ids[expired_count:]),
            execution_checks=tuple(self._execution_checks[check_count:]),
        )

    def finish(self) -> ResearchExecutionResult:
        """Cancel any remaining simulated orders and return the cumulative result."""

        self._expire_pending()
        return ResearchExecutionResult(
            proposals=self._oms.proposals,
            decisions=self._oms.decisions,
            orders=self._oms.orders,
            fills=self._broker.fills,
            snapshots=self._portfolio.snapshots,
            active_reservations=self._oms.active_reservations,
            expired_order_ids=tuple(self._expired_order_ids),
            execution_checks=tuple(self._execution_checks),
        )

    def reset(self) -> None:
        self._strategy.reset()
        self._broker.reset()
        self._oms.reset()
        self._portfolio.reset()
        self._expired_order_ids.clear()
        self._execution_checks.clear()
        self._active_session = None
        self._previous_date = None

    def _process_session(self, session: ResearchSession) -> PortfolioTarget | None:
        self._active_session = session
        timestamp = datetime.combine(
            session.trading_date, time(15, 0, 0, 1), tzinfo=ZoneInfo("Asia/Shanghai")
        ).astimezone(UTC)
        opening = datetime.combine(
            session.trading_date, time(9, 25), tzinfo=ZoneInfo("Asia/Shanghai")
        ).astimezone(UTC)
        actions = sorted(session.corporate_actions, key=corporate_action_sort_key)
        demergers = sorted(session.demergers, key=lambda e: str(e.parent_security))
        mergers = sorted(session.mergers, key=lambda e: str(e.parent_security))
        surrenders = sorted(session.partial_surrenders, key=lambda e: str(e.security_id))
        pass_through = sorted(session.pass_through_events, key=lambda e: str(e.security_id))
        pass_ids = [str(e.security_id) for e in pass_through]
        consolidations = sorted(session.consolidations, key=lambda e: str(e.security_id))
        consolidation_ids = [str(e.security_id) for e in consolidations]
        parents = [str(e.parent_security) for e in demergers] + [
            str(e.parent_security) for e in mergers
        ]
        if len(parents) != len(set(parents)):
            raise ValueError("duplicate session mandatory conversion")
        structural_ids = (
            parents + [str(e.security_id) for e in surrenders] + pass_ids + consolidation_ids
        )
        if len(structural_ids) != len(set(structural_ids)) or any(
            str(a.security_id) in set(structural_ids) for a in actions
        ):
            raise ValueError("partial surrender concurrent action ordering unsupported")
        for consolidation in consolidations:
            consolidation.require_supported()
            if consolidation.effective_date != session.trading_date:
                raise ValueError("consolidation session mismatch")
            if session.consolidation_holder_class != consolidation.affected_holder_class:
                raise ValueError("CONSOLIDATION_HOLDER_APPLICABILITY_UNVERIFIED")
        for pass_event in pass_through:
            pass_event.require_supported()
            if pass_event.effective_date != session.trading_date:
                raise ValueError("pass-through session mismatch")
            if any(b.security_id == pass_event.security_id for b in session.bars):
                raise ValueError("PASS_THROUGH_TRADING_OBSERVATION_CONFLICT")
        for surrender in surrenders:
            surrender.require_supported()
            if surrender.application_date != session.trading_date:
                raise ValueError("partial surrender session mismatch")
            if surrender.research_effective_date is not None:
                status = next(
                    (
                        s.status
                        for s in session.statuses
                        if s.status.security_id == surrender.security_id
                    ),
                    None,
                )
                if (
                    not any(b.security_id == surrender.security_id for b in session.bars)
                    or status is None
                    or status.is_tradeable is not True
                    or status.is_suspended is not False
                ):
                    raise ValueError("SURRENDER_FIRST_TRADABLE_BOUNDARY_REQUIRED")
            holder_class = dict(session.surrender_holder_classes).get(
                surrender.security_id, session.surrender_holder_class
            )
            if holder_class != surrender.affected_holder_class:
                raise ValueError("PARTIAL_SURRENDER_HOLDER_APPLICABILITY_UNVERIFIED")
        for merger in mergers:
            merger.require_supported()
            if merger.effective_date != session.trading_date:
                raise ValueError("merger session mismatch")
        if len({str(e.parent_security) for e in demergers}) != len(demergers):
            raise ValueError("duplicate session demerger")
        for event in demergers:
            event.require_supported()
            if event.application_date != session.trading_date:
                raise ValueError("demerger session mismatch")
        for action in actions:
            if action.ex_date != session.trading_date:
                raise ValueError("corporate action must belong to the research session")
            require_supported_corporate_action(action)
        for action in actions:
            self._portfolio.apply_corporate_action(
                _domain_symbol(action.security_id), action, opening
            )
        for event in demergers:
            self._portfolio.recognize_demerger(event, session.trading_date, opening)
        for merger in mergers:
            self._portfolio.recognize_merger(merger, session.trading_date, opening)
        for consolidation in consolidations:
            self._portfolio.apply_consolidation(
                consolidation, opening, holder_class=session.consolidation_holder_class
            )
        for surrender in surrenders:
            holder_class = dict(session.surrender_holder_classes).get(
                surrender.security_id, session.surrender_holder_class
            )
            self._portfolio.apply_partial_surrender(surrender, opening, holder_class=holder_class)
        for pass_event in pass_through:
            self._portfolio.apply_pass_through(pass_event, opening)
        self._portfolio.activate_demergers(
            session.trading_date,
            {_domain_symbol(b.security_id): b.raw_open for b in session.bars},
            opening,
        )
        ordered_bars = sorted(session.bars, key=lambda item: str(item.security_id))
        self._portfolio.activate_mergers(
            session.trading_date,
            {_domain_symbol(b.security_id): b.raw_open for b in session.bars},
            opening,
        )
        for source in ordered_bars:
            self._broker.execute_pending(_domain_bar(source, opening))
        self._expire_pending()
        for source in ordered_bars:
            # Official zero-volume rows preserve feature continuity during suspension;
            # they are not a new tradable mark or a new merger last-trade boundary.
            if source.volume > ZERO:
                self._portfolio.mark_to_market(_domain_bar(source, timestamp), snapshot=False)
        if ordered_bars or (
            self._portfolio.pending_demergers
            or self._portfolio.pending_mergers
            or mergers
            or surrenders
            or pass_through
            or consolidations
        ):
            self._portfolio.snapshot_at(timestamp)

        snapshot = self._portfolio.latest_snapshot
        if snapshot is None:
            return None
        # Accounting evidence (including later allocation sources) is never a factor input.
        target = self._strategy.target_for_completed_session(
            replace(
                session,
                demergers=(),
                mergers=(),
                partial_surrenders=(),
                surrender_holder_class=None,
                surrender_holder_classes=(),
                pass_through_events=(),
                consolidations=(),
                consolidation_holder_class=None,
                unexplained_reference_adjustment_ids=(),
            ),
            snapshot.equity,
        )
        if target is None:
            self._portfolio.compact_closed_positions()
            return None
        self._expire_pending()
        self._route_target(target, timestamp)
        self._portfolio.compact_closed_positions()
        return target

    def _fill_eligible(self, order: Order, bar: Bar) -> bool:
        session = self._active_session
        assert session is not None
        if not self._portfolio.is_orderable(order.symbol):
            self._execution_checks.append((order.id, "CORPORATE_ACTION_NON_ORDERABLE"))
            return False
        source = next(
            item for item in session.bars if _domain_symbol(item.security_id) == order.symbol
        )
        status = next(
            (
                item.status
                for item in session.statuses
                if item.status.security_id == source.security_id
            ),
            None,
        )
        rules = next(
            (item for item in session.trading_rules if item.security_id == source.security_id), None
        )
        held = next(
            (item.quantity for item in self._portfolio.positions if item.symbol == order.symbol),
            ZERO,
        )
        reason = rejection_reason(order, source, status, rules, held)
        if any(item.security_id == source.security_id for item in session.corporate_actions) or any(
            item.security_id == source.security_id for item in session.partial_surrenders
        ):
            reason = "CORPORATE_ACTION_OPENING_UNCERTAINTY"
        self._execution_checks.append((order.id, reason or "ELIGIBLE_SIMULATION_ASSUMPTION"))
        return reason is None

    def _route_target(self, target: PortfolioTarget, timestamp: datetime) -> None:
        session = self._active_session
        assert session is not None
        execution_date = self._next_session.get(session.trading_date)
        if execution_date is None:
            return
        prices = {_domain_symbol(item.security_id): item.raw_close for item in session.bars}
        current = {position.symbol: position.quantity for position in self._portfolio.positions}
        target_by_symbol = {
            _domain_symbol(position.security_id): position.quantity for position in target.positions
        }
        if len(target_by_symbol) != len(target.positions):
            raise ValueError("duplicate target security")
        deltas = {
            symbol: target_by_symbol.get(symbol, ZERO) - current.get(symbol, ZERO)
            for symbol in set(current) | set(target_by_symbol)
        }
        ordered = sorted(deltas.items(), key=lambda item: (item[1] > ZERO, item[0]))
        for symbol, delta in ordered:
            if delta == ZERO or symbol not in prices or not self._portfolio.is_orderable(symbol):
                continue
            side = OrderSide.BUY if delta > ZERO else OrderSide.SELL
            quantity = abs(delta)
            proposal = OrderProposal(
                proposal_id=uuid5(
                    NAMESPACE_URL,
                    ":".join(
                        (
                            "quant-trading-platform-research",
                            VERSION,
                            self._strategy.strategy_id,
                            timestamp.isoformat(),
                            symbol,
                            side.value,
                            format(quantity, "f"),
                            format(prices[symbol], "f"),
                            execution_date.isoformat(),
                        )
                    ),
                ),
                strategy_id=self._strategy.strategy_id,
                symbol=symbol,
                side=side,
                order_type=OrderType.LIMIT,
                limit_price=prices[symbol],
                intended_execution_session=execution_date,
                quantity=quantity,
                signal_timestamp=timestamp,
            )
            self._event_bus.publish(
                Event(EventType.ORDER_PROPOSAL, proposal, occurred_at=timestamp)
            )

    def _expire_pending(self) -> None:
        cancelled = self._broker.cancel_pending()
        checked = {order_id for order_id, _ in self._execution_checks}
        for order in cancelled:
            if order.id not in checked:
                reason = (
                    "MISSING_OBSERVATION"
                    if self._active_session is not None
                    and order.intended_execution_session == self._active_session.trading_date
                    else "END_OF_RUN"
                )
                self._execution_checks.append((order.id, reason))
        self._expired_order_ids.extend(order.id for order in cancelled)


def _domain_symbol(security_id: object) -> str:
    value = str(security_id)
    _, exchange, symbol = value.split(":")
    return f"{symbol}.{exchange}"


def _domain_bar(source: object, timestamp: datetime) -> Bar:
    from app.data.providers.research import DailyBarRecord

    if not isinstance(source, DailyBarRecord):
        raise TypeError("research session bars must be DailyBarRecord values")
    return Bar(
        symbol=_domain_symbol(source.security_id),
        timestamp=timestamp,
        open=source.raw_open,
        high=source.raw_high,
        low=source.raw_low,
        close=source.raw_close,
        volume=source.volume,
    )
