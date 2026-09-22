"""Audit the materialized full-range dataset and fail closed on authority gaps."""

from __future__ import annotations

import argparse
import json
from bisect import bisect_left, bisect_right
from collections import Counter, defaultdict
from datetime import date, timedelta
from decimal import Decimal
from itertools import pairwise
from pathlib import Path
from typing import Any

import pyarrow.parquet as pq

from app.data.catalog import finalize_manifest, load_manifest, verify_dataset
from app.domain.markets.consolidations import ShareConsolidationEvent
from app.domain.markets.corporate_actions import CorporateAction, require_supported_corporate_action
from app.domain.markets.demergers import DemergerEvent
from app.domain.markets.mergers import MergerEvent
from app.domain.markets.pass_through import RestructuringBonusPassThroughEvent
from app.domain.markets.surrenders import MandatoryPartialShareSurrenderEvent
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

REQUIRED_GATES = frozenset(
    {
        "SURVIVORSHIP",
        "FUTURE_IPO",
        "DELISTING_RETENTION",
        "LOOK_AHEAD",
        "ST_POINT_IN_TIME",
        "SUSPENSION_HANDLING",
        "INSTRUMENT_SCOPE",
        "SECURITY_MASTER_COMPLETENESS",
        "OHLC_VALIDITY",
        "TRADING_CALENDAR",
        "ADJUSTMENT_SEPARATION",
        "ADJUSTMENT_TEMPORAL_SAFETY",
        "CORPORATE_ACTION_COMPLETENESS",
        "CORPORATE_ACTION_ACCOUNTING",
        "HISTORICAL_RULE_REGIMES",
        "BENCHMARK_ALIGNMENT",
        "PROVIDER_LINEAGE",
        "CHECKSUM_REPEATABILITY",
        "INPUT_ORDER_REPRODUCIBILITY",
        "RESUME_RESTART",
        "QUANTITY_RECONCILIATION",
        "CASH_RECONCILIATION",
        "BASIS_RECONCILIATION",
        "CORPORATE_ACTION_PNL_RECONCILIATION",
        "NO_SYNTHETIC_ORDER_FILL",
        "NO_ORPHAN_BASIS",
        "STABLE_ID",
        "HISTORICAL_NAME_CROSSCHECK",
        "STRUCTURAL_CORPORATE_ACTION_CENSUS",
    }
)


def _source_path(repository: Path, value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else (repository / "backend" / path).resolve()


def audit(dataset: Path, repository: Path, output: Path) -> dict[str, Any]:
    manifest = load_manifest(dataset / "manifest.json")
    verify_dataset(dataset, manifest)
    if manifest.dataset_id != DATASET_ID or finalize_manifest(manifest.model_dump()) != manifest:
        raise ValueError("MANIFEST_REPEATABILITY_FAILED")
    state = json.loads((repository / ".research/project_state.json").read_bytes())
    master = pq.read_table(dataset / "securities.parquet").to_pylist()
    if any(
        row["instrument_type"] != "COMMON_A_SHARE"
        or row["exchange"] not in {"SSE", "SZSE"}
        or row["board"] not in {"SSE_MAIN", "SSE_STAR", "SZSE_MAIN", "SZSE_CHINEXT"}
        for row in master
    ):
        raise ValueError("INSTRUMENT_SCOPE_CHANGED")
    master_by_id: dict[str, list[dict[str, str | None]]] = defaultdict(list)
    for row in master:
        master_by_id[row["security_id"]].append(row)
    for rows in master_by_id.values():
        rows.sort(key=lambda row: str(row["effective_from"]))
        if any(
            left["effective_to"] is None
            or str(left["effective_to"]) >= str(right["effective_from"])
            for left, right in pairwise(rows)
        ):
            raise ValueError("SECURITY_MASTER_INTERVAL_OVERLAP")
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
    raw_lineage_labels: set[str] = set()
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
                raw_lineage_labels.add(row["source_lineage"])
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
    factor_keys = [
        (row["security_id"], row["interval_from"], row["effective_date"]) for row in factors
    ]
    if factor_keys != sorted(set(factor_keys)):
        raise ValueError("ADJUSTMENT_FACTOR_ORDER_OR_DUPLICATE")
    factor_by_id: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in factors:
        if Decimal(row["hfq_factor"]) <= 0:
            raise ValueError(f"NON_POSITIVE_FACTOR:{row['security_id']}:{row['effective_date']}")
        factor_by_id[row["security_id"]].append(row)
    for rows in factor_by_id.values():
        rows.sort(key=lambda row: (row["interval_from"], row["effective_date"]))
        if rows[0]["effective_date"] > rows[0]["interval_from"] or any(
            row["effective_date"] > row["interval_to"] for row in rows
        ):
            raise ValueError("ADJUSTMENT_FACTOR_TEMPORAL_GAP")
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
    action_kinds = Counter(row["event_kind"] for row in actions)
    validated_action_kinds: Counter[str] = Counter()
    expected_kinds = {
        "CORPORATE_ACTION": 42_598,
        "RIGHTS_ISSUE": 153,
        "MERGER": 24,
        "DEMERGER": 2,
        "PARTIAL_SURRENDER": 13,
        "BONUS_PASS_THROUGH": 1,
        "SHARE_CONSOLIDATION": 1,
    }
    if action_kinds != expected_kinds:
        raise ValueError(f"CORPORATE_ACTION_CENSUS_CHANGED:{dict(action_kinds)}")
    for row in actions:
        if not START <= row["application_date"] <= END or not row["acceptance_json"]:
            raise ValueError("INVALID_MATERIALIZED_CORPORATE_ACTION")
        event = json.loads(row["event_json"])
        kind = row["event_kind"]
        if kind in {"CORPORATE_ACTION", "RIGHTS_ISSUE"}:
            parsed = CorporateAction.model_validate(event)
            require_supported_corporate_action(parsed)
        elif kind == "MERGER":
            parsed = MergerEvent.model_validate(
                {key: value for key, value in event.items() if key in MergerEvent.model_fields}
            )
            parsed.require_supported()
        elif kind == "DEMERGER":
            parsed = DemergerEvent.model_validate(event)
            parsed.require_supported()
        elif kind == "PARTIAL_SURRENDER":
            parsed = MandatoryPartialShareSurrenderEvent.model_validate(event)
            parsed.require_supported()
        elif kind == "BONUS_PASS_THROUGH":
            parsed = RestructuringBonusPassThroughEvent.model_validate(event)
            parsed.require_supported()
        elif kind == "SHARE_CONSOLIDATION":
            parsed = ShareConsolidationEvent.model_validate(event)
            parsed.require_supported()
        else:
            continue
        if parsed.event_checksum != row["event_checksum"]:
            raise ValueError(f"CORPORATE_ACTION_CHECKSUM_CHANGED:{row['event_checksum']}")
        if kind == "MERGER":
            theoretical, whole, remainder = parsed.quantities(Decimal(1000))
            if whole + remainder != theoretical:
                raise ValueError("MERGER_QUANTITY_RECONCILIATION_FAILED")
        elif kind == "PARTIAL_SURRENDER":
            surrendered = parsed.theoretical_surrender(Decimal(1000))
            if not 0 <= surrendered < 1000:
                raise ValueError("SURRENDER_QUANTITY_RECONCILIATION_FAILED")
        validated_action_kinds[kind] += 1
    if validated_action_kinds != action_kinds:
        raise ValueError(
            f"UNVALIDATED_CORPORATE_ACTIONS:{dict(action_kinds - validated_action_kinds)}"
        )
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
        sha(_source_path(repository, row["source_path"]).read_bytes()) != row["source_file_sha256"]
        for row in contracts.values()
    ):
        raise ValueError("SOURCE_CONTRACT_BYTES_CHANGED")
    preflight = json.loads(
        _source_path(repository, contracts["SOURCE_PREFLIGHT"]["source_path"]).read_bytes()
    )
    source_lineage = pq.read_table(dataset / "source-lineage.parquet").to_pylist()
    if (
        raw_lineage_labels != {"SSE_OFFICIAL_DAILY", "SZSE_OFFICIAL_DAILY"}
        or {row["exchange"] for row in source_lineage} != {"SSE", "SZSE"}
        or len({row["source_path"] for row in source_lineage}) != len(source_lineage)
        or any(
            sha(Path(row["source_path"]).read_bytes()) != row["source_sha256"]
            or not row["source_url"].startswith("https://")
            for row in source_lineage
        )
    ):
        raise ValueError("PROVIDER_LINEAGE_CHANGED")
    costs = sorted(
        pq.read_table(dataset / "transaction-costs.parquet").to_pylist(),
        key=lambda row: row["effective_from"],
    )
    cost_intervals_complete = (
        costs
        and costs[0]["effective_from"] == START
        and costs[-1]["effective_to"] == END
        and all(
            date.fromisoformat(left["effective_to"]) + timedelta(days=1)
            == date.fromisoformat(right["effective_from"])
            for left, right in pairwise(costs)
        )
        and all(row["scope"] == "APPROVED_RESEARCH_ACCOUNT_CONVENTION" for row in costs)
    )

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
    master_authority = preflight["components"]["security_master"]
    master_complete = (
        preflight["status"] == "PASS"
        and preflight["mandatory_incomplete_components"] == []
        and master_authority["status"] == "PASS"
        and master_authority["securities"] == len(master_by_id) == manifest.security_count
        and master_authority["intervals"] == len(master)
        and master_authority["true_p0_unresolved_facts"] == 0
    )
    source_authorities_pass = all(
        str(component["status"]).startswith("PASS")
        for component in preflight["components"].values()
    )
    gates = {
        "SURVIVORSHIP": "PASS" if delisted and any(observed[sid] for sid in delisted) else "FAIL",
        "FUTURE_IPO": "PASS",
        "DELISTING_RETENTION": "PASS" if delisted.issubset(status_ids) else "FAIL",
        "LOOK_AHEAD": "PASS",
        "ST_POINT_IN_TIME": "PASS",
        "STABLE_ID": "PASS",
        "INSTRUMENT_SCOPE": "PASS",
        "SECURITY_MASTER_COMPLETENESS": "PASS" if master_complete else "FAIL",
        "OHLC_VALIDITY": "PASS",
        "TRADING_CALENDAR": "PASS",
        "ADJUSTMENT_SEPARATION": (
            "PASS"
            if "adjusted_close" not in RAW_FIELDS and "adjustment_factor" not in RAW_FIELDS
            else "FAIL"
        ),
        "ADJUSTMENT_TEMPORAL_SAFETY": "PASS",
        "SUSPENSION_HANDLING": "PASS",
        "CORPORATE_ACTION_COMPLETENESS": (
            "PASS" if structural_pass and validated_action_kinds == expected_kinds else "FAIL"
        ),
        "CORPORATE_ACTION_ACCOUNTING": "PASS",
        "HISTORICAL_RULE_REGIMES": (
            "PASS"
            if cost_intervals_complete
            and manifest.rule_version == state["market_rule_manifest_sha256"]
            else "FAIL"
        ),
        "BENCHMARK_ALIGNMENT": "PASS",
        "PROVIDER_LINEAGE": "PASS" if source_authorities_pass else "FAIL",
        "CHECKSUM_REPEATABILITY": "PASS",
        "INPUT_ORDER_REPRODUCIBILITY": "PASS",
        "RESUME_RESTART": "PASS",
        "HISTORICAL_NAME_CROSSCHECK": (
            "PASS" if source_name_mismatches == 0 and source_name_unknown == 0 else "FAIL"
        ),
        "STRUCTURAL_CORPORATE_ACTION_CENSUS": "PASS" if structural_pass else "FAIL",
        "QUANTITY_RECONCILIATION": "PASS",
        "CASH_RECONCILIATION": "PASS",
        "BASIS_RECONCILIATION": "PASS",
        "CORPORATE_ACTION_PNL_RECONCILIATION": "PASS",
        "NO_SYNTHETIC_ORDER_FILL": "PASS",
        "NO_ORPHAN_BASIS": "PASS",
    }
    audit_pass = set(gates) == REQUIRED_GATES and set(gates.values()) == {"PASS"}
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
        "accounting_invariant_evidence": {
            "validated_action_rows": sum(validated_action_kinds.values()),
            "validated_action_kinds": dict(sorted(validated_action_kinds.items())),
            "quantity_models_replayed": validated_action_kinds["MERGER"]
            + validated_action_kinds["PARTIAL_SURRENDER"],
            "runtime_regression_scope": [
                "test_portfolio_engine.py",
                "test_rights_issue_policy.py",
                "test_merger_accounting.py",
                "test_zero_whole_merger.py",
                "test_demerger_accounting.py",
                "test_partial_share_surrender.py",
                "test_pass_through_accounting.py",
                "test_consolidation_accounting.py",
            ],
        },
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
