import hashlib
import json
from collections.abc import Callable
from contextlib import suppress
from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID, uuid4

from app.application.backtests.models import (
    BacktestRun,
    BacktestRunStatus,
    CreateBacktestCommand,
)
from app.application.backtests.registry import DatasetRegistry, StrategyRegistry
from app.application.backtests.repositories import BacktestRepository
from app.backtest import BacktestConfig, BacktestEngine


class IdempotencyConflictError(ValueError):
    """Raised when an idempotency key is reused for different content."""


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
        request_hash = self._request_hash(command)
        if command.client_request_id is not None:
            existing = await self._repository.get_by_client_request_id(command.client_request_id)
            if existing is not None:
                if existing.request_hash != request_hash:
                    raise IdempotencyConflictError(
                        "idempotency key was already used for a different request"
                    )
                return existing

        provider = self._datasets.resolve(command.dataset_id, command.symbol)
        strategy_id = f"{command.strategy_type}:{command.symbol}"
        strategy = self._strategies.build(
            command.strategy_type,
            strategy_id,
            command.symbol,
            command.strategy_parameters,
        )
        created_at = self._clock()
        run = BacktestRun(
            id=uuid4(),
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
            request_hash=request_hash,
        )
        run = await self._repository.create(run)
        run = await self._repository.transition(
            run.id,
            BacktestRunStatus.CREATED,
            BacktestRunStatus.RUNNING,
            self._clock(),
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
            return await self._repository.persist_success(run.id, result, self._clock())
        except Exception as exc:
            safe_message = f"{type(exc).__name__}: backtest execution failed"
            with suppress(Exception):
                await self._repository.transition(
                    run.id,
                    BacktestRunStatus.RUNNING,
                    BacktestRunStatus.FAILED,
                    self._clock(),
                    safe_message,
                )
            raise BacktestExecutionError(run.id, safe_message) from exc

    @staticmethod
    def _risk_dict(command: CreateBacktestCommand) -> dict[str, object]:
        return {
            key: (str(value) if isinstance(value, Decimal) else value)
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
            if isinstance(value, (Decimal, datetime)):
                return str(value)
            raise TypeError(f"unsupported request value: {type(value).__name__}")

        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=default)
        return hashlib.sha256(canonical.encode()).hexdigest()
