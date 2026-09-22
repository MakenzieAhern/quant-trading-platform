"""Consolidate audited merger evidence and expose the exact residual set."""

from __future__ import annotations

import argparse
import json
import re
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Any

from app.data.catalog.checksums import canonical_json_bytes, canonical_sha256, sha256_file
from app.data.catalog.freeze import write_immutable
from app.domain.markets.demergers import DemergerSource
from app.domain.markets.mergers import ZERO_WHOLE_SHARE_POLICY, MergerEvent
from scripts.reconcile_merger_implementation_batch import event_from_review

PARENTS = ("000418", "600607", "600631", "600832", "600842")
FACT_CLOSURES = {
    "MERGER:000522:600332",
    "MERGER:000578:000792",
    "MERGER:002013:600372",
    "MERGER_NEW:600253:600056",
}
LAST_TRADING_DATES = {
    "CN-A:SZSE:000522": "2013-03-13",
    "CN-A:SZSE:002013": "2023-02-07",
}


def _security_value(value: str | dict[str, str]) -> str:
    return value["value"] if isinstance(value, dict) else value


def _source(document: dict[str, Any]) -> DemergerSource:
    matched = re.search(r"/(\d{4}-\d{2}-\d{2})/", document["url"])
    if matched is None:
        raise ValueError("MERGER_SOURCE_PUBLICATION_DATE_UNAVAILABLE")
    return DemergerSource(
        url=document["url"],
        sha256=document["sha256"],
        published_on=date.fromisoformat(matched.group(1)),
        retrieved_at=document["retrieved_at_utc"],
        document=document["path"],
    )


def event_from_fact_closure(item: dict[str, Any]) -> MergerEvent:
    facts = item["facts"]
    ratio = str(facts["conversion_ratio"])
    numerator, _, denominator = ratio.partition("/")
    denominator = denominator or "1"
    parent = facts["parent_security_id"]
    effective = facts["converted_shares_tradable_from"]
    event = MergerEvent(
        parent_security={"value": parent},
        successor_security={"value": facts["successor_security_id"]},
        conversion_ratio=Decimal(numerator),
        conversion_denominator=Decimal(denominator),
        parent_last_trading_date=facts.get("parent_last_trading_date")
        or LAST_TRADING_DATES[parent],
        record_date=facts.get("merger_record_date") or facts["parent_termination_date"],
        effective_date=effective,
        successor_listing_date=effective,
        official_fractional_method="GLOBAL_SHAREHOLDER_ALLOCATION_UNREPRODUCIBLE",
        research_fractional_method="FLOOR_NO_CASH_COMPENSATION_RESEARCH_CONVENTION",
        cash_election_offered=None,
        sources=tuple(_source(document) for document in item["documents"]),
        zero_whole_share_policy=ZERO_WHOLE_SHARE_POLICY,
    )
    event.require_supported()
    event.quantities(Decimal(1))
    return event


def executable_events(
    prior: dict[str, Any],
    admitted: list[dict[str, Any]],
    fact_rows: dict[str, dict[str, Any]],
    fixtures: Path,
) -> list[dict[str, Any]]:
    result = []
    for row in prior["events"]:
        parent = _security_value(row["parent_security"])
        code = parent.rsplit(":", 1)[-1]
        if code in {"000024", "600005"}:
            event = MergerEvent.model_validate_json((fixtures / f"{code}_merger.json").read_bytes())
        else:
            event = MergerEvent.model_validate(
                {key: value for key, value in row.items() if key in MergerEvent.model_fields}
            )
        event.require_supported()
        if event.event_checksum != row["event_checksum"]:
            raise ValueError(f"PRIOR_MERGER_EVENT_CHANGED:{parent}")
        result.append(
            {
                "event": event.model_dump(mode="json"),
                "event_checksum": event.event_checksum,
                "accounting": row["accounting"],
                "classification": row["classification"],
                "source": "MERGER_INVENTORY_V7",
            }
        )
    result.extend(admitted)
    for key in sorted(fact_rows):
        item = fact_rows[key]
        event = event_from_fact_closure(item)
        result.append(
            {
                "event": event.model_dump(mode="json"),
                "event_checksum": event.event_checksum,
                "accounting": "PASS_APPROVED_FLOOR_AND_ZERO_WHOLE_CONVENTION",
                "classification": item["classification"],
                "source": "P1_RESIDUAL_MERGER_FACT_CLOSURE_V3",
                "source_fact_checksum": item["fact_checksum"],
            }
        )
    if len(result) != 24 or len({row["event_checksum"] for row in result}) != 24:
        raise ValueError("EXECUTABLE_MERGER_LEDGER_CHANGED")
    return sorted(result, key=lambda row: str(row["event"]["parent_security"]))


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

    complete_events = executable_events(prior, admitted, fact_rows, fixtures)
    report = {
        "report_id": "R5_MERGER_CANDIDATE_CENSUS_V4",
        "coverage": prior["requested_coverage"],
        "official_query_announcements": 2849,
        "official_query_pages": 95,
        "implementation_leads": 69,
        "implementation_leads_terminally_classified": 69,
        "false_parent_candidates": 2,
        "prior_supported_events": 15,
        "newly_admitted_events": admitted,
        "newly_admitted_fact_closures": [fact_rows[key] for key in sorted(fact_rows)],
        "executable_events": complete_events,
        "executable_event_count": len(complete_events),
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
        "parser_version": "MERGER_CANDIDATE_CENSUS_V4",
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
