import asyncio
from collections.abc import Awaitable, Callable, Sequence
from contextlib import suppress
from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import NAMESPACE_URL, uuid5

from app.backtest import BacktestConfig
from app.domain.common import normalize_symbol
from app.domain.market import Bar
from app.domain.risk import OrderProposal, RiskDecision
from app.domain.trading import Fill, Order, OrderSide, OrderType, PortfolioSnapshot, Signal
from app.event import Event, EventBus, EventType
from app.execution import OrderManager, SimulatedBroker
from app.portfolio import PortfolioEngine
from app.risk import RiskEngine
from app.strategies import BaseStrategy, StrategyEngine

BarHandler = Callable[[Bar], Awaitable[None]]


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
