"""Read-only final R3 identity verification; explicit approved freeze is a separate step."""

import argparse
import json
import subprocess
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

import pyarrow.parquet as parquet

from app.data.catalog import load_manifest, verify_dataset
from app.data.catalog.checksums import canonical_json_bytes, canonical_sha256, sha256_file
from app.data.catalog.freeze import MARKER, write_immutable
from scripts.publish_akshare_pilot import ACCEPTED_INPUTS

CHECKS = frozenset(
    [
        "INSTRUMENT_TYPE_SCOPE",
        "NON_A_SHARE_INSTRUMENT_LEAKAGE",
        "INSTRUMENT_CLASSIFICATION_REPRODUCIBILITY",
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
        "RESUME_RESTART",
    ]
)


def verify(staging: Path, dataset: Path, repository: Path) -> dict:
    if dataset.name == "cn-a-pilot-akshare-20230101-20240731-v2":
        from scripts.freeze_revised_pilot import verify_revised

        return verify_revised(staging, dataset, repository)
    approval = json.loads((repository / ".research/approvals/gate-a-pilot-v1.json").read_bytes())
    state = json.loads((repository / ".research/project_state.json").read_bytes())
    root = staging / "pilot-akshare-20260911"
    for name, field in (
        ("dataset-audit.json", "r3_audit_sha256"),
        ("publication-report.json", "publication_report_sha256"),
    ):
        if sha256_file(root / name) != approval[field]:
            raise ValueError("PRE_FREEZE_R3_EVIDENCE_CHANGED")
    audit = json.loads((root / "dataset-audit.json").read_bytes())
    report = json.loads((root / "publication-report.json").read_bytes())
    manifest = load_manifest(dataset / "manifest.json")
    if not (
        approval["decision"] == "APPROVED"
        and audit["dataset_audited"]
        and set(audit["completed_checks"]) == CHECKS
        and len(audit["completed_checks"]) == len(CHECKS)
        and approval["manifest_sha256"]
        == manifest.canonical_sha256
        == audit["manifest_sha256"]
        == report["manifest_sha256"]
        == state["pilot_manifest_sha256"]
        and manifest.dataset_id == approval["dataset_id"] == dataset.name
    ):
        raise ValueError("PRE_FREEZE_IDENTITY_OR_AUDIT_MISMATCH")
    verify_dataset(dataset, manifest)
    if {p.relative_path for p in manifest.partitions} != {
        p.relative_to(dataset).as_posix() for p in dataset.rglob("*.parquet")
    }:
        raise ValueError("PRE_FREEZE_PARTITION_SET_CHANGED")
    members = parquet.read_table(dataset / "securities.parquet").to_pylist()
    counts = Counter(m["exchange"] for m in members)
    actual = dict(
        coverage=[str(manifest.coverage_start), str(manifest.coverage_end)],
        security_count=len(members),
        sse_count=counts["SSE"],
        szse_count=counts["SZSE"],
        trading_session_count=report["trading_sessions"],
        raw_bar_count=report["total_bars"],
        primary_source_count=report["primary_source_securities"],
        secondary_source_count=report["secondary_source_securities"],
        missing_observations=report["missing_observations"],
    )
    if any(actual[k] != approval[k] for k in actual) or any(
        report[k] != 0
        for k in ("failed_securities", "unresolved_required_data", "rejected_observations")
    ):
        raise ValueError("PRE_FREEZE_COUNTS_CHANGED")
    if (
        manifest.security_count != len(members)
        or audit["securities"] != len(members)
        or sum(p.row_count for p in manifest.partitions if p.relative_path.endswith("/raw.parquet"))
        != actual["raw_bar_count"]
    ):
        raise ValueError("PRE_FREEZE_MANIFEST_COUNTS_CHANGED")
    contracts = {
        r["name"]: json.loads(r["payload"])
        for r in parquet.read_table(dataset / "contracts.parquet").to_pylist()
    }
    preflight = contracts["SOURCE_AUTHORITY_PREFLIGHT"]
    if (
        canonical_sha256({k: v for k, v in preflight.items() if k != "canonical_sha256"})
        != state["source_manifest_sha256"]
    ):
        raise ValueError("SOURCE_PREFLIGHT_CHANGED")
    if contracts["ACCEPTED_INPUT_HASHES"] != ACCEPTED_INPUTS:
        raise ValueError("ACCEPTED_SOURCE_PINS_CHANGED")
    for relative, expected in ACCEPTED_INPUTS.items():
        if sha256_file(staging / relative) != expected:
            raise ValueError("ACCEPTED_SOURCE_CHANGED")

    def group(suffix: str) -> str:
        entries = [p.model_dump() for p in manifest.partitions if p.relative_path.endswith(suffix)]
        if not entries:
            raise ValueError("EMPTY_FREEZE_COMPONENT")
        return canonical_sha256({"partitions": entries})

    return dict(
        dataset_id=manifest.dataset_id,
        dataset_version="1",
        **actual,
        failed_required_securities=0,
        unresolved_required_data=0,
        created_at=manifest.retrieval_timestamp.isoformat(),
        security_master_version="PILOT_OFFICIAL_PIT_MASTER_WITH_APPROVED_ORDINARY_A_SHARE_SCOPE_V1",
        security_master_sha256=group("securities.parquet"),
        sse_st_sha256=ACCEPTED_INPUTS["sse-st-pilot/pilot-scope-20260910/coverage-intervals.json"],
        szse_st_sha256=ACCEPTED_INPUTS["szse-st-recovery-20260910/audit/security-timelines.json"],
        raw_bars_sha256=group("/raw.parquet"),
        adjustment_sha256=group("/factors.parquet"),
        benchmark_sha256=group("csi300-bars.parquet"),
        source_authority_manifest_sha256=state["source_manifest_sha256"],
        dataset_manifest_sha256=manifest.canonical_sha256,
        dataset_manifest_file_sha256=sha256_file(dataset / "manifest.json"),
        market_rule_version=manifest.rule_version,
        execution_convention_version="CN_A_DAILY_OPENING_LIMIT_V1",
        raw_failover_policy_version="CN_A_RAW_OHLCV_FAILOVER_V1",
        raw_failover_policy_sha256=state["raw_failover_policy_sha256"],
        instrument_scope_version="ORDINARY_A_SHARE_EQUITIES_ONLY_V1",
        instrument_scope_manifest_sha256=state["instrument_scope_audit_sha256"],
        akshare_version=manifest.provider_version,
        r3_audit_sha256=approval["r3_audit_sha256"],
        r3_checks=sorted(CHECKS),
        approval_sha256=canonical_sha256(approval),
        accepted_source_sha256=ACCEPTED_INPUTS,
        component_hash_method=(
            "SHA256 canonical JSON {partitions: sorted manifest partition records}; "
            "not concatenated vendor bytes"
        ),
        limitations=list(manifest.known_limitations),
        publication_limitations_note=(
            "Original manifest notes describe the publication stage. "
            "The separate approved freeze record supersedes only its not-frozen status."
        ),
        execution_constraint=(
            "Unknown executable liquidity, official suspension/tradeability "
            "or reference price means NO FILL"
        ),
        verification="PASS",
    )


def freeze(staging: Path, dataset: Path, repository: Path) -> dict:
    verified = verify(staging, dataset, repository)
    record_path = repository / ".research/freezes" / (dataset.name + ".json")
    if record_path.exists():
        record = json.loads(record_path.read_bytes())
        if record.get("freeze_record_sha256") != canonical_sha256(
            {k: v for k, v in record.items() if k != "freeze_record_sha256"}
        ):
            raise ValueError("FREEZE_RECORD_CHECKSUM_MISMATCH")
        if any(record[k] != v for k, v in verified.items()):
            raise ValueError("FROZEN_DATASET_REVISION_REQUIRES_NEW_VERSION")
    else:
        record = dict(
            verified,
            frozen_at=datetime.now(UTC).isoformat(),
            git_commit=subprocess.check_output(
                ["git", "rev-parse", "HEAD"], cwd=repository, text=True
            ).strip(),
        )
        record["freeze_record_sha256"] = canonical_sha256(record)
    content = canonical_json_bytes(record) + b"\n"
    write_immutable(record_path, content)
    write_immutable(dataset / MARKER, content)
    return record


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--staging", type=Path, required=True)
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--freeze", action="store_true")
    args = parser.parse_args()
    operation = freeze if args.freeze else verify
    print(json.dumps(operation(args.staging, args.dataset, args.repository), ensure_ascii=False))
