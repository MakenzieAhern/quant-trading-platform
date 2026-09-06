import asyncio
import hashlib
import json
import logging
from collections.abc import Callable
from contextlib import suppress
from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.application.backtests.decimal_policy import canonical_decimal, validate_storage_decimal
from app.application.backtests.registry import DatasetRegistry, StrategyRegistry
from app.backtest import BacktestConfig
from app.data.providers import Timeframe
from app.db.repositories.paper import SQLAlchemyPaperRepository
from app.domain.market import Bar
from app.domain.risk import RiskConfig, RiskDecision
from app.domain.trading import Fill, Order, PortfolioSnapshot, Signal
from app.paper.hub import PaperEventHub
from app.paper.models import (
    CreatePaperSessionCommand,
    PaperEventRecord,
    PaperSession,
    PaperSessionConcurrencyError,
    PaperSessionStatus,
)
from app.paper.runtime import PaperRuntimeDelta, PaperTradingRuntime, ReplayMarketDataProvider


class PaperSessionConflictError(ValueError):
    """Raised when an idempotency key is reused for different content."""


class PaperSessionStateError(ValueError):
    """Raised when a lifecycle command is not valid for the persisted state."""


Clock = Callable[[], datetime]
logger = logging.getLogger(__name__)


class PaperTradingManager:
    """Own background tasks while every session owns a fully isolated trading runtime."""

    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        datasets: DatasetRegistry,
        strategies: StrategyRegistry,
        *,
        replay_interval_seconds: float = 0.75,
        clock: Clock | None = None,
        hub: PaperEventHub | None = None,
    ) -> None:
        self._session_factory = session_factory
        self._datasets = datasets
        self._strategies = strategies
        self._replay_interval_seconds = replay_interval_seconds
        self._clock = clock or (lambda: datetime.now(UTC))
        self.hub = hub or PaperEventHub()
        self._tasks: dict[UUID, asyncio.Task[None]] = {}
        self._providers: dict[UUID, ReplayMarketDataProvider] = {}
        self._lock = asyncio.Lock()

    async def recover_interrupted(self) -> int:
        async with self._session_factory() as db:
            interrupted = await SQLAlchemyPaperRepository(db).interrupt_active(self._now())
        if interrupted:
            logger.warning("Interrupted %d orphaned paper session(s) during startup", interrupted)
        return interrupted

    async def create(self, command: CreatePaperSessionCommand) -> PaperSession:
        if command.provider_type != "replay":
            raise ValueError("unknown paper market data provider")
        validate_storage_decimal(command.initial_cash, "initial_cash")
        validate_storage_decimal(command.default_order_quantity, "default_order_quantity")
        self._datasets.resolve(command.dataset_id, command.symbol)
        self._strategies.build(
            command.strategy_type,
            f"{command.strategy_type}:{command.symbol}",
            command.symbol,
            command.strategy_parameters,
        )
        request_hash = self._request_hash(command)
        async with self._session_factory() as db:
            repository = SQLAlchemyPaperRepository(db)
            if command.client_request_id is not None:
                existing = await repository.get_by_client_request_id(command.client_request_id)
                if existing is not None:
                    if existing.request_hash != request_hash:
                        raise PaperSessionConflictError(
                            "idempotency key was already used for different paper session content"
                        )
                    return existing
            session = PaperSession(
                id=uuid4(),
                status=PaperSessionStatus.CREATED,
                provider_type=command.provider_type,
                dataset_id=command.dataset_id,
                symbol=command.symbol,
                strategy_type=command.strategy_type,
                strategy_parameters=self._json_decimals(command.strategy_parameters),
                initial_cash=command.initial_cash,
                default_order_quantity=command.default_order_quantity,
                risk=self._json_decimals(command.risk.model_dump()),
                created_at=self._now(),
                started_at=None,
                stopped_at=None,
                error_message=None,
                client_request_id=command.client_request_id,
                request_hash=request_hash if command.client_request_id is not None else None,
            )
            try:
                created = await repository.create(session)
                logger.info("Created paper session %s", created.id)
                return created
            except IntegrityError:
                await db.rollback()
                if command.client_request_id is None:
                    raise
                existing = await repository.get_by_client_request_id(command.client_request_id)
                if existing is None:
                    raise
                if existing.request_hash != request_hash:
                    raise PaperSessionConflictError(
                        "idempotency key was already used for different paper session content"
                    ) from None
                return existing

    async def get(self, session_id: UUID) -> PaperSession | None:
        async with self._session_factory() as db:
            return await SQLAlchemyPaperRepository(db).get(session_id)

    async def list(self, limit: int, offset: int) -> tuple[tuple[PaperSession, ...], int]:
        async with self._session_factory() as db:
            return await SQLAlchemyPaperRepository(db).list(limit, offset)

    async def events(self, session_id: UUID) -> tuple[PaperEventRecord, ...]:
        async with self._session_factory() as db:
            return await SQLAlchemyPaperRepository(db).list_events(session_id)

    async def snapshot(
        self, session_id: UUID
    ) -> tuple[PaperSession, tuple[PaperEventRecord, ...]] | None:
        async with self._session_factory() as db:
            return await SQLAlchemyPaperRepository(db).snapshot(session_id)

    async def start(self, session_id: UUID) -> PaperSession:
        async with self._lock:
            session = await self.get(session_id)
            if session is None:
                raise LookupError("paper session not found")
            if session.status in {PaperSessionStatus.STARTING, PaperSessionStatus.RUNNING}:
                return session
            if session.status is not PaperSessionStatus.CREATED:
                raise PaperSessionStateError(
                    f"paper session cannot start from {session.status.value}"
                )
            session = await self._transition(session, PaperSessionStatus.STARTING, "session.status")
            task = asyncio.create_task(self._run(session), name=f"paper-session-{session_id}")
            self._tasks[session_id] = task
            task.add_done_callback(lambda _: self._tasks.pop(session_id, None))
            logger.info("Started paper session task %s", session_id)
            return session

    async def stop(self, session_id: UUID) -> PaperSession:
        async with self._lock:
            session = await self.get(session_id)
            if session is None:
                raise LookupError("paper session not found")
            if session.status is PaperSessionStatus.STOPPED:
                return session
            if session.status is PaperSessionStatus.CREATED:
                stopped = await self._transition(
                    session, PaperSessionStatus.STOPPED, "session.status"
                )
                logger.info("Stopped idle paper session %s", session_id)
                return stopped
            if session.status is PaperSessionStatus.STOPPING:
                return session
            if session.status not in {PaperSessionStatus.STARTING, PaperSessionStatus.RUNNING}:
                raise PaperSessionStateError(
                    f"paper session cannot stop from {session.status.value}"
                )
            session = await self._transition(session, PaperSessionStatus.STOPPING, "session.status")
            provider = self._providers.get(session_id)
            if provider is not None:
                await provider.stop()
            logger.info("Requested stop for paper session %s", session_id)
            return session

    async def shutdown(self) -> None:
        for task in tuple(self._tasks.values()):
            task.cancel()
        for provider in tuple(self._providers.values()):
            await provider.stop()
        if self._tasks:
            await asyncio.gather(*tuple(self._tasks.values()), return_exceptions=True)
        self._tasks.clear()
        self._providers.clear()

    async def _run(self, initial: PaperSession) -> None:
        session = initial
        provider: ReplayMarketDataProvider | None = None
        runtime: PaperTradingRuntime | None = None
        try:
            provider, runtime = self._build_runtime(session)
            self._providers[session.id] = provider
            async with self._lock:
                current = await self.get(session.id)
                if current is None:
                    raise RuntimeError("paper session disappeared")
                if current.status is PaperSessionStatus.STOPPING:
                    await self._transition(current, PaperSessionStatus.STOPPED, "session.status")
                    return
                session = await self._transition(
                    current, PaperSessionStatus.RUNNING, "session.status"
                )

            async def process(bar: Bar) -> None:
                delta = await runtime.process_bar(bar)
                events = self._serialize_delta(delta)
                async with self._session_factory() as db:
                    stored = await SQLAlchemyPaperRepository(db).append_events(session.id, events)
                for event in stored:
                    self.hub.publish(session.id, self._wire_event(event))

            await provider.start(process)
            async with self._lock:
                current = await self.get(session.id)
                if current is not None and current.status in {
                    PaperSessionStatus.RUNNING,
                    PaperSessionStatus.STOPPING,
                }:
                    cancelled = runtime.cancel_pending_orders()
                    await self._transition(
                        current,
                        PaperSessionStatus.STOPPED,
                        "session.status",
                        cancelled_orders=cancelled,
                    )
                    logger.info("Paper session %s stopped", session.id)
        except asyncio.CancelledError:
            current = await self.get(session.id)
            if current is not None and current.status in {
                PaperSessionStatus.STARTING,
                PaperSessionStatus.RUNNING,
                PaperSessionStatus.STOPPING,
            }:
                with suppress(Exception):
                    cancelled = runtime.cancel_pending_orders() if runtime is not None else ()
                    await self._transition(
                        current,
                        PaperSessionStatus.INTERRUPTED,
                        "session.status",
                        "Paper runtime interrupted by backend shutdown.",
                        cancelled_orders=cancelled,
                    )
                    logger.warning("Paper session %s interrupted by shutdown", session.id)
            raise
        except Exception as exc:
            current = await self.get(session.id)
            if (
                isinstance(exc, PaperSessionConcurrencyError)
                and current is not None
                and current.status is PaperSessionStatus.STOPPING
            ):
                cancelled = runtime.cancel_pending_orders() if runtime is not None else ()
                await self._transition(
                    current,
                    PaperSessionStatus.STOPPED,
                    "session.status",
                    cancelled_orders=cancelled,
                )
                logger.info("Paper session %s stopped after a concurrent command", session.id)
                return
            logger.error("Paper session %s failed with %s", session.id, type(exc).__name__)
            if current is not None and current.status in {
                PaperSessionStatus.STARTING,
                PaperSessionStatus.RUNNING,
                PaperSessionStatus.STOPPING,
            }:
                with suppress(Exception):
                    cancelled = runtime.cancel_pending_orders() if runtime is not None else ()
                    await self._transition(
                        current,
                        PaperSessionStatus.FAILED,
                        "session.status",
                        f"{type(exc).__name__}: paper session failed",
                        cancelled_orders=cancelled,
                    )
        finally:
            if provider is not None:
                await provider.stop()
            self._providers.pop(session.id, None)

    def _build_runtime(
        self, session: PaperSession
    ) -> tuple[ReplayMarketDataProvider, PaperTradingRuntime]:
        historical = self._datasets.resolve(session.dataset_id, session.symbol)
        bars = historical.get_historical_bars(session.symbol, None, None, Timeframe.DAY_1)
        parameters = dict(session.strategy_parameters)
        if session.strategy_type == "rsi_mean_reversion":
            parameters["oversold"] = Decimal(str(parameters["oversold"]))
            parameters["overbought"] = Decimal(str(parameters["overbought"]))
        strategy = self._strategies.build(
            session.strategy_type,
            f"{session.strategy_type}:{session.symbol}",
            session.symbol,
            parameters,
        )

        def optional_decimal(name: str) -> Decimal | None:
            value = session.risk.get(name)
            return Decimal(str(value)) if value is not None else None

        risk = RiskConfig(
            max_order_notional=optional_decimal("max_order_notional"),
            max_position_quantity=optional_decimal("max_position_quantity"),
            max_symbol_exposure=optional_decimal("max_symbol_exposure"),
            max_gross_exposure=optional_decimal("max_gross_exposure"),
            max_leverage=optional_decimal("max_leverage"),
            enforce_buying_power=bool(session.risk.get("enforce_buying_power", False)),
            max_drawdown=optional_decimal("max_drawdown"),
        )
        runtime = PaperTradingRuntime(
            (strategy,),
            BacktestConfig(
                initial_cash=session.initial_cash,
                default_order_quantity=session.default_order_quantity,
                risk=risk,
            ),
        )
        provider = ReplayMarketDataProvider(bars, self._replay_interval_seconds)
        provider.subscribe(session.symbol)
        return provider, runtime

    async def _transition(
        self,
        session: PaperSession,
        target: PaperSessionStatus,
        event_type: str,
        error_message: str | None = None,
        cancelled_orders: tuple[Order, ...] = (),
    ) -> PaperSession:
        now = self._now()
        preceding_events = tuple(
            ("order.updated", now, self._order(order)) for order in cancelled_orders
        )
        async with self._session_factory() as db:
            repository = SQLAlchemyPaperRepository(db)
            updated, stored = await repository.transition_with_event(
                session.id,
                session.status,
                target,
                now,
                event_type,
                error_message,
                preceding_events,
            )
        for event in stored:
            self.hub.publish(session.id, self._wire_event(event))
        return updated

    @classmethod
    def _serialize_delta(
        cls, delta: PaperRuntimeDelta
    ) -> tuple[tuple[str, datetime, dict[str, object]], ...]:
        events: list[tuple[str, datetime, dict[str, object]]] = [
            ("market.bar", delta.bar.timestamp, cls._bar(delta.bar))
        ]
        filled_order_ids = {fill.order_id for fill in delta.fills}
        events.extend(
            ("order.updated", delta.bar.timestamp, cls._order(item))
            for item in delta.orders
            if item.id in filled_order_ids
        )
        events.extend(("fill.created", item.timestamp, cls._fill(item)) for item in delta.fills)
        events.extend(
            ("signal.created", item.timestamp, cls._signal(item)) for item in delta.signals
        )
        events.extend(
            ("risk.decision", item.timestamp, cls._decision(item)) for item in delta.decisions
        )
        events.extend(
            ("order.updated", item.created_at, cls._order(item))
            for item in delta.orders
            if item.id not in filled_order_ids
        )
        events.append(
            (
                "portfolio.snapshot",
                delta.snapshot.timestamp,
                cls._snapshot(delta.snapshot),
            )
        )
        return tuple(events)

    @staticmethod
    def _bar(bar: Bar) -> dict[str, object]:
        return {
            "symbol": bar.symbol,
            "timestamp": bar.timestamp.isoformat(),
            "open": canonical_decimal(bar.open),
            "high": canonical_decimal(bar.high),
            "low": canonical_decimal(bar.low),
            "close": canonical_decimal(bar.close),
            "volume": canonical_decimal(bar.volume),
        }

    @staticmethod
    def _signal(signal: Signal) -> dict[str, object]:
        return {
            "strategy_id": signal.strategy_id,
            "symbol": signal.symbol,
            "timestamp": signal.timestamp.isoformat(),
            "signal_type": signal.signal_type.value,
        }

    @staticmethod
    def _decision(decision: RiskDecision) -> dict[str, object]:
        payload: dict[str, object] = {
            "proposal_id": str(decision.proposal_id),
            "approved": decision.approved,
            "reason_code": decision.reason_code.value,
            "message": decision.message,
            "timestamp": decision.timestamp.isoformat(),
            "risk_increasing": decision.risk_increasing,
        }
        for name in (
            "reference_price",
            "order_notional",
            "projected_position_quantity",
            "projected_symbol_exposure",
            "projected_gross_exposure",
            "projected_net_exposure",
            "projected_gross_leverage",
            "projected_cash",
            "estimated_transaction_cost",
        ):
            value = getattr(decision, name)
            payload[name] = canonical_decimal(value) if value is not None else None
        return payload

    @staticmethod
    def _order(order: Order) -> dict[str, object]:
        return {
            "order_id": str(order.id),
            "strategy_id": order.strategy_id,
            "symbol": order.symbol,
            "side": order.side.value,
            "order_type": order.order_type.value,
            "quantity": canonical_decimal(order.quantity),
            "price": canonical_decimal(order.price) if order.price is not None else None,
            "status": order.status.value,
            "created_at": order.created_at.isoformat(),
        }

    @staticmethod
    def _fill(fill: Fill) -> dict[str, object]:
        return {
            "order_id": str(fill.order_id),
            "strategy_id": fill.strategy_id,
            "symbol": fill.symbol,
            "side": fill.side.value,
            "quantity": canonical_decimal(fill.quantity),
            "price": canonical_decimal(fill.price),
            "commission": canonical_decimal(fill.commission),
            "timestamp": fill.timestamp.isoformat(),
        }

    @staticmethod
    def _snapshot(snapshot: PortfolioSnapshot) -> dict[str, object]:
        return {
            "timestamp": snapshot.timestamp.isoformat(),
            "cash": canonical_decimal(snapshot.cash),
            "market_value": canonical_decimal(snapshot.market_value),
            "equity": canonical_decimal(snapshot.equity),
            "realized_pnl": canonical_decimal(snapshot.realized_pnl),
            "unrealized_pnl": canonical_decimal(snapshot.unrealized_pnl),
            "cumulative_commission": canonical_decimal(snapshot.cumulative_commission),
            "drawdown": canonical_decimal(snapshot.drawdown),
            "positions": [
                {
                    "symbol": position.symbol,
                    "quantity": canonical_decimal(position.quantity),
                    "average_price": canonical_decimal(position.average_price),
                    "market_price": canonical_decimal(position.market_price),
                    "unrealized_pnl": canonical_decimal(position.unrealized_pnl),
                    "realized_pnl": canonical_decimal(position.realized_pnl),
                }
                for position in snapshot.positions
            ],
        }

    @staticmethod
    def _wire_event(event: PaperEventRecord) -> dict[str, object]:
        return {
            "sequence": event.sequence,
            "type": event.event_type,
            "occurred_at": event.occurred_at.isoformat(),
            "payload": event.payload,
        }

    @staticmethod
    def _json_decimals(values: dict[str, object]) -> dict[str, object]:
        return {
            key: canonical_decimal(value) if isinstance(value, Decimal) else value
            for key, value in values.items()
        }

    @classmethod
    def _request_hash(cls, command: CreatePaperSessionCommand) -> str:
        payload = {
            "provider_type": command.provider_type,
            "dataset_id": command.dataset_id,
            "symbol": command.symbol,
            "strategy_type": command.strategy_type,
            "strategy_parameters": cls._json_decimals(command.strategy_parameters),
            "initial_cash": canonical_decimal(command.initial_cash),
            "default_order_quantity": canonical_decimal(command.default_order_quantity),
            "risk": cls._json_decimals(command.risk.model_dump()),
        }
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode()).hexdigest()

    def _now(self) -> datetime:
        now = self._clock()
        if now.tzinfo is None or now.utcoffset() is None:
            raise ValueError("paper session clock must be timezone-aware")
        return now.astimezone(UTC)
