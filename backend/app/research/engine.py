from dataclasses import dataclass
from datetime import UTC, datetime, time
from decimal import Decimal
from typing import Protocol
from uuid import NAMESPACE_URL, UUID, uuid5

from app.domain.market import Bar
from app.domain.risk import OrderProposal, RiskConfig, RiskDecision, RiskReservation
from app.domain.trading import Fill, Order, OrderSide, OrderType, PortfolioSnapshot
from app.event import Event, EventBus, EventType
from app.execution import FixedBasisPointSlippage, OrderManager, SimulatedBroker
from app.execution.costs import CommissionModel, SlippageModel
from app.portfolio import PortfolioEngine
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


class ResearchExecutionEngine:
    """Multi-security daily engine reusing the existing risk/OMS/broker/portfolio path."""

    def __init__(
        self,
        strategy: ResearchStrategy,
        *,
        initial_cash: Decimal,
        commission_model: CommissionModel,
        slippage_model: SlippageModel | None = None,
        risk_config: RiskConfig | None = None,
    ) -> None:
        self._strategy = strategy
        self._event_bus = EventBus()
        self._portfolio = PortfolioEngine(self._event_bus, initial_cash)
        self._broker = SimulatedBroker(
            self._event_bus,
            commission_model,
            slippage_model or FixedBasisPointSlippage(),
        )
        self._oms = OrderManager(
            self._event_bus,
            self._broker,
            self._portfolio,
            RiskEngine(risk_config or RiskConfig(enforce_buying_power=True)),
            commission_model,
        )
        self._expired_order_ids: list[UUID] = []

    def run(self, sessions: tuple[ResearchSession, ...]) -> ResearchExecutionResult:
        self.reset()
        previous_date = None
        for session in sessions:
            if previous_date is not None and session.trading_date <= previous_date:
                raise ValueError("research sessions must be strictly chronological")
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
        )

    def reset(self) -> None:
        self._strategy.reset()
        self._broker.reset()
        self._oms.reset()
        self._portfolio.reset()
        self._expired_order_ids.clear()

    def _process_session(self, session: ResearchSession) -> None:
        timestamp = datetime.combine(session.trading_date, time(15), tzinfo=UTC)
        for action in sorted(session.corporate_actions, key=lambda item: str(item.security_id)):
            if action.ex_date != session.trading_date:
                raise ValueError("corporate action must belong to the research session")
            self._portfolio.apply_corporate_action(
                _domain_symbol(action.security_id), action, timestamp
            )
        statuses = {item.status.security_id: item.status for item in session.statuses}
        ordered_bars = sorted(session.bars, key=lambda item: str(item.security_id))
        for source in ordered_bars:
            bar = _domain_bar(source, timestamp)
            status = statuses.get(source.security_id)
            if status is not None and not status.is_suspended and not status.is_one_price_limit:
                self._broker.execute_pending(bar)
            self._event_bus.publish(Event(EventType.MARKET_DATA, bar, occurred_at=timestamp))

        snapshot = self._portfolio.latest_snapshot
        if snapshot is None:
            return
        target = self._strategy.target_for_completed_session(session, snapshot.equity)
        if target is None:
            return
        self._expire_pending()
        self._route_target(target, timestamp)

    def _route_target(self, target: PortfolioTarget, timestamp: datetime) -> None:
        current = {position.symbol: position.quantity for position in self._portfolio.positions}
        target_by_symbol = {
            _domain_symbol(position.security_id): position.quantity for position in target.positions
        }
        deltas = {
            symbol: target_by_symbol.get(symbol, ZERO) - current.get(symbol, ZERO)
            for symbol in set(current) | set(target_by_symbol)
        }
        ordered = sorted(deltas.items(), key=lambda item: (item[1] > ZERO, item[0]))
        for symbol, delta in ordered:
            if delta == ZERO:
                continue
            side = OrderSide.BUY if delta > ZERO else OrderSide.SELL
            quantity = abs(delta)
            proposal = OrderProposal(
                proposal_id=uuid5(
                    NAMESPACE_URL,
                    ":".join(
                        (
                            "quant-trading-platform-research",
                            self._strategy.strategy_id,
                            timestamp.isoformat(),
                            symbol,
                            side.value,
                            format(quantity, "f"),
                        )
                    ),
                ),
                strategy_id=self._strategy.strategy_id,
                symbol=symbol,
                side=side,
                order_type=OrderType.MARKET,
                quantity=quantity,
                signal_timestamp=timestamp,
            )
            self._event_bus.publish(
                Event(EventType.ORDER_PROPOSAL, proposal, occurred_at=timestamp)
            )

    def _expire_pending(self) -> None:
        cancelled = self._broker.cancel_pending()
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
