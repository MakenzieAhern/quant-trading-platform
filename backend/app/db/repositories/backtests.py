from collections.abc import Sequence
from datetime import datetime
from decimal import Decimal
from typing import Any, TypeVar
from uuid import UUID

from sqlalchemy import Select, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.backtests.decimal_policy import (
    canonical_decimal,
    validate_storage_decimal,
)
from app.application.backtests.models import (
    BacktestRun,
    BacktestRunStatus,
    Page,
    ResultSummary,
    require_transition,
)
from app.backtest.result import BacktestResult
from app.db.models.backtest import (
    BacktestFillModel,
    BacktestMetricsModel,
    BacktestOrderModel,
    BacktestOrderProposalModel,
    BacktestPortfolioSnapshotModel,
    BacktestRiskDecisionModel,
    BacktestRiskReservationModel,
    BacktestRunModel,
    BacktestSignalModel,
)
from app.domain.analytics import EquityPoint, PerformanceMetrics
from app.domain.risk import OrderProposal, RiskDecision, RiskReasonCode, RiskReservation
from app.domain.trading import (
    Fill,
    Order,
    OrderSide,
    OrderStatus,
    OrderType,
    PortfolioSnapshot,
    Position,
    Signal,
    SignalType,
)

ModelT = TypeVar("ModelT")


def _decimal_json(value: object) -> object:
    if isinstance(value, Decimal):
        return canonical_decimal(validate_storage_decimal(value, "JSONB Decimal"))
    return value


def _numeric(value: Decimal, field: str) -> Decimal:
    return validate_storage_decimal(value, field)


class SQLAlchemyBacktestRepository:
    """PostgreSQL implementation; application code depends only on its protocol."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, run: BacktestRun) -> BacktestRun:
        self._session.add(
            BacktestRunModel(
                id=run.id,
                status=run.status.value,
                strategy_id=run.strategy_id,
                symbol=run.symbol,
                dataset_id=run.dataset_id,
                created_at=run.created_at,
                started_at=run.started_at,
                completed_at=run.completed_at,
                config=self._config_json(run),
                error_message=run.error_message,
                client_request_id=run.client_request_id,
                request_hash=run.request_hash,
            )
        )
        try:
            await self._session.commit()
        except IntegrityError:
            await self._session.rollback()
            if run.client_request_id is not None:
                existing = await self.get_by_client_request_id(run.client_request_id)
                if existing is not None:
                    return existing
            raise
        return run

    async def get(self, run_id: UUID) -> BacktestRun | None:
        model = await self._session.scalar(
            select(BacktestRunModel)
            .where(BacktestRunModel.id == run_id)
            .execution_options(populate_existing=True)
        )
        return self._to_run(model) if model is not None else None

    async def get_by_client_request_id(self, value: str) -> BacktestRun | None:
        model = await self._session.scalar(
            select(BacktestRunModel).where(BacktestRunModel.client_request_id == value)
        )
        return self._to_run(model) if model is not None else None

    async def transition(
        self,
        run_id: UUID,
        expected: BacktestRunStatus,
        target: BacktestRunStatus,
        occurred_at: datetime,
        error_message: str | None = None,
    ) -> BacktestRun:
        require_transition(expected, target)
        async with self._session.begin():
            model = await self._session.scalar(
                select(BacktestRunModel).where(BacktestRunModel.id == run_id).with_for_update()
            )
            if model is None:
                raise LookupError(f"unknown backtest run: {run_id}")
            if model.status != expected.value:
                raise ValueError(f"backtest status is {model.status}, expected {expected.value}")
            model.status = target.value
            if target is BacktestRunStatus.RUNNING:
                model.started_at = occurred_at
            if target in {BacktestRunStatus.SUCCEEDED, BacktestRunStatus.FAILED}:
                model.completed_at = occurred_at
            model.error_message = error_message
        return self._to_run(model)

    async def persist_success(
        self, run_id: UUID, result: BacktestResult, completed_at: datetime
    ) -> BacktestRun:
        async with self._session.begin():
            run = await self._session.scalar(
                select(BacktestRunModel).where(BacktestRunModel.id == run_id).with_for_update()
            )
            if run is None:
                raise LookupError(f"unknown backtest run: {run_id}")
            require_transition(BacktestRunStatus(run.status), BacktestRunStatus.SUCCEEDED)
            await self._add_result(run_id, result)
            run.status = BacktestRunStatus.SUCCEEDED.value
            run.completed_at = completed_at
            run.error_message = None
        return self._to_run(run)

    async def list_runs(
        self,
        limit: int,
        offset: int,
        status: BacktestRunStatus | None = None,
        symbol: str | None = None,
    ) -> Page[BacktestRun]:
        filters: list[Any] = []
        if status is not None:
            filters.append(BacktestRunModel.status == status.value)
        if symbol is not None:
            filters.append(BacktestRunModel.symbol == symbol)
        total = await self._session.scalar(
            select(func.count()).select_from(BacktestRunModel).where(*filters)
        )
        rows = (
            await self._session.scalars(
                select(BacktestRunModel)
                .where(*filters)
                .order_by(BacktestRunModel.created_at.desc(), BacktestRunModel.id)
                .limit(limit)
                .offset(offset)
            )
        ).all()
        return Page(tuple(self._to_run(row) for row in rows), limit, offset, total or 0)

    async def get_result_summary(self, run_id: UUID) -> ResultSummary | None:
        metrics = await self._session.get(BacktestMetricsModel, run_id)
        if metrics is None:
            return None
        counts = []
        for model in (
            BacktestSignalModel,
            BacktestOrderProposalModel,
            BacktestRiskDecisionModel,
            BacktestOrderModel,
            BacktestFillModel,
            BacktestPortfolioSnapshotModel,
            BacktestRiskReservationModel,
        ):
            counts.append(
                await self._session.scalar(
                    select(func.count()).select_from(model).where(model.run_id == run_id)
                )
                or 0
            )
        bounds = (
            await self._session.execute(
                select(
                    func.min(BacktestPortfolioSnapshotModel.timestamp),
                    func.max(BacktestPortfolioSnapshotModel.timestamp),
                ).where(BacktestPortfolioSnapshotModel.run_id == run_id)
            )
        ).one()
        rejections = await self._session.scalar(
            select(func.count())
            .select_from(BacktestRiskDecisionModel)
            .where(
                BacktestRiskDecisionModel.run_id == run_id,
                BacktestRiskDecisionModel.approved.is_(False),
            )
        )
        return ResultSummary(
            metrics=self._to_metrics(metrics),
            signal_count=counts[0],
            proposal_count=counts[1],
            risk_decision_count=counts[2],
            risk_rejection_count=rejections or 0,
            order_count=counts[3],
            fill_count=counts[4],
            snapshot_count=counts[5],
            reservation_count=counts[6],
            start_time=bounds[0],
            end_time=bounds[1],
        )

    async def list_signals(self, run_id: UUID, limit: int, offset: int) -> Page[Signal]:
        rows, total = await self._page(BacktestSignalModel, run_id, limit, offset)
        return Page(
            tuple(
                Signal(
                    strategy_id=row.strategy_id,
                    symbol=row.symbol,
                    timestamp=row.timestamp,
                    signal_type=SignalType(row.signal_type),
                )
                for row in rows
            ),
            limit,
            offset,
            total,
        )

    async def list_proposals(self, run_id: UUID, limit: int, offset: int) -> Page[OrderProposal]:
        rows, total = await self._page(BacktestOrderProposalModel, run_id, limit, offset)
        return Page(
            tuple(
                OrderProposal(
                    proposal_id=row.proposal_id,
                    strategy_id=row.strategy_id,
                    symbol=row.symbol,
                    side=OrderSide(row.side),
                    order_type=OrderType(row.order_type),
                    quantity=row.quantity,
                    signal_timestamp=row.signal_timestamp,
                )
                for row in rows
            ),
            limit,
            offset,
            total,
        )

    async def list_risk_decisions(
        self, run_id: UUID, limit: int, offset: int
    ) -> Page[RiskDecision]:
        rows, total = await self._page(BacktestRiskDecisionModel, run_id, limit, offset)
        items = []
        for row in rows:
            values = {
                key: Decimal(value) if value is not None else None
                for key, value in row.diagnostics.items()
                if key != "risk_increasing"
            }
            items.append(
                RiskDecision(
                    proposal_id=row.proposal_id,
                    approved=row.approved,
                    reason_code=RiskReasonCode(row.reason_code),
                    message=row.message,
                    timestamp=row.timestamp,
                    risk_increasing=bool(row.diagnostics["risk_increasing"]),
                    **values,
                )
            )
        return Page(tuple(items), limit, offset, total)

    async def list_orders(self, run_id: UUID, limit: int, offset: int) -> Page[Order]:
        rows, total = await self._page(BacktestOrderModel, run_id, limit, offset)
        return Page(
            tuple(
                Order(
                    id=row.order_id,
                    strategy_id=row.strategy_id,
                    symbol=row.symbol,
                    side=OrderSide(row.side),
                    order_type=OrderType(row.order_type),
                    quantity=row.quantity,
                    price=row.price,
                    status=OrderStatus(row.status),
                    created_at=row.created_at,
                )
                for row in rows
            ),
            limit,
            offset,
            total,
        )

    async def list_fills(self, run_id: UUID, limit: int, offset: int) -> Page[Fill]:
        rows, total = await self._page(BacktestFillModel, run_id, limit, offset)
        return Page(
            tuple(
                Fill(
                    order_id=row.order_id,
                    strategy_id=row.strategy_id,
                    symbol=row.symbol,
                    side=OrderSide(row.side),
                    quantity=row.quantity,
                    price=row.price,
                    commission=row.commission,
                    timestamp=row.timestamp,
                )
                for row in rows
            ),
            limit,
            offset,
            total,
        )

    async def list_equity(self, run_id: UUID, limit: int, offset: int) -> Page[EquityPoint]:
        rows, total = await self._page(BacktestPortfolioSnapshotModel, run_id, limit, offset)
        return Page(
            tuple(
                EquityPoint(
                    timestamp=row.timestamp,
                    equity=row.equity,
                    cash=row.cash,
                    market_value=row.market_value,
                )
                for row in rows
            ),
            limit,
            offset,
            total,
        )

    async def list_snapshots(
        self, run_id: UUID, limit: int, offset: int
    ) -> Page[PortfolioSnapshot]:
        rows, total = await self._page(BacktestPortfolioSnapshotModel, run_id, limit, offset)
        return Page(
            tuple(
                PortfolioSnapshot(
                    timestamp=row.timestamp,
                    cash=row.cash,
                    positions=tuple(
                        Position(
                            symbol=position["symbol"],
                            quantity=Decimal(position["quantity"]),
                            average_price=Decimal(position["average_price"]),
                            market_price=Decimal(position["market_price"]),
                            unrealized_pnl=Decimal(position["unrealized_pnl"]),
                            realized_pnl=Decimal(position["realized_pnl"]),
                        )
                        for position in row.positions
                    ),
                    market_value=row.market_value,
                    equity=row.equity,
                    realized_pnl=row.realized_pnl,
                    unrealized_pnl=row.unrealized_pnl,
                    cumulative_commission=row.cumulative_commission,
                    drawdown=row.drawdown,
                )
                for row in rows
            ),
            limit,
            offset,
            total,
        )

    async def list_reservations(
        self, run_id: UUID, limit: int, offset: int
    ) -> Page[RiskReservation]:
        rows, total = await self._page(BacktestRiskReservationModel, run_id, limit, offset)
        return Page(
            tuple(
                RiskReservation(
                    proposal_id=row.proposal_id,
                    order_id=row.order_id,
                    symbol=row.symbol,
                    signed_quantity=row.signed_quantity,
                    cash_delta=row.cash_delta,
                    buying_power_consumed=row.buying_power_consumed,
                )
                for row in rows
            ),
            limit,
            offset,
            total,
        )

    async def _page(
        self, model: type[ModelT], run_id: UUID, limit: int, offset: int
    ) -> tuple[Sequence[ModelT], int]:
        run_column = model.run_id  # type: ignore[attr-defined]
        sequence_column = model.sequence  # type: ignore[attr-defined]
        total = await self._session.scalar(
            select(func.count()).select_from(model).where(run_column == run_id)
        )
        statement: Select[tuple[ModelT]] = (
            select(model)
            .where(run_column == run_id)
            .order_by(sequence_column)
            .limit(limit)
            .offset(offset)
        )
        rows = (await self._session.scalars(statement)).all()
        return rows, total or 0

    async def _add_result(self, run_id: UUID, result: BacktestResult) -> None:
        self._session.add_all(
            [
                BacktestSignalModel(
                    run_id=run_id,
                    sequence=index,
                    strategy_id=item.strategy_id,
                    symbol=item.symbol,
                    timestamp=item.timestamp,
                    signal_type=item.signal_type.value,
                )
                for index, item in enumerate(result.signals)
            ]
        )
        self._session.add_all(
            [
                BacktestOrderProposalModel(
                    run_id=run_id,
                    sequence=index,
                    proposal_id=item.proposal_id,
                    strategy_id=item.strategy_id,
                    symbol=item.symbol,
                    side=item.side.value,
                    order_type=item.order_type.value,
                    quantity=_numeric(item.quantity, "proposal.quantity"),
                    signal_timestamp=item.signal_timestamp,
                )
                for index, item in enumerate(result.order_proposals)
            ]
        )
        await self._session.flush()
        self._session.add_all(
            [
                BacktestRiskDecisionModel(
                    run_id=run_id,
                    sequence=index,
                    proposal_id=item.proposal_id,
                    approved=item.approved,
                    reason_code=item.reason_code.value,
                    message=item.message,
                    timestamp=item.timestamp,
                    diagnostics={
                        key: _decimal_json(value)
                        for key, value in item.model_dump().items()
                        if key
                        not in {"proposal_id", "approved", "reason_code", "message", "timestamp"}
                    },
                )
                for index, item in enumerate(result.risk_decisions)
            ]
        )
        self._session.add_all(
            [
                BacktestOrderModel(
                    run_id=run_id,
                    sequence=index,
                    order_id=item.id,
                    proposal_id=item.id,
                    strategy_id=item.strategy_id,
                    symbol=item.symbol,
                    side=item.side.value,
                    order_type=item.order_type.value,
                    quantity=_numeric(item.quantity, "order.quantity"),
                    price=(_numeric(item.price, "order.price") if item.price is not None else None),
                    status=item.status.value,
                    created_at=item.created_at,
                    submitted_at=None,
                    accepted_at=None,
                )
                for index, item in enumerate(result.orders)
            ]
        )
        await self._session.flush()
        self._session.add_all(
            [
                BacktestFillModel(
                    run_id=run_id,
                    sequence=index,
                    order_id=item.order_id,
                    strategy_id=item.strategy_id,
                    symbol=item.symbol,
                    side=item.side.value,
                    quantity=_numeric(item.quantity, "fill.quantity"),
                    price=_numeric(item.price, "fill.price"),
                    commission=_numeric(item.commission, "fill.commission"),
                    timestamp=item.timestamp,
                )
                for index, item in enumerate(result.fills)
            ]
        )
        self._session.add_all(
            [
                BacktestPortfolioSnapshotModel(
                    run_id=run_id,
                    sequence=index,
                    timestamp=item.timestamp,
                    cash=_numeric(item.cash, "snapshot.cash"),
                    market_value=_numeric(item.market_value, "snapshot.market_value"),
                    equity=_numeric(item.equity, "snapshot.equity"),
                    realized_pnl=_numeric(item.realized_pnl, "snapshot.realized_pnl"),
                    unrealized_pnl=_numeric(item.unrealized_pnl, "snapshot.unrealized_pnl"),
                    cumulative_commission=_numeric(
                        item.cumulative_commission, "snapshot.cumulative_commission"
                    ),
                    drawdown=_numeric(item.drawdown, "snapshot.drawdown"),
                    positions=[
                        {key: _decimal_json(value) for key, value in position.model_dump().items()}
                        for position in item.positions
                    ],
                )
                for index, item in enumerate(result.portfolio_snapshots)
            ]
        )
        metrics = result.performance_metrics
        self._session.add(
            BacktestMetricsModel(
                run_id=run_id,
                initial_equity=_numeric(metrics.initial_equity, "metrics.initial_equity"),
                final_equity=_numeric(metrics.final_equity, "metrics.final_equity"),
                total_return=_numeric(metrics.total_return, "metrics.total_return"),
                cagr=_numeric(metrics.cagr, "metrics.cagr") if metrics.cagr is not None else None,
                max_drawdown=_numeric(metrics.max_drawdown, "metrics.max_drawdown"),
                sharpe_ratio=(
                    _numeric(metrics.sharpe_ratio, "metrics.sharpe_ratio")
                    if metrics.sharpe_ratio is not None
                    else None
                ),
                sortino_ratio=(
                    _numeric(metrics.sortino_ratio, "metrics.sortino_ratio")
                    if metrics.sortino_ratio is not None
                    else None
                ),
                total_commission=_numeric(metrics.total_commission, "metrics.total_commission"),
                number_of_fills=metrics.number_of_fills,
            )
        )
        self._session.add_all(
            [
                BacktestRiskReservationModel(
                    run_id=run_id,
                    sequence=index,
                    proposal_id=item.proposal_id,
                    order_id=item.order_id,
                    symbol=item.symbol,
                    signed_quantity=_numeric(item.signed_quantity, "reservation.signed_quantity"),
                    cash_delta=_numeric(item.cash_delta, "reservation.cash_delta"),
                    buying_power_consumed=_numeric(
                        item.buying_power_consumed, "reservation.buying_power_consumed"
                    ),
                )
                for index, item in enumerate(result.active_risk_reservations)
            ]
        )

    @staticmethod
    def _config_json(run: BacktestRun) -> dict[str, Any]:
        return {
            "strategy_type": run.strategy_type,
            "strategy_parameters": {
                key: _decimal_json(value) for key, value in run.strategy_parameters.items()
            },
            "initial_cash": canonical_decimal(
                validate_storage_decimal(run.initial_cash, "config.initial_cash")
            ),
            "default_order_quantity": canonical_decimal(
                validate_storage_decimal(
                    run.default_order_quantity, "config.default_order_quantity"
                )
            ),
            "risk": run.risk,
            "start": run.start.isoformat() if run.start is not None else None,
            "end": run.end.isoformat() if run.end is not None else None,
        }

    @staticmethod
    def _to_run(model: BacktestRunModel) -> BacktestRun:
        config = model.config
        parameters = {
            key: Decimal(value) if key in {"oversold", "overbought"} else value
            for key, value in config["strategy_parameters"].items()
        }
        return BacktestRun(
            id=model.id,
            status=BacktestRunStatus(model.status),
            strategy_id=model.strategy_id,
            strategy_type=str(config["strategy_type"]),
            strategy_parameters=parameters,
            symbol=model.symbol,
            dataset_id=model.dataset_id,
            created_at=model.created_at,
            started_at=model.started_at,
            completed_at=model.completed_at,
            initial_cash=Decimal(config["initial_cash"]),
            default_order_quantity=Decimal(config["default_order_quantity"]),
            risk=dict(config["risk"]),
            start=datetime.fromisoformat(config["start"]) if config["start"] else None,
            end=datetime.fromisoformat(config["end"]) if config["end"] else None,
            error_message=model.error_message,
            client_request_id=model.client_request_id,
            request_hash=model.request_hash,
        )

    @staticmethod
    def _to_metrics(model: BacktestMetricsModel) -> PerformanceMetrics:
        return PerformanceMetrics(
            initial_equity=model.initial_equity,
            final_equity=model.final_equity,
            total_return=model.total_return,
            cagr=model.cagr,
            max_drawdown=model.max_drawdown,
            sharpe_ratio=model.sharpe_ratio,
            sortino_ratio=model.sortino_ratio,
            total_commission=model.total_commission,
            number_of_fills=model.number_of_fills,
        )
