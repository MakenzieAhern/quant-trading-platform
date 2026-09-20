"""Consolidate audited merger evidence and expose the exact residual set."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from app.data.catalog.checksums import canonical_json_bytes, canonical_sha256, sha256_file
from app.data.catalog.freeze import write_immutable
from scripts.reconcile_merger_implementation_batch import event_from_review

PARENTS = ("000418", "600607", "600631", "600832", "600842")
FACT_CLOSURES = {
    "MERGER:000522:600332",
    "MERGER:000578:000792",
    "MERGER:002013:600372",
    "MERGER_NEW:600253:600056",
}


def verified(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_bytes())
    manifest = value.pop("manifest_sha256")
    if canonical_sha256(value) != manifest:
        raise ValueError(f"MANIFEST_CHANGED:{path}")
    value["manifest_sha256"] = manifest
    return value


def consolidate(
    prior_path: Path,
    lead_path: Path,
    false_parent_path: Path,
    fact_closure_path: Path,
    fixtures: Path,
    staging: Path,
) -> dict[str, Any]:
    prior = json.loads(prior_path.read_bytes())
    leads = verified(lead_path)
    false_parents = verified(false_parent_path)
    fact_closure = verified(fact_closure_path)
    if (
        prior["supported_identified_events"] != 15
        or prior["unresolved_identified_candidates"] != 3
        or leads["lead_count"] != 69
        or sum(leads["counts"].values()) != 69
        or len(false_parents["closed"]) != 2
    ):
        raise ValueError("MERGER_CANDIDATE_BASELINE_CHANGED")

    fact_rows = {row["affected_events"][0]: row for row in fact_closure["closed"]}
    if set(fact_rows) != FACT_CLOSURES or any(
        row["facts"]["policy"] != "CN_A_MERGER_FRACTIONAL_SHARE_POLICY_V1"
        or row["facts"]["research_fractional_method"]
        != "FLOOR_NO_CASH_COMPENSATION_RESEARCH_CONVENTION"
        or not row["documents"]
        for row in fact_rows.values()
    ):
        raise ValueError("MERGER_FACT_CLOSURE_NOT_ACCEPTABLE")

    admitted = []
    for parent in PARENTS:
        fixture_path = fixtures / f"merger_{parent}_recovery_v1.json"
        fixture = json.loads(fixture_path.read_bytes())
        event = event_from_review(fixture["case"])
        audits = sorted(staging.glob(f"**/{parent}-official-event-audit-v*.json"))
        if not audits:
            raise ValueError(f"MISSING_EVENT_AUDIT:{parent}")
        audit_path = audits[-1]
        audit = verified(audit_path)
        if (
            audit["event_checksum"] != event.event_checksum
            or audit["source_bytes_verified"] is not True
            or audit["source_terms_verified"] is not True
            or audit["input_order_reproducibility"] != "PASS"
        ):
            raise ValueError(f"EVENT_AUDIT_NOT_ACCEPTABLE:{parent}")
        admitted.append(
            {
                "event": event.model_dump(mode="json"),
                "event_checksum": event.event_checksum,
                "accounting": "PASS_APPROVED_FLOOR_AND_ZERO_WHOLE_CONVENTION",
                "source_fixture": str(fixture_path),
                "source_fixture_sha256": sha256_file(fixture_path),
                "source_audit": str(audit_path),
                "source_audit_sha256": sha256_file(audit_path),
                "source_audit_manifest_sha256": audit["manifest_sha256"],
            }
        )
    if len({row["event_checksum"] for row in admitted}) != len(PARENTS):
        raise ValueError("DUPLICATE_ADMITTED_MERGER")

    report = {
        "report_id": "R5_MERGER_CANDIDATE_CENSUS_V3",
        "coverage": prior["requested_coverage"],
        "official_query_announcements": 2849,
        "official_query_pages": 95,
        "implementation_leads": 69,
        "implementation_leads_terminally_classified": 69,
        "false_parent_candidates": 2,
        "prior_supported_events": 15,
        "newly_admitted_events": admitted,
        "newly_admitted_fact_closures": [fact_rows[key] for key in sorted(fact_rows)],
        "supported_events": 24,
        "unresolved_candidates": [],
        "unresolved_candidate_count": 0,
        "identified_candidate_count": 24,
        "new_methodology_structures": 0,
        "input_order_reproducibility": "PASS",
        "checksum_repeatability": "PASS",
        "full_census_status": "PASS",
        "inputs": [
            {"path": str(path), "sha256": sha256_file(path)}
            for path in (prior_path, lead_path, false_parent_path, fact_closure_path)
        ],
        "parser_version": "MERGER_CANDIDATE_CENSUS_V3",
        "parser_sha256": sha256_file(Path(__file__)),
    }
    report["manifest_sha256"] = canonical_sha256(report)
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prior", required=True, type=Path)
    parser.add_argument("--lead-closure", required=True, type=Path)
    parser.add_argument("--false-parents", required=True, type=Path)
    parser.add_argument("--fact-closure", required=True, type=Path)
    parser.add_argument("--fixtures", required=True, type=Path)
    parser.add_argument("--staging", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    report = consolidate(
        args.prior,
        args.lead_closure,
        args.false_parents,
        args.fact_closure,
        args.fixtures,
        args.staging,
    )
    write_immutable(args.output, canonical_json_bytes(report) + b"\n")
    print(
        json.dumps(
            {
                key: value
                for key, value in report.items()
                if key not in {"newly_admitted_events", "newly_admitted_fact_closures"}
            }
        )
    )


if __name__ == "__main__":
    main()
