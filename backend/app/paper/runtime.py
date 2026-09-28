import asyncio
from collections.abc import Awaitable, Callable, Iterable, Sequence
from contextlib import suppress
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from itertools import pairwise
from typing import Any
from uuid import NAMESPACE_URL, uuid5

from app.backtest import BacktestConfig
from app.domain.common import normalize_symbol
from app.domain.market import Bar
from app.domain.markets.calendar import TradingCalendar
from app.domain.risk import OrderProposal, RiskConfig, RiskDecision
from app.domain.trading import Fill, Order, OrderSide, OrderType, PortfolioSnapshot, Signal
from app.event import Event, EventBus, EventType
from app.execution import OrderManager, SimulatedBroker
from app.execution.costs import CommissionModel
from app.portfolio import PortfolioEngine
from app.research import (
    ResearchExecutionDelta,
    ResearchExecutionEngine,
    ResearchExecutionResult,
    ResearchSession,
)
from app.research.strategy import ChinaAMomentumLowVolResearchStrategy
from app.risk import RiskEngine
from app.strategies import BaseStrategy, StrategyEngine

BarHandler = Callable[[Bar], Awaitable[None]]
AShareSessionHandler = Callable[[ResearchSession], Awaitable[None]]
FROZEN_A_SHARE_STRATEGY_ID = "cn_a_cross_sectional_momentum_low_vol_v1"


class ReplayProviderError(ValueError):
    """Raised when deterministic replay lifecycle or data is invalid."""


class ReplayMarketDataProvider:
    """Replay immutable completed Bars in strict order without future leakage."""

    def __init__(self, bars: Sequence[Bar], interval_seconds: float = 0.5) -> None:
        if interval_seconds < 0:
            raise ValueError("interval_seconds must be non-negative")
        self._bars = tuple(bars)
        self._interval_seconds = interval_seconds
        self._subscriptions: set[str] = set()
        self._running = False
        self._stop = asyncio.Event()
        previous: Bar | None = None
        for bar in self._bars:
            if previous is not None and bar.timestamp <= previous.timestamp:
                raise ReplayProviderError("replay bars must be strictly chronological")
            previous = bar

    @property
    def running(self) -> bool:
        return self._running

    def subscribe(self, symbol: str) -> None:
        self._subscriptions.add(normalize_symbol(symbol))

    def unsubscribe(self, symbol: str) -> None:
        self._subscriptions.discard(normalize_symbol(symbol))

    async def start(self, handler: BarHandler) -> None:
        if self._running:
            raise ReplayProviderError("replay provider is already running")
        self._running = True
        self._stop.clear()
        try:
            for index, bar in enumerate(self._bars):
                if self._stop.is_set():
                    break
                if bar.symbol in self._subscriptions:
                    await handler(bar)
                if index + 1 < len(self._bars) and self._interval_seconds:
                    with suppress(TimeoutError):
                        await asyncio.wait_for(self._stop.wait(), timeout=self._interval_seconds)
        finally:
            self._running = False

    async def stop(self) -> None:
        self._stop.set()


class SimulatedAShareSessionProvider:
    """Replay completed cross-sectional sessions, including lazy frozen archives."""

    def __init__(
        self,
        sessions: Iterable[ResearchSession],
        interval_seconds: float = 0.5,
        *,
        pace_from_date: date | None = None,
    ) -> None:
        if interval_seconds < 0:
            raise ValueError("interval_seconds must be non-negative")
        self._streaming = not isinstance(sessions, Sequence)
        self._sessions = sessions if self._streaming else tuple(sessions)
        self._interval_seconds = interval_seconds
        self._pace_from_date = pace_from_date
        self._running = False
        self._stop = asyncio.Event()
        previous: date | None = None
        for session in () if self._streaming else self._sessions:
            if previous is not None and session.trading_date <= previous:
                raise ReplayProviderError("A-share sessions must be strictly chronological")
            previous = session.trading_date

    @property
    def running(self) -> bool:
        return self._running

    async def start(self, handler: AShareSessionHandler) -> None:
        if self._running:
            raise ReplayProviderError("A-share session provider is already running")
        self._running = True
        self._stop.clear()
        try:
            iterator = iter(self._sessions)
            previous: date | None = None
            while not self._stop.is_set():
                session = (
                    await asyncio.to_thread(next, iterator, None)
                    if self._streaming
                    else next(iterator, None)
                )
                if session is None:
                    break
                if previous is not None and session.trading_date <= previous:
                    raise ReplayProviderError("A-share sessions must be strictly chronological")
                previous = session.trading_date
                if self._stop.is_set():
                    break
                await handler(session)
                if self._interval_seconds and (
                    self._pace_from_date is None or session.trading_date >= self._pace_from_date
                ):
                    with suppress(TimeoutError):
                        await asyncio.wait_for(self._stop.wait(), timeout=self._interval_seconds)
        finally:
            self._running = False

    async def stop(self) -> None:
        self._stop.set()


class PaperBroker(SimulatedBroker):
    """Local-only paper broker using reviewed next-Bar OPEN execution semantics."""


@dataclass(frozen=True, slots=True)
class PaperRuntimeDelta:
    bar: Bar
    signals: tuple[Signal, ...]
    decisions: tuple[RiskDecision, ...]
    orders: tuple[Order, ...]
    fills: tuple[Fill, ...]
    snapshot: PortfolioSnapshot


class PaperTradingRuntime:
    """One isolated Signal -> Risk -> OMS -> PaperBroker -> Portfolio runtime."""

    def __init__(
        self,
        strategies: Sequence[BaseStrategy],
        config: BacktestConfig,
        event_bus: EventBus | None = None,
    ) -> None:
        self._config = config
        self._event_bus = event_bus or EventBus()
        self._portfolio = PortfolioEngine(self._event_bus, config.initial_cash)
        self._strategy_engine = StrategyEngine(self._event_bus)
        for strategy in strategies:
            self._strategy_engine.register(strategy)
        self._broker = PaperBroker(self._event_bus, config.commission_model, config.slippage_model)
        self._order_manager = OrderManager(
            self._event_bus,
            self._broker,
            self._portfolio,
            RiskEngine(config.risk),
            config.commission_model,
        )
        self._signals: list[Signal] = []
        self._last_bar_time: datetime | None = None
        self._event_bus.subscribe(EventType.SIGNAL, self._on_signal)

    @property
    def broker(self) -> PaperBroker:
        return self._broker

    @property
    def portfolio(self) -> PortfolioEngine:
        return self._portfolio

    @property
    def order_manager(self) -> OrderManager:
        return self._order_manager

    async def process_bar(self, bar: Bar) -> PaperRuntimeDelta:
        if self._last_bar_time is not None and bar.timestamp <= self._last_bar_time:
            raise ReplayProviderError("paper bars must be strictly chronological")
        signal_count = len(self._signals)
        decision_count = len(self._order_manager.decisions)
        proposal_count = len(self._order_manager.proposals)
        fill_count = len(self._broker.fills)
        self._broker.execute_pending(bar)
        self._event_bus.publish(Event(EventType.MARKET_DATA, bar, occurred_at=bar.timestamp))
        self._last_bar_time = bar.timestamp
        snapshot = self._portfolio.latest_snapshot
        if snapshot is None:
            raise RuntimeError("market data did not produce a portfolio snapshot")
        new_fills = self._broker.fills[fill_count:]
        new_order_ids = {
            proposal.proposal_id for proposal in self._order_manager.proposals[proposal_count:]
        } | {fill.order_id for fill in new_fills}
        return PaperRuntimeDelta(
            bar=bar,
            signals=tuple(self._signals[signal_count:]),
            decisions=self._order_manager.decisions[decision_count:],
            orders=tuple(
                order for order in self._order_manager.orders if order.id in new_order_ids
            ),
            fills=new_fills,
            snapshot=snapshot,
        )

    def cancel_pending_orders(self) -> tuple[Order, ...]:
        """Cancel unfilled local orders and release their OMS reservations on stop."""
        return self._broker.cancel_pending()

    def _on_signal(self, event: Event[Any]) -> None:
        if not isinstance(event.payload, Signal):
            raise TypeError("SIGNAL event payload must be a Signal")
        signal = event.payload
        self._signals.append(signal)
        side = (
            OrderSide.BUY
            if signal.signal_type.value == "BUY"
            else OrderSide.SELL
            if signal.signal_type.value == "SELL"
            else None
        )
        if side is None:
            return
        proposal = OrderProposal(
            proposal_id=uuid5(
                NAMESPACE_URL,
                ":".join(
                    (
                        "quant-trading-platform-paper",
                        signal.strategy_id,
                        signal.symbol,
                        signal.timestamp.isoformat(),
                        signal.signal_type.value,
                    )
                ),
            ),
            strategy_id=signal.strategy_id,
            symbol=signal.symbol,
            side=side,
            order_type=OrderType.MARKET,
            quantity=self._config.default_order_quantity,
            signal_timestamp=signal.timestamp,
        )
        self._event_bus.publish(
            Event(EventType.ORDER_PROPOSAL, proposal, occurred_at=proposal.signal_timestamp)
        )


class ASharePaperTradingRuntime:
    """Frozen A-share strategy on the shared Risk/OMS/simulated execution path."""

    def __init__(
        self,
        *,
        initial_cash: Decimal,
        commission_model: CommissionModel,
        calendar: TradingCalendar,
        risk_config: RiskConfig | None = None,
        strategy: ChinaAMomentumLowVolResearchStrategy | None = None,
    ) -> None:
        strategy = strategy or ChinaAMomentumLowVolResearchStrategy()
        if strategy.strategy_id != FROZEN_A_SHARE_STRATEGY_ID:
            raise ValueError("frozen A-share strategy identity changed")
        self._engine = ResearchExecutionEngine(
            strategy,
            initial_cash=initial_cash,
            commission_model=commission_model,
            calendar=calendar,
            risk_config=risk_config,
        )
        self._engine.reset()
        accepted_dates = tuple(item.session_date for item in calendar.sessions if item.is_open)
        self._next_accepted_session = dict(pairwise(accepted_dates))
        self._completed_sessions = 0
        self._result: ResearchExecutionResult | None = None

    @property
    def strategy_id(self) -> str:
        return FROZEN_A_SHARE_STRATEGY_ID

    @property
    def completed_sessions(self) -> int:
        return self._completed_sessions

    def next_accepted_session(self, trading_date: date) -> date | None:
        return self._next_accepted_session.get(trading_date)

    async def process_session(self, session: ResearchSession) -> ResearchExecutionDelta:
        if self._result is not None:
            raise ReplayProviderError("A-share paper runtime is already stopped")
        delta = self._engine.process_session(session)
        self._completed_sessions += 1
        return delta

    def finish(self) -> ResearchExecutionResult:
        if self._result is None:
            self._result = self._engine.finish()
        return self._result

    def cancel_pending_orders(self) -> tuple[Order, ...]:
        expired_before = len(self._engine._expired_order_ids)
        result = self.finish()
        expired = set(result.expired_order_ids[expired_before:])
        return tuple(item for item in result.orders if item.id in expired)
