"""Operator-only real frozen-data smoke; never formal Development/Validation/OOS."""

import argparse
import asyncio
import gc
import json
import subprocess
from bisect import bisect_left
from dataclasses import asdict
from datetime import UTC, date, datetime
from decimal import Decimal
from itertools import groupby
from pathlib import Path
from uuid import NAMESPACE_URL, uuid5

import pyarrow as pa
import pyarrow.parquet as pq

from app.data.catalog import load_manifest, verify_dataset
from app.data.catalog.checksums import canonical_json_bytes, canonical_sha256
from app.data.catalog.freeze import MARKER, write_immutable
from app.data.providers.research import DailyBarRecord, SecurityStatusRecord
from app.domain.markets import (
    Board,
    DailySecurityStatus,
    Exchange,
    Market,
    SecurityId,
    TradingRuleResolver,
)
from app.domain.markets.calendar import TradingCalendar, TradingSession
from app.domain.markets.rules import TradingRuleVersion
from app.domain.trading import OrderSide, OrderType
from app.research.analytics import analyze_research_period
from app.research.costs import EffectiveDatedAShareCommission
from app.research.engine import ResearchExecutionEngine
from app.research.models import ResearchSession
from app.research.strategy import ChinaAMomentumLowVolResearchStrategy
from scripts.sina_adjustment_audit import factor_at

LABEL = "PILOT_ENGINEERING_SMOKE_ONLY"
CASH = Decimal("1000000")  # Engineering fixture capital, not an optimized strategy parameter.


def json_value(value):
    if isinstance(value, Decimal):
        return format(value, "f")
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, SecurityId):
        return str(value)
    raise TypeError(type(value).__name__)


def plain(value):
    return json.loads(json.dumps(value, default=json_value))


def frozen_inputs(dataset: Path, repository: Path):
    record = json.loads((dataset / MARKER).read_bytes())
    if (dataset / MARKER).read_bytes() != (
        repository / ".research/freezes" / (dataset.name + ".json")
    ).read_bytes():
        raise ValueError("FREEZE_RECORD_PARITY_FAILED")
    if (
        canonical_sha256({k: v for k, v in record.items() if k != "freeze_record_sha256"})
        != record["freeze_record_sha256"]
    ):
        raise ValueError("FREEZE_RECORD_CHANGED")
    manifest = load_manifest(dataset / "manifest.json")
    if manifest.canonical_sha256 != record["dataset_manifest_sha256"]:
        raise ValueError("FROZEN_MANIFEST_CHANGED")
    verify_dataset(dataset, manifest)
    return record, manifest


class SmokeStrategy(ChinaAMomentumLowVolResearchStrategy):
    """Observe the existing strategy; no replacement scoring/construction logic."""

    def reset(self):
        super().reset()
        self.rebalances = []

    def target_for_completed_session(self, session, available_equity):
        target = super().target_for_completed_session(session, available_equity)
        if target is not None:
            self.rebalances.append(
                dict(
                    date=str(session.trading_date),
                    factor_count=len(self.last_factors),
                    score_count=len(self.last_cross_section.scores),
                    factors_sha256=canonical_sha256(
                        {"values": plain([asdict(v) for v in self.last_factors])}
                    ),
                    scores_sha256=canonical_sha256(
                        {"values": plain(asdict(self.last_cross_section))}
                    ),
                    target=plain(asdict(target)),
                )
            )
        return target


def session_stream(dataset, manifest, *, reverse=False, through=None):
    members = {
        r["security_id"]: r for r in pq.read_table(dataset / "securities.parquet").to_pylist()
    }
    if any(r["instrument_type"] != "COMMON_A_SHARE" for r in members.values()):
        raise ValueError("NON_A_SHARE_LEAKAGE")
    ids = {sid: SecurityId(value=sid) for sid in members}
    contracts = {
        r["name"]: json.loads(r["payload"])
        for r in pq.read_table(dataset / "contracts.parquet").to_pylist()
    }
    rules = TradingRuleVersion.model_validate(contracts["EFFECTIVE_MARKET_RULES"])
    resolver = TradingRuleResolver(rules)
    history = [
        r["session_date"] for r in pq.read_table(dataset / "calendar-history.parquet").to_pylist()
    ]
    paths = [
        p.relative_path for p in manifest.partitions if p.relative_path.endswith("/raw.parquet")
    ]
    if reverse:
        paths.reverse()
    curves = {}
    for path in paths:
        rows = pq.read_table(dataset / Path(path).with_name("factors.parquet")).to_pylist()
        sid = rows[0]["security_id"]
        curves[sid] = tuple((r["effective_from"], Decimal(r["hfq_factor"])) for r in rows)
    raw = pa.concat_tables([pq.read_table(dataset / p) for p in paths]).sort_by(
        [("trading_date", "ascending"), ("security_id", "ascending")]
    )
    states = pa.concat_tables(
        [pq.read_table(dataset / Path(p).with_name("daily-state.parquet")) for p in paths]
    ).sort_by([("trading_date", "ascending"), ("security_id", "ascending")])
    state_groups = {}
    offset = 0
    for day, group in groupby(states.column("trading_date").to_pylist()):
        length = sum(1 for _ in group)
        state_groups[day] = (offset, length)
        offset += length
    offset = 0
    for n, (day, group) in enumerate(groupby(raw.column("trading_date").to_pylist()), 1):
        length = sum(1 for _ in group)
        if through and day > through:
            break
        rows = raw.slice(offset, length).to_pylist()
        offset += length
        a, b = state_groups[day]
        statuses, resolved, lots, bars = [], [], [], []
        cache = {}
        for row in states.slice(a, b).to_pylist():
            sid = row["security_id"]
            member = members[sid]
            if day < member["listing_date"] or (
                member["delisting_date"] and day >= member["delisting_date"]
            ):
                raise ValueError("LIFECYCLE_LEAKAGE")
            if row["is_suspended"] is not None or row["is_tradeable"] is not None:
                raise ValueError("PILOT_UNKNOWN_EXECUTION_CONTRACT_CHANGED")
            status = DailySecurityStatus(
                security_id=ids[sid],
                trading_date=date.fromisoformat(day),
                is_st=row["is_st"] == "1",
                is_suspended=None,
                is_tradeable=None,
                delisting_period_start=row["delisting_period_start"],
                source_version=row["status_source"],
            )
            age = (
                999
                if member["listing_date"] < history[0]
                else bisect_left(history, day) - bisect_left(history, member["listing_date"])
            )
            key = (member["board"], status.is_st, min(age, 999), status.delisting_period_start)
            if key not in cache:
                cache[key] = resolver.resolve(
                    security_id=ids[sid],
                    market=Market.CN_A,
                    exchange=Exchange(member["exchange"]),
                    board=Board(member["board"]),
                    trading_date=status.trading_date,
                    side=OrderSide.BUY,
                    order_type=OrderType.LIMIT,
                    security_status=status,
                    listing_age_sessions=age,
                )
            rule = cache[key].model_copy(update={"security_id": ids[sid]})
            statuses.append(SecurityStatusRecord(status=status))
            resolved.append(rule)
            lots.append((ids[sid], rule.buy_lot_size))
        for row in rows:
            sid = row["security_id"]
            fields = {k: v for k, v in row.items() if k in DailyBarRecord.model_fields}
            fields["security_id"] = ids[sid]
            # H(t) is available on t. The common H(T) denominator cancels in all v1 factors.
            fields["adjusted_close"] = Decimal(row["raw_close"]) * factor_at(curves[sid], day)
            bars.append(DailyBarRecord.model_validate(fields))
        if n % 50 == 0:
            print(f"{LABEL} completed_session={n} date={day}", flush=True)
        yield ResearchSession(
            date.fromisoformat(day),
            tuple(bars),
            tuple(statuses),
            tuple(lots),
            trading_rules=tuple(resolved),
        )


def run_once(dataset, manifest, *, reverse=False, through=None):
    contracts = {
        r["name"]: json.loads(r["payload"])
        for r in pq.read_table(dataset / "contracts.parquet").to_pylist()
    }
    version = TradingRuleVersion.model_validate(contracts["EFFECTIVE_MARKET_RULES"])
    schedules = {r.cost_schedule.valid_from: r.cost_schedule for r in version.rules}
    calendar = TradingCalendar(
        market=Market.CN_A,
        sessions=tuple(
            TradingSession(
                session_date=r["session_date"],
                is_open=True,
                source_version=manifest.canonical_sha256,
            )
            for r in pq.read_table(dataset / "calendar.parquet").to_pylist()
        ),
    )
    strategy = SmokeStrategy()
    engine = ResearchExecutionEngine(
        strategy,
        initial_cash=CASH,
        calendar=calendar,
        commission_model=EffectiveDatedAShareCommission(tuple(schedules.values())),
    )
    result = engine.run(session_stream(dataset, manifest, reverse=reverse, through=through))
    # The approved Pilot cannot certify a fill. Do not silently turn that into trading evidence.
    if (
        result.fills
        or result.active_reservations
        or any(s.equity != CASH or s.positions for s in result.snapshots)
    ):
        raise ValueError("UNKNOWN_EXECUTION_STATE_MUST_NOT_FILL")
    by_day = {s.timestamp.date().isoformat(): s for s in result.snapshots}
    benchmark = {
        r["trading_date"]: Decimal(r["close"])
        for r in pq.read_table(dataset / "csi300-bars.parquet").to_pylist()
    }
    dates = sorted(by_day)
    if len(dates) != (
        sum(s.session_date.isoformat() <= through for s in calendar.sessions)
        if through
        else len(calendar.sessions)
    ):
        raise ValueError("SMOKE_SESSION_GAP")
    benchmark_equity = tuple(CASH * benchmark[d] / benchmark[dates[0]] for d in dates)
    metrics = analyze_research_period(
        equity=tuple(by_day[d].equity for d in dates),
        benchmark_equity=benchmark_equity,
        gross_exposures=tuple(Decimal(0) for _ in dates),
        net_exposures=tuple(Decimal(0) for _ in dates),
    )
    return plain(
        dict(
            label=LABEL,
            dataset_id=manifest.dataset_id,
            dataset_checksum=manifest.canonical_sha256,
            strategy_config_hash=strategy.config.configuration_hash,
            strategy_config=asdict(strategy.config),
            initial_cash=CASH,
            period_kind="PILOT_SMOKE",
            metrics=asdict(metrics),
            equity=[dict(trading_date=d, value=by_day[d].equity) for d in dates],
            benchmark=[
                dict(trading_date=d, value=v) for d, v in zip(dates, benchmark_equity, strict=True)
            ],
            rebalances=strategy.rebalances,
            proposals=[p.model_dump(mode="json") for p in result.proposals],
            decisions=[d.model_dump(mode="json") for d in result.decisions],
            orders=[o.model_dump(mode="json") for o in result.orders],
            execution_checks=[(str(i), reason) for i, reason in result.execution_checks],
            fills=0,
            active_reservations=0,
            execution_convention=result.execution_convention,
            known_limitations=(
                "PILOT_ENGINEERING_SMOKE_ONLY; unknown official suspension/tradeability "
                "and raw pre_close -> NO FILL. No profitability inference; "
                "no formal Development/Validation/OOS."
            ),
        )
    )


async def persist(result, manifest, git_commit):
    from app.db.models.research import (
        ResearchBenchmarkPointModel,
        ResearchDatasetModel,
        ResearchDrawdownPointModel,
        ResearchEquityPointModel,
        ResearchMetricModel,
        ResearchRebalanceModel,
        ResearchRunModel,
    )
    from app.db.session import SessionFactory

    digest = canonical_sha256(result)
    run_id = uuid5(NAMESPACE_URL, LABEL + ":" + digest)
    now = datetime.now(UTC)
    async with SessionFactory() as session:
        existing = await session.get(ResearchRunModel, run_id)
        if existing is not None:
            if existing.diagnostics.get("result_sha256") != digest:
                raise ValueError("PERSISTED_SMOKE_CHANGED")
            return str(run_id)
        dataset = await session.get(ResearchDatasetModel, manifest.dataset_id)
        if dataset is None:
            session.add(
                ResearchDatasetModel(
                    dataset_id=manifest.dataset_id,
                    provider=manifest.provider,
                    provider_version=manifest.provider_version,
                    retrieval_timestamp=manifest.retrieval_timestamp,
                    coverage_start=manifest.coverage_start,
                    coverage_end=manifest.coverage_end,
                    security_count=manifest.security_count,
                    canonical_sha256=manifest.canonical_sha256,
                    rule_version=manifest.rule_version,
                    adjustment_method="Separate Sina HFQ; raw execution",
                    manifest=manifest.model_dump(mode="json"),
                    readiness_status="PASSED",
                    frozen=True,
                )
            )
            await session.flush()
        elif dataset.canonical_sha256 != manifest.canonical_sha256 or not dataset.frozen:
            raise ValueError("PERSISTED_DATASET_DIFFERS")
        split = {
            "label": LABEL,
            "start": str(manifest.coverage_start),
            "end": str(manifest.coverage_end),
        }
        session.add(
            ResearchRunModel(
                id=run_id,
                status="SUCCEEDED",
                period_kind="PILOT_SMOKE",
                git_commit=git_commit,
                dataset_id=manifest.dataset_id,
                dataset_checksum=manifest.canonical_sha256,
                provider=manifest.provider,
                provider_version=manifest.provider_version,
                market_rule_version=manifest.rule_version,
                strategy_id="cn_a_cross_sectional_momentum_low_vol_v1",
                strategy_config_hash=result["strategy_config_hash"],
                strategy_config=result["strategy_config"],
                transaction_cost_config={
                    "schedule": "frozen-effective-dated",
                    "realized_costs": "0",
                },
                benchmark_id="CSI300",
                benchmark_version=manifest.dataset_id + ":CSI300",
                temporal_split_hash=canonical_sha256(split),
                temporal_split=split,
                random_seed=0,
                created_at=now,
                started_at=now,
                completed_at=now,
                diagnostics=dict(
                    label=LABEL,
                    result_sha256=digest,
                    known_limitations=result["known_limitations"],
                    proposals=len(result["proposals"]),
                    orders=len(result["orders"]),
                    fills=0,
                    execution_checks=result["execution_checks"],
                ),
            )
        )
        await session.flush()
        for name, value in result["metrics"].items():
            session.add(
                ResearchMetricModel(
                    run_id=run_id,
                    period_kind="PILOT_SMOKE",
                    metric_name=name,
                    value=Decimal(str(value)) if value is not None else None,
                )
            )
        for kind, model in (
            ("equity", ResearchEquityPointModel),
            ("benchmark", ResearchBenchmarkPointModel),
        ):
            for n, point in enumerate(result[kind]):
                session.add(
                    model(
                        run_id=run_id,
                        sequence=n,
                        trading_date=date.fromisoformat(point["trading_date"]),
                        value=Decimal(point["value"]),
                    )
                )
        for n, point in enumerate(result["equity"]):
            session.add(
                ResearchDrawdownPointModel(
                    run_id=run_id,
                    sequence=n,
                    trading_date=date.fromisoformat(point["trading_date"]),
                    value=Decimal(0),
                )
            )
        for n, row in enumerate(result["rebalances"]):
            session.add(
                ResearchRebalanceModel(
                    run_id=run_id,
                    sequence=n,
                    trading_date=date.fromisoformat(row["date"]),
                    turnover=Decimal(0),
                    transaction_cost=Decimal(0),
                )
            )
        await session.commit()
    return str(run_id)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", required=True, type=Path)
    parser.add_argument("--repository", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--persist", action="store_true")
    parser.add_argument("--persist-existing", action="store_true")
    parser.add_argument("--git-commit")
    args = parser.parse_args()
    record, manifest = frozen_inputs(args.dataset, args.repository)
    if args.persist_existing:
        result = json.loads((args.output / "result.json").read_bytes())
        receipt = json.loads((args.output / "receipt.json").read_bytes())
        if (
            receipt["result_sha256"] != canonical_sha256(result)
            or receipt["freeze_record_sha256"] != record["freeze_record_sha256"]
            or result["dataset_checksum"] != manifest.canonical_sha256
            or result["label"] != LABEL
            or any(
                receipt[k] != "PASS"
                for k in (
                    "pipeline_complete",
                    "deterministic_replay",
                    "no_look_ahead",
                    "metric_reproducibility",
                )
            )
        ):
            raise ValueError("SMOKE_PERSISTENCE_INPUT_NOT_VERIFIED")
        if (
            not args.git_commit
            or len(args.git_commit) != 40
            or any(c not in "0123456789abcdef" for c in args.git_commit)
        ):
            raise ValueError("EXACT_GIT_COMMIT_REQUIRED")
        run_id = asyncio.run(persist(result, manifest, args.git_commit))
        persistence = dict(
            run_id=run_id,
            result_sha256=receipt["result_sha256"],
            label=LABEL,
            git_commit=args.git_commit,
        )
        write_immutable(args.output / "persistence.json", canonical_json_bytes(persistence) + b"\n")
        print(json.dumps(persistence))
        raise SystemExit(0)
    result = run_once(args.dataset, manifest)
    gc.collect()
    replay = run_once(args.dataset, manifest, reverse=True)
    if result != replay:
        raise ValueError("SMOKE_REPLAY_MISMATCH")
    del replay
    gc.collect()
    prefix = run_once(args.dataset, manifest, through="2024-02-21")
    if prefix["rebalances"] != [r for r in result["rebalances"] if r["date"] <= "2024-02-21"]:
        raise ValueError("SMOKE_FUTURE_DATA_LEAKAGE")
    if (
        not result["proposals"]
        or not result["orders"]
        or not all(r["factor_count"] > 0 and r["score_count"] > 0 for r in result["rebalances"])
    ):
        raise ValueError("SMOKE_PIPELINE_NOT_EXERCISED")
    digest = canonical_sha256(result)
    write_immutable(args.output / "result.json", canonical_json_bytes(result) + b"\n")
    git_commit = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=args.repository, text=True
    ).strip()
    run_id = asyncio.run(persist(result, manifest, git_commit)) if args.persist else None
    receipt = dict(
        label=LABEL,
        result_sha256=digest,
        run_id=run_id,
        freeze_record_sha256=record["freeze_record_sha256"],
        pipeline_complete="PASS",
        deterministic_replay="PASS",
        no_look_ahead="PASS",
        metric_reproducibility="PASS",
        api_result_parity="NOT_YET_CHECKED",
        ui_result_parity="NOT_YET_CHECKED",
        proposals=len(result["proposals"]),
        orders=len(result["orders"]),
        fills=0,
        sessions=len(result["equity"]),
        rebalances=len(result["rebalances"]),
    )
    write_immutable(args.output / "receipt.json", canonical_json_bytes(receipt) + b"\n")
    print(json.dumps(receipt))
