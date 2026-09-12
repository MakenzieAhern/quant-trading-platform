"""Read-only verification of the exact human-approved v2 review; reuse immutable freeze writer."""

import json
from collections import Counter
from pathlib import Path

import pyarrow.parquet as pq

from app.data.catalog import load_manifest, verify_dataset
from app.data.catalog.checksums import canonical_sha256, sha256_file
from scripts.freeze_pilot import CHECKS
from scripts.run_pilot_smoke import frozen_inputs


def verify_revised(staging: Path, dataset: Path, repository: Path) -> dict:
    approval = json.loads((repository / ".research/approvals/gate-a-pilot-v2.json").read_bytes())
    review_path = repository / ".research/reports/revised-pilot-v2.json"
    root = staging / "pilot-v2-build"
    if (
        approval["decision"] != "APPROVED"
        or approval["dataset_id"] != dataset.name
        or sha256_file(review_path) != approval["review_sha256"]
        or sha256_file(root / "revision-context.json") != approval["context_sha256"]
    ):
        raise ValueError("PRE_FREEZE_APPROVED_V2_EVIDENCE_CHANGED")
    review = json.loads(review_path.read_bytes())
    context = json.loads((root / "revision-context.json").read_bytes())
    audit = json.loads((root / "dataset-audit.json").read_bytes())
    publication = json.loads((root / "publication-report.json").read_bytes())
    checks = CHECKS | {"SECURITY_MASTER_COMPLETENESS", "BOARD_COVERAGE", "STAR_EXIT_COVERAGE"}
    if (
        sha256_file(root / "dataset-audit.json") != review["R3_AUDIT_SHA256"]
        or not audit["dataset_audited"]
        or set(audit["completed_checks"]) != checks
        or len(audit["completed_checks"]) != len(checks)
        or publication != review["PUBLICATION"]
        or canonical_sha256(json.loads((root / "reuse-rebuild-manifest.json").read_bytes()))
        != review["REUSE_REBUILD_MANIFEST_SHA256"]
    ):
        raise ValueError("PRE_FREEZE_REVISED_AUDIT_CHANGED")
    parent_record, parent = frozen_inputs(dataset.parent / review["V1_DATASET_ID"], repository)
    if parent.canonical_sha256 != review["V1_MANIFEST_SHA256"]:
        raise ValueError("PRESERVED_V1_CHANGED")
    manifest = load_manifest(dataset / "manifest.json")
    verify_dataset(dataset, manifest)
    if (
        manifest.dataset_id != approval["dataset_id"]
        or manifest.canonical_sha256 != review["DATASET_MANIFEST_SHA256"]
        or audit["manifest_sha256"] != manifest.canonical_sha256
        or sha256_file(dataset / "manifest.json") != publication["manifest_file_sha256"]
        or {p.relative_path for p in manifest.partitions}
        != {p.relative_to(dataset).as_posix() for p in dataset.rglob("*.parquet")}
    ):
        raise ValueError("PRE_FREEZE_V2_MANIFEST_CHANGED")
    members = pq.read_table(dataset / "securities.parquet").to_pylist()
    if (
        len(members) != 5180
        or dict(Counter(m["exchange"] for m in members)) != {"SSE": 2289, "SZSE": 2891}
        or dict(Counter(m["board"] for m in members)) != review["V2_BOARD_COUNTS"]
        or any(m["instrument_type"] != "COMMON_A_SHARE" for m in members)
        or pq.read_metadata(dataset / "candidate-master.parquet").num_rows != 5181
        or pq.read_metadata(dataset / "calendar.parquet").num_rows != 382
        or sum(p.row_count for p in manifest.partitions if p.relative_path.endswith("/raw.parquet"))
        != 1922643
        or any(publication[k] != 0 for k in ("failed_securities", "unresolved_required_data"))
        or review["UNEXPLAINED_MASTER_DIFFS"] != 0
    ):
        raise ValueError("PRE_FREEZE_V2_COUNTS_CHANGED")
    contracts = {
        r["name"]: json.loads(r["payload"])
        for r in pq.read_table(dataset / "contracts.parquet").to_pylist()
    }
    if (
        contracts["ACCEPTED_INPUT_HASHES"] != context["accepted_inputs"]
        or contracts["SOURCE_AUTHORITY_PREFLIGHT"] != context["preflight"]
    ):
        raise ValueError("PRE_FREEZE_SOURCE_CONTRACT_CHANGED")
    for relative, expected in context["accepted_inputs"].items():
        if sha256_file(staging / relative) != expected:
            raise ValueError(f"PRE_FREEZE_SOURCE_CHANGED: {relative}")
    hashes = {}
    for field, suffix in (
        ("security_master_sha256", "securities.parquet"),
        ("raw_bars_sha256", "/raw.parquet"),
        ("adjustment_sha256", "/factors.parquet"),
        ("benchmark_sha256", "csi300-bars.parquet"),
    ):
        hashes[field] = canonical_sha256(
            {
                "partitions": [
                    p.model_dump() for p in manifest.partitions if p.relative_path.endswith(suffix)
                ]
            }
        )
    hashes["sse_st_sha256"] = canonical_sha256(
        dict(
            parent_intervals_sha256=context["accepted_inputs"][
                "sse-st-pilot/pilot-scope-20260910/coverage-intervals.json"
            ],
            new_member_evidence_sha256=context["accepted_inputs"][
                "pilot-v2-master/new-member-evidence.json"
            ],
        )
    )
    hashes["szse_st_sha256"] = context["accepted_inputs"][
        "szse-st-recovery-20260910/audit/security-timelines.json"
    ]
    hashes["source_authority_manifest_sha256"] = canonical_sha256(
        {k: v for k, v in context["preflight"].items() if k != "canonical_sha256"}
    )
    if any(value != review[key.upper()] for key, value in hashes.items()):
        raise ValueError("PRE_FREEZE_APPROVED_COMPONENT_CHANGED")
    return dict(
        dataset_id=manifest.dataset_id,
        parent_dataset_id=parent.dataset_id,
        supersedes_dataset_id=parent.dataset_id,
        supersedes_reason="SECURITY_MASTER_COMPLETENESS_DEFECT",
        parent_freeze_record_sha256=parent_record["freeze_record_sha256"],
        dataset_version="2",
        coverage=[str(manifest.coverage_start), str(manifest.coverage_end)],
        security_count=5180,
        sse_count=2289,
        szse_count=2891,
        trading_session_count=382,
        raw_bar_count=1922643,
        **hashes,
        dataset_manifest_sha256=manifest.canonical_sha256,
        dataset_manifest_file_sha256=sha256_file(dataset / "manifest.json"),
        market_rule_version=manifest.rule_version,
        execution_convention_version="CN_A_DAILY_OPENING_LIMIT_V1",
        raw_failover_policy_version="CN_A_RAW_OHLCV_FAILOVER_V1",
        instrument_scope_version="ORDINARY_A_SHARE_EQUITIES_ONLY_V1",
        instrument_scope_manifest_sha256=canonical_sha256(context["scope"]),
        akshare_version=manifest.provider_version,
        r3_audit_sha256=review["R3_AUDIT_SHA256"],
        r3_checks=sorted(checks),
        approval_sha256=canonical_sha256(approval),
        accepted_source_sha256=context["accepted_inputs"],
        limitations=list(manifest.known_limitations),
        execution_constraint="Unknown official tradeability or execution inputs means NO FILL",
        verification="PASS",
    )
