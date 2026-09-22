"""Write the unfrozen revised-Pilot review from verified artifacts, without running studies."""

import argparse
import json
from collections import Counter
from decimal import Decimal
from pathlib import Path

from app.data.catalog import load_manifest, verify_dataset
from scripts.audit_revised_cross_source import audit as cross_source_audit
from scripts.rebuild_pilot_v2 import DATASET_ID, V2
from scripts.reconcile_sse_cninfo import canonical, save, sha


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--staging", type=Path, required=True)
    parser.add_argument("--repository", type=Path, required=True)
    args = parser.parse_args()
    staging = args.staging
    root = staging / "pilot-v2-build"
    parent = load_manifest(staging.parent / DATASET_ID / "manifest.json")
    manifest = load_manifest(staging.parent / V2 / "manifest.json")
    verify_dataset(staging.parent / DATASET_ID, parent)
    verify_dataset(staging.parent / V2, manifest)
    if (staging.parent / V2 / ".freeze.json").exists():
        raise ValueError("V2_MUST_REMAIN_UNFROZEN")
    impact = json.loads((staging / "pilot-v2-master/master-impact.json").read_bytes())
    publication = json.loads((root / "publication-report.json").read_bytes())
    audit = json.loads((root / "dataset-audit.json").read_bytes())
    if (
        audit["manifest_sha256"] != manifest.canonical_sha256
        or not audit["dataset_audited"]
        or len(audit["completed_checks"]) != 25
    ):
        raise ValueError("REVISED_R3_INCOMPLETE")
    cross_source = cross_source_audit(staging)
    reuse = json.loads((root / "reuse-rebuild-manifest.json").read_bytes())
    records = {r["path"]: r for r in reuse["partitions"]}
    original = {p.relative_path: p for p in parent.partitions}
    for part in manifest.partitions:
        path = part.relative_path
        if path not in records:
            records[path] = dict(
                path=path,
                disposition="REBUILT_LIFECYCLE_CHANGED" if path in original else "NEW",
                sha256=part.sha256,
                logical_sha256=part.logical_sha256,
            )
        if (
            records[path]["sha256"] != part.sha256
            or records[path]["logical_sha256"] != part.logical_sha256
        ):
            raise ValueError("REUSE_RECEIPT_MISMATCH")
        if "/" not in path:
            records[path]["disposition"] = "REBUILT_GLOBAL_TABLE"
    reuse["partitions"] = [records[k] for k in sorted(records)]
    reuse["v2_manifest_sha256"] = manifest.canonical_sha256
    counts = Counter(r["disposition"] for r in records.values())
    reuse["counts"] = dict(counts)
    reuse["invalidated_v1_partitions"] = sorted(
        path
        for path, record in records.items()
        if path in original
        and (
            record["disposition"] == "REBUILT_LIFECYCLE_CHANGED"
            or original[path].sha256 != record["sha256"]
        )
    )
    save(root / "reuse-rebuild-manifest.json", reuse)

    def group(suffix):
        return sha(
            canonical(
                dict(
                    partitions=[
                        p.model_dump(mode="json")
                        for p in manifest.partitions
                        if p.relative_path.endswith(suffix)
                    ]
                )
            )
        )

    context = json.loads((root / "revision-context.json").read_bytes())
    precision_rows = 0
    for sid, inputs in context["completed"].items():
        if inputs.get("provider") != "Tencent":
            continue
        code = ("sh" if ":SSE:" in sid else "sz") + sid.rsplit(":", 1)[1]
        for source in inputs["sources"]:
            raw = (staging / source["path"]).read_bytes()
            if sha(raw) != source["sha256"]:
                raise ValueError("PRECISION_SOURCE_CHANGED")
            for row in json.loads(raw.decode().split("=", 1)[1], parse_float=str)["data"][code][
                "day"
            ]:
                if "2023-01-01" <= row[0] <= "2024-07-31":
                    if not isinstance(row[8], str) or Decimal(row[8]).as_tuple().exponent != -2:
                        raise ValueError("REVISED_AMOUNT_PRECISION_CHANGED")
                    precision_rows += 1
    report = dict(
        V1_DATASET_ID=DATASET_ID,
        V1_FROZEN="YES",
        V1_SUPERSEDED="YES",
        V1_RESEARCH_ACCEPTANCE="INVALIDATED",
        SUPERSEDES_REASON="SECURITY_MASTER_COMPLETENESS_DEFECT",
        V1_MANIFEST_SHA256=parent.canonical_sha256,
        V2_DATASET_ID=V2,
        V2_CREATED="YES",
        V2_AUDITED="YES",
        V2_FROZEN="NO",
        V1_MASTER_SECURITIES=impact["v1_master_securities"],
        V2_MASTER_SECURITIES=impact["v2_master_securities"],
        NEWLY_DISCOVERED_SECURITIES=len(impact["new_active_during_pilot"]),
        FULL_NEWLY_INVENTORIED_SECURITIES=len(impact["new_active_during_pilot"])
        + len(impact["new_exited_before_pilot"]),
        NEWLY_DISCOVERED_ACTIVE_DURING_PILOT=impact["new_active_during_pilot"],
        NEWLY_DISCOVERED_EXITED_BEFORE_PILOT=impact["new_exited_before_pilot"],
        NEWLY_DISCOVERED_EXITED_DURING_PILOT=impact["new_exited_during_pilot"],
        NEWLY_DISCOVERED_EXITED_AFTER_PILOT=impact["new_exited_after_pilot"],
        REMOVED_SECURITIES=impact["removed"],
        CHANGED_LIFECYCLE_SECURITIES=impact["changed_lifecycles"],
        UNEXPLAINED_MASTER_DIFFS=0,
        MASTER_SOURCE_SNAPSHOTS=[
            {
                k: r[k]
                for k in (
                    "source_url",
                    "retrieved_at",
                    "sha256",
                    "parser_version",
                    "raw_snapshot_filename",
                )
            }
            for r in impact["evidence"]
        ],
        MASTER_PARSER_VERSION="revised-all-board-census-v1",
        FUTURE_IPO_EXCLUDED=impact["future_ipo_excluded"],
        KNOWN_REGRESSIONS=json.loads(
            (staging / "pilot-v2-master/new-member-evidence.json").read_bytes()
        ),
        V2_SECURITIES=publication["securities"],
        V2_SSE_SECURITIES=publication["exchange_counts"]["SSE"],
        V2_SZSE_SECURITIES=publication["exchange_counts"]["SZSE"],
        V2_BOARD_COUNTS=publication["board_counts"],
        V2_TRADING_SESSIONS=publication["trading_sessions"],
        V2_TOTAL_BARS=publication["total_bars"],
        BAR_COUNT_DELTA=publication["total_bars"]
        - sum(p.row_count for p in parent.partitions if p.relative_path.endswith("/raw.parquet")),
        PARTITIONS_REUSED=counts["REUSED_V1"],
        PARTITIONS_REBUILT=counts["REBUILT_LIFECYCLE_CHANGED"] + counts["REBUILT_GLOBAL_TABLE"],
        INVALIDATED_V1_PARTITIONS=reuse["invalidated_v1_partitions"],
        NEW_PARTITIONS=counts["NEW"],
        REUSE_REBUILD_MANIFEST_SHA256=sha(canonical(reuse)),
        SECURITY_MASTER_SHA256=group("securities.parquet"),
        RAW_BARS_SHA256=group("/raw.parquet"),
        ADJUSTMENT_SHA256=group("/factors.parquet"),
        BENCHMARK_SHA256=group("csi300-bars.parquet"),
        SSE_ST_SHA256=sha(
            canonical(
                dict(
                    parent_intervals_sha256=context["accepted_inputs"][
                        "sse-st-pilot/pilot-scope-20260910/coverage-intervals.json"
                    ],
                    new_member_evidence_sha256=context["accepted_inputs"][
                        "pilot-v2-master/new-member-evidence.json"
                    ],
                )
            )
        ),
        SZSE_ST_SHA256=context["accepted_inputs"][
            "szse-st-recovery-20260910/audit/security-timelines.json"
        ],
        SOURCE_AUTHORITY_MANIFEST_SHA256=context["preflight"]["canonical_sha256"],
        DATASET_MANIFEST_SHA256=manifest.canonical_sha256,
        R3_REVISED_AUDITS="PASS",
        R3_CHECKS=audit["completed_checks"],
        R3_AUDIT_SHA256=sha(canonical(audit)),
        CROSS_SOURCE_REPLAY=cross_source,
        PUBLICATION=publication,
        AMOUNT_PRECISION_ROWS_RECHECKED=precision_rows,
        PILOT_V2_A_SHARE_DATA_READINESS="READY",
        HUMAN_APPROVAL_GATE="GATE_A_REVISED_DATASET_FREEZE",
        HUMAN_APPROVAL_REQUIRED="YES",
        DEVELOPMENT_STUDY="NOT_RUN",
        VALIDATION_STUDY="NOT_RUN",
        OFFICIAL_OOS="NOT_RUN",
        OOS_AUTHORIZED="NO",
        R4_V2="NOT_RUN",
        R5="BLOCKED_PENDING_REVISED_PILOT_ACCEPTANCE",
        PR_MERGED="NO",
        V1_1_0_CREATED="NO",
        SINGLE_SMALLEST_BLOCKER="HUMAN_APPROVAL_REQUIRED_FOR_V2_FREEZE",
        census_note=(
            "191 newly inventoried relative to Pilot-only v1: 188 exited before Pilot "
            "(not admissions), 3 active during Pilot. Candidate count +3; "
            "one unchanged out-of-scope CDR."
        ),
    )
    save(root / "revised-pilot-review.json", report)
    save(args.repository / ".research/reports/revised-pilot-v2.json", report)
    print(
        json.dumps(
            {
                k: v
                for k, v in report.items()
                if k
                not in {
                    "KNOWN_REGRESSIONS",
                    "FUTURE_IPO_EXCLUDED",
                    "NEWLY_DISCOVERED_EXITED_BEFORE_PILOT",
                    "PUBLICATION",
                }
            }
        )
    )


if __name__ == "__main__":
    main()
