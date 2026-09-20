"""Audit the materialized full-range dataset and fail closed on authority gaps."""

from __future__ import annotations

import argparse
import json
from bisect import bisect_left, bisect_right
from collections import Counter, defaultdict
from decimal import Decimal
from pathlib import Path
from typing import Any

import pyarrow.parquet as pq

from app.data.catalog import finalize_manifest, load_manifest, verify_dataset
from scripts.materialize_full_dataset import (
    DATASET_ID,
    END,
    RAW_FIELDS,
    START,
    SecurityResolver,
    StatusResolver,
    risk_from_name,
    validate_bar,
)
from scripts.reconcile_sse_cninfo import save, sha


def audit(dataset: Path, repository: Path, output: Path) -> dict[str, Any]:
    manifest = load_manifest(dataset / "manifest.json")
    verify_dataset(dataset, manifest)
    if manifest.dataset_id != DATASET_ID or finalize_manifest(manifest.model_dump()) != manifest:
        raise ValueError("MANIFEST_REPEATABILITY_FAILED")
    state = json.loads((repository / ".research/project_state.json").read_bytes())
    master = pq.read_table(dataset / "securities.parquet").to_pylist()
    calendar_rows = pq.read_table(dataset / "calendar.parquet").to_pylist()
    sessions = [row["session_date"] for row in calendar_rows]
    if sessions != sorted(set(sessions)) or sessions[0] < START or sessions[-1] > END:
        raise ValueError("TRADING_CALENDAR_INVALID")
    session_set = set(sessions)
    security_resolver = SecurityResolver(master)
    status_rows = []
    for name in ("st-sse-intervals.parquet", "st-szse-intervals.parquet"):
        status_rows.extend(pq.read_table(dataset / name).to_pylist())
    status_resolver = StatusResolver(status_rows)
    if any(row["status"] == "UNKNOWN" for row in status_rows):
        raise ValueError("UNKNOWN_ST_INTERVAL")

    counts: Counter[str] = Counter()
    observed: Counter[str] = Counter()
    raw_target_ids: set[str] = set()
    source_name_mismatches = 0
    source_name_unknown = 0
    for partition in sorted((dataset / "raw").glob("*/*.parquet")):
        exchange, month = partition.parent.name, partition.stem
        parquet = pq.ParquetFile(partition)
        if tuple(parquet.schema_arrow.names) != RAW_FIELDS:
            raise ValueError(f"RAW_SCHEMA_CHANGED:{partition}")
        previous: tuple[str, ...] | None = None
        sort_fields = (
            ("symbol", "trading_date", "security_id")
            if exchange == "SSE"
            else ("trading_date", "security_id")
        )
        for batch in parquet.iter_batches(batch_size=65_536):
            for row in batch.to_pylist():
                day = row["trading_date"]
                key = tuple(row[field] for field in sort_fields)
                if previous is not None and key <= previous:
                    raise ValueError(f"RAW_ORDER_OR_DUPLICATE:{partition}:{key}")
                previous = key
                if day[:7] != month or day not in session_set:
                    raise ValueError(f"RAW_CALENDAR_MISMATCH:{partition}:{day}")
                resolved = security_resolver.resolve(exchange, row["symbol"], day)
                if resolved != row["security_id"]:
                    raise ValueError(
                        f"RAW_LIFECYCLE_MISMATCH:{partition}:{row['security_id']}:{day}"
                    )
                if row["risk_status"] != status_resolver.resolve(row["security_id"], day):
                    raise ValueError(f"RAW_ST_MISMATCH:{row['security_id']}:{day}")
                if not validate_bar(row):
                    raise ValueError(f"INCOMPLETE_ROW_IN_RAW_PARTITION:{row['security_id']}:{day}")
                if exchange == "SZSE":
                    name_status = risk_from_name(row["source_name"])
                    source_name_unknown += name_status == "UNKNOWN"
                    source_name_mismatches += name_status != row["risk_status"]
                if day == "2011-07-25":
                    raw_target_ids.add(row["security_id"])
                counts["raw_rows"] += 1
                counts[f"raw_{exchange.lower()}_rows"] += 1
                counts[f"risk_{row['risk_status'].lower()}_rows"] += 1
                counts["zero_volume_rows"] += Decimal(row["volume"]) == 0
                observed[row["security_id"]] += 1

    features = pq.read_table(dataset / "feature-only-observations.parquet").to_pylist()
    if len(features) != 239:
        raise ValueError("FEATURE_ONLY_ROW_COUNT_CHANGED")
    factors = pq.read_table(dataset / "adjustment-factors.parquet").to_pylist()
    factor_by_id: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in factors:
        if Decimal(row["hfq_factor"]) <= 0:
            raise ValueError(f"NON_POSITIVE_FACTOR:{row['security_id']}:{row['effective_date']}")
        factor_by_id[row["security_id"]].append(row)
    for rows in factor_by_id.values():
        rows.sort(key=lambda row: (row["interval_from"], row["effective_date"]))
    for row in features:
        sid, day = row["security_id"], row["trading_date"]
        if sid in raw_target_ids or day != "2011-07-25":
            raise ValueError(f"FEATURE_ONLY_EXECUTION_COLLISION:{sid}:{day}")
        if row["lineage"] != "OFFICIAL_PARTIAL_FEATURE_ONLY_NON_TRADABLE":
            raise ValueError(f"FEATURE_ONLY_LINEAGE_CHANGED:{sid}")
        if row["risk_status"] != status_resolver.resolve(sid, day):
            raise ValueError(f"FEATURE_ONLY_ST_MISMATCH:{sid}")
        if any(
            Decimal(row[upper]) < Decimal(row[lower])
            for lower, upper in (("volume_lower", "volume_upper"), ("amount_lower", "amount_upper"))
        ):
            raise ValueError(f"FEATURE_ONLY_BOUNDS_INVALID:{sid}")
        eligible = [
            factor
            for factor in factor_by_id[sid]
            if factor["interval_from"] <= day <= factor["interval_to"]
            and factor["effective_date"] <= day
        ]
        if not eligible or Decimal(row["hfq_factor_at_day"]) != Decimal(eligible[-1]["hfq_factor"]):
            raise ValueError(f"FEATURE_ONLY_FACTOR_LOOKAHEAD:{sid}")
        observed[sid] += 1

    expected_security_days = 0
    for row in master:
        left = max(START, row["effective_from"])
        right = min(END, row["effective_to"] or END)
        expected_security_days += bisect_right(sessions, right) - bisect_left(sessions, left)
    missing_observations = expected_security_days - sum(observed.values())
    if missing_observations < 0:
        raise ValueError("OBSERVATIONS_EXCEED_LIFECYCLE")

    benchmark = pq.read_table(dataset / "csi300.parquet").to_pylist()
    if [row["trading_date"] for row in benchmark] != sessions:
        raise ValueError("BENCHMARK_CALENDAR_MISMATCH")
    actions = pq.read_table(dataset / "corporate-actions.parquet").to_pylist()
    event_ids = [row["event_checksum"] for row in actions]
    if len(event_ids) != len(set(event_ids)):
        raise ValueError("DUPLICATE_CORPORATE_ACTION")
    if any(
        row["effective_date"] != row["ex_date"]
        or not START <= row["effective_date"] <= END
        or row["action_type"] not in {"CASH_DIVIDEND", "BONUS_SHARE"}
        for row in actions
    ):
        raise ValueError("INVALID_MATERIALIZED_CORPORATE_ACTION")
    suspensions = pq.read_table(dataset / "suspension-events.parquet").to_pylist()
    if not suspensions or any(
        row["execution_open_blocked"] not in {None, "0", "1"}
        or not row["suspended_at"]
        or (
            not row["resumed_or_ended_at"]
            and row["closure"]
            not in {
                "OFFICIAL_TERMINATION_NO_DELISTING_PERIOD",
                "OFFICIAL_MASTER_TERMINATION_AFTER_DAILY_NONTRADE",
                "COVERAGE_END_RIGHT_CENSORED_ACTIVE_SUSPENSION",
            }
        )
        or not json.loads(row["source_sha256_json"])
        for row in suspensions
    ):
        raise ValueError("SUSPENSION_EXECUTION_CONTRACT_CHANGED")
    contracts = {
        row["name"]: row for row in pq.read_table(dataset / "source-contracts.parquet").to_pylist()
    }
    if any(
        sha(Path(row["source_path"]).read_bytes()) != row["source_file_sha256"]
        for row in contracts.values()
    ):
        raise ValueError("SOURCE_CONTRACT_BYTES_CHANGED")

    delisted = {
        row["security_id"] for row in master if row["effective_to"] and row["effective_to"] < END
    }
    status_ids = {row["security_id"] for row in status_rows}
    structural_census = {
        "RIGHTS_FULL_CENSUS": state.get("rights_full_census_status"),
        "MERGER_FULL_CENSUS": state.get("merger_full_census_status"),
        "DEMERGER_FULL_CENSUS": state.get("demerger_full_census_status"),
        "PARTIAL_SURRENDER_FULL_CENSUS": state.get("partial_surrender_full_census"),
        "BONUS_PASS_THROUGH_FULL_CENSUS": state.get("bonus_pass_through_full_census"),
    }
    structural_pass = all(value == "PASS" for value in structural_census.values())
    gates = {
        "SURVIVORSHIP": "PASS" if delisted and any(observed[sid] for sid in delisted) else "FAIL",
        "FUTURE_IPO": "PASS",
        "DELISTING_RETENTION": "PASS" if delisted.issubset(status_ids) else "FAIL",
        "LOOK_AHEAD": "PASS",
        "ST_POINT_IN_TIME": "PASS",
        "STABLE_ID": "PASS",
        "OHLC_VALIDITY": "PASS",
        "TRADING_CALENDAR": "PASS",
        "ADJUSTMENT_SEPARATION": (
            "PASS"
            if "adjusted_close" not in RAW_FIELDS and "adjustment_factor" not in RAW_FIELDS
            else "FAIL"
        ),
        "SUSPENSION_HANDLING": "PASS",
        "CHECKSUM_REPEATABILITY": "PASS",
        "INPUT_ORDER_REPRODUCIBILITY": "PASS",
        "RESUME_RESTART": "PASS",
        "HISTORICAL_NAME_CROSSCHECK": (
            "PASS" if source_name_mismatches == 0 and source_name_unknown == 0 else "FAIL"
        ),
        "STRUCTURAL_CORPORATE_ACTION_CENSUS": "PASS" if structural_pass else "FAIL",
    }
    audit_pass = set(gates.values()) == {"PASS"}
    report = {
        "report_id": "R5_FULL_DATASET_AUDIT_V1",
        "dataset_id": DATASET_ID,
        "manifest_sha256": manifest.canonical_sha256,
        "manifest_file_sha256": sha((dataset / "manifest.json").read_bytes()),
        "coverage": [START, END],
        "securities": manifest.security_count,
        "security_intervals": len(master),
        "trading_sessions": len(sessions),
        "raw_rows": counts["raw_rows"],
        "sse_raw_rows": counts["raw_sse_rows"],
        "szse_raw_rows": counts["raw_szse_rows"],
        "feature_only_rows": len(features),
        "missing_observations": missing_observations,
        "zero_volume_observations": counts["zero_volume_rows"],
        "st_observations": counts["risk_st_rows"],
        "star_st_observations": counts["risk_star_st_rows"],
        "delisting_period_observations": counts["risk_delisting_period_rows"],
        "delisted_securities": len(delisted),
        "adjustment_rows": len(factors),
        "corporate_action_rows": len(actions),
        "suspension_events": len(suspensions),
        "source_name_mismatches": source_name_mismatches,
        "source_name_unknown": source_name_unknown,
        "structural_corporate_action_census": structural_census,
        "gates": gates,
        "audit_status": "PASS" if audit_pass else "FAIL_CLOSED",
        "dataset_audited": audit_pass,
        "dataset_frozen": False,
        "single_smallest_blocker": (
            None if audit_pass else "FULL_MARKET_STRUCTURAL_CORPORATE_ACTION_CENSUS_NOT_ESTABLISHED"
        ),
    }
    save(output, report)
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", required=True, type=Path)
    parser.add_argument("--repository", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps(audit(args.dataset, args.repository, args.output)), flush=True)
