from datetime import datetime
from typing import Protocol
from uuid import UUID

from app.application.backtests.models import (
    BacktestRun,
    BacktestRunStatus,
    Page,
    ResultSummary,
)
from app.backtest.result import BacktestResult
from app.domain.analytics import EquityPoint
from app.domain.risk import OrderProposal, RiskDecision, RiskReservation
from app.domain.trading import Fill, Order, PortfolioSnapshot, Signal


class BacktestRepository(Protocol):
    async def create(self, run: BacktestRun) -> BacktestRun: ...

    async def get(self, run_id: UUID) -> BacktestRun | None: ...

    async def get_by_client_request_id(self, value: str) -> BacktestRun | None: ...

    async def transition(
        self,
        run_id: UUID,
        expected: BacktestRunStatus,
        target: BacktestRunStatus,
        occurred_at: datetime,
        error_message: str | None = None,
    ) -> BacktestRun: ...

    async def persist_success(
        self, run_id: UUID, result: BacktestResult, completed_at: datetime
    ) -> BacktestRun: ...

    async def list_runs(
        self,
        limit: int,
        offset: int,
        status: BacktestRunStatus | None = None,
        symbol: str | None = None,
    ) -> Page[BacktestRun]: ...

    async def get_result_summary(self, run_id: UUID) -> ResultSummary | None: ...

    async def list_signals(self, run_id: UUID, limit: int, offset: int) -> Page[Signal]: ...

    async def list_proposals(
        self, run_id: UUID, limit: int, offset: int
    ) -> Page[OrderProposal]: ...

    async def list_risk_decisions(
        self, run_id: UUID, limit: int, offset: int
    ) -> Page[RiskDecision]: ...

    async def list_orders(self, run_id: UUID, limit: int, offset: int) -> Page[Order]: ...

    async def list_fills(self, run_id: UUID, limit: int, offset: int) -> Page[Fill]: ...

    async def list_equity(self, run_id: UUID, limit: int, offset: int) -> Page[EquityPoint]: ...

    async def list_snapshots(
        self, run_id: UUID, limit: int, offset: int
    ) -> Page[PortfolioSnapshot]: ...

    async def list_reservations(
        self, run_id: UUID, limit: int, offset: int
    ) -> Page[RiskReservation]: ...
