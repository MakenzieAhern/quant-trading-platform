"""Finite, cancellable experiments over the existing financial engine."""

from collections import Counter
from collections.abc import Callable
from dataclasses import asdict, dataclass, replace
from datetime import date, datetime
from decimal import ROUND_FLOOR, Decimal
from enum import Enum
from pathlib import Path
from threading import Event
from typing import Any
from uuid import UUID
from zoneinfo import ZoneInfo

from app.application.backtests.decimal_policy import canonical_decimal
from app.application.experiments.data import (
    DEMO_ID,
    ExperimentDatasetRegistry,
    ExperimentInputError,
    load_experiment_dataset,
)
from app.application.experiments.models import CreateExperimentRequest
from app.data.catalog.checksums import canonical_sha256, sha256_file
from app.data.full_dataset import FullDataset
from app.domain.risk import RiskConfig
from app.domain.trading import PortfolioSnapshot
from app.research.analytics import analyze_research_period
from app.research.costs import EffectiveDatedAShareCommission
from app.research.engine import ResearchExecutionEngine
from app.research.models import PortfolioTarget, ResearchSession
from app.research.strategy import ChinaAMomentumLowVolResearchStrategy
from app.strategies.research import ChinaAMomentumLowVolConfig

TRADING_ZONE = ZoneInfo("Asia/Shanghai")


def json_value(value: Any) -> Any:
    if isinstance(value, Decimal):
        return canonical_decimal(value)
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, dict):
        return {key: json_value(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [json_value(item) for item in value]
    return value


class ExperimentCancelled(Exception):
    pass


class ExploratoryStrategy(ChinaAMomentumLowVolResearchStrategy):
    def __init__(self, request: CreateExperimentRequest) -> None:
        super().__init__(
            ChinaAMomentumLowVolConfig(**request.strategy.model_dump()),
            active_from=request.start_date,
        )
        self.universe = request.universe
        self.max_weight = request.risk.max_position_weight

    def target_for_completed_session(
        self,
        session: ResearchSession,
        available_equity: Decimal,
    ) -> PortfolioTarget | None:
        # Candidate selection only: execution still receives all observations and actions.
        selected_session = session
        if self.universe != "ALL":
            prefix = f"CN-A:{self.universe}:"
            selected_session = replace(
                session,
                bars=tuple(b for b in session.bars if str(b.security_id).startswith(prefix)),
                feature_only_observations=tuple(
                    b
                    for b in session.feature_only_observations
                    if str(b.security_id).startswith(prefix)
                ),
            )
        target = super().target_for_completed_session(selected_session, available_equity)
        if target is None:
            return None
        lots = dict(session.buy_lot_sizes)
        positions = []
        for item in target.positions:
            weight = min(item.target_weight, self.max_weight)
            lot = Decimal(lots[item.security_id])
            quantity = (available_equity * weight / (item.reference_price * lot)).to_integral_value(
                rounding=ROUND_FLOOR
            ) * lot
            positions.append(replace(item, target_weight=weight, quantity=quantity))
        invested = sum((p.quantity * p.reference_price for p in positions), Decimal(0))
        return PortfolioTarget(
            positions=tuple(positions), residual_cash=available_equity - invested
        )


@dataclass
class ExperimentOutput:
    summary: dict[str, Any]
    rows: dict[str, list[dict[str, Any]]]


def run_experiment(
    registry: ExperimentDatasetRegistry,
    request: CreateExperimentRequest,
    expected_sha256: str,
    cancelled: Event,
    progress: Callable[[str, int, int | None], None],
) -> ExperimentOutput:
    def check_cancelled() -> None:
        if cancelled.is_set():
            raise ExperimentCancelled

    check_cancelled()
    implementation_sha256 = _implementation_checksum()
    registered = registry.resolve(request.dataset_id)
    if registered["sha256"] != expected_sha256:
        raise ExperimentInputError("DATASET_CHANGED_SINCE_SUBMISSION")
    progress("VERIFYING_DATA", 0, None)
    check_cancelled()
    data = load_experiment_dataset(
        registry, request.dataset_id, request.start_date, request.end_date
    )
    check_cancelled()
    if not any(request.start_date <= day <= request.end_date for day in data.calendar_days):
        raise ExperimentInputError("NO_TRADING_SESSIONS_IN_RANGE")
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
    engine = ResearchExecutionEngine(
        ExploratoryStrategy(request),
        initial_cash=request.initial_cash,
        commission_model=commission,
        calendar=data.calendar,
        risk_config=RiskConfig(
            enforce_buying_power=True,
            max_leverage=Decimal(1),
            max_drawdown=request.risk.max_drawdown,
        ),
    )
    total = len(data.calendar_days)
    progress("EXECUTING", 0, total)
    for completed, session in enumerate(data.sessions(), start=1):
        check_cancelled()
        engine.process_session(session)
        if completed % 10 == 0 or completed == total:
            progress("EXECUTING", completed, total)
    check_cancelled()
    result = engine.finish()
    snapshots = tuple(
        s for s in result.snapshots if request.start_date <= s.timestamp.date() <= request.end_date
    )
    dates = tuple(s.timestamp.date() for s in snapshots)
    equity = tuple(s.equity for s in snapshots)
    benchmark = tuple(
        request.initial_cash
        * data.benchmark[day.isoformat()]
        / data.benchmark[dates[0].isoformat()]
        for day in dates
    )
    costs = sum((f.commission for f in result.fills), Decimal(0))
    traded_notional = sum((f.quantity * f.price for f in result.fills), Decimal(0))
    mean_equity = sum(equity, Decimal(0)) / Decimal(len(equity))
    analysis = analyze_research_period(
        equity=equity,
        benchmark_equity=benchmark,
        transaction_costs=costs,
        turnover=traded_notional / mean_equity,
    )
    metrics = json_value(asdict(analysis))
    metrics["number_of_trades"] = len(result.fills)
    metrics["number_of_fills"] = len(result.fills)
    reasons = Counter(reason for _, reason in result.execution_checks)
    reasons.update(d.reason_code.value for d in result.decisions if not d.approved)
    rows: dict[str, list[dict[str, Any]]] = {
        "holdings": [_holdings_row(i, snapshot) for i, snapshot in enumerate(snapshots)],
        "equity": [
            json_value(
                {
                    "sequence": i,
                    "trading_date": day,
                    "equity": s.equity,
                    "benchmark": benchmark[i],
                    "drawdown": s.drawdown,
                }
            )
            for i, (day, s) in enumerate(zip(dates, snapshots, strict=True))
        ],
        "trades": [
            json_value(
                {
                    "sequence": i,
                    "order_id": f.order_id,
                    "security_id": _security_id(f.symbol),
                    "side": f.side,
                    "quantity": f.quantity,
                    "price": f.price,
                    "transaction_cost": f.commission,
                    "timestamp": f.timestamp,
                    "trading_date": f.timestamp.astimezone(TRADING_ZONE).date(),
                }
            )
            for i, f in enumerate(result.fills)
        ],
        "decisions": [
            json_value(
                {
                    "sequence": i,
                    "proposal_id": d.proposal_id,
                    "security_id": _security_id(result.proposals[i].symbol),
                    "approved": d.approved,
                    "reason_code": d.reason_code,
                    "message": d.message,
                    "timestamp": d.timestamp,
                    "trading_date": d.timestamp.astimezone(TRADING_ZONE).date(),
                }
            )
            for i, d in enumerate(result.decisions)
        ],
    }
    limitations = [
        "EXPLORATORY_NOT_UNSEEN_EVIDENCE",
        "NO_RETURN_GUARANTEE",
        "DAILY_BAR_NEXT_SESSION_EXECUTION",
        "253_SESSION_WARMUP",
        "POSITION_WEIGHT_IS_REBALANCE_TARGET_NOT_INTRADAY_GUARANTEE",
        "DRAWDOWN_LIMIT_REJECTS_NEW_RISK_NOT_AUTOMATIC_LIQUIDATION",
        "TRADE_COUNT_IS_EXECUTED_FILLS",
    ]
    if request.dataset_id == DEMO_ID:
        limitations.append("SYNTHETIC_DEMO_NOT_MARKET_OR_RESEARCH_EVIDENCE")
    if not result.fills:
        limitations.append("NO_EXECUTED_TRADES_CHECK_WARMUP_LOTS_AND_RISK")
    return ExperimentOutput(
        summary={
            "result_schema_version": 2,
            "available_collections": ["equity", "trades", "decisions", "holdings"],
            "mode": registered["mode"],
            "metrics": metrics,
            "limitations": limitations,
            "execution": {
                "proposals": len(result.proposals),
                "approved_decisions": sum(d.approved for d in result.decisions),
                "orders": len(result.orders),
                "fills": len(result.fills),
                "reason_counts": dict(sorted(reasons.items())),
            },
            "date_start": dates[0].isoformat(),
            "date_end": dates[-1].isoformat(),
            "benchmark_id": registered["benchmark_id"],
            "provenance": (
                {
                    "provider": data.manifest.provider,
                    "provider_version": data.manifest.provider_version,
                    "retrieval_timestamp": data.manifest.retrieval_timestamp.isoformat(),
                    "market_rule_version": data.manifest.rule_version,
                    "adjustment_method": data.manifest.adjustment_method,
                    "source_lineage": list(data.manifest.source_lineage),
                    "dataset_known_limitations": list(data.manifest.known_limitations),
                }
                if isinstance(data, FullDataset)
                else {
                    "provider": "DETERMINISTIC_SYNTHETIC_GENERATOR",
                    "provider_version": "cn-a-exploration-demo-v1",
                    "retrieval_timestamp": None,
                    "market_rule_version": "SYNTHETIC_SCENARIO_RULES",
                    "adjustment_method": "SYNTHETIC_UNADJUSTED_PRICES",
                    "source_lineage": ["SYNTHETIC_DEMO_NOT_MARKET_OR_RESEARCH_EVIDENCE"],
                    "dataset_known_limitations": ["SYNTHETIC_DEMO_NOT_MARKET_OR_RESEARCH_EVIDENCE"],
                }
            ),
            "implementation_sha256": implementation_sha256,
            "strategy_version": "1",
            "execution_model": {
                "convention": result.execution_convention,
                "fill_price": "NEXT_SESSION_RAW_OPEN",
                "additional_slippage_basis_points": "0",
                "merger_policy": result.merger_policy,
                "zero_whole_share_policy": result.zero_whole_share_policy,
                "partial_surrender_policy": result.partial_surrender_policy,
                "partial_surrender_fraction_policy": result.partial_surrender_fraction_policy,
                "partial_surrender_boundary_policy": result.partial_surrender_boundary_policy,
                "pass_through_policy": result.pass_through_policy,
                "consolidation_policy": result.consolidation_policy,
            },
            "effective_transaction_cost_schedules": [
                json_value(schedule.model_dump()) for schedule in commission.schedules
            ],
            "effective_risk_limits": {
                **json_value(request.risk.model_dump()),
                "enforce_buying_power": True,
                "max_leverage": "1",
                "long_only": True,
                "position_weight_applies_to": "REBALANCE_TARGET",
            },
            "analytics_definitions": {
                "turnover": "GROSS_TRADED_NOTIONAL_OVER_MEAN_SESSION_EQUITY",
                "number_of_trades": "EXECUTED_FILLS",
                "holdings_market_value": "POSITIONS_PLUS_PENDING_CORPORATE_ACTION_CARRYING_VALUE",
                "holdings_realized_pnl": "TRADING_ONLY_SEPARATE_FROM_CORPORATE_ACTION_REALIZED_PNL",
            },
        },
        rows=rows,
    )


def _security_id(symbol: str) -> str:
    number, exchange = symbol.split(".")
    return f"CN-A:{exchange}:{number}"


def _holdings_row(sequence: int, snapshot: PortfolioSnapshot) -> dict[str, Any]:
    result: dict[str, Any] = json_value(
        {
            "sequence": sequence,
            "trading_date": snapshot.timestamp.astimezone(TRADING_ZONE).date(),
            "timestamp": snapshot.timestamp,
            "cash": snapshot.cash,
            "equity": snapshot.equity,
            "market_value": snapshot.market_value,
            "realized_pnl": snapshot.realized_pnl,
            "corporate_action_realized_pnl": snapshot.corporate_action_realized_pnl,
            "total_pnl": snapshot.total_pnl,
            "unrealized_pnl": snapshot.unrealized_pnl,
            "cumulative_commission": snapshot.cumulative_commission,
            "pending_corporate_action_value": sum(
                (
                    item.carrying_value
                    for item in (*snapshot.pending_demergers, *snapshot.pending_mergers)
                ),
                Decimal(0),
            ),
            "positions": [
                {
                    "security_id": _security_id(position.symbol),
                    "quantity": position.quantity,
                    "average_price": position.average_price,
                    "market_price": position.market_price,
                    "market_value": position.quantity * position.market_price,
                    "weight": (position.quantity * position.market_price / snapshot.equity)
                    if snapshot.equity > 0
                    else None,
                }
                for position in snapshot.positions
                if position.quantity != 0
            ],
        }
    )
    return result


def _implementation_checksum() -> str:
    root = Path(__file__).resolve().parents[2]
    return canonical_sha256(
        {
            path.relative_to(root).as_posix(): sha256_file(path)
            for path in sorted(root.rglob("*.py"))
        }
    )
