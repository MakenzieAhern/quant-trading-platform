"""Audit the immutable Pilot catalog without freezing it or executing a strategy."""

import argparse
import json
from bisect import bisect_left
from collections import Counter
from datetime import date
from decimal import Decimal
from pathlib import Path
from tempfile import TemporaryDirectory

import pyarrow.parquet as parquet

from app.data.catalog import (
    finalize_manifest,
    load_manifest,
    verify_dataset,
    write_canonical_parquet,
)
from app.data.catalog.normalized import _canonical_rows
from app.data.providers.research import DailyBarRecord
from app.domain.markets.identifiers import Board, Exchange, Market, SecurityId
from app.domain.markets.rules import DailySecurityStatus, TradingRuleResolver, TradingRuleVersion
from app.domain.markets.security import InstrumentClassification
from app.domain.trading import OrderSide, OrderType
from scripts.audit_amount_impact import status_lookup
from scripts.audit_pilot_observations import missing_intervals
from scripts.materialize_akshare_partitions import normalized_bars
from scripts.publish_akshare_pilot import ACCEPTED_INPUTS, delisting_starts
from scripts.reconcile_sse_cninfo import canonical, save, sha
from scripts.sina_adjustment_audit import factor_at, feature_close, parse_factors
from scripts.stage_akshare_pilot import (
    DATASET_ID,
    END,
    START,
    candidate_members,
    pilot_members,
    scope_members,
)


def require(condition: bool, reason: str) -> None:
    if not condition:
        raise ValueError(reason)


def verify_preserved_checkpoint(root: Path) -> str:
    primary = json.loads((root / "recovery-checkpoint.json").read_bytes())
    secondary = json.loads((root / "secondary-checkpoint.json").read_bytes())
    original = set(primary["completed"]) | {
        r["security_id"]
        for r in secondary["history"][:1924]
        if r["status"] == "PRIMARY_FAILED_SECONDARY_RECOVERED"
    }
    current = json.loads((root / "partition-checkpoint.json").read_bytes())["partitions"]
    parts = {sid: receipt for sid, receipt in current.items() if sid in original}
    previous = dict(
        securities_partitioned=len(parts),
        raw_rows=sum(r["raw_rows"] for r in parts.values()),
        factor_rows=sum(r["factor_rows"] for r in parts.values()),
        partitions=parts,
        failures={},
        published=False,
        dataset_audited=False,
        dataset_frozen=False,
    )
    signature = sha(canonical(previous))
    require(
        signature == "ff844abd20b651ae9a962515a6feb6cc551f90468daf7b984959da7121149ca6",
        "ORIGINAL_2580_PARTITION_RECEIPTS_CHANGED",
    )
    return signature


def audit_security(member, bars, factors, states, sessions, get_status) -> dict:
    """Check the entire listing lifecycle; missing status is never favorable."""
    sid = member["security_id"]
    days = [r["trading_date"] for r in bars]
    require(bool(days) and days == sorted(set(days)), "BAR_DATE_ORDER_OR_EMPTY")
    gaps = missing_intervals(member, sessions, days)
    expected_days = [
        d
        for d in sessions
        if d >= member["listing_date"]
        and (not member["delisting_date"] or d < member["delisting_date"])
    ]
    require([r["trading_date"] for r in states] == expected_days, "STATUS_LIFECYCLE_GAP")
    curve = [(r["effective_from"], Decimal(r["hfq_factor"])) for r in factors]
    require(bool(curve) and curve == sorted(set(curve)), "FACTOR_ORDER_OR_EMPTY")
    require(len({d for d, _ in curve}) == len(curve), "DUPLICATE_FACTOR_DATE")
    require(all(d <= END and v.is_finite() and v > 0 for d, v in curve), "INVALID_FACTOR")
    require(all(r["security_id"] == sid for r in factors), "FACTOR_IDENTITY")
    present = set(days)
    for row in bars:
        values = {k: v for k, v in row.items() if k != "source"}
        values["security_id"] = dict(value=row["security_id"])
        bar = DailyBarRecord.model_validate(values)
        require(str(bar.security_id) == sid, "BAR_IDENTITY")
        require(bar.amount is not None, "MISSING_REQUIRED_AMOUNT")
        require(bar.adjusted_close is None and bar.adjustment_factor is None, "RAW_ADJUSTED_MIX")
        day = row["trading_date"]
        require(START <= day <= END, "BAR_OUTSIDE_PILOT")
        factor_at(curve, day)
        truncated = [(d, v) for d, v in curve if d <= day]
        # Use the first historical close at every later as-of, not a strategy return.
        value = feature_close(Decimal(bars[0]["raw_close"]), days[0], day, curve)
        require(
            value == feature_close(Decimal(bars[0]["raw_close"]), days[0], day, truncated[::-1]),
            "ADJUSTMENT_FUTURE_EVENT_LEAKAGE",
        )
    counts = Counter()
    for row in states:
        day = row["trading_date"]
        risk = get_status(sid, day)
        require(risk in {"NORMAL", "ST", "STAR_ST", "DELISTING_PERIOD"}, "UNKNOWN_ST")
        require(row["security_id"] == sid and row["risk_status"] == risk, "ST_IDENTITY_OR_REPLAY")
        require(row["is_st"] == str(int(risk in {"ST", "STAR_ST"})), "ST_FLAG")
        require(row["is_star_st"] == str(int(risk == "STAR_ST")), "STAR_ST_FLAG")
        require(row["bar_observed"] == str(int(day in present)), "OBSERVATION_FLAG")
        require(
            row["is_suspended"] is None and row["is_tradeable"] is None, "INFERRED_TRADEABILITY"
        )
        require(
            row["execution_state"] == "NO_FILL_UNLESS_SEPARATE_OFFICIAL_TRADEABILITY_EVIDENCE",
            "UNKNOWN_EXECUTION_NOT_FAIL_CLOSED",
        )
        counts[risk] += 1
    return dict(bars=len(bars), lifecycle_sessions=len(states), risk_counts=dict(counts), gaps=gaps)


def check_rule_resolution(version, members, sessions, history, get_status, starts=None) -> int:
    """Resolve each distinct board/date/risk/listing-age case, without submitting orders."""
    forward = TradingRuleResolver(version)
    reverse = TradingRuleResolver(version.model_copy(update={"rules": version.rules[::-1]}))
    seen = set()
    starts = starts or {}
    specific = {str(r.security_id) for r in version.rules if r.security_id}
    max_age = max(
        max(r.ipo_no_limit_sessions, r.conservative_no_fill_listing_sessions) for r in version.rules
    )
    for member in members:
        listed = bisect_left(history, member["listing_date"])
        for day in sessions:
            if day < member["listing_date"] or (
                member["delisting_date"] and day >= member["delisting_date"]
            ):
                continue
            age = min(max_age, bisect_left(history, day) - listed)
            risk = get_status(member["security_id"], day)
            # Identity is retained if any security-specific rule exists.
            identity = member["security_id"] if member["security_id"] in specific else ""
            period_start = starts.get(member["security_id"]) if risk == "DELISTING_PERIOD" else None
            require(
                risk != "DELISTING_PERIOD" or period_start is not None, "DELISTING_START_UNKNOWN"
            )
            key = (member["exchange"], member["board"], day, risk, age, identity, period_start)
            if key in seen:
                continue
            seen.add(key)
            sid = SecurityId(value=member["security_id"])
            on = date.fromisoformat(day)
            candidates = [
                r
                for r in version.rules
                if r.applies_on(on)
                and r.market == Market.CN_A
                and (r.exchange is None or r.exchange == member["exchange"])
                and (r.board is None or r.board == member["board"])
                and (r.security_id is None or r.security_id == sid)
            ]
            require(bool(candidates), "MARKET_RULE_GAP")
            require(all(r.source_publication_date <= on for r in candidates), "FUTURE_RULE_LEAKAGE")
            kwargs = dict(
                security_id=sid,
                market=Market.CN_A,
                exchange=Exchange(member["exchange"]),
                board=Board(member["board"]),
                trading_date=on,
                side=OrderSide.BUY,
                order_type=OrderType.LIMIT,
                listing_age_sessions=age,
                # Conservative audit proxy only, never written as an official suspension fact.
                security_status=DailySecurityStatus(
                    security_id=sid,
                    trading_date=on,
                    is_st=risk in {"ST", "STAR_ST"},
                    is_suspended=True,
                    is_tradeable=None,
                    source_version="AUDIT_NO_FILL_PROXY",
                    delisting_period_start=period_start,
                ),
            )
            resolved = forward.resolve(**kwargs)
            require(resolved == reverse.resolve(**kwargs), "RULE_ORDER_DEPENDENCE")
            require(not resolved.executable, "CONSERVATIVE_PROXY_EXECUTABLE")
            cost = resolved.cost_schedule
            require(
                cost.valid_from <= on and (cost.valid_to is None or on <= cost.valid_to),
                "COST_EFFECTIVE_DATE_GAP",
            )
    return len(seen)


def audit(staging: Path, dataset: Path) -> dict:
    manifest = load_manifest(dataset / "manifest.json")
    require(manifest.dataset_id == DATASET_ID, "WRONG_DATASET")
    verify_dataset(dataset, manifest)
    require(
        {p.relative_to(dataset).as_posix() for p in dataset.rglob("*.parquet")}
        == {p.relative_path for p in manifest.partitions},
        "UNMANIFESTED_DATA_PARTITION",
    )
    members = pilot_members(staging)
    candidates = candidate_members(staging)
    facts = [
        InstrumentClassification.model_validate(r["classification"])
        for r in json.loads(
            (staging / "instrument-scope-20260912/approved-classifications.json").read_bytes()
        )
    ]
    require(scope_members(candidates[::-1], facts[::-1]) == members, "INSTRUMENT_ORDER_DEPENDENCE")

    def read(name):
        return parquet.read_table(dataset / name).to_pylist()

    require(
        read("securities.parquet")
        == sorted(
            [dict(**m, instrument_type="COMMON_A_SHARE") for m in members],
            key=lambda m: m["security_id"],
        ),
        "SURVIVORSHIP_OR_INSTRUMENT_SCOPE_CHANGED",
    )
    require(
        read("candidate-master.parquet") == sorted(candidates, key=lambda m: m["security_id"]),
        "ORIGINAL_CANDIDATE_MASTER_CHANGED",
    )
    required = {m["security_id"] for m in members}
    require(
        {r["security_id"] for r in read("out-of-scope.parquet")}
        == {m["security_id"] for m in candidates} - required,
        "EXCLUSION_LEDGER_CHANGED",
    )
    contracts = {r["name"]: json.loads(r["payload"]) for r in read("contracts.parquet")}
    require(
        contracts["ACCEPTED_INPUT_HASHES"] == ACCEPTED_INPUTS, "ACCEPTED_INPUT_CONTRACT_CHANGED"
    )
    for relative, expected in ACCEPTED_INPUTS.items():
        require(sha((staging / relative).read_bytes()) == expected, "ACCEPTED_INPUT_BYTES_CHANGED")
    sessions = [r["session_date"] for r in read("calendar.parquet")]
    require(
        sessions
        == json.loads(
            (
                staging / "sse-st-pilot/completeness-20260910/calendar/pilot-sessions.json"
            ).read_bytes()
        ),
        "CALENDAR_CHANGED",
    )
    benchmark = read("csi300-bars.parquet")
    require([r["trading_date"] for r in benchmark] == sessions, "BENCHMARK_ALIGNMENT")
    original_benchmark = json.loads(
        (staging / "benchmark-route-20260910/CSI300-1.json").read_bytes()
    )
    require(
        [Decimal(r["close"]) for r in benchmark]
        == [Decimal(r.split(",")[2]) for r in original_benchmark["data"]["klines"]]
        and all(r["benchmark_id"] == "CSI300_PRICE_INDEX" for r in benchmark),
        "BENCHMARK_SOURCE_MISMATCH",
    )
    require(
        all(Decimal(r["close"]).is_finite() and Decimal(r["close"]) > 0 for r in benchmark),
        "BENCHMARK_PRICE_INVALID",
    )
    history = [r["session_date"] for r in read("calendar-history.parquet")]
    require(
        sha(canonical(history)) == contracts["CALENDAR_HISTORY_PROVENANCE"]["history_sha256"],
        "LISTING_AGE_HISTORY_CHANGED",
    )
    get_status = status_lookup(staging)
    starts = delisting_starts(staging)
    lineage = {
        r["security_id"]: json.loads(r["input_lineage_json"]) for r in read("lineage.parquet")
    }
    require(set(lineage) == required, "PROVIDER_LINEAGE_INCOMPLETE")
    totals, missing, providers = Counter(), [], Counter()
    expected_paths = {p.relative_path for p in manifest.partitions if "/" not in p.relative_path}
    for n, member in enumerate(members, 1):
        sid = member["security_id"]
        prefix = f"{member['exchange']}/{member['symbol']}/"
        expected_paths.update(
            prefix + name for name in ("raw.parquet", "factors.parquet", "daily-state.parquet")
        )
        bars, factors, states = [
            read(prefix + name)
            for name in ("raw.parquet", "factors.parquet", "daily-state.parquet")
        ]
        result = audit_security(member, bars, factors, states, sessions, get_status)
        require(
            all(
                r["delisting_period_start"]
                == (starts.get(sid) if r["risk_status"] == "DELISTING_PERIOD" else None)
                for r in states
            ),
            "DELISTING_START_CHANGED",
        )
        totals.update({k: result[k] for k in ("bars", "lifecycle_sessions")})
        missing.extend(
            dict(security_id=sid, **g, classification="MISSING_NOT_INFERRED_SUSPENSION")
            for g in result["gaps"]
        )
        inputs = lineage[sid]
        for kind in ("raw", "factor"):
            require(
                sha((staging / inputs[kind + "_path"]).read_bytes()) == inputs[kind + "_sha256"],
                "PROVIDER_SOURCE_BYTES_CHANGED",
            )
        symbol = ("sh" if member["exchange"] == "SSE" else "sz") + member["symbol"]
        curve = parse_factors((staging / inputs["factor_path"]).read_bytes(), symbol, "hfq")
        baseline = max((d for d, _ in curve if d <= START), default=None)
        require(
            [(r["effective_from"], Decimal(r["hfq_factor"])) for r in factors]
            == [(d, v) for d, v in curve if d <= END and (d >= START or d == baseline)],
            "ADJUSTMENT_SOURCE_MISMATCH",
        )
        provider = inputs.get("provider", "Eastmoney")
        require(provider in {"Eastmoney", "Tencent"}, "UNACCEPTED_PROVIDER")
        raw = (staging / inputs["raw_path"]).read_bytes()
        if provider == "Tencent":
            expected_bars = []
            for row in json.loads(raw)["rows"]:
                expected_bar = DailyBarRecord.model_validate(row).model_dump(mode="python")
                expected_bar["security_id"] = sid
                expected_bar["source"] = "AKShare:stock_zh_a_hist_tx:Tencent:day:raw"
                expected_bars.append(expected_bar)
        else:
            expected_bars = normalized_bars(raw, member, set(sessions))
        require(
            bars
            == _canonical_rows(
                tuple(sorted(bars[0])), expected_bars, ("security_id", "trading_date")
            ),
            "RAW_SOURCE_NORMALIZATION_CHANGED",
        )
        providers[provider] += 1
        for source in inputs.get("sources", []):
            require(
                sha((staging / source["path"]).read_bytes()) == source["sha256"],
                "RAW_LINEAGE_CHANGED",
            )
        if n % 250 == 0:
            print(f"audited_securities={n}/{len(members)}", flush=True)
    require(
        {p.relative_path for p in manifest.partitions} == expected_paths,
        "NON_A_SHARE_PARTITION_LEAKAGE",
    )
    normalized_missing = [
        {k: str(v) for k, v in row.items()}
        for row in sorted(missing, key=lambda r: (r["security_id"], r["effective_from"]))
    ]
    require(read("missing-observations.parquet") == normalized_missing, "MISSING_LEDGER_CHANGED")
    amount = contracts["AMOUNT_PRECISION_AUDIT"]
    require(
        amount["available_securities"] == len(members)
        and amount["available_rows"] == totals["bars"]
        and amount["amount_decisions_ambiguous"] == 0
        and amount["outlier_count"] == 0
        and amount["cross_source_rows"] > 0
        and amount["classification"] == "LIMITED_PRECISION_PARITY",
        "AMOUNT_OR_CROSS_SOURCE_AUDIT_NOT_PASS",
    )
    rule_cases = check_rule_resolution(
        TradingRuleVersion.model_validate(contracts["EFFECTIVE_MARKET_RULES"]),
        members,
        sessions,
        history,
        get_status,
        starts,
    )
    with TemporaryDirectory(prefix="pilot-audit-") as temporary:
        for part in manifest.partitions:
            table = parquet.read_table(dataset / part.relative_path)
            fields = table.schema.names
            if "trading_date" in fields:
                keys = (
                    ("security_id", "trading_date")
                    if "security_id" in fields
                    else ("trading_date",)
                )
            elif "effective_from" in fields:
                keys = ("security_id", "effective_from")
            elif "session_date" in fields:
                keys = ("session_date",)
            else:
                keys = (
                    ("name",)
                    if "name" in fields and "security_id" not in fields
                    else ("security_id",)
                )
            repeated = write_canonical_parquet(
                Path(temporary) / "repeat.parquet",
                fieldnames=fields,
                rows=table.to_pylist()[::-1],
                sort_keys=keys,
            )
            require(
                (repeated.sha256, repeated.logical_sha256, repeated.row_count)
                == (part.sha256, part.logical_sha256, part.row_count),
                "PARTITION_REPLAY_CHANGED",
            )
    require(finalize_manifest(manifest.model_dump()) == manifest, "MANIFEST_REPEATABILITY")
    root = staging / "pilot-akshare-20260911"
    preserved = verify_preserved_checkpoint(root)
    resume = json.loads((root / "publication-resume-verification.json").read_bytes())
    publication = json.loads((root / "publication-report.json").read_bytes())
    require(
        resume["status"] == "PASS"
        and resume["manifest_sha256"] == manifest.canonical_sha256
        and resume["input_sha256"] == publication["input_sha256"]
        and not resume["source_refetched"]
        and not resume["partitions_rewritten"],
        "PUBLICATION_RESUME_NOT_VERIFIED",
    )
    report = dict(
        dataset_id=DATASET_ID,
        manifest_sha256=manifest.canonical_sha256,
        securities=len(members),
        candidate_securities=len(candidates),
        board_counts=dict(Counter(m["board"] for m in members)),
        providers=dict(providers),
        total_bars=totals["bars"],
        lifecycle_sessions=totals["lifecycle_sessions"],
        missing_observations=sum(g["sessions"] for g in missing),
        unclassified_securities=0,
        non_a_share_instrument_leakage=0,
        market_rule_cases=rule_cases,
        dataset_frozen=False,
        suspension_tradeability_limit=(
            "Official daily tradeability/suspension remains unknown; "
            "no fill without separate evidence"
        ),
        resume_restart="PASS",
        original_2580_partition_checkpoint_sha256=preserved,
        dataset_audited=True,
        completed_checks=[
            "SURVIVORSHIP",
            "FUTURE_IPO",
            "DELISTING_RETENTION",
            "LOOK_AHEAD",
            "ST_POINT_IN_TIME",
            "STABLE_ID",
            "OHLC_VALIDITY",
            "TRADING_CALENDAR",
            "ADJUSTMENT_SEPARATION",
            "ADJUSTMENT_TEMPORAL_SAFETY",
            "SUSPENSION_HANDLING",
            "BENCHMARK_ALIGNMENT",
            "MARKET_RULE_RESOLUTION",
            "PROVIDER_LINEAGE",
            "CROSS_SOURCE_PARITY",
            "AMOUNT_SEMANTIC_VALIDATION",
            "CHECKSUM_REPEATABILITY",
            "INPUT_ORDER_REPRODUCIBILITY",
            "INSTRUMENT_TYPE_SCOPE",
            "NON_A_SHARE_INSTRUMENT_LEAKAGE",
            "INSTRUMENT_CLASSIFICATION_REPRODUCIBILITY",
            "RESUME_RESTART",
        ],
    )
    save(staging / "pilot-akshare-20260911/dataset-audit.json", report)
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--staging", type=Path, required=True)
    parser.add_argument("--dataset", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(audit(args.staging, args.dataset)))
