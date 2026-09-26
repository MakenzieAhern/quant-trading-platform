import asyncio
import hashlib
import json
import logging
from collections.abc import Callable
from contextlib import suppress
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.application.backtests.decimal_policy import canonical_decimal, validate_storage_decimal
from app.application.backtests.registry import DatasetRegistry, StrategyRegistry
from app.application.experiments.data import (
    HISTORICAL_ID,
    ExperimentDatasetRegistry,
    load_experiment_dataset,
)
from app.application.experiments.models import CreateExperimentRequest
from app.application.experiments.runner import ExploratoryStrategy, build_plan_preview, json_value
from app.backtest import BacktestConfig
from app.data.catalog.checksums import canonical_sha256
from app.data.full_dataset import FullDataset
from app.data.providers import Timeframe
from app.db.repositories.paper import SQLAlchemyPaperRepository
from app.domain.market import Bar
from app.domain.markets.calendar import TradingCalendar
from app.domain.risk import RiskConfig, RiskDecision
from app.domain.trading import Fill, Order, PortfolioSnapshot, Signal
from app.paper.a_share_fixture import (
    SIMULATED_A_SHARE_DATASET_ID,
    SIMULATED_A_SHARE_SYMBOL,
    SIMULATED_SOURCE,
    simulated_a_share_fixture,
)
from app.paper.hub import PaperEventHub
from app.paper.models import (
    CreatePaperSessionCommand,
    PaperEventRecord,
    PaperSession,
    PaperSessionConcurrencyError,
    PaperSessionStatus,
)
from app.paper.runtime import (
    FROZEN_A_SHARE_STRATEGY_ID,
    ASharePaperTradingRuntime,
    PaperRuntimeDelta,
    PaperTradingRuntime,
    ReplayMarketDataProvider,
    SimulatedAShareSessionProvider,
)
from app.research import ResearchExecutionDelta, ResearchSession
from app.research.costs import EffectiveDatedAShareCommission


class PaperSessionConflictError(ValueError):
    """Raised when an idempotency key is reused for different content."""


class PaperSessionStateError(ValueError):
    """Raised when a lifecycle command is not valid for the persisted state."""


Clock = Callable[[], datetime]
logger = logging.getLogger(__name__)
HISTORICAL_SOURCE = "FROZEN_HISTORICAL_A_SHARE_REPLAY_V1"


class PaperTradingManager:
    """Own background tasks while every session owns a fully isolated trading runtime."""

    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        datasets: DatasetRegistry,
        strategies: StrategyRegistry,
        *,
        historical_datasets: ExperimentDatasetRegistry | None = None,
        replay_interval_seconds: float = 0.75,
        clock: Clock | None = None,
        hub: PaperEventHub | None = None,
    ) -> None:
        self._session_factory = session_factory
        self._datasets = datasets
        self._strategies = strategies
        self._historical_datasets = historical_datasets
        self._replay_interval_seconds = replay_interval_seconds
        self._clock = clock or (lambda: datetime.now(UTC))
        self.hub = hub or PaperEventHub()
        self._tasks: dict[UUID, asyncio.Task[None]] = {}
        self._providers: dict[UUID, ReplayMarketDataProvider | SimulatedAShareSessionProvider] = {}
        self._lock = asyncio.Lock()

    async def recover_interrupted(self) -> int:
        async with self._session_factory() as db:
            interrupted = await SQLAlchemyPaperRepository(db).interrupt_active(self._now())
        if interrupted:
            logger.warning("Interrupted %d orphaned paper session(s) during startup", interrupted)
        return interrupted

    async def create(self, command: CreatePaperSessionCommand) -> PaperSession:
        if command.provider_type not in {"replay", "simulated_a_share", "historical_a_share"}:
            raise ValueError("unknown paper market data provider")
        validate_storage_decimal(command.initial_cash, "initial_cash")
        validate_storage_decimal(command.default_order_quantity, "default_order_quantity")
        if command.provider_type == "replay":
            self._datasets.resolve(command.dataset_id, command.symbol)
            self._strategies.build(
                command.strategy_type,
                f"{command.strategy_type}:{command.symbol}",
                command.symbol,
                command.strategy_parameters,
            )
        elif command.provider_type == "historical_a_share":
            if (
                self._historical_datasets is None
                or command.dataset_id != HISTORICAL_ID
                or command.symbol != "CN-A"
                or command.strategy_type != FROZEN_A_SHARE_STRATEGY_ID
            ):
                raise ValueError("invalid historical A-share paper configuration")
            registered = await asyncio.to_thread(
                self._historical_datasets.resolve, command.dataset_id
            )
            start = command.strategy_parameters["start_date"]
            end = command.strategy_parameters["end_date"]
            if not isinstance(start, date) or not isinstance(end, date):
                raise ValueError("historical paper dates are required")
            if not (
                registered["coverage_start"]
                <= start.isoformat()
                <= end.isoformat()
                <= registered["coverage_end"]
            ):
                raise ValueError("historical paper range is outside the accepted archive")
        elif (
            command.dataset_id != SIMULATED_A_SHARE_DATASET_ID
            or command.symbol != SIMULATED_A_SHARE_SYMBOL
            or command.strategy_type != FROZEN_A_SHARE_STRATEGY_ID
            or command.strategy_parameters
        ):
            raise ValueError("invalid frozen A-share paper configuration")
        request_hash = self._request_hash(command)
        parameters = self._json_decimals(command.strategy_parameters)
        if command.provider_type == "historical_a_share":
            parameters["dataset_sha256"] = str(registered["sha256"])
            parameters["plan_version"] = "PAPER_ACCOUNT_PLAN_V1"
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
                strategy_parameters=parameters,
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
            if command.provider_type == "historical_a_share":
                try:
                    self._historical_request(session)
                except ValueError as exc:
                    raise ValueError("invalid historical A-share paper configuration") from exc
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
            if session.status not in {PaperSessionStatus.CREATED, PaperSessionStatus.PAUSED}:
                raise PaperSessionStateError(
                    f"paper session cannot start from {session.status.value}"
                )
            session = await self._transition(session, PaperSessionStatus.STARTING, "session.status")
            task = asyncio.create_task(self._run(session), name=f"paper-session-{session_id}")
            self._tasks[session_id] = task
            task.add_done_callback(
                lambda finished: self._tasks.pop(session_id, None)
                if self._tasks.get(session_id) is finished
                else None
            )
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
            if session.status is PaperSessionStatus.PAUSED:
                events = await self.events(session_id)
                cancellations = self._pending_order_events(events, self._now())
                return await self._transition(
                    session,
                    PaperSessionStatus.STOPPED,
                    "session.status",
                    preceding_events=cancellations,
                )
            if session.status is PaperSessionStatus.STOPPING:
                return session
            if session.status not in {
                PaperSessionStatus.STARTING,
                PaperSessionStatus.RUNNING,
                PaperSessionStatus.PAUSING,
            }:
                raise PaperSessionStateError(
                    f"paper session cannot stop from {session.status.value}"
                )
            session = await self._transition(session, PaperSessionStatus.STOPPING, "session.status")
            provider = self._providers.get(session_id)
            if provider is not None:
                await provider.stop()
            logger.info("Requested stop for paper session %s", session_id)
            return session

    async def pause(self, session_id: UUID) -> PaperSession:
        async with self._lock:
            session = await self.get(session_id)
            if session is None:
                raise LookupError("paper session not found")
            if session.status in {PaperSessionStatus.PAUSING, PaperSessionStatus.PAUSED}:
                return session
            if session.status not in {PaperSessionStatus.STARTING, PaperSessionStatus.RUNNING}:
                raise PaperSessionStateError(
                    f"paper session cannot pause from {session.status.value}"
                )
            session = await self._transition(session, PaperSessionStatus.PAUSING, "session.status")
            provider = self._providers.get(session_id)
            if provider is not None:
                await provider.stop()
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
        provider: ReplayMarketDataProvider | SimulatedAShareSessionProvider | None = None
        runtime: PaperTradingRuntime | ASharePaperTradingRuntime | None = None
        history: tuple[PaperEventRecord, ...] = ()
        matched_cursor = False
        try:
            history = await self.events(session.id)
            resumed = any(
                item.event_type == "session.status" and item.payload.get("status") == "PAUSED"
                for item in history
            )
            market_type = "market.bar" if session.provider_type == "replay" else "market.session"
            last_market = (
                next((item for item in reversed(history) if item.event_type == market_type), None)
                if resumed
                else None
            )
            expected_replay = tuple(
                (item.event_type, item.payload)
                for item in history
                if item.event_type != "session.status"
            )
            replayed: list[tuple[str, dict[str, object]]] = []
            if last_market is not None and not expected_replay:
                raise ValueError("paper replay has no persisted market checkpoint")
            cursor_time = (
                datetime.fromisoformat(str(last_market.payload["timestamp"]))
                if last_market is not None and market_type == "market.bar"
                else None
            )
            cursor_date = (
                date.fromisoformat(str(last_market.payload["trading_date"]))
                if last_market is not None and market_type == "market.session"
                else None
            )
            matched_cursor = last_market is None
            provider, runtime = await asyncio.to_thread(self._build_runtime, session, cursor_date)
            assert provider is not None
            self._providers[session.id] = provider
            async with self._lock:
                current = await self.get(session.id)
                if current is None:
                    raise RuntimeError("paper session disappeared")
                if current.status is PaperSessionStatus.PAUSING:
                    await self._transition(current, PaperSessionStatus.PAUSED, "session.status")
                    return
                if current.status is PaperSessionStatus.STOPPING:
                    await self._transition(
                        current,
                        PaperSessionStatus.STOPPED,
                        "session.status",
                        preceding_events=self._pending_order_events(history, self._now()),
                    )
                    return
                session = await self._transition(
                    current, PaperSessionStatus.RUNNING, "session.status"
                )

            async def persist(
                events: tuple[tuple[str, datetime, dict[str, object]], ...],
            ) -> None:
                if not matched_cursor:
                    raise ValueError("paper replay checkpoint disappeared from source data")
                async with self._session_factory() as db:
                    stored = await SQLAlchemyPaperRepository(db).append_events(session.id, events)
                for event in stored:
                    self.hub.publish(session.id, self._wire_event(event))

            if isinstance(provider, ReplayMarketDataProvider):
                assert isinstance(runtime, PaperTradingRuntime)

                async def process_bar(bar: Bar) -> None:
                    nonlocal matched_cursor
                    events = self._serialize_delta(await runtime.process_bar(bar))
                    if cursor_time is not None and bar.timestamp <= cursor_time:
                        replayed.extend((kind, payload) for kind, _, payload in events)
                        if bar.timestamp == cursor_time:
                            if tuple(replayed) != expected_replay:
                                raise ValueError("paper replay checkpoint no longer matches")
                            matched_cursor = True
                        return
                    await persist(events)

                await provider.start(process_bar)
            else:
                assert isinstance(provider, SimulatedAShareSessionProvider)
                assert isinstance(runtime, ASharePaperTradingRuntime)
                historical_start = (
                    date.fromisoformat(str(session.strategy_parameters["start_date"]))
                    if session.provider_type == "historical_a_share"
                    else None
                )
                plan_request = (
                    self._historical_request(session)
                    if session.strategy_parameters.get("plan_version") == "PAPER_ACCOUNT_PLAN_V1"
                    else None
                )

                async def process_session(item: ResearchSession) -> None:
                    nonlocal matched_cursor
                    delta = await runtime.process_session(item)
                    if historical_start is not None and item.trading_date < historical_start:
                        return  # Warm up from accepted past only; no pre-range account events.
                    source = (
                        HISTORICAL_SOURCE
                        if session.provider_type == "historical_a_share"
                        else SIMULATED_SOURCE
                    )
                    plan = None
                    if plan_request is not None:
                        plan = build_plan_preview(
                            plan_request,
                            str(session.strategy_parameters["dataset_sha256"]),
                            "historical_exploration",
                            delta,
                            delta.target,
                            runtime.next_accepted_session(item.trading_date),
                            runtime.completed_sessions,
                        )
                        plan.update(
                            paper_session_id=str(session.id),
                            account_mode="HISTORICAL_PAPER_REPLAY",
                            submitted_to_account=bool(delta.proposals),
                            plan_version="PAPER_ACCOUNT_PLAN_V1",
                            configuration_sha256=self._historical_plan_sha(session, plan_request),
                        )
                    events = self._serialize_a_share_delta(delta, source=source, plan=plan)
                    if cursor_date is not None and item.trading_date <= cursor_date:
                        replayed.extend((kind, payload) for kind, _, payload in events)
                        if item.trading_date == cursor_date:
                            if tuple(replayed) != expected_replay:
                                raise ValueError("paper replay checkpoint no longer matches")
                            matched_cursor = True
                        return
                    await persist(events)

                await provider.start(process_session)
            async with self._lock:
                current = await self.get(session.id)
                if current is not None and current.status is PaperSessionStatus.PAUSING:
                    await self._transition(current, PaperSessionStatus.PAUSED, "session.status")
                    return
                if (
                    not matched_cursor
                    and current is not None
                    and current.status is PaperSessionStatus.RUNNING
                ):
                    raise ValueError("paper replay checkpoint disappeared from source data")
                if current is not None and current.status in {
                    PaperSessionStatus.RUNNING,
                    PaperSessionStatus.STOPPING,
                }:
                    cancelled = runtime.cancel_pending_orders() if matched_cursor else ()
                    await self._transition(
                        current,
                        PaperSessionStatus.STOPPED,
                        "session.status",
                        cancelled_orders=cancelled,
                        preceding_events=(
                            self._pending_order_events(history, self._now())
                            if not matched_cursor
                            else ()
                        ),
                    )
                    logger.info("Paper session %s stopped", session.id)
        except asyncio.CancelledError:
            current = await self.get(session.id)
            if current is not None and current.status in {
                PaperSessionStatus.STARTING,
                PaperSessionStatus.RUNNING,
                PaperSessionStatus.PAUSING,
                PaperSessionStatus.STOPPING,
            }:
                with suppress(Exception):
                    cancelled = (
                        runtime.cancel_pending_orders()
                        if runtime is not None and matched_cursor
                        else ()
                    )
                    await self._transition(
                        current,
                        PaperSessionStatus.INTERRUPTED,
                        "session.status",
                        "Paper runtime interrupted by backend shutdown.",
                        cancelled_orders=cancelled,
                        preceding_events=(
                            self._pending_order_events(history, self._now())
                            if not matched_cursor
                            else ()
                        ),
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
                cancelled = (
                    runtime.cancel_pending_orders()
                    if runtime is not None and matched_cursor
                    else ()
                )
                await self._transition(
                    current,
                    PaperSessionStatus.STOPPED,
                    "session.status",
                    cancelled_orders=cancelled,
                    preceding_events=(
                        self._pending_order_events(history, self._now())
                        if not matched_cursor
                        else ()
                    ),
                )
                logger.info("Paper session %s stopped after a concurrent command", session.id)
                return
            logger.error("Paper session %s failed with %s", session.id, type(exc).__name__)
            if current is not None and current.status in {
                PaperSessionStatus.STARTING,
                PaperSessionStatus.RUNNING,
                PaperSessionStatus.PAUSING,
                PaperSessionStatus.STOPPING,
            }:
                with suppress(Exception):
                    cancelled = (
                        runtime.cancel_pending_orders()
                        if runtime is not None and matched_cursor
                        else ()
                    )
                    await self._transition(
                        current,
                        PaperSessionStatus.FAILED,
                        "session.status",
                        f"{type(exc).__name__}: paper session failed",
                        cancelled_orders=cancelled,
                        preceding_events=(
                            self._pending_order_events(history, self._now())
                            if not matched_cursor
                            else ()
                        ),
                    )
        finally:
            if provider is not None:
                await provider.stop()
            if self._providers.get(session.id) is provider:
                self._providers.pop(session.id, None)

    @staticmethod
    def _historical_request(session: PaperSession) -> CreateExperimentRequest:
        params = session.strategy_parameters
        return CreateExperimentRequest.model_validate(
            {
                "name": "Historical paper replay",
                "dataset_id": session.dataset_id,
                "start_date": params["start_date"],
                "end_date": params["end_date"],
                "initial_cash": canonical_decimal(session.initial_cash),
                "universe": params["universe"],
                "strategy": {
                    "rebalance_sessions": params["rebalance_sessions"],
                    "maximum_holdings": params["maximum_holdings"],
                },
                "costs": {
                    "commission_rate": params["commission_rate"],
                    "minimum_commission": params["minimum_commission"],
                },
                "risk": {
                    "max_drawdown": session.risk["max_drawdown"],
                    "max_position_weight": params["max_position_weight"],
                },
            }
        )

    @classmethod
    def _historical_plan_sha(cls, session: PaperSession, request: CreateExperimentRequest) -> str:
        return canonical_sha256(
            json_value(
                {
                    "request": request.model_dump(),
                    "effective_risk": cls._historical_effective_risk(session).model_dump(),
                }
            )
        )

    def _build_runtime(
        self, session: PaperSession, cursor_date: date | None = None
    ) -> tuple[
        ReplayMarketDataProvider | SimulatedAShareSessionProvider,
        PaperTradingRuntime | ASharePaperTradingRuntime,
    ]:
        risk = self._risk_config(session)
        if session.provider_type == "simulated_a_share":
            calendar, sessions, commission = simulated_a_share_fixture()
            return (
                SimulatedAShareSessionProvider(
                    sessions,
                    self._replay_interval_seconds,
                    pace_from_date=cursor_date + timedelta(days=1) if cursor_date else None,
                ),
                ASharePaperTradingRuntime(
                    initial_cash=session.initial_cash,
                    commission_model=commission,
                    calendar=calendar,
                    risk_config=risk,
                ),
            )
        if session.provider_type == "historical_a_share":
            assert self._historical_datasets is not None
            params = session.strategy_parameters
            request = self._historical_request(session)
            data = load_experiment_dataset(
                self._historical_datasets, session.dataset_id, request.start_date, request.end_date
            )
            if not isinstance(data, FullDataset):
                raise ValueError("historical paper requires the accepted archive")
            if data.manifest.canonical_sha256 != params["dataset_sha256"]:
                raise ValueError("historical paper dataset changed since account creation")
            commission = EffectiveDatedAShareCommission(
                tuple(
                    item.model_copy(
                        update={
                            "commission_rate": request.costs.commission_rate,
                            "minimum_commission": request.costs.minimum_commission,
                        }
                    )
                    for item in data.cost_model.schedules
                )
            )
            calendar = (
                TradingCalendar(
                    market=data.calendar.market,
                    sessions=(*data.calendar.sessions, data.next_session),
                )
                if data.next_session is not None
                else data.calendar
            )
            return (
                SimulatedAShareSessionProvider(
                    data.sessions(),
                    self._replay_interval_seconds,
                    pace_from_date=(cursor_date + timedelta(days=1))
                    if cursor_date
                    else request.start_date,
                ),
                ASharePaperTradingRuntime(
                    initial_cash=session.initial_cash,
                    commission_model=commission,
                    calendar=calendar,
                    risk_config=self._historical_effective_risk(session),
                    strategy=ExploratoryStrategy(request),
                ),
            )
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

    @staticmethod
    def _pending_order_events(
        events: tuple[PaperEventRecord, ...], timestamp: datetime
    ) -> tuple[tuple[str, datetime, dict[str, object]], ...]:
        latest: dict[str, dict[str, object]] = {}
        for event in events:
            if event.event_type == "order.updated":
                latest[str(event.payload["order_id"])] = event.payload
        return tuple(
            ("order.updated", timestamp, {**payload, "status": "CANCELLED"})
            for payload in latest.values()
            if payload.get("status") in {"CREATED", "SUBMITTED", "ACCEPTED", "PARTIALLY_FILLED"}
        )

    @staticmethod
    def _risk_config(session: PaperSession) -> RiskConfig:
        def optional_decimal(name: str) -> Decimal | None:
            value = session.risk.get(name)
            return Decimal(str(value)) if value is not None else None

        return RiskConfig(
            max_order_notional=optional_decimal("max_order_notional"),
            max_position_quantity=optional_decimal("max_position_quantity"),
            max_symbol_exposure=optional_decimal("max_symbol_exposure"),
            max_gross_exposure=optional_decimal("max_gross_exposure"),
            max_leverage=optional_decimal("max_leverage"),
            enforce_buying_power=bool(session.risk.get("enforce_buying_power", False)),
            max_drawdown=optional_decimal("max_drawdown"),
        )

    @classmethod
    def _historical_effective_risk(cls, session: PaperSession) -> RiskConfig:
        return RiskConfig(
            **{
                **cls._risk_config(session).model_dump(),
                "enforce_buying_power": True,
                "max_leverage": Decimal(1),
            }
        )

    async def _transition(
        self,
        session: PaperSession,
        target: PaperSessionStatus,
        event_type: str,
        error_message: str | None = None,
        cancelled_orders: tuple[Order, ...] = (),
        preceding_events: tuple[tuple[str, datetime, dict[str, object]], ...] = (),
    ) -> PaperSession:
        now = self._now()
        cancellations = tuple(
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
                (*preceding_events, *cancellations),
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

    @classmethod
    def _serialize_a_share_delta(
        cls,
        delta: ResearchExecutionDelta,
        *,
        source: str = SIMULATED_SOURCE,
        plan: dict[str, object] | None = None,
    ) -> tuple[tuple[str, datetime, dict[str, object]], ...]:
        if delta.snapshot is None:
            raise RuntimeError("A-share session did not produce a portfolio snapshot")
        timestamp = delta.snapshot.timestamp
        events: list[tuple[str, datetime, dict[str, object]]] = [
            (
                "market.session",
                timestamp,
                {
                    "trading_date": delta.session.trading_date.isoformat(),
                    "security_count": len(delta.session.bars),
                    "source": source,
                },
            )
        ]
        filled_order_ids = {fill.order_id for fill in delta.fills}
        events.extend(
            ("order.updated", timestamp, cls._order(item))
            for item in delta.orders
            if item.id in filled_order_ids
        )
        events.extend(("fill.created", item.timestamp, cls._fill(item)) for item in delta.fills)
        events.extend(
            (
                "signal.created",
                item.signal_timestamp,
                {
                    "strategy_id": item.strategy_id,
                    "symbol": item.symbol,
                    "timestamp": item.signal_timestamp.isoformat(),
                    "signal_type": item.side.value,
                },
            )
            for item in delta.proposals
        )
        events.extend(
            ("risk.decision", item.timestamp, cls._decision(item)) for item in delta.decisions
        )
        events.extend(
            ("order.updated", item.created_at, cls._order(item))
            for item in delta.orders
            if item.id not in filled_order_ids
        )
        snapshot = cls._snapshot(delta.snapshot)
        if plan is not None:
            snapshot["plan"] = plan
        events.append(("portfolio.snapshot", timestamp, snapshot))
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
            key: (
                canonical_decimal(value)
                if isinstance(value, Decimal)
                else value.isoformat()
                if isinstance(value, date)
                else value
            )
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
