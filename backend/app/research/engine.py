from collections.abc import Iterable
from dataclasses import dataclass, replace
from datetime import UTC, datetime, time
from decimal import Decimal
from itertools import pairwise
from typing import Protocol
from uuid import NAMESPACE_URL, UUID, uuid5
from zoneinfo import ZoneInfo

from app.domain.market import Bar
from app.domain.markets.calendar import TradingCalendar
from app.domain.markets.corporate_actions import (
    corporate_action_sort_key,
    require_supported_corporate_action,
)
from app.domain.markets.mergers import MERGER_POLICY, ZERO_WHOLE_SHARE_POLICY
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
        dates = tuple(item.session_date for item in calendar.sessions if item.is_open)
        self._next_session = dict(pairwise(dates))
        self._calendar_dates = frozenset(dates)
        self._active_session: ResearchSession | None = None
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

    def run(self, sessions: Iterable[ResearchSession]) -> ResearchExecutionResult:
        self.reset()
        previous_date = None
        for session in sessions:
            if previous_date is not None and session.trading_date <= previous_date:
                raise ValueError("research sessions must be strictly chronological")
            if session.trading_date not in self._calendar_dates:
                raise ValueError("session outside accepted calendar")
            if (
                previous_date is not None
                and self._next_session.get(previous_date) != session.trading_date
            ):
                raise ValueError("missing calendar session must be represented explicitly")
            self._process_session(session)
            previous_date = session.trading_date
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

    def _process_session(self, session: ResearchSession) -> None:
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
        parents = [str(e.parent_security) for e in demergers] + [
            str(e.parent_security) for e in mergers
        ]
        if len(parents) != len(set(parents)):
            raise ValueError("duplicate session mandatory conversion")
        structural_ids = parents + [str(e.security_id) for e in surrenders]
        if len(structural_ids) != len(set(structural_ids)) or any(
            str(a.security_id) in {str(e.security_id) for e in surrenders} for a in actions
        ):
            raise ValueError("partial surrender concurrent action ordering unsupported")
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
            if session.surrender_holder_class != surrender.affected_holder_class:
                raise ValueError("PARTIAL_SURRENDER_HOLDER_APPLICABILITY_UNVERIFIED")
        for merger in mergers:
            merger.require_supported()
            if merger.effective_date != session.trading_date:
                raise ValueError("merger session mismatch")
        if len({str(e.parent_security) for e in demergers}) != len(demergers):
            raise ValueError("duplicate session demerger")
        for event in demergers:
            event.require_supported()
            if event.effective_date != session.trading_date:
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
        for surrender in surrenders:
            self._portfolio.apply_partial_surrender(
                surrender, opening, holder_class=session.surrender_holder_class
            )
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
            bar = _domain_bar(source, timestamp)
            self._event_bus.publish(Event(EventType.MARKET_DATA, bar, occurred_at=timestamp))
        if not ordered_bars and (
            self._portfolio.pending_demergers
            or self._portfolio.pending_mergers
            or mergers
            or surrenders
        ):
            self._portfolio.snapshot_at(timestamp)

        snapshot = self._portfolio.latest_snapshot
        if snapshot is None:
            return
        # Accounting evidence (including later allocation sources) is never a factor input.
        target = self._strategy.target_for_completed_session(
            replace(
                session,
                demergers=(),
                mergers=(),
                partial_surrenders=(),
                surrender_holder_class=None,
            ),
            snapshot.equity,
        )
        if target is None:
            return
        self._expire_pending()
        self._route_target(target, timestamp)

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
