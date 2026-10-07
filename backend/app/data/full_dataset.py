"""Read-only accepted A-share dataset sessions, shared by formal and personal research."""

from bisect import bisect_left, bisect_right
from collections import defaultdict
from collections.abc import Iterator
from datetime import date
from decimal import Context, Decimal, localcontext
from importlib import import_module
from itertools import groupby
from pathlib import Path
from typing import Any

from app.data.catalog.checksums import sha256_file
from app.data.catalog.models import DatasetManifest
from app.data.providers.research import (
    DailyBarRecord,
    FeatureOnlyDailyObservation,
    SecurityStatusRecord,
)
from app.data.suspensions import suspension_boundary, suspension_evidence
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
from app.domain.markets.corporate_actions import (
    CorporateActionType,
    OrdinaryDistributionReference,
    cash_bonus_reference_price,
    require_unambiguous_ordinary_distributions,
)
from app.domain.markets.demergers import DemergerEvent
from app.domain.markets.mergers import MergerEvent
from app.domain.markets.pass_through import RestructuringBonusPassThroughEvent
from app.domain.markets.rules import TransactionCostSchedule
from app.domain.markets.surrenders import MandatoryPartialShareSurrenderEvent
from app.domain.trading import OrderSide, OrderType
from app.research.costs import EffectiveDatedAShareCommission
from app.research.models import ResearchSession
from app.research.splits import TemporalPeriod

pa: Any = import_module("pyarrow")
pq: Any = import_module("pyarrow.parquet")


def _adjusted_close(raw_close: str, factor: Decimal) -> Decimal:
    # Preserve the existing normal 28-digit output, independent of caller context.
    with localcontext(Context(prec=28)):
        return Decimal(raw_close) * factor


def _raw_paths(manifest: DatasetManifest, end: date) -> tuple[str, ...]:
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


class FullDataset:
    def __init__(self, root: Path, manifest: DatasetManifest, period: TemporalPeriod) -> None:
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
        # The accepted calendar can identify the next session without revealing
        # future prices, statuses or events to the strategy.
        all_calendar_days = tuple(
            date.fromisoformat(row["session_date"])
            for row in pq.read_table(
                root / "calendar.parquet", columns=["session_date"]
            ).to_pylist()
        )
        self.calendar_days = tuple(day for day in all_calendar_days if day <= period.end)
        next_day = next((day for day in all_calendar_days if day > period.end), None)
        self.next_session = (
            TradingSession(
                session_date=next_day,
                is_open=True,
                source_version=manifest.canonical_sha256,
            )
            if next_day is not None
            else None
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
        self.members: dict[str, list[dict[str, Any]]] = defaultdict(list)
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
        self.suspension_open_states = self._suspension_open_states(end)
        self.actions = self._actions(end)
        self.resolver = TradingRuleResolver(historical_cn_a_rules())
        self.cost_model = EffectiveDatedAShareCommission(self._costs())
        self.benchmark = {
            row["trading_date"]: Decimal(row["close"])
            for row in pq.read_table(
                root / "csi300.parquet", filters=[("trading_date", "<=", end)]
            ).to_pylist()
        }

    def _curves(self, end: str) -> dict[str, Any]:
        grouped: dict[str, Any] = defaultdict(lambda: defaultdict(list))
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
        return Decimal(values[index][1])

    def _features(self, end: str) -> dict[str, tuple[FeatureOnlyDailyObservation, ...]]:
        grouped: dict[str, list[FeatureOnlyDailyObservation]] = defaultdict(list)
        for row in pq.read_table(
            self.root / "feature-only-observations.parquet",
            filters=[("trading_date", "<=", end)],
        ).to_pylist():
            grouped[row["trading_date"]].append(
                FeatureOnlyDailyObservation(
                    security_id=self.ids[row["security_id"]],
                    trading_date=date.fromisoformat(row["trading_date"]),
                    raw_close=Decimal(row["raw_close"]),
                    adjusted_close=_adjusted_close(
                        row["raw_close"], Decimal(row["hfq_factor_at_day"])
                    ),
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

    def _suspension_open_states(self, end: str) -> dict[tuple[str, str], bool | None]:
        result: dict[tuple[str, str], bool | None] = {}
        # Raw slash dates/intraday text cannot be filtered against ISO date strings.
        for row in pq.read_table(self.root / "suspension-events.parquet").to_pylist():
            start, _ = suspension_boundary(row["suspended_at"])
            finish, _ = suspension_boundary(row["resumed_or_ended_at"])
            if start is None or (finish is not None and finish < start):
                raise ValueError("DATASET_INTEGRITY_FAILED")
            first = bisect_left(self.calendar_text, start)
            last = bisect_right(self.calendar_text, min(finish or end, end))
            for day in self.calendar_text[first:last]:
                evidence = suspension_evidence(row, day)
                assert evidence is not None
                key = (row["security_id"], day)
                states = (result.get(key, False), evidence["day_open_blocked"])
                result[key] = True if True in states else None if None in states else False
        return result

    def _actions(self, end: str) -> dict[str, Any]:
        classes: dict[str, Any] = {
            "CORPORATE_ACTION": CorporateAction,
            "RIGHTS_ISSUE": CorporateAction,
            "MERGER": MergerEvent,
            "DEMERGER": DemergerEvent,
            "PARTIAL_SURRENDER": MandatoryPartialShareSurrenderEvent,
            "BONUS_PASS_THROUGH": RestructuringBonusPassThroughEvent,
            "SHARE_CONSOLIDATION": ShareConsolidationEvent,
            "ORDINARY_REFERENCE": OrdinaryDistributionReference,
        }
        grouped: dict[str, Any] = defaultdict(lambda: defaultdict(list))
        # Validate before filtering: a wrong later record date must not hide a due event.
        for row in pq.read_table(self.root / "corporate-actions.parquet").to_pylist():
            event = classes[row["event_kind"]].model_validate_json(row["event_json"])
            is_reference = isinstance(event, OrdinaryDistributionReference)
            application_date = (
                event.ex_date
                if is_reference
                else getattr(event, "application_date", event.effective_date)
            )
            if (
                application_date is None
                or row["application_date"] != application_date.isoformat()
                or row.get("event_checksum") != event.event_checksum
            ):
                prefix = "ORDINARY_REFERENCE" if is_reference else "CORPORATE_ACTION"
                raise ValueError(f"{prefix}_RECORD_MISMATCH")
            if row["application_date"] > end:
                continue
            grouped[row["application_date"]][row["event_kind"]].append(event)
        for kinds in grouped.values():
            seen = set()
            for reference in kinds.get("ORDINARY_REFERENCE", ()):
                key = (reference.security_id, reference.ex_date)
                if key in seen:
                    raise ValueError("DUPLICATE_ORDINARY_REFERENCE")
                seen.add(key)
                pair = [
                    event
                    for kind, events in kinds.items()
                    if kind != "ORDINARY_REFERENCE"
                    for event in events
                    if (
                        getattr(event, "security_id", None)
                        or getattr(event, "parent_security", None)
                    )
                    == reference.security_id
                ]
                if any(not isinstance(event, CorporateAction) for event in pair):
                    raise ValueError("ORDINARY_REFERENCE_STRUCTURAL_BOUNDARY_UNSUPPORTED")
                reference.require_matching_actions(pair)
        return grouped

    def _costs(self) -> tuple[TransactionCostSchedule, ...]:
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

    def _member(self, security_id: str, day: str) -> dict[str, Any]:
        matches = [
            row
            for row in self.members[security_id]
            if row["effective_from"] <= day
            and (row["effective_to"] is None or day <= row["effective_to"])
        ]
        if len(matches) != 1:
            raise ValueError(f"MASTER_INTERVAL_NOT_FOUND:{security_id}:{day}")
        return matches[0]

    def sessions(self, *, execution: bool = True) -> Iterator[ResearchSession]:
        # Local to this iteration, keyed by stable identity, and retained across months.
        previous_closes: dict[str, Decimal] = {}
        pending_boundaries: dict[str, list[Any]] = defaultdict(list)
        pending_references: dict[str, list[OrdinaryDistributionReference]] = defaultdict(list)
        paths_by_month: dict[str, list[str]] = defaultdict(list)
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
                unexplained = []
                action = self.actions.get(day, {}) if execution else {}
                for kind, events in action.items():
                    if kind == "ORDINARY_REFERENCE":
                        for reference in events:
                            pending_references[str(reference.security_id)].append(reference)
                        continue
                    for event in events:
                        identity = getattr(event, "security_id", None) or getattr(
                            event, "parent_security", None
                        )
                        if identity is not None:
                            pending_boundaries[str(identity)].append(event)
                rule_cache = {}
                for row in rows:
                    security_id = row["security_id"]
                    sid = self.ids[security_id]
                    previous = previous_closes.get(security_id)
                    boundaries = pending_boundaries.pop(security_id, [])
                    references = pending_references.pop(security_id, [])
                    # Observation only; never reconstruct entitlement or execution prices.
                    previous_closes[security_id] = Decimal(row["raw_close"])
                    member = self._member(security_id, day)
                    open_state = self.suspension_open_states.get((security_id, day), False)
                    # Unknown boundaries prohibit execution; they are not normal states.
                    blocked = open_state is not False
                    risky = row["risk_status"] != "NORMAL"
                    status = DailySecurityStatus(
                        security_id=sid,
                        trading_date=session_date,
                        is_st=risky,
                        is_suspended=blocked,
                        is_tradeable=not blocked,
                        is_one_price_limit=row["raw_high"] == row["raw_low"],
                        source_version=(
                            f"{row['source_lineage']}:FULL_SUSPENSION_INTERVAL_V2"
                            + (":UNCERTAIN_OPEN" if open_state is None else "")
                        ),
                    )
                    adjusted = _adjusted_close(row["raw_close"], self.factor_at(security_id, day))
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
                    key = (
                        member["board"],
                        risky,
                        min(age, 5),
                        blocked,
                        status.is_one_price_limit,
                        special,
                    )
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
                    if (
                        previous is not None
                        and row["pre_close"] is not None
                        and Decimal(row["pre_close"]) != previous
                    ):
                        explained = bool(boundaries)
                        ordinary = [
                            event
                            for event in boundaries
                            if isinstance(event, CorporateAction)
                            and event.action_type
                            in {
                                CorporateActionType.CASH_DIVIDEND,
                                CorporateActionType.STOCK_DIVIDEND,
                                CorporateActionType.BONUS_SHARE,
                            }
                        ]
                        try:
                            # Validate the ordinary subset even alongside rights/conversions.
                            require_unambiguous_ordinary_distributions(ordinary)
                            shares = [
                                event
                                for event in ordinary
                                if event.action_type is not CorporateActionType.CASH_DIVIDEND
                            ]
                            explained = (
                                explained
                                and len(shares) <= 1
                                and (not shares or len({event.ex_date for event in ordinary}) == 1)
                                and (not references or len(ordinary) == len(boundaries))
                            )
                            if explained and len(ordinary) == len(boundaries):
                                with localcontext(Context(prec=50)):
                                    cash = sum(
                                        (event.cash_per_share for event in ordinary), Decimal(0)
                                    )
                                ratio = shares[0].share_ratio if shares else Decimal(0)
                                assert ratio is not None  # Validated by the shared supporter.
                                if references:
                                    if len(references) != 1:
                                        raise ValueError("MULTIPLE_ORDINARY_REFERENCES_UNSUPPORTED")
                                    expected = references[0].reference_price(
                                        previous, rule.minimum_tick, ordinary
                                    )
                                else:
                                    expected = cash_bonus_reference_price(
                                        previous,
                                        cash_per_old_share=cash,
                                        aggregate_share_ratio=ratio,
                                        minimum_tick=rule.minimum_tick,
                                    )
                                explained = expected == Decimal(row["pre_close"])
                        except ValueError:
                            explained = False
                        # ponytail: multi-share/multi-ex distributions require a separate
                        # reference audit; mixed explicit-reference boundaries fail closed.
                        # Without a reference, structural boundaries retain existing accounting.
                        # This observed-gap guard is not a corporate-action census.
                        if not explained:
                            unexplained.append(sid)
                    rules.append(rule)
                    lots.append((sid, rule.buy_lot_size))
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
                    unexplained_reference_adjustment_ids=tuple(unexplained),
                )
        if yielded != len(self.calendar_days):
            raise ValueError("SESSION_COUNT_CHANGED")
