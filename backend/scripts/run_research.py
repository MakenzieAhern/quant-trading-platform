"""Run the fixed S0-S4 family against the immutable full A-share dataset."""

import argparse
import json
import subprocess
from bisect import bisect_left, bisect_right
from collections import Counter, defaultdict, deque
from dataclasses import asdict
from datetime import date
from decimal import Decimal, localcontext
from itertools import groupby, pairwise
from pathlib import Path
from uuid import UUID

import pyarrow as pa
import pyarrow.parquet as pq

from app.data.catalog import load_manifest
from app.data.catalog.checksums import canonical_json_bytes, canonical_sha256, sha256_file
from app.data.catalog.freeze import MARKER, write_immutable
from app.data.providers.research import (
    DailyBarRecord,
    FeatureOnlyDailyObservation,
    SecurityStatusRecord,
)
from app.domain.markets import (
    Board,
    CorporateAction,
    DailySecurityStatus,
    Exchange,
    Market,
    SecurityId,
    TradingRuleResolver,
)
from app.domain.markets.calendar import TradingCalendar, TradingSession
from app.domain.markets.cn_a_rules import historical_cn_a_rules
from app.domain.markets.consolidations import ShareConsolidationEvent
from app.domain.markets.demergers import DemergerEvent
from app.domain.markets.mergers import MergerEvent
from app.domain.markets.pass_through import RestructuringBonusPassThroughEvent
from app.domain.markets.rules import TransactionCostSchedule
from app.domain.markets.surrenders import MandatoryPartialShareSurrenderEvent
from app.domain.trading import OrderSide, OrderType
from app.research.analytics import ClosedTrade, analyze_research_period
from app.research.costs import EffectiveDatedAShareCommission
from app.research.engine import ResearchExecutionEngine
from app.research.models import ResearchPeriodKind, ResearchSession
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


def _raw_paths(manifest, end: date) -> tuple[str, ...]:
    maximum_month = end.strftime("%Y-%m")
    paths = tuple(
        sorted(
            partition.relative_path
            for partition in manifest.partitions
            if partition.relative_path.startswith("raw/")
            and partition.relative_path.endswith(".parquet")
            and Path(partition.relative_path).stem <= maximum_month
        )
    )
    if not paths or any(Path(path).stem > maximum_month for path in paths):
        raise ValueError("PERIOD_PARTITION_LOCK_FAILED")
    return paths


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


class FullDataset:
    def __init__(self, root: Path, manifest, period: TemporalPeriod) -> None:
        self.root = root
        self.manifest = manifest
        self.period = period
        self.paths = _raw_paths(manifest, period.end)
        expected = {partition.relative_path: partition.sha256 for partition in manifest.partitions}
        for relative in (
            *self.paths,
            "adjustment-factors.parquet",
            "calendar.parquet",
            "corporate-actions.parquet",
            "csi300.parquet",
            "feature-only-observations.parquet",
            "securities.parquet",
            "suspension-events.parquet",
            "transaction-costs.parquet",
        ):
            if sha256_file(root / relative) != expected[relative]:
                raise ValueError(f"FROZEN_PARTITION_CHANGED:{relative}")

        end = period.end.isoformat()
        self.calendar_days = tuple(
            date.fromisoformat(row["session_date"])
            for row in pq.read_table(
                root / "calendar.parquet", filters=[("session_date", "<=", end)]
            ).to_pylist()
        )
        self.calendar = TradingCalendar(
            market=Market.CN_A,
            sessions=tuple(
                TradingSession(
                    session_date=day,
                    is_open=True,
                    source_version=manifest.canonical_sha256,
                )
                for day in self.calendar_days
            ),
        )
        self.calendar_text = tuple(day.isoformat() for day in self.calendar_days)
        self.calendar_index = {day: index for index, day in enumerate(self.calendar_text)}
        self.members = defaultdict(list)
        for row in pq.read_table(
            root / "securities.parquet", filters=[("effective_from", "<=", end)]
        ).to_pylist():
            if row["instrument_type"] != "COMMON_A_SHARE":
                raise ValueError("NON_A_SHARE_LEAKAGE")
            self.members[row["security_id"]].append(row)
        for rows in self.members.values():
            rows.sort(key=lambda row: row["effective_from"])
        self.ids = {key: SecurityId(value=key) for key in self.members}
        self.listing_dates = {
            key: min(row["effective_from"] for row in rows) for key, rows in self.members.items()
        }
        self.curves = self._curves(end)
        self.features = self._features(end)
        self.blocked_starts = self._blocked_starts(end)
        self.actions = self._actions(end)
        self.resolver = TradingRuleResolver(historical_cn_a_rules())
        self.cost_model = EffectiveDatedAShareCommission(self._costs())
        self.benchmark = {
            row["trading_date"]: Decimal(row["close"])
            for row in pq.read_table(
                root / "csi300.parquet", filters=[("trading_date", "<=", end)]
            ).to_pylist()
        }

    def _curves(self, end: str):
        grouped = defaultdict(lambda: defaultdict(list))
        rows = pq.read_table(
            self.root / "adjustment-factors.parquet", filters=[("effective_date", "<=", end)]
        ).to_pylist()
        for row in rows:
            grouped[row["security_id"]][(row["interval_from"], row["interval_to"])].append(
                (row["effective_date"], Decimal(row["hfq_factor"]))
            )
        result = {}
        for security_id, intervals in grouped.items():
            result[security_id] = tuple(
                (start, finish, tuple(sorted(values)))
                for (start, finish), values in sorted(intervals.items())
            )
        return result

    def factor_at(self, security_id: str, day: str) -> Decimal:
        matches = [
            values for start, finish, values in self.curves[security_id] if start <= day <= finish
        ]
        if len(matches) != 1:
            raise ValueError(f"ADJUSTMENT_INTERVAL_NOT_FOUND:{security_id}:{day}")
        values = matches[0]
        index = bisect_right([item[0] for item in values], day) - 1
        if index < 0:
            raise ValueError(f"ADJUSTMENT_BASELINE_NOT_FOUND:{security_id}:{day}")
        return values[index][1]

    def _features(self, end: str):
        grouped = defaultdict(list)
        for row in pq.read_table(
            self.root / "feature-only-observations.parquet",
            filters=[("trading_date", "<=", end)],
        ).to_pylist():
            grouped[row["trading_date"]].append(
                FeatureOnlyDailyObservation(
                    security_id=self.ids[row["security_id"]],
                    trading_date=date.fromisoformat(row["trading_date"]),
                    raw_close=Decimal(row["raw_close"]),
                    adjusted_close=Decimal(row["raw_close"]) * Decimal(row["hfq_factor_at_day"]),
                    volume_lower=Decimal(row["volume_lower"]),
                    volume_upper=Decimal(row["volume_upper"]),
                    amount_lower=Decimal(row["amount_lower"]),
                    amount_upper=Decimal(row["amount_upper"]),
                    lineage=row["lineage"],
                )
            )
        return {
            key: tuple(sorted(values, key=lambda item: str(item.security_id)))
            for key, values in grouped.items()
        }

    def _blocked_starts(self, end: str):
        result = {}
        for row in pq.read_table(
            self.root / "suspension-events.parquet", filters=[("suspended_at", "<=", end)]
        ).to_pylist():
            key = (row["security_id"], row["suspended_at"])
            blocked = row["execution_open_blocked"] != "0"
            result[key] = result.get(key, False) or blocked
        return result

    def _actions(self, end: str):
        classes = {
            "CORPORATE_ACTION": CorporateAction,
            "RIGHTS_ISSUE": CorporateAction,
            "MERGER": MergerEvent,
            "DEMERGER": DemergerEvent,
            "PARTIAL_SURRENDER": MandatoryPartialShareSurrenderEvent,
            "BONUS_PASS_THROUGH": RestructuringBonusPassThroughEvent,
            "SHARE_CONSOLIDATION": ShareConsolidationEvent,
        }
        grouped = defaultdict(lambda: defaultdict(list))
        for row in pq.read_table(
            self.root / "corporate-actions.parquet", filters=[("application_date", "<=", end)]
        ).to_pylist():
            grouped[row["application_date"]][row["event_kind"]].append(
                classes[row["event_kind"]].model_validate_json(row["event_json"])
            )
        return grouped

    def _costs(self):
        return tuple(
            TransactionCostSchedule(
                commission_rate=Decimal(row["commission_rate"]),
                minimum_commission=Decimal(row["minimum_commission_cny"]),
                sell_stamp_duty_rate=Decimal(row["seller_stamp_duty_rate"]),
                transfer_fee_rate=Decimal(row["transfer_allowance_rate"]),
                valid_from=date.fromisoformat(row["effective_from"]),
                valid_to=date.fromisoformat(row["effective_to"]),
                source_version="APPROVED_RESEARCH_ACCOUNT_CONVENTION",
            )
            for row in pq.read_table(self.root / "transaction-costs.parquet").to_pylist()
        )

    def _member(self, security_id: str, day: str):
        matches = [
            row
            for row in self.members[security_id]
            if row["effective_from"] <= day
            and (row["effective_to"] is None or day <= row["effective_to"])
        ]
        if len(matches) != 1:
            raise ValueError(f"MASTER_INTERVAL_NOT_FOUND:{security_id}:{day}")
        return matches[0]

    def sessions(self, *, execution: bool = True):
        paths_by_month = defaultdict(list)
        for path in self.paths:
            paths_by_month[Path(path).stem].append(path)
        yielded = 0
        for month in sorted(paths_by_month):
            table = pa.concat_tables(
                [pq.read_table(self.root / path) for path in sorted(paths_by_month[month])]
            ).sort_by([("trading_date", "ascending"), ("security_id", "ascending")])
            rows_by_day = {
                day: list(rows)
                for day, rows in groupby(table.to_pylist(), key=lambda row: row["trading_date"])
            }
            for day in (value for value in self.calendar_text if value.startswith(month)):
                rows = rows_by_day.get(day)
                if not rows:
                    raise ValueError(f"EMPTY_ACCEPTED_SESSION:{day}")
                session_date = date.fromisoformat(day)
                bars, statuses, lots, rules = [], [], [], []
                rule_cache = {}
                for row in rows:
                    security_id = row["security_id"]
                    sid = self.ids[security_id]
                    member = self._member(security_id, day)
                    blocked = self.blocked_starts.get((security_id, day), False)
                    risky = row["risk_status"] != "NORMAL"
                    status = DailySecurityStatus(
                        security_id=sid,
                        trading_date=session_date,
                        is_st=risky,
                        is_suspended=blocked,
                        is_tradeable=not blocked,
                        is_one_price_limit=row["raw_high"] == row["raw_low"],
                        source_version=f"{row['source_lineage']}:FULL_SUSPENSION_V1",
                    )
                    adjusted = Decimal(row["raw_close"]) * self.factor_at(security_id, day)
                    fields = {
                        key: value
                        for key, value in row.items()
                        if key in DailyBarRecord.model_fields
                    }
                    fields.update(security_id=sid, adjusted_close=adjusted)
                    bars.append(DailyBarRecord.model_validate(fields))
                    statuses.append(SecurityStatusRecord(status=status))
                    if not execution:
                        continue
                    age = self.calendar_index[day] - bisect_left(
                        self.calendar_text, self.listing_dates[security_id]
                    )
                    special = (
                        security_id
                        if security_id.endswith(("300090", "300156", "300216"))
                        else None
                    )
                    key = (member["board"], risky, min(age, 5), blocked, special)
                    if key not in rule_cache:
                        rule_cache[key] = self.resolver.resolve(
                            security_id=sid,
                            market=Market.CN_A,
                            exchange=Exchange(member["exchange"]),
                            board=Board(member["board"]),
                            trading_date=session_date,
                            side=OrderSide.BUY,
                            order_type=OrderType.LIMIT,
                            security_status=status,
                            listing_age_sessions=age,
                        )
                    rule = rule_cache[key].model_copy(update={"security_id": sid})
                    rules.append(rule)
                    lots.append((sid, rule.buy_lot_size))
                action = self.actions.get(day, {}) if execution else {}
                surrenders = tuple(action.get("PARTIAL_SURRENDER", ()))
                consolidations = tuple(action.get("SHARE_CONSOLIDATION", ()))
                consolidation_classes = {item.affected_holder_class for item in consolidations}
                if len(consolidation_classes) > 1:
                    raise ValueError("MULTIPLE_HOLDER_CLASSES_IN_SESSION")
                yielded += 1
                yield ResearchSession(
                    trading_date=session_date,
                    bars=tuple(bars),
                    statuses=tuple(statuses),
                    buy_lot_sizes=tuple(lots),
                    feature_only_observations=self.features.get(day, ()),
                    corporate_actions=tuple(
                        (*action.get("CORPORATE_ACTION", ()), *action.get("RIGHTS_ISSUE", ()))
                    ),
                    trading_rules=tuple(rules),
                    demergers=tuple(action.get("DEMERGER", ())),
                    mergers=tuple(action.get("MERGER", ())),
                    partial_surrenders=surrenders,
                    surrender_holder_classes=tuple(
                        (item.security_id, item.affected_holder_class) for item in surrenders
                    ),
                    pass_through_events=tuple(action.get("BONUS_PASS_THROUGH", ())),
                    consolidations=consolidations,
                    consolidation_holder_class=next(iter(consolidation_classes), None),
                )
        if yielded != len(self.calendar_days):
            raise ValueError("SESSION_COUNT_CHANGED")


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
    for candidate in CANDIDATES:
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
        "candidate_order": ["S0", "S1", "S2", "S3", "S4"],
        "selection_pool": ["S2", "S3", "S4"],
        "results": results,
    }
    replay_status = "NOT_REQUESTED"
    if replay:
        replay_data = FullDataset(dataset, manifest, period)
        replay_baselines, replay_common = run_baselines(replay_data)
        replay_results = {**replay_baselines}
        for candidate in CANDIDATES:
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
    parser.add_argument("--methodology-freeze", type=Path)
    args = parser.parse_args()
    if args.period is ResearchPeriodKind.OUT_OF_SAMPLE:
        if args.methodology_freeze is None:
            raise SystemExit("OOS_LOCKED: Gate C methodology freeze is required")
        frozen = json.loads(args.methodology_freeze.read_bytes())
        if frozen.get("status") != "FROZEN" or frozen.get("dataset_id") != DATASET_ID:
            raise SystemExit("OOS_LOCKED: invalid Gate C methodology freeze")
    result = run_study(
        args.dataset,
        args.repository,
        args.period,
        replay=args.verify_replay,
        checkpoints=args.output,
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
        "status": "PASS",
    }
    write_immutable(args.output / "receipt.json", canonical_json_bytes(receipt) + b"\n")
    print(json.dumps(receipt, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
