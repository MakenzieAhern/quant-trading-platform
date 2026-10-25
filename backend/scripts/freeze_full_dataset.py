"""Verify and immutably freeze the pre-authorized R5 Full Dataset."""

import argparse
import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pyarrow.parquet as pq

from app.data.catalog import load_manifest, verify_dataset
from app.data.catalog.checksums import canonical_json_bytes, canonical_sha256, sha256_file
from app.data.catalog.freeze import MARKER, write_immutable
from app.domain.markets.consolidations import CONSOLIDATION_POLICY
from app.research.execution_convention import VERSION as EXECUTION_CONVENTION
from scripts.audit_full_dataset import REQUIRED_GATES
from scripts.full_dataset_sources import verify_source_contracts, verify_source_lineage


def verify(dataset: Path, repository: Path) -> dict[str, Any]:
    state = json.loads((repository / ".research/project_state.json").read_bytes())
    contracts = pq.read_table(dataset / "source-contracts.parquet").to_pylist()
    verify_source_contracts(contracts, repository, state)
    audit_path = repository / state["full_dataset_audit_report"]
    materialization_path = Path(state["full_dataset_materialization_report"])
    audit = json.loads(audit_path.read_bytes())
    materialization = json.loads(materialization_path.read_bytes())
    manifest = load_manifest(dataset / "manifest.json")
    verify_source_lineage(contracts, manifest.source_lineage)
    verify_dataset(dataset, manifest)
    if (
        state["r5_status"] != "PASS_AUDITED_GATE_B_PREAUTHORIZED"
        or state["gate_b_decision"] != "CONDITIONALLY_PREAUTHORIZED_BY_USER"
        or state["gate_b_conditions"] != "PASS"
        or not state["full_dataset_created"]
        or not state["full_dataset_audited"]
        or state["full_dataset_frozen"]
        or state["full_dataset_unresolved_required_data"] != 0
    ):
        raise ValueError("GATE_B_NOT_AUTHORIZED")
    if (
        manifest.dataset_id != dataset.name
        or manifest.dataset_id != state["full_dataset_id"]
        or len(
            {
                manifest.canonical_sha256,
                state["full_dataset_manifest_sha256"],
                audit["manifest_sha256"],
                materialization["manifest_sha256"],
            }
        )
        != 1
        or len(
            {
                sha256_file(dataset / "manifest.json"),
                state["full_dataset_manifest_file_sha256"],
                audit["manifest_file_sha256"],
                materialization["manifest_file_sha256"],
            }
        )
        != 1
    ):
        raise ValueError("FULL_DATASET_IDENTITY_CHANGED")
    if (
        sha256_file(audit_path) != state["full_dataset_audit_file_sha256"]
        or sha256_file(materialization_path) != state["full_dataset_materialization_report_sha256"]
        or audit["audit_status"] != "PASS"
        or not audit["dataset_audited"]
        or audit["dataset_frozen"]
        or set(audit["gates"]) != REQUIRED_GATES
        or set(audit["gates"].values()) != {"PASS"}
        or materialization["failed_sources"] != 0
    ):
        raise ValueError("FULL_DATASET_AUDIT_CHANGED")
    if {part.relative_path for part in manifest.partitions} != {
        part.relative_to(dataset).as_posix() for part in dataset.rglob("*.parquet")
    }:
        raise ValueError("FULL_DATASET_PARTITION_SET_CHANGED")
    return {
        "dataset_id": manifest.dataset_id,
        "dataset_version": "1",
        "coverage": [str(manifest.coverage_start), str(manifest.coverage_end)],
        "security_count": audit["securities"],
        "security_interval_count": audit["security_intervals"],
        "trading_session_count": audit["trading_sessions"],
        "raw_bar_count": audit["raw_rows"],
        "feature_only_non_tradable_count": audit["feature_only_rows"],
        "corporate_action_count": audit["corporate_action_rows"],
        "suspension_event_count": audit["suspension_events"],
        "failed_sources": 0,
        "unresolved_required_data": 0,
        "dataset_manifest_sha256": manifest.canonical_sha256,
        "dataset_manifest_file_sha256": sha256_file(dataset / "manifest.json"),
        "materialization_report_sha256": sha256_file(materialization_path),
        "audit_report_sha256": sha256_file(audit_path),
        "audit_gates": sorted(REQUIRED_GATES),
        "source_manifest_sha256": {row["name"]: row["source_manifest_sha256"] for row in contracts},
        "source_contracts_sha256": canonical_sha256(contracts),
        "policy_versions": {
            "corporate_action_matrix_sha256": state["corporate_action_policy_matrix_sha256"],
            "rights_issue": state["rights_issue_policy"],
            "rights_entitlement": state["rights_entitlement_policy"],
            "merger": state["merger_policy"],
            "merger_zero_whole": state["merger_zero_whole_basis_policy"],
            "demerger": state["demerger_policy"],
            "partial_surrender": state["partial_surrender_policy"],
            "partial_surrender_fraction": state["partial_surrender_fraction_policy"],
            "partial_surrender_boundary": state["partial_surrender_boundary_policy"],
            "bonus_pass_through": state["bonus_pass_through_policy"],
            "share_consolidation": CONSOLIDATION_POLICY,
        },
        "rule_versions": {
            "market_rule_manifest_sha256": manifest.rule_version,
            "execution_convention": EXECUTION_CONVENTION,
        },
        "known_limitations": list(manifest.known_limitations),
        "verification": "PASS",
    }


def freeze(dataset: Path, repository: Path) -> dict[str, Any]:
    verified = verify(dataset, repository)
    record_path = repository / ".research/freezes" / f"{dataset.name}.json"
    if record_path.exists():
        record = json.loads(record_path.read_bytes())
        if record.get("freeze_record_sha256") != canonical_sha256(
            {key: value for key, value in record.items() if key != "freeze_record_sha256"}
        ) or any(record[key] != value for key, value in verified.items()):
            raise ValueError("FROZEN_DATASET_REVISION_REQUIRES_NEW_VERSION")
    else:
        if subprocess.check_output(
            ["git", "status", "--porcelain"], cwd=repository, text=True
        ).strip():
            raise ValueError("FREEZE_REQUIRES_CLEAN_GIT_WORKTREE")
        record = {
            **verified,
            "frozen_at": datetime.now(UTC).isoformat(),
            "git_commit": subprocess.check_output(
                ["git", "rev-parse", "HEAD"], cwd=repository, text=True
            ).strip(),
        }
        record["freeze_record_sha256"] = canonical_sha256(record)
    content = canonical_json_bytes(record) + b"\n"
    write_immutable(record_path, content)
    write_immutable(dataset / MARKER, content)
    return record


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", required=True, type=Path)
    parser.add_argument("--repository", required=True, type=Path)
    parser.add_argument("--freeze", action="store_true")
    args = parser.parse_args()
    operation = freeze if args.freeze else verify
    print(json.dumps(operation(args.dataset, args.repository), ensure_ascii=False))
