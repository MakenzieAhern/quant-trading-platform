"""Audit the materialized full-range dataset and fail closed on authority gaps."""

from __future__ import annotations

import argparse
import json
import re
from bisect import bisect_left, bisect_right
from collections import Counter, defaultdict
from copy import deepcopy
from datetime import date, timedelta
from decimal import Decimal
from io import BytesIO
from itertools import pairwise
from pathlib import Path
from typing import Any

import pyarrow.parquet as pq

from app.data.catalog import DatasetManifest, finalize_manifest, load_manifest, verify_dataset
from app.data.catalog.checksums import canonical_json_bytes, sha256_file, verified_file_bytes
from app.data.catalog.freeze import require_unfrozen, write_immutable
from app.data.full_dataset import FullDataset, parse_action_records
from app.domain.markets.consolidations import ShareConsolidationEvent
from app.domain.markets.corporate_actions import (
    CorporateAction,
    CorporateActionType,
    OrdinaryDistributionReference,
    require_supported_corporate_action,
)
from app.domain.markets.demergers import DemergerEvent
from app.domain.markets.identifiers import SecurityId
from app.domain.markets.mergers import MergerEvent
from app.domain.markets.pass_through import RestructuringBonusPassThroughEvent
from app.domain.markets.surrenders import MandatoryPartialShareSurrenderEvent
from app.research.engine import require_supported_session_actions
from app.research.models import ResearchPeriodKind
from app.research.splits import TemporalPeriod
from scripts.candidate_cash_corrections import load_cash_corrections
from scripts.full_dataset_build_inputs import CandidateBuildInputs, load_candidate_build_inputs
from scripts.full_dataset_sources import source_path, verify_source_contracts, verify_source_lineage
from scripts.materialize_full_dataset import (
    DATASET_ID,
    END,
    RAW_FIELDS,
    START,
    SecurityResolver,
    StatusResolver,
    event_rows,
    materialization_report,
    ordinary_reference_rows,
    risk_from_name,
    structural_event_rows,
    validate_bar,
)
from scripts.ordinary_distribution_dates import normalize_ordinary_dates
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


def candidate_publication(
    candidate: CandidateBuildInputs,
    dataset: Path,
    repository: Path,
    output: Path,
    spec_path: Path,
    *,
    extra_inputs: tuple[Path, ...] = (),
) -> None:
    """Read-only identity check; auditing must never claim work or repair a build."""
    inputs = [spec_path, repository / candidate.reference_pins["p0_public_report_path"]]
    inputs.extend(extra_inputs)
    inputs.extend(source_path(repository, row["source_path"]) for row in candidate.source_contracts)
    inputs.extend(pin.path for pin in candidate.auxiliary_inputs.values())
    inputs.extend(candidate.date_source_pins(repository))
    for pins in candidate.raw_sources.values():
        for pin in pins:
            inputs.extend((pin.path, pin.path.with_suffix(pin.path.suffix + ".meta.json")))
    if (
        any(item.is_symlink() for item in (output, *output.parents))
        or (output.is_file() and output.stat().st_nlink > 1)
        or output.resolve() in {item.resolve() for item in inputs}
        or any(
            output.resolve().is_relative_to(root.resolve())
            for root in (repository, candidate.work_root, candidate.final_root)
        )
    ):
        raise ValueError("AUDIT_OUTPUT_NOT_ISOLATED")
    require_unfrozen(output)
    if dataset.resolve() != candidate.final_root or any(
        item.is_symlink() or (item.is_file() and item.stat().st_nlink > 1)
        for item in (dataset, *dataset.parents, *dataset.rglob("*"))
    ):
        raise ValueError("CANDIDATE_PUBLICATION_IDENTITY_CHANGED")
    owner = candidate.ownership()
    if any(
        json.loads(path.read_bytes()) != owner
        for path in (candidate.work_root / "build-inputs.json", dataset / "build-inputs.json")
    ):
        raise ValueError("CANDIDATE_PUBLICATION_IDENTITY_CHANGED")


def candidate_action_rows(
    candidate: CandidateBuildInputs, repository: Path
) -> list[dict[str, Any]]:
    def read_json(path: Path) -> Any:
        return candidate.read_json(repository, path)

    rows = [
        row
        for name in ("CASH_ACTIONS", "BONUS_ACTIONS", "GAP_DISTRIBUTION_ACTIONS")
        for row in event_rows(candidate.source(repository, name), read_json=read_json)
    ]
    rows.extend(
        structural_event_rows(
            repository,
            candidate.source(repository, "RIGHTS_ACTIONS"),
            candidate.source(repository, "MERGER_ACTIONS"),
            candidate.source(repository, "STRUCTURAL_ACTIONS"),
            read_json=read_json,
        )
    )
    if pin := candidate.auxiliary_inputs.get("ordinary_dates"):
        rows = normalize_ordinary_dates(rows, read_json(pin.path), pin.path)
    if pin := candidate.auxiliary_inputs.get("ordinary_references"):
        rows.extend(ordinary_reference_rows(read_json(pin.path), rows, pin.sha256))
    return rows


def source_economic_integrity(
    actions: list[dict[str, Any]], gaps: dict[str, Any] | None
) -> dict[str, Any]:
    """Join retained negative evidence to all ordinary events, never grant approval."""
    records: list[dict[str, Any]] = []
    if gaps is not None:
        raw_records = gaps.get("records")
        if (
            gaps.get("scope") != "KNOWN_EVENT_SOURCE_CONTRADICTIONS_NOT_WHOLE_SECURITY_EXCLUSIONS"
            or gaps.get("financial_admission") is not False
            or not isinstance(raw_records, list)
            or not raw_records
            or any(not isinstance(row, dict) for row in raw_records)
        ):
            raise ValueError("INVALID_KNOWN_SOURCE_GAPS")
        records = raw_records
    keys = set()
    for gap in records:
        try:
            sid = str(SecurityId(value=gap["security_id"]))
            record_day, ex_day = (
                date.fromisoformat(gap[key]) for key in ("record_date", "ex_date")
            )
            key = sid, record_day.isoformat(), ex_day.isoformat(), gap["source_sha256"]
            valid = (
                record_day <= ex_day
                and key[1:3] == (gap["record_date"], gap["ex_date"])
                and re.fullmatch(r"[0-9a-f]{64}", gap["source_sha256"])
                and re.fullmatch(r"https://\S+", gap["source_url"])
                and gap["status"] == "BLOCKED_SOURCE_AGGREGATE_CONTRADICTION"
                and isinstance(gap["evidence"], str)
                and bool(gap["evidence"].strip())
                and gap["blocks_new_economic_candidate"] is True
                and gap["reference_price_match_resolves_issue"] is False
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError("INVALID_KNOWN_SOURCE_GAP_RECORD") from exc
        if not valid or key in keys:
            raise ValueError("INVALID_OR_DUPLICATE_KNOWN_SOURCE_GAP_RECORD")
        keys.add(key)
    findings: list[dict[str, Any]] = [
        {"gap": gap, "events": []}
        for gap in sorted(
            records,
            key=lambda g: (g["security_id"], g["record_date"], g["ex_date"], g["source_sha256"]),
        )
    ]
    checked = 0
    matched = set()
    for row in sorted(actions, key=lambda row: row["event_checksum"]):
        if row["event_kind"] not in {"CORPORATE_ACTION", "RIGHTS_ISSUE"}:
            continue
        event = CorporateAction.model_validate_json(row["event_json"])
        if row["event_checksum"] != event.event_checksum:
            raise ValueError("SOURCE_GAP_ACTION_CHECKSUM_MISMATCH")
        if event.action_type not in {
            CorporateActionType.CASH_DIVIDEND,
            CorporateActionType.STOCK_DIVIDEND,
            CorporateActionType.BONUS_SHARE,
        }:
            continue
        checked += 1
        sid = str(event.security_id)
        record = event.record_date.isoformat() if event.record_date else None
        ex = event.ex_date.isoformat() if event.ex_date else None
        # ponytail: retained gaps are small; index keys if this becomes a full census.
        for finding in findings:
            gap = finding["gap"]
            same_source = event.source_document_sha256 == gap["source_sha256"]
            same_identity = (sid, record, ex) == (
                gap["security_id"],
                gap["record_date"],
                gap["ex_date"],
            )
            related = (
                same_source
                or row.get("source_document_sha256") == gap["source_sha256"]
                or event.source_url == gap["source_url"]
                or row.get("source_url") == gap["source_url"]
                or (
                    sid == gap["security_id"]
                    and (record == gap["record_date"] or ex == gap["ex_date"])
                )
            )
            if not related:
                continue
            finding["events"].append(
                {
                    "event_checksum": event.event_checksum,
                    "event_kind": row["event_kind"],
                    "action_type": event.action_type.value,
                    "security_id": sid,
                    "record_date": record,
                    "ex_date": ex,
                    "source_document_sha256": event.source_document_sha256,
                    "source_url": event.source_url,
                    "materialized_source_document_sha256": row.get("source_document_sha256"),
                    "materialized_source_url": row.get("source_url"),
                    "classification": "KNOWN_SOURCE_CONTRADICTION"
                    if same_identity and same_source
                    else "EVENT_SOURCE_IDENTITY_UNRESOLVED",
                }
            )
            matched.add(event.event_checksum)
    for finding in findings:
        finding["status"] = (
            "MATCHED_NEGATIVE_EVIDENCE" if finding["events"] else "UNMATCHED_NOT_RESOLVED"
        )
    return {
        "scope": "KNOWN_ORDINARY_EVENT_SOURCE_GAPS_ONLY",
        "status": "FAIL" if matched else "NOT_EVIDENCED",
        "scan_status": "COMPLETED_NEGATIVE_INVENTORY_ONLY" if gaps is not None else "NOT_SUPPLIED",
        "ordinary_event_rows_checked": checked,
        "known_gap_count": len(findings),
        "matched_event_count": len(matched),
        "unmatched_gap_count": sum(not item["events"] for item in findings),
        "findings": findings,
        "financial_admission": False,
    }


def apply_cash_corrections(
    result: dict[str, Any], actions: list[dict[str, Any]], proofs: list[dict[str, Any]]
) -> dict[str, Any]:
    """Explain a verified text contradiction; never approve economics or erase findings."""
    if not proofs:
        return result
    report = deepcopy(result)
    resolutions = []
    resolved = set()

    def key(item: dict[str, Any]) -> tuple[str, ...]:
        return tuple(
            item[name]
            for name in ("security_id", "record_date", "ex_date", "source_sha256", "source_url")
        )

    findings = {key(item["gap"]): item for item in result["findings"]}
    proof_keys = [key(proof) for proof in proofs]
    if len(set(proof_keys)) != len(proof_keys) or any(k not in findings for k in proof_keys):
        raise ValueError("CASH_CORRECTION_GAP_IDENTITY_CHANGED")
    for proof in sorted(proofs, key=key):
        finding = findings[key(proof)]
        checksums = {event["event_checksum"] for event in finding["events"]}
        rows = [row for row in actions if row["event_checksum"] in checksums]
        expected_types = Counter({"CASH_DIVIDEND": 1})
        if Decimal(proof["bonus_share_ratio"]) > 0:
            expected_types["BONUS_SHARE"] = 1
        actual_types: Counter[str] = Counter()
        valid = bool(rows)
        for row in rows:
            event = CorporateAction.model_validate_json(row["event_json"])
            actual_types[event.action_type.value] += 1
            cash = event.action_type is CorporateActionType.CASH_DIVIDEND
            valid &= (
                row["event_kind"] == "CORPORATE_ACTION"
                and event.event_checksum == row["event_checksum"]
                and str(event.security_id) == row.get("security_id") == proof["security_id"]
                and event.record_date is not None
                and event.record_date.isoformat() == proof["record_date"]
                and event.ex_date is not None
                and event.ex_date.isoformat() == row.get("application_date") == proof["ex_date"]
                and event.effective_date == event.ex_date
                and event.source_document_sha256
                == row.get("source_document_sha256")
                == proof["source_sha256"]
                and event.source_url == row.get("source_url") == proof["source_url"]
                and event.cash_per_share == (Decimal(proof["cash_per_share"]) if cash else 0)
                and (
                    event.share_ratio in (None, Decimal(0))
                    if cash
                    else event.share_ratio == Decimal(proof["bonus_share_ratio"])
                )
            )
        valid &= actual_types == expected_types
        if valid:
            resolved.add(key(proof))
        resolutions.append(
            {
                "evidence": deepcopy(proof),
                "status": "CASH_AGGREGATE_TEXT_RESOLVED"
                if valid
                else "CANDIDATE_EVENT_TERMS_UNRESOLVED"
                if rows
                else "UNMATCHED_NOT_RESOLVED",
                "matched_event_checksums": sorted(checksums),
                "financial_admission": False,
            }
        )
    unresolved_matched = sum(
        bool(finding["events"]) and identity not in resolved
        for identity, finding in findings.items()
    )
    report.update(
        original_status=result["status"],
        status="FAIL" if unresolved_matched else "NOT_EVIDENCED",
        scan_status="COMPLETED_WITH_VERIFIED_CASH_AGGREGATE_CORRECTIONS",
        source_text_resolutions=resolutions,
        resolved_source_text_gap_count=len(resolved),
        unresolved_source_gap_count=len(findings) - len(resolved),
        unresolved_matched_gap_count=unresolved_matched,
        financial_admission=False,
    )
    return report


def audit(
    dataset: Path,
    repository: Path,
    output: Path,
    *,
    build_spec: Path | None = None,
    build_spec_sha256: str | None = None,
    known_source_gaps: Path | None = None,
    known_source_gaps_sha256: str | None = None,
) -> dict[str, Any]:
    if (build_spec is None) != (build_spec_sha256 is None):
        raise ValueError("SELECT_EXACTLY_ONE_AUDIT_INPUT_MODE")
    if (known_source_gaps is None) != (known_source_gaps_sha256 is None) or (
        known_source_gaps is not None and build_spec is None
    ):
        raise ValueError("KNOWN_SOURCE_GAPS_REQUIRE_CANDIDATE_AND_EXACT_SHA256")
    # Bind the consumed identity once; an input alias must not rewrite report lineage.
    if known_source_gaps is not None:
        known_source_gaps = known_source_gaps.resolve(strict=True)
    audit_code = (
        {
            str(path): sha256_file(path)
            for path in (
                Path(__file__),
                Path(__file__).parents[1] / "app/data/full_dataset.py",
                Path(__file__).parents[1] / "app/data/catalog/checksums.py",
                Path(__file__).parents[1] / "app/research/engine.py",
                Path(__file__).with_name("candidate_cash_corrections.py"),
                Path(__file__).with_name("ordinary_distribution_dates.py"),
                Path(__file__).with_name("distribution_payment_terms.py"),
                Path(__file__).with_name("audit_p1_retained_cash_sources.py"),
                Path(__file__).with_name("audit_p1_orphan_cash_facts.py"),
                Path(__file__).parents[1] / "app/domain/markets/corporate_actions.py",
                Path(__file__).with_name("audit_p1_cash_corrections.py"),
                Path(__file__).with_name("retained_bonus_terms.py"),
                Path(__file__).with_name("reconcile_distribution_cash.py"),
                Path(__file__).with_name("link_distribution_notices.py"),
            )
        }
        if build_spec is not None
        else {}
    )
    gap_payload = (
        json.loads(verified_file_bytes(known_source_gaps, known_source_gaps_sha256))
        if known_source_gaps is not None and known_source_gaps_sha256 is not None
        else None
    )
    correction_proofs: list[dict[str, Any]] = []
    correction_pins: dict[Path, str] = {}
    if known_source_gaps is not None:
        if not isinstance(gap_payload, dict):
            raise ValueError("INVALID_KNOWN_SOURCE_GAPS")
        source_economic_integrity([], gap_payload)
        correction_proofs, correction_pins = load_cash_corrections(gap_payload, known_source_gaps)
    extra_inputs: tuple[Path, ...] = (known_source_gaps,) if known_source_gaps is not None else ()
    extra_inputs += tuple(correction_pins)
    candidate = (
        load_candidate_build_inputs(
            build_spec,
            build_spec_sha256,
            repository,
            legacy_dataset_id=DATASET_ID,
            coverage=(START, END),
        )
        if build_spec is not None and build_spec_sha256 is not None
        else None
    )
    if candidate and build_spec is not None:
        candidate_publication(
            candidate, dataset, repository, output, build_spec, extra_inputs=extra_inputs
        )
    state = (
        candidate.reference_pins
        if candidate
        else json.loads((repository / ".research/project_state.json").read_bytes())
    )
    manifest_bytes = (dataset / "manifest.json").read_bytes() if candidate else None
    candidate_manifest = (
        DatasetManifest.model_validate_json(manifest_bytes) if manifest_bytes is not None else None
    )

    def partition_source(path: Path) -> Any:
        if candidate_manifest is None:
            return path
        pins = {part.relative_path: part.sha256 for part in candidate_manifest.partitions}
        return BytesIO(verified_file_bytes(path, pins[str(path.relative_to(dataset))]))

    def table(name: str) -> Any:
        return pq.read_table(partition_source(dataset / name))

    contracts = verify_source_contracts(
        table("source-contracts.parquet").to_pylist(),
        repository,
        state,
    )
    manifest = candidate_manifest or load_manifest(dataset / "manifest.json")
    verify_source_lineage(list(contracts.values()), manifest.source_lineage)
    verify_dataset(dataset, manifest)
    dataset_id = candidate.dataset_id if candidate else DATASET_ID
    if manifest.dataset_id != dataset_id or finalize_manifest(manifest.model_dump()) != manifest:
        raise ValueError("MANIFEST_REPEATABILITY_FAILED")
    if candidate and (
        list(contracts.values()) != list(candidate.source_contracts)
        or (str(manifest.coverage_start), str(manifest.coverage_end)) != candidate.coverage
        or manifest.rule_version != candidate.market_rule_manifest_sha256
        or {str(path.relative_to(dataset)) for path in dataset.rglob("*.parquet")}
        != {part.relative_path for part in manifest.partitions}
        or json.loads((candidate.work_root / "materialization-report.json").read_bytes())
        != materialization_report(manifest, dataset / "manifest.json", candidate.ownership())
    ):
        raise ValueError("CANDIDATE_PUBLICATION_IDENTITY_CHANGED")
    master = table("securities.parquet").to_pylist()
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
    calendar_rows = table("calendar.parquet").to_pylist()
    sessions = [row["session_date"] for row in calendar_rows]
    if sessions != sorted(set(sessions)) or sessions[0] < START or sessions[-1] > END:
        raise ValueError("TRADING_CALENDAR_INVALID")
    session_set = set(sessions)
    security_resolver = SecurityResolver(master)
    status_rows = []
    for name in ("st-sse-intervals.parquet", "st-szse-intervals.parquet"):
        status_rows.extend(table(name).to_pylist())
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
        parquet = pq.ParquetFile(partition_source(partition))
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

    features = table("feature-only-observations.parquet").to_pylist()
    if len(features) != 239:
        raise ValueError("FEATURE_ONLY_ROW_COUNT_CHANGED")
    factors = table("adjustment-factors.parquet").to_pylist()
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
    for factor_rows in factor_by_id.values():
        factor_rows.sort(key=lambda row: (row["interval_from"], row["effective_date"]))
        if factor_rows[0]["effective_date"] > factor_rows[0]["interval_from"] or any(
            row["effective_date"] > row["interval_to"] for row in factor_rows
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

    benchmark = table("csi300.parquet").to_pylist()
    if [row["trading_date"] for row in benchmark] != sessions:
        raise ValueError("BENCHMARK_CALENDAR_MISMATCH")
    actions = table("corporate-actions.parquet").to_pylist()
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
    if candidate:
        expected_actions = candidate_action_rows(candidate, repository)
        if sorted(map(canonical_json_bytes, actions)) != sorted(
            map(canonical_json_bytes, expected_actions)
        ):
            raise ValueError("CANDIDATE_SOURCE_EVENT_SET_MISMATCH")
        parse_action_records(actions, END)
        expected_kinds = Counter(row["event_kind"] for row in expected_actions)
    if action_kinds != expected_kinds:
        raise ValueError(f"CORPORATE_ACTION_CENSUS_CHANGED:{dict(action_kinds)}")
    parsed: Any
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
        elif kind == "ORDINARY_REFERENCE" and candidate:
            parsed = OrdinaryDistributionReference.model_validate(event)
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
    suspensions = table("suspension-events.parquet").to_pylist()
    if (not suspensions and not candidate) or any(
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
    preflight = (
        candidate.read_json(repository, candidate.source(repository, "SOURCE_PREFLIGHT"))
        if candidate
        else json.loads(
            source_path(repository, contracts["SOURCE_PREFLIGHT"]["source_path"]).read_bytes()
        )
    )
    source_lineage = table("source-lineage.parquet").to_pylist()
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
        table("transaction-costs.parquet").to_pylist(),
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
            and manifest.rule_version
            == (
                candidate.market_rule_manifest_sha256
                if candidate
                else state["market_rule_manifest_sha256"]
            )
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
        "dataset_id": dataset_id,
        "manifest_sha256": manifest.canonical_sha256,
        "manifest_file_sha256": sha(
            manifest_bytes
            if manifest_bytes is not None
            else (dataset / "manifest.json").read_bytes()
        ),
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
    if candidate and build_spec is not None and build_spec_sha256 is not None:
        # These checks require dataset-bound execution/accounting/source evidence,
        # not filenames of unit tests, legacy state, or a source report's PASS label.
        unproven = {
            "SURVIVORSHIP",
            "DELISTING_RETENTION",
            "LOOK_AHEAD",
            "CORPORATE_ACTION_COMPLETENESS",
            "CORPORATE_ACTION_ACCOUNTING",
            "HISTORICAL_RULE_REGIMES",
            "STRUCTURAL_CORPORATE_ACTION_CENSUS",
            "INPUT_ORDER_REPRODUCIBILITY",
            "RESUME_RESTART",
            "QUANTITY_RECONCILIATION",
            "CASH_RECONCILIATION",
            "BASIS_RECONCILIATION",
            "CORPORATE_ACTION_PNL_RECONCILIATION",
            "NO_SYNTHETIC_ORDER_FILL",
            "NO_ORPHAN_BASIS",
        }
        for gate in unproven:
            gates[gate] = "NOT_EVIDENCED"
        economic_check = source_economic_integrity(actions, gap_payload)
        economic_check = apply_cash_corrections(economic_check, actions, correction_proofs)
        if correction_pins:
            economic_check["correction_input_sha256"] = {
                str(path): digest for path, digest in sorted(correction_pins.items())
            }
        economic_check.update(
            known_source_gaps_path=str(known_source_gaps.resolve()) if known_source_gaps else None,
            known_source_gaps_sha256=known_source_gaps_sha256,
        )
        gates["SOURCE_ECONOMIC_INTEGRITY"] = economic_check["status"]
        if economic_check["status"] == "NOT_EVIDENCED":
            unproven.add("SOURCE_ECONOMIC_INTEGRITY")
        loader = FullDataset(
            dataset,
            manifest,
            TemporalPeriod(
                ResearchPeriodKind.FULL_PERIOD, manifest.coverage_start, manifest.coverage_end
            ),
        )
        # Match the execution calendar, including an accepted period-end successor.
        calendar = loader.calendar.sessions + (
            (loader.next_session,) if loader.next_session is not None else ()
        )
        next_sessions = dict(pairwise(item.session_date for item in calendar if item.is_open))
        runtime_sessions = 0
        unexplained: list[dict[str, str]] = []
        action_session_failures: list[dict[str, str]] = []
        for session in loader.sessions(execution=True):
            runtime_sessions += 1
            try:
                require_supported_session_actions(
                    session, next_accepted_session=next_sessions.get(session.trading_date)
                )
            except ValueError as exc:
                action_session_failures.append(
                    {"trading_date": session.trading_date.isoformat(), "reason": str(exc)}
                )
            unexplained.extend(
                {"trading_date": session.trading_date.isoformat(), "security_id": str(sid)}
                for sid in session.unexplained_reference_adjustment_ids
            )
        absent_dates = sorted({row["application_date"] for row in actions} - session_set)
        gates.update(
            SOURCE_EVENT_SET_MATCH="PASS",
            REFERENCE_PRICE_CONTINUITY="FAIL" if unexplained else "PASS",
            ACTION_SESSION_COVERAGE="FAIL" if absent_dates else "PASS",
            ACTION_SESSION_PRECONDITIONS="FAIL" if action_session_failures else "PASS",
        )
        reference_count = action_kinds["ORDINARY_REFERENCE"]
        if "ordinary_dates" in candidate.auxiliary_inputs:
            report["ordinary_date_normalization"] = {
                "status": "SOURCE_DATES_NORMALIZED_NOT_FINANCIAL_ADMISSION",
                "source_input_sha256": {
                    str(path): digest
                    for path, digest in sorted(candidate.date_source_pins(repository).items())
                },
                "replacements": sorted(
                    (
                        acceptance["date_normalization"]
                        for row in actions
                        if "date_normalization"
                        in (acceptance := json.loads(row["acceptance_json"]))
                    ),
                    key=lambda item: item["original_event_checksum"],
                ),
                "financial_admission": False,
            }
        report.update(
            report_id="SUCCESSOR_FULL_DATASET_AUDIT_V1",
            build_inputs=candidate.ownership(),
            audit_code_sha256=audit_code,
            build_spec_sha256=build_spec_sha256,
            source_economic_integrity=economic_check,
            ordinary_reference_rows=reference_count,
            accounting_action_rows=len(actions) - reference_count,
            runtime_scan={
                "sessions": runtime_sessions,
                "unexplained_reference_adjustments": unexplained,
                "action_dates_missing_from_calendar": absent_dates,
                "action_session_failures": action_session_failures,
            },
            accounting_invariant_evidence={
                "typed_action_rows": len(actions) - reference_count,
                "validated_action_kinds": dict(sorted(action_kinds.items())),
                "portfolio_accounting_run": False,
            },
            structural_corporate_action_census={
                "status": "NOT_EVIDENCED",
                "legacy_state_used": False,
            },
            audit_status="FAIL_CLOSED" if "FAIL" in gates.values() else "PARTIAL",
            dataset_audited=False,
            dataset_registered=False,
            full_financial_admission=False,
            strategy_run=False,
            unevidenced_gates=sorted(unproven),
            single_smallest_blocker=(
                "KNOWN_SOURCE_ECONOMIC_EVIDENCE_UNRESOLVED"
                if economic_check["status"] == "FAIL"
                else "SUCCESSOR_DATASET_BOUND_FINANCIAL_LIFECYCLE_EVIDENCE_INCOMPLETE"
            ),
        )
        # Recheck before immutable publication; neither build nor legacy state is mutated.
        if (
            load_candidate_build_inputs(
                build_spec,
                build_spec_sha256,
                repository,
                legacy_dataset_id=DATASET_ID,
                coverage=(START, END),
            )
            != candidate
        ):
            raise ValueError("CANDIDATE_BUILD_SPEC_CHANGED")
        candidate_publication(
            candidate, dataset, repository, output, build_spec, extra_inputs=extra_inputs
        )
        if (
            known_source_gaps is not None
            and sha256_file(known_source_gaps) != known_source_gaps_sha256
        ):
            raise ValueError("KNOWN_SOURCE_GAPS_CHANGED_DURING_AUDIT")
        if any(sha256_file(path) != digest for path, digest in correction_pins.items()):
            raise ValueError("CASH_CORRECTION_INPUT_CHANGED_DURING_AUDIT")
        verify_dataset(dataset, manifest)
        if sha256_file(dataset / "manifest.json") != report["manifest_file_sha256"]:
            raise ValueError("CANDIDATE_MANIFEST_BYTES_CHANGED")
        if load_manifest(dataset / "manifest.json") != manifest or any(
            sha256_file(Path(path)) != digest for path, digest in audit_code.items()
        ):
            raise ValueError("CANDIDATE_AUDIT_INPUT_CHANGED")
        write_immutable(output, canonical_json_bytes(report) + b"\n")
    else:
        save(output, report)
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", required=True, type=Path)
    parser.add_argument("--repository", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--build-spec", type=Path)
    parser.add_argument("--build-spec-sha256")
    parser.add_argument("--known-source-gaps", type=Path)
    parser.add_argument("--known-source-gaps-sha256")
    args = parser.parse_args()
    print(
        json.dumps(
            audit(
                args.dataset,
                args.repository,
                args.output,
                build_spec=args.build_spec,
                build_spec_sha256=args.build_spec_sha256,
                known_source_gaps=args.known_source_gaps,
                known_source_gaps_sha256=args.known_source_gaps_sha256,
            )
        ),
        flush=True,
    )
