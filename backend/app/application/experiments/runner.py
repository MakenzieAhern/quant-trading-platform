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
from app.domain.markets.calendar import TradingCalendar
from app.domain.risk import RiskConfig
from app.domain.trading import PortfolioSnapshot
from app.research.analytics import analyze_research_period
from app.research.costs import EffectiveDatedAShareCommission
from app.research.engine import (
    ResearchExecutionDelta,
    ResearchExecutionEngine,
    UnexplainedReferenceAdjustment,
)
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
        self.last_target: PortfolioTarget | None = None

    def target_for_completed_session(
        self,
        session: ResearchSession,
        available_equity: Decimal,
    ) -> PortfolioTarget | None:
        # Candidate selection only: execution still receives all observations and actions.
        self.last_target = None
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
        self.last_target = PortfolioTarget(
            positions=tuple(positions), residual_cash=available_equity - invested
        )
        return self.last_target

    def reset(self) -> None:
        super().reset()
        self.last_target = None


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
    strategy = ExploratoryStrategy(request)
    execution_calendar = (
        TradingCalendar(
            market=data.calendar.market,
            sessions=(*data.calendar.sessions, data.next_session),
        )
        if data.next_session is not None
        else data.calendar
    )
    engine = ResearchExecutionEngine(
        strategy,
        initial_cash=request.initial_cash,
        commission_model=commission,
        calendar=execution_calendar,
        risk_config=RiskConfig(
            enforce_buying_power=True,
            max_leverage=Decimal(1),
            max_drawdown=request.risk.max_drawdown,
        ),
    )
    total = len(data.calendar_days)
    progress("EXECUTING", 0, total)
    last_delta: ResearchExecutionDelta | None = None
    for completed, session in enumerate(data.sessions(), start=1):
        check_cancelled()
        try:
            last_delta = engine.process_session(session)
        except UnexplainedReferenceAdjustment as exc:
            raise ExperimentInputError(exc.code) from exc
        if completed % 10 == 0 or completed == total:
            progress("EXECUTING", completed, total)
    check_cancelled()
    assert last_delta is not None
    plan = build_plan_preview(
        request,
        registered["sha256"],
        registered["mode"],
        last_delta,
        last_delta.target,
        data.next_session.session_date if data.next_session is not None else None,
        total,
    )
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
            "result_schema_version": 3,
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
            "simulation_plan": plan,
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


def build_plan_preview(
    request: CreateExperimentRequest,
    dataset_sha256: str,
    mode: str,
    delta: ResearchExecutionDelta,
    target: PortfolioTarget | None,
    next_session: date | None,
    completed_sessions: int,
    *,
    legacy_checkpoint: bool = False,
) -> dict[str, Any]:
    """Describe the existing engine's final-session account and OMS decisions."""

    snapshot = delta.snapshot
    as_of = delta.session.trading_date
    # V1 replay only: reproduce already persisted projections without rewriting history.
    if (
        not legacy_checkpoint
        and snapshot is not None
        and snapshot.timestamp.astimezone(TRADING_ZONE).date() != as_of
    ):
        snapshot = None
    status = (
        "ACCOUNT_SNAPSHOT_UNAVAILABLE"
        if snapshot is None
        else "NEXT_SESSION_UNAVAILABLE"
        if next_session is None
        else "INSUFFICIENT_WARMUP"
        if completed_sessions < 253
        else "NOT_REBALANCE_SESSION"
        if target is None
        else "NO_ELIGIBLE_CANDIDATES"
        if not target.positions and not snapshot.positions
        else "SIMULATION_PREVIEW"
    )
    common = {
        "status": status,
        "mode": mode,
        "as_of_trading_date": as_of.isoformat(),
        "next_accepted_session": next_session.isoformat() if next_session else None,
        "dataset_sha256": dataset_sha256,
        "configuration_sha256": canonical_sha256(json_value(request.model_dump())),
        "strategy_id": request.strategy_id,
        "strategy_version": "1",
        "simulation_only": True,
        "submitted_to_account": False,
        "price_basis": "COMPLETED_RAW_CLOSE_ESTIMATE_NOT_NEXT_OPEN",
        "account_mode": "EXPLORATORY_REPLAY" if mode != "synthetic_demo" else "SYNTHETIC_DEMO",
        "not_today_advice": True,
        "data_snapshot_sha256": canonical_sha256(
            {
                "dataset_sha256": dataset_sha256,
                "as_of": as_of.isoformat(),
                "observed_raw_closes": [
                    (str(bar.security_id), canonical_decimal(bar.raw_close))
                    for bar in sorted(delta.session.bars, key=lambda item: str(item.security_id))
                ],
            }
        ),
    }
    if not legacy_checkpoint:
        common["account_snapshot_trading_date"] = (
            snapshot.timestamp.astimezone(TRADING_ZONE).date().isoformat() if snapshot else None
        )
    if snapshot is None:
        return {**common, "account": None, "candidates": [], "estimated_cash_required": None}

    account = _holdings_row(0, snapshot)
    account_view = {
        "cash": account["cash"],
        "equity": account["equity"],
        "positions": account["positions"],
        "snapshot_sha256": canonical_sha256(account),
    }
    if status != "SIMULATION_PREVIEW":
        return {
            **common,
            "account": account_view,
            "candidates": [],
            "estimated_cash_required": None,
            "risk_rejections": 0,
        }
    positions = {_security_id(item.symbol): item for item in snapshot.positions}
    targets = {str(item.security_id): item for item in target.positions} if target else {}
    proposals = {_security_id(item.symbol): item for item in delta.proposals}
    decisions = {item.proposal_id: item for item in delta.decisions}
    prices = {str(item.security_id): item.raw_close for item in delta.session.bars}
    cash_required = Decimal(0)
    cash_known = True
    candidates = []
    for sid in sorted(positions.keys() | targets.keys()):
        held = positions[sid].quantity if sid in positions else Decimal(0)
        desired = targets[sid].quantity if sid in targets else Decimal(0)
        proposal = proposals.get(sid)
        decision = decisions.get(proposal.proposal_id) if proposal else None
        side = (
            proposal.side.value
            if proposal
            else ("BUY" if desired > held else "SELL" if desired < held else "HOLD")
        )
        if proposal and decision and decision.approved and side == "BUY":
            if decision.reference_price is None or decision.estimated_transaction_cost is None:
                cash_known = False
            else:
                cash_required += (
                    proposal.quantity * decision.reference_price
                    + decision.estimated_transaction_cost
                )
        candidates.append(
            json_value(
                {
                    "security_id": sid,
                    "target_weight": targets[sid].target_weight if sid in targets else Decimal(0),
                    "held_quantity": held,
                    "target_quantity": desired,
                    "desired_change_quantity": abs(desired - held),
                    "proposed_quantity": proposal.quantity if proposal else Decimal(0),
                    "side": side,
                    "reference_raw_close": prices.get(sid),
                    "trigger_reason": "TOP_DECILE_MOMENTUM_LOW_VOL"
                    if sid in targets
                    else "EXITED_STRATEGY_TARGET",
                    "risk_approved": decision.approved if decision else None,
                    "risk_reason_code": decision.reason_code.value
                    if decision
                    else "NO_CHANGE"
                    if desired == held
                    else "PROPOSAL_NOT_CREATED",
                }
            )
        )
    return {
        **common,
        "account": account_view,
        "candidates": candidates,
        "estimated_cash_required": canonical_decimal(cash_required)
        if cash_known and status == "SIMULATION_PREVIEW"
        else None,
        "risk_rejections": sum(item.approved is False for item in delta.decisions),
    }


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
