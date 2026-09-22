"""Run the fixed S0-S4 family against the immutable full A-share dataset."""

import argparse
import json
import subprocess
from collections import Counter, defaultdict, deque
from dataclasses import asdict
from datetime import date
from decimal import Decimal, localcontext
from itertools import pairwise
from pathlib import Path
from uuid import UUID

from app.data.catalog import load_manifest
from app.data.catalog.checksums import canonical_json_bytes, canonical_sha256, sha256_file
from app.data.catalog.freeze import MARKER, write_immutable
from app.data.full_dataset import FullDataset
from app.data.full_dataset import _raw_paths as _raw_paths
from app.domain.markets import (
    SecurityId,
)
from app.domain.trading import OrderSide
from app.research.analytics import ClosedTrade, analyze_research_period
from app.research.engine import ResearchExecutionEngine
from app.research.models import ResearchPeriodKind
from app.research.splits import INITIAL_SPLIT, TemporalPeriod
from app.research.strategy import ChinaAMomentumLowVolResearchStrategy

DATASET_ID = "cn-a-research-20100101-20251231-v1"
INITIAL_CASH = Decimal("100000000")
MINIMUM_AMOUNT = Decimal("10000000")
CANDIDATES = {
    "S2": ("cn_a_mom_12_1_v1", ("MOM_12_1",)),
    "S3": ("cn_a_trend_low_vol_v1", ("TREND_120", "LOW_VOL")),
    "S4": (
        "cn_a_cross_sectional_momentum_low_vol_v1",
        ("MOM_12_1", "TREND_120", "LOW_VOL"),
    ),
}
IMPLEMENTATION_FILES = (
    "backend/app/data/full_dataset.py",
    "backend/app/portfolio/engine.py",
    "backend/app/research/engine.py",
    "backend/app/research/models.py",
    "backend/app/research/portfolio_construction.py",
    "backend/app/research/strategy.py",
    "backend/scripts/run_research.py",
)
ZERO = Decimal(0)
ONE = Decimal(1)


def _plain(value):
    if isinstance(value, Decimal):
        return format(value, "f")
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, SecurityId):
        return str(value)
    if isinstance(value, UUID):
        return str(value)
    raise TypeError(type(value).__name__)


def plain(value):
    return json.loads(json.dumps(value, default=_plain))


def stable_result(result: dict) -> dict:
    for sequence, trade in enumerate(result.get("trades", [])):
        trade.pop("order_id", None)
        trade["sequence"] = sequence
    return result


def implementation_sha256(repository: Path) -> str:
    return canonical_sha256({path: sha256_file(repository / path) for path in IMPLEMENTATION_FILES})


def load_candidate_freeze(path: Path, dataset_sha256: str) -> dict:
    record = json.loads(path.read_bytes())
    digest = record.pop("freeze_record_sha256")
    if (
        canonical_sha256(record) != digest
        or record["status"] != "FROZEN"
        or record["dataset_id"] != DATASET_ID
        or record["dataset_sha256"] != dataset_sha256
        or record["validation_period"] != {"start": "2018-01-01", "end": "2021-12-31"}
        or record["candidate_order"] != ["S0", "S1", "S2", "S3", "S4"]
        or record["selection_pool"] != ["S2", "S3", "S4"]
        or any(
            record["candidates"][name]["strategy_id"] != strategy_id
            or tuple(record["candidates"][name]["config"]["factor_names"]) != factor_names
            for name, (strategy_id, factor_names) in CANDIDATES.items()
        )
    ):
        raise ValueError("CANDIDATE_FREEZE_CHANGED")
    record["freeze_record_sha256"] = digest
    return record


def load_methodology_freeze(path: Path, dataset_sha256: str) -> dict:
    record = json.loads(path.read_bytes())
    digest = record.pop("freeze_record_sha256")
    candidate = record["selected_candidate"]
    strategy_id, factor_names = CANDIDATES[candidate]
    if (
        canonical_sha256(record) != digest
        or record["status"] != "FROZEN"
        or record["freeze_id"] != "FROZEN_STRATEGY_SPEC_V1"
        or record["dataset_id"] != DATASET_ID
        or record["dataset_sha256"] != dataset_sha256
        or record["oos_period"] != {"start": "2022-01-01", "end": "2025-12-31"}
        or record["selected_strategy_id"] != strategy_id
        or tuple(record["selected_config"]["factor_names"]) != factor_names
        or canonical_sha256(record["selected_config"]) != record["selected_config_sha256"]
    ):
        raise ValueError("METHODOLOGY_FREEZE_CHANGED")
    record["freeze_record_sha256"] = digest
    return record


def frozen_inputs(dataset: Path, repository: Path):
    marker = (dataset / MARKER).read_bytes()
    receipt = repository / ".research" / "freezes" / f"{dataset.name}.json"
    if marker != receipt.read_bytes():
        raise ValueError("FREEZE_RECORD_PARITY_FAILED")
    record = json.loads(marker)
    if (
        canonical_sha256({k: v for k, v in record.items() if k != "freeze_record_sha256"})
        != record["freeze_record_sha256"]
    ):
        raise ValueError("FREEZE_RECORD_CHANGED")
    manifest = load_manifest(dataset / "manifest.json")
    if (
        manifest.dataset_id != DATASET_ID
        or manifest.canonical_sha256 != record["dataset_manifest_sha256"]
    ):
        raise ValueError("FROZEN_MANIFEST_CHANGED")
    return record, manifest


def _period(kind: ResearchPeriodKind) -> TemporalPeriod:
    return {
        ResearchPeriodKind.DEVELOPMENT: INITIAL_SPLIT.development,
        ResearchPeriodKind.VALIDATION: INITIAL_SPLIT.validation,
        ResearchPeriodKind.OUT_OF_SAMPLE: INITIAL_SPLIT.out_of_sample,
    }[kind]


class RecordingStrategy(ChinaAMomentumLowVolResearchStrategy):
    def reset(self) -> None:
        super().reset()
        self.rebalances = []

    def target_for_completed_session(self, session, available_equity):
        target = super().target_for_completed_session(session, available_equity)
        if target is not None:
            self.rebalances.append(
                {
                    "date": str(session.trading_date),
                    "factor_count": len(self.last_factors),
                    "score_count": len(self.last_cross_section.scores),
                    "factors_sha256": canonical_sha256(
                        {"values": plain([asdict(value) for value in self.last_factors])}
                    ),
                    "scores_sha256": canonical_sha256(
                        {"values": plain(asdict(self.last_cross_section))}
                    ),
                    "target": plain(asdict(target)),
                }
            )
        return target


def _benchmark_equity(data: FullDataset, dates: tuple[str, ...]) -> tuple[Decimal, ...]:
    first = data.benchmark[dates[0]]
    return tuple(INITIAL_CASH * data.benchmark[day] / first for day in dates)


def _annual_and_monthly(dates: tuple[str, ...], equity: tuple[Decimal, ...]):
    returns = tuple(current / previous - ONE for previous, current in pairwise(equity))
    buckets = {"annual": defaultdict(list), "monthly": defaultdict(list)}
    for day, value in zip(dates[1:], returns, strict=True):
        buckets["annual"][day[:4]].append(value)
        buckets["monthly"][day[:7]].append(value)
    return {
        name: {key: format(_compound(tuple(values)), "f") for key, values in sorted(groups.items())}
        for name, groups in buckets.items()
    }


def _compound(values: tuple[Decimal, ...]) -> Decimal:
    result = ONE
    for value in values:
        result *= ONE + value
    return result - ONE


def _rolling(dates: tuple[str, ...], equity: tuple[Decimal, ...], window: int = 252):
    returns = tuple(current / previous - ONE for previous, current in pairwise(equity))
    values = []
    for index in range(window, len(returns) + 1):
        sample = returns[index - window : index]
        mean = sum(sample, ZERO) / Decimal(window)
        variance = sum(((value - mean) ** 2 for value in sample), ZERO) / Decimal(window)
        with localcontext() as context:
            sharpe = (
                None
                if variance == ZERO
                else mean / context.sqrt(variance) * context.sqrt(Decimal(252))
            )
        window_equity = equity[index - window : index + 1]
        peak = window_equity[0]
        drawdown = ZERO
        for value in window_equity:
            peak = max(peak, value)
            drawdown = min(drawdown, value / peak - ONE)
        values.append({"trading_date": dates[index], "sharpe": sharpe, "drawdown": drawdown})
    return plain(values)


def _holding_period(snapshots) -> Decimal | None:
    opened, completed = {}, []
    for index, snapshot in enumerate(snapshots):
        live = {position.symbol for position in snapshot.positions if position.quantity > ZERO}
        for symbol in live - opened.keys():
            opened[symbol] = index
        for symbol in set(opened) - live:
            completed.append(index - opened.pop(symbol))
    return Decimal(sum(completed)) / Decimal(len(completed)) if completed else None


def _metrics(dates, equity, benchmark, *, snapshots=(), fills=()):
    fills = tuple(
        fill for fill in fills if dates[0] <= fill.timestamp.date().isoformat() <= dates[-1]
    )
    sell_days = {fill.timestamp.date().isoformat() for fill in fills if fill.side is OrderSide.SELL}
    closed = []
    if snapshots:
        previous_realized = previous_commission = ZERO
        for snapshot in snapshots:
            day = snapshot.timestamp.date().isoformat()
            realized = snapshot.realized_pnl
            commission = snapshot.cumulative_commission
            if day in sell_days:
                closed.append(
                    ClosedTrade(
                        realized - previous_realized - (commission - previous_commission), 0
                    )
                )
            previous_realized, previous_commission = realized, commission
    average_equity = sum(equity, ZERO) / Decimal(len(equity))
    traded = sum((fill.quantity * fill.price for fill in fills), ZERO)
    costs = sum((fill.commission for fill in fills), ZERO)
    exposures = (
        tuple(snapshot.market_value / snapshot.equity for snapshot in snapshots)
        if snapshots
        else tuple(ZERO for _ in equity)
    )
    analytics = analyze_research_period(
        equity=equity,
        benchmark_equity=benchmark,
        closed_trades=tuple(closed),
        turnover=traded / average_equity,
        transaction_costs=costs,
        gross_exposures=exposures,
        net_exposures=exposures,
    )
    values = asdict(analytics)
    values["number_of_trades"] = len(fills)
    values["average_holding_period"] = _holding_period(snapshots) if snapshots else None
    values["closed_trade_sessions"] = len(closed)
    return plain(values)


def run_baselines(data: FullDataset):
    start, end = data.period.start.isoformat(), data.period.end.isoformat()
    dates = tuple(day for day in data.calendar_text if start <= day <= end)
    benchmark = _benchmark_equity(data, dates)
    previous, amounts, eligible = {}, defaultdict(lambda: deque(maxlen=20)), set()
    value = INITIAL_CASH
    equal_weight = []
    for session in data.sessions(execution=False):
        day = session.trading_date.isoformat()
        current = {str(bar.security_id): bar.adjusted_close for bar in session.bars}
        current.update(
            {
                str(item.security_id): item.adjusted_close
                for item in session.feature_only_observations
            }
        )
        if day >= start:
            returns = [
                current[sid] / previous[sid] - ONE
                for sid in sorted(eligible)
                if sid in current and sid in previous
            ]
            if returns:
                value *= ONE + sum(returns, ZERO) / Decimal(len(eligible))
            equal_weight.append(value)
        status = {str(item.status.security_id): item.status for item in session.statuses}
        for bar in session.bars:
            sid = str(bar.security_id)
            if bar.amount is not None:
                amounts[sid].append(bar.amount)
        eligible = {
            str(bar.security_id)
            for bar in session.bars
            if status[str(bar.security_id)].is_st is False
            and status[str(bar.security_id)].is_tradeable is True
            and len(amounts[str(bar.security_id)]) == 20
            and sum(amounts[str(bar.security_id)], ZERO) / Decimal(20) >= MINIMUM_AMOUNT
        }
        previous.update(current)
    equal_weight_equity = tuple(equal_weight)
    if len(equal_weight_equity) != len(dates):
        raise ValueError("S1_SESSION_GAP")
    common = {"dates": dates, "benchmark_equity": benchmark}
    results = {}
    for candidate, strategy_id, equity in (
        ("S0", "CSI300_PRICE_INDEX", benchmark),
        ("S1", "cn_a_equal_weight_eligible_universe_v1", equal_weight_equity),
    ):
        result = {
            "candidate": candidate,
            "role": "COMPARATOR",
            "strategy_id": strategy_id,
            "config": {
                "weighting": "EQUAL",
                "eligibility": ("POINT_IN_TIME" if candidate == "S1" else "CSI300_PRICE_INDEX"),
                "rebalance": ("DAILY_CLOSE_TO_CLOSE" if candidate == "S1" else "NOT_APPLICABLE"),
                "minimum_average_daily_amount": (
                    str(MINIMUM_AMOUNT) if candidate == "S1" else None
                ),
                "transaction_costs": "NOT_APPLIED_COMPARATOR",
            },
            "metrics": _metrics(dates, equity, benchmark),
            "equity": [
                {"trading_date": day, "value": point}
                for day, point in zip(dates, equity, strict=True)
            ],
            **_annual_and_monthly(dates, equity),
            "rolling": _rolling(dates, equity),
        }
        result["config_sha256"] = canonical_sha256(result["config"])
        results[candidate] = plain(result)
    return results, common


def run_candidate(data: FullDataset, candidate: str, common):
    strategy_id, factor_names = CANDIDATES[candidate]
    strategy = RecordingStrategy(
        minimum_average_daily_amount=MINIMUM_AMOUNT,
        factor_names=factor_names,
        active_from=data.period.start,
        strategy_id=strategy_id,
    )
    engine = ResearchExecutionEngine(
        strategy,
        initial_cash=INITIAL_CASH,
        calendar=data.calendar,
        commission_model=data.cost_model,
    )
    execution = engine.run(data.sessions())
    start, end = data.period.start.isoformat(), data.period.end.isoformat()
    snapshots = tuple(
        snapshot
        for snapshot in execution.snapshots
        if start <= snapshot.timestamp.date().isoformat() <= end
    )
    dates = tuple(snapshot.timestamp.date().isoformat() for snapshot in snapshots)
    if dates != common["dates"]:
        raise ValueError("STRATEGY_SESSION_GAP")
    equity = tuple(snapshot.equity for snapshot in snapshots)
    config = {
        **asdict(strategy.config),
        "factor_names": factor_names,
        "minimum_average_daily_amount": MINIMUM_AMOUNT,
        "initial_cash": INITIAL_CASH,
        "execution_convention": execution.execution_convention,
        "portfolio_role": "VALIDATION_ELIGIBLE_CANDIDATE",
    }
    reasons = Counter(reason for _, reason in execution.execution_checks)
    result = {
        "candidate": candidate,
        "role": "VALIDATION_ELIGIBLE_CANDIDATE",
        "strategy_id": strategy_id,
        "config": plain(config),
        "config_sha256": canonical_sha256(plain(config)),
        "metrics": _metrics(
            dates,
            equity,
            common["benchmark_equity"],
            snapshots=snapshots,
            fills=execution.fills,
        ),
        "equity": [
            {"trading_date": day, "value": point} for day, point in zip(dates, equity, strict=True)
        ],
        "benchmark": [
            {"trading_date": day, "value": point}
            for day, point in zip(dates, common["benchmark_equity"], strict=True)
        ],
        "drawdown": [
            {"trading_date": day, "value": snapshot.drawdown}
            for day, snapshot in zip(dates, snapshots, strict=True)
        ],
        "rebalances": strategy.rebalances,
        "trades": [
            {
                "sequence": sequence,
                **plain(
                    {
                        key: value
                        for key, value in fill.model_dump(mode="python").items()
                        if key != "order_id"
                    }
                ),
            }
            for sequence, fill in enumerate(
                fill
                for fill in execution.fills
                if start <= fill.timestamp.date().isoformat() <= end
            )
        ],
        "execution": {
            "proposals": len(execution.proposals),
            "approved_decisions": sum(item.approved for item in execution.decisions),
            "orders": len(execution.orders),
            "fills": len(execution.fills),
            "expired_orders": len(execution.expired_order_ids),
            "reason_counts": dict(sorted(reasons.items())),
            "active_reservations": len(execution.active_reservations),
        },
        **_annual_and_monthly(dates, equity),
        "rolling": _rolling(dates, equity),
    }
    return plain(result)


def _checkpoint(
    root: Path,
    candidate: str,
    result: dict | None,
    *,
    dataset_sha256: str,
    implementation_sha256: str,
    period: TemporalPeriod,
):
    path = root / f"{candidate.lower()}.json"
    if path.exists():
        payload = json.loads(path.read_bytes())
        digest = payload.pop("checkpoint_sha256")
        if (
            canonical_sha256(payload) != digest
            or payload["candidate"] != candidate
            or payload["dataset_sha256"] != dataset_sha256
            or payload["implementation_sha256"] != implementation_sha256
            or payload["period"] != [str(period.start), str(period.end)]
        ):
            raise ValueError(f"STUDY_CHECKPOINT_CHANGED:{candidate}")
        return stable_result(payload["result"])
    if result is None:
        return None
    payload = {
        "candidate": candidate,
        "dataset_sha256": dataset_sha256,
        "implementation_sha256": implementation_sha256,
        "period": [str(period.start), str(period.end)],
        "result": stable_result(result),
    }
    payload["checkpoint_sha256"] = canonical_sha256(payload)
    write_immutable(path, canonical_json_bytes(payload) + b"\n")
    return result


def run_study(
    dataset: Path,
    repository: Path,
    kind: ResearchPeriodKind,
    *,
    replay: bool,
    checkpoints: Path | None = None,
    candidate_freeze: dict | None = None,
    methodology_freeze: dict | None = None,
):
    record, manifest = frozen_inputs(dataset, repository)
    implementation_sha = implementation_sha256(repository)
    period = _period(kind)
    data = FullDataset(dataset, manifest, period)
    dates = tuple(
        day
        for day in data.calendar_text
        if period.start.isoformat() <= day <= period.end.isoformat()
    )
    common = {"dates": dates, "benchmark_equity": _benchmark_equity(data, dates)}
    cached = (
        {
            candidate: _checkpoint(
                checkpoints,
                candidate,
                None,
                dataset_sha256=manifest.canonical_sha256,
                implementation_sha256=implementation_sha,
                period=period,
            )
            for candidate in ("S0", "S1")
        }
        if checkpoints is not None
        else {"S0": None, "S1": None}
    )
    if all(cached.values()):
        results = cached
    else:
        baselines, common = run_baselines(data)
        results = {**baselines}
        if checkpoints is not None:
            for candidate in ("S0", "S1"):
                _checkpoint(
                    checkpoints,
                    candidate,
                    results[candidate],
                    dataset_sha256=manifest.canonical_sha256,
                    implementation_sha256=implementation_sha,
                    period=period,
                )
    candidate_names = (
        (methodology_freeze["selected_candidate"],)
        if methodology_freeze is not None
        else tuple(CANDIDATES)
    )
    for candidate in candidate_names:
        existing = (
            _checkpoint(
                checkpoints,
                candidate,
                None,
                dataset_sha256=manifest.canonical_sha256,
                implementation_sha256=implementation_sha,
                period=period,
            )
            if checkpoints is not None
            else None
        )
        if existing is not None:
            results[candidate] = existing
            print(f"{kind.value} {candidate} restored", flush=True)
            continue
        print(f"{kind.value} {candidate} start", flush=True)
        results[candidate] = run_candidate(data, candidate, common)
        if checkpoints is not None:
            _checkpoint(
                checkpoints,
                candidate,
                results[candidate],
                dataset_sha256=manifest.canonical_sha256,
                implementation_sha256=implementation_sha,
                period=period,
            )
        print(
            f"{kind.value} {candidate} complete sha256={canonical_sha256(results[candidate])}",
            flush=True,
        )
    if candidate_freeze is not None and any(
        results[name]["config_sha256"] != candidate_freeze["candidates"][name]["config_sha256"]
        for name in candidate_freeze["candidate_order"]
    ):
        raise ValueError("VALIDATION_CANDIDATE_CONFIG_CHANGED")
    if methodology_freeze is not None:
        selected = methodology_freeze["selected_candidate"]
        if results[selected]["config_sha256"] != methodology_freeze["selected_config_sha256"]:
            raise ValueError("OOS_STRATEGY_CONFIG_CHANGED")
    payload = {
        "report_id": f"R6_R7_FIXED_FAMILY_{kind.value}_V1",
        "period_kind": kind.value,
        "period": {"start": str(period.start), "end": str(period.end)},
        "dataset_id": manifest.dataset_id,
        "dataset_sha256": manifest.canonical_sha256,
        "freeze_record_sha256": record["freeze_record_sha256"],
        "implementation_sha256": implementation_sha,
        "initial_cash": INITIAL_CASH,
        "oos_lock": (
            "LOCKED" if kind is not ResearchPeriodKind.OUT_OF_SAMPLE else "UNLOCKED_BY_GATE_C"
        ),
        "official_oos_accessed": kind is ResearchPeriodKind.OUT_OF_SAMPLE,
        "candidate_order": ["S0", "S1", *candidate_names],
        "selection_pool": list(candidate_names),
        "candidate_freeze_sha256": (
            candidate_freeze["freeze_record_sha256"] if candidate_freeze is not None else None
        ),
        "methodology_freeze_sha256": (
            methodology_freeze["freeze_record_sha256"] if methodology_freeze is not None else None
        ),
        "results": results,
    }
    replay_status = "NOT_REQUESTED"
    if replay:
        replay_data = FullDataset(dataset, manifest, period)
        replay_baselines, replay_common = run_baselines(replay_data)
        replay_results = {**replay_baselines}
        for candidate in candidate_names:
            replay_results[candidate] = run_candidate(replay_data, candidate, replay_common)
        if canonical_sha256(results) != canonical_sha256(replay_results):
            raise ValueError("STRATEGY_RESULT_REPLAY_MISMATCH")
        replay_status = "PASS"
    payload["strategy_result_replay"] = replay_status
    payload = plain(payload)
    payload["result_sha256"] = canonical_sha256(payload)
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--period",
        type=ResearchPeriodKind,
        choices=(
            ResearchPeriodKind.DEVELOPMENT,
            ResearchPeriodKind.VALIDATION,
            ResearchPeriodKind.OUT_OF_SAMPLE,
        ),
        required=True,
    )
    parser.add_argument("--verify-replay", action="store_true")
    parser.add_argument("--candidate-freeze", type=Path)
    parser.add_argument("--methodology-freeze", type=Path)
    args = parser.parse_args()
    candidate_freeze = None
    if args.period is ResearchPeriodKind.VALIDATION:
        if args.candidate_freeze is None:
            raise SystemExit("VALIDATION_LOCKED: Development candidate freeze is required")
        manifest = load_manifest(args.dataset / "manifest.json")
        candidate_freeze = load_candidate_freeze(args.candidate_freeze, manifest.canonical_sha256)
    methodology_freeze = None
    oos_claim = None
    if args.period is ResearchPeriodKind.OUT_OF_SAMPLE:
        if args.verify_replay:
            raise SystemExit("OOS_EXACTLY_ONCE: replay is prohibited")
        if args.methodology_freeze is None:
            raise SystemExit("OOS_LOCKED: Gate C methodology freeze is required")
        manifest = load_manifest(args.dataset / "manifest.json")
        methodology_freeze = load_methodology_freeze(
            args.methodology_freeze, manifest.canonical_sha256
        )
        lock = json.loads((args.repository / ".research/oos_lock.json").read_bytes())
        if (
            not lock["oos_authorized"]
            or not lock["methodology_frozen"]
            or lock["methodology_sha256"] != methodology_freeze["freeze_record_sha256"]
            or lock["official_oos_runs"]
        ):
            raise SystemExit("OOS_LOCKED: Gate C authorization is invalid or already consumed")
        claim_path = args.repository / ".research/official-oos-v1-claim.json"
        claim = {
            "claim_id": "OFFICIAL_OOS_V1_EXACTLY_ONCE",
            "dataset_id": DATASET_ID,
            "methodology_sha256": methodology_freeze["freeze_record_sha256"],
            "output": str(args.output.resolve()),
            "git_commit": subprocess.check_output(
                ["git", "rev-parse", "HEAD"], cwd=args.repository, text=True
            ).strip(),
        }
        claim["claim_sha256"] = canonical_sha256(claim)
        if claim_path.exists():
            if json.loads(claim_path.read_bytes()) != claim:
                raise SystemExit("OOS_ALREADY_CLAIMED")
            if (args.output / "receipt.json").exists():
                raise SystemExit("OOS_ALREADY_COMPLETED")
        else:
            write_immutable(claim_path, canonical_json_bytes(claim) + b"\n")
        oos_claim = claim
    result = run_study(
        args.dataset,
        args.repository,
        args.period,
        replay=args.verify_replay,
        checkpoints=args.output,
        candidate_freeze=candidate_freeze,
        methodology_freeze=methodology_freeze,
    )
    git_commit = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=args.repository, text=True
    ).strip()
    result["git_commit"] = git_commit
    result["result_sha256"] = canonical_sha256(
        {key: value for key, value in result.items() if key != "result_sha256"}
    )
    write_immutable(args.output / "result.json", canonical_json_bytes(result) + b"\n")
    receipt = {
        "report_id": result["report_id"],
        "period_kind": result["period_kind"],
        "dataset_id": result["dataset_id"],
        "dataset_sha256": result["dataset_sha256"],
        "freeze_record_sha256": result["freeze_record_sha256"],
        "git_commit": git_commit,
        "result_sha256": result["result_sha256"],
        "strategy_result_replay": result["strategy_result_replay"],
        "official_oos_accessed": result["official_oos_accessed"],
        "candidate_freeze_sha256": result["candidate_freeze_sha256"],
        "methodology_freeze_sha256": result["methodology_freeze_sha256"],
        "oos_claim_sha256": oos_claim["claim_sha256"] if oos_claim is not None else None,
        "status": "PASS",
    }
    write_immutable(args.output / "receipt.json", canonical_json_bytes(receipt) + b"\n")
    print(json.dumps(receipt, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
