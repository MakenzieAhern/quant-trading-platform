import asyncio
import hashlib
import json
from collections.abc import Callable
from contextlib import suppress
from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID, uuid4

from app.application.backtests.decimal_policy import (
    canonical_decimal,
    validate_storage_decimal,
)
from app.application.backtests.models import (
    BacktestRun,
    BacktestRunStatus,
    CreateBacktestCommand,
)
from app.application.backtests.registry import DatasetRegistry, StrategyRegistry
from app.application.backtests.repositories import BacktestRepository
from app.backtest import BacktestConfig, BacktestEngine
from app.domain.common import ensure_utc


class IdempotencyConflictError(ValueError):
    """Raised when an idempotency key is reused for different content."""


class IdempotencyInProgressError(RuntimeError):
    """Raised when an earlier synchronous request does not reach a terminal state."""


class BacktestExecutionError(RuntimeError):
    def __init__(self, run_id: UUID, message: str) -> None:
        super().__init__(message)
        self.run_id = run_id


Clock = Callable[[], datetime]


class BacktestApplicationService:
    def __init__(
        self,
        repository: BacktestRepository,
        datasets: DatasetRegistry,
        strategies: StrategyRegistry,
        clock: Clock | None = None,
    ) -> None:
        self._repository = repository
        self._datasets = datasets
        self._strategies = strategies
        self._clock = clock or (lambda: datetime.now(UTC))

    async def create_and_run(self, command: CreateBacktestCommand) -> BacktestRun:
        self._validate_decimals(command)
        request_hash = self._request_hash(command)
        if command.client_request_id is not None:
            existing = await self._repository.get_by_client_request_id(command.client_request_id)
            if existing is not None:
                return await self._resolve_existing(existing, request_hash)

        provider = self._datasets.resolve(command.dataset_id, command.symbol)
        strategy_id = f"{command.strategy_type}:{command.symbol}"
        strategy = self._strategies.build(
            command.strategy_type,
            strategy_id,
            command.symbol,
            command.strategy_parameters,
        )
        created_at = self._now()
        proposed_run_id = uuid4()
        run = BacktestRun(
            id=proposed_run_id,
            status=BacktestRunStatus.CREATED,
            strategy_id=strategy_id,
            strategy_type=command.strategy_type,
            strategy_parameters=command.strategy_parameters,
            symbol=command.symbol,
            dataset_id=command.dataset_id,
            created_at=created_at,
            started_at=None,
            completed_at=None,
            initial_cash=command.initial_cash,
            default_order_quantity=command.default_order_quantity,
            risk=self._risk_dict(command),
            start=command.start,
            end=command.end,
            error_message=None,
            client_request_id=command.client_request_id,
            request_hash=(request_hash if command.client_request_id is not None else None),
        )
        run = await self._repository.create(run)
        if run.id != proposed_run_id:
            return await self._resolve_existing(run, request_hash)
        run = await self._repository.transition(
            run.id,
            BacktestRunStatus.CREATED,
            BacktestRunStatus.RUNNING,
            self._now(),
        )
        try:
            result = BacktestEngine(
                provider,
                (strategy,),
                BacktestConfig(
                    initial_cash=command.initial_cash,
                    default_order_quantity=command.default_order_quantity,
                    risk=command.risk,
                ),
            ).run(command.symbol, command.start, command.end)
            return await self._repository.persist_success(run.id, result, self._now())
        except Exception as exc:
            safe_message = f"{type(exc).__name__}: backtest execution failed"
            with suppress(Exception):
                await self._repository.transition(
                    run.id,
                    BacktestRunStatus.RUNNING,
                    BacktestRunStatus.FAILED,
                    self._now(),
                    safe_message,
                )
            raise BacktestExecutionError(run.id, safe_message) from exc

    @staticmethod
    def _risk_dict(command: CreateBacktestCommand) -> dict[str, object]:
        return {
            key: (canonical_decimal(value) if isinstance(value, Decimal) else value)
            for key, value in command.risk.model_dump().items()
        }

    @staticmethod
    def _request_hash(command: CreateBacktestCommand) -> str:
        payload = {
            "dataset_id": command.dataset_id,
            "symbol": command.symbol,
            "strategy_type": command.strategy_type,
            "strategy_parameters": command.strategy_parameters,
            "initial_cash": command.initial_cash,
            "default_order_quantity": command.default_order_quantity,
            "risk": command.risk.model_dump(),
            "start": command.start,
            "end": command.end,
        }

        def default(value: object) -> str:
            if isinstance(value, Decimal):
                return canonical_decimal(value)
            if isinstance(value, datetime):
                return ensure_utc(value).isoformat()
            raise TypeError(f"unsupported request value: {type(value).__name__}")

        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=default)
        return hashlib.sha256(canonical.encode()).hexdigest()

    async def _resolve_existing(self, existing: BacktestRun, request_hash: str) -> BacktestRun:
        if existing.request_hash != request_hash:
            raise IdempotencyConflictError(
                "idempotency key was already used for a different request"
            )
        for _ in range(6000):
            if existing.status in {
                BacktestRunStatus.SUCCEEDED,
                BacktestRunStatus.FAILED,
            }:
                return existing
            await asyncio.sleep(0.01)
            refreshed = await self._repository.get(existing.id)
            if refreshed is None:
                raise RuntimeError("idempotent backtest run disappeared")
            existing = refreshed
        raise IdempotencyInProgressError(
            "matching idempotent backtest is still running; retry later"
        )

    def _now(self) -> datetime:
        return ensure_utc(self._clock())

    @staticmethod
    def _validate_decimals(command: CreateBacktestCommand) -> None:
        validate_storage_decimal(command.initial_cash, "initial_cash")
        validate_storage_decimal(command.default_order_quantity, "default_order_quantity")
        for name, value in command.strategy_parameters.items():
            if isinstance(value, Decimal):
                validate_storage_decimal(value, f"strategy.parameters.{name}")
        for name, value in command.risk.model_dump().items():
            if isinstance(value, Decimal):
                validate_storage_decimal(value, f"risk.{name}")
