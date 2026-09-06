"""Opt-in synthetic baseline. Run only against the disposable test database."""

import asyncio
import json
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from time import perf_counter
from uuid import uuid4

from httpx import ASGITransport, AsyncClient

from app.application.backtests.models import BacktestRun, BacktestRunStatus
from app.backtest import BacktestConfig, BacktestEngine
from app.data.providers import Timeframe
from app.db.repositories import SQLAlchemyBacktestRepository
from app.db.session import SessionFactory
from app.domain.market import Bar
from app.main import app
from app.strategies import MovingAverageCrossoverStrategy


class SyntheticProvider:
    def __init__(self, count: int) -> None:
        self.bars = tuple(
            Bar(
                symbol="DEMO",
                timestamp=datetime(2000, 1, 1, tzinfo=UTC) + timedelta(days=i),
                open=Decimal(100 + i % 20),
                high=Decimal(121),
                low=Decimal(99),
                close=Decimal(100 + i % 20),
                volume=Decimal(1000),
            )
            for i in range(count)
        )

    def get_historical_bars(
        self,
        symbol: str,
        start: datetime | None = None,
        end: datetime | None = None,
        timeframe: Timeframe = Timeframe.DAY_1,
    ) -> tuple[Bar, ...]:
        return self.bars


async def main() -> None:
    for count, strategies in ((1000, 1), (10000, 1), (10000, 2)):
        provider = SyntheticProvider(count)
        engine = BacktestEngine(
            provider,
            tuple(
                MovingAverageCrossoverStrategy(f"baseline-{i}", "DEMO", 2 + i, 5 + i)
                for i in range(strategies)
            ),
            BacktestConfig(initial_cash=Decimal("1000000")),
        )
        before = perf_counter()
        result = engine.run("DEMO")
        execution = perf_counter() - before
        now = datetime.now(UTC)
        run = BacktestRun(
            uuid4(),
            BacktestRunStatus.CREATED,
            "baseline",
            "moving_average_crossover",
            {"short_period": 2, "long_period": 5},
            "DEMO",
            "synthetic-baseline",
            now,
            None,
            None,
            Decimal("1000000"),
            Decimal(1),
            {},
            None,
            None,
            None,
            None,
            None,
        )
        async with SessionFactory() as db:
            repository = SQLAlchemyBacktestRepository(db)
            await repository.create(run)
            await repository.transition(
                run.id, BacktestRunStatus.CREATED, BacktestRunStatus.RUNNING, now
            )
            before = perf_counter()
            await repository.persist_success(run.id, result, now)
            persistence = perf_counter() - before
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            durations = {}
            for label, path in (
                ("history", "/api/backtests"),
                ("detail", f"/api/backtests/{run.id}"),
            ):
                before = perf_counter()
                response = await client.get(path)
                response.raise_for_status()
                durations[label] = round(perf_counter() - before, 6)
        print(
            json.dumps(
                {
                    "bars": count,
                    "strategies": strategies,
                    "fills": len(result.fills),
                    "backtest_seconds": round(execution, 6),
                    "persistence_seconds": round(persistence, 6),
                    **durations,
                }
            )
        )


if __name__ == "__main__":
    asyncio.run(main())
