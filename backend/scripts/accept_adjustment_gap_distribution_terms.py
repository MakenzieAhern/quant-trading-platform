"""Accept exact official distribution terms already validated by factor parity."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from decimal import Decimal
from pathlib import Path
from typing import Any

from app.data.catalog.checksums import canonical_json_bytes, canonical_sha256, sha256_file
from app.data.catalog.freeze import write_immutable
from app.domain.markets.corporate_actions import CorporateAction, require_supported_corporate_action


def verified(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_bytes())
    manifest = value.pop("manifest_sha256")
    if canonical_sha256(value) != manifest:
        raise ValueError(f"MANIFEST_CHANGED:{path}")
    value["manifest_sha256"] = manifest
    return value


def _sources(staging: Path, inventory: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in inventory:
        grouped.setdefault(row["source_sha256"], []).append(row)
    result = {}
    for digest, rows in grouped.items():
        identities = {
            (
                row["issuer"],
                row["published_on"],
                row["retrieved_at_utc"],
                row["title"],
                row["url"],
            )
            for row in rows
        }
        if len(identities) != 1:
            raise ValueError(f"CONFLICTING_SOURCE_METADATA:{digest}")
        row = min(rows, key=lambda item: item["source_path"])
        if sha256_file(staging / row["source_path"]) != digest:
            raise ValueError(f"SOURCE_BYTES_CHANGED:{digest}")
        result[digest] = row
    return result


def build(
    staging: Path,
    terms: dict[str, Any],
    economics: dict[str, Any],
    authority: dict[str, Any],
    inventory: list[dict[str, Any]],
    master: list[dict[str, Any]],
) -> dict[str, Any]:
    if (
        terms["status"] != "CANDIDATE_TERMS_ONLY_NO_EVENT_OR_AUTHORITY_ACCEPTANCE"
        or economics["eligible_exact_cash_bonus_terms"] != 1348
        or authority["adjustment_authority"] != "PASS_FOR_FULL_DATASET"
        or authority["factor_change_counts"]["OFFICIAL_GROSS_TERMS_FACTOR_PARITY"] != 1348
    ):
        raise ValueError("DISTRIBUTION_TERMS_BASELINE_CHANGED")
    economics_by_factor = {row["factor_change"]: row for row in economics["rows"]}
    parity = set(economics_by_factor)
    accepted_by_authority = {
        row["factor_change"]
        for row in authority["factor_change_classifications"]
        if row["classification"] == "OFFICIAL_GROSS_TERMS_FACTOR_PARITY"
    }
    if parity != accepted_by_authority:
        raise ValueError("FACTOR_PARITY_AUTHORITY_SET_CHANGED")
    sources = _sources(staging, inventory)
    lifecycles = {
        (
            row["security_id"],
            row["effective_from"],
            row.get("effective_to") or "2025-12-31",
        )
        for row in master
        if row["instrument_type"] == "COMMON_A_SHARE"
    }
    events = []
    factors = set()
    for result in sorted(terms["factor_results"], key=lambda row: row["factor_change"]):
        if result["status"] != "UNIQUE_EXACT_OFFICIAL_TERMS_CANDIDATE":
            continue
        factor = result["factor_change"]
        evidence_rows = result["evidence"]
        if factor not in parity:
            continue
        source_sha256 = economics_by_factor[factor]["official_terms_source_sha256"]
        evidence = [row for row in evidence_rows if row["source_sha256"] == source_sha256]
        if len(evidence) != 1:
            raise ValueError(f"TERMS_NOT_AUTHORITY_BOUND:{factor}")
        evidence = evidence[0]
        body = factor.removeprefix("FACTOR:")
        security_id, effective_date = body.rsplit(":", 1)
        source = sources[evidence["source_sha256"]]
        if not any(
            sid == security_id and start <= evidence["record_date"] <= effective_date <= end
            for sid, start, end in lifecycles
        ):
            raise ValueError(f"DISTRIBUTION_LIFECYCLE_UNRESOLVED:{factor}")
        factors.add(factor)
        for action_type, field, policy_id in (
            ("CASH_DIVIDEND", "cash_per_share", "EXISTING_ACCEPTED_CASH_DIVIDEND"),
            ("BONUS_SHARE", "bonus_share_ratio", "BASIS_CONSERVED_RETAINED_BONUS"),
        ):
            amount = Decimal(evidence[field])
            if amount <= 0:
                continue
            source_record_hash = canonical_sha256(
                {
                    "action_type": action_type,
                    "evidence": evidence,
                    "factor_change": factor,
                    "source_sha256": source["source_sha256"],
                }
            )
            event = CorporateAction.model_validate(
                {
                    "security_id": {"value": security_id},
                    "action_type": action_type,
                    "announcement_date": source["published_on"],
                    "effective_date": effective_date,
                    "record_date": evidence["record_date"],
                    "ex_date": effective_date,
                    "cash_per_share": str(amount) if action_type == "CASH_DIVIDEND" else "0",
                    "share_ratio": str(amount) if action_type == "BONUS_SHARE" else None,
                    "source_document": source["title"],
                    "source_url": source["url"],
                    "source_document_sha256": source["source_sha256"],
                    "retrieved_at": source["retrieved_at_utc"],
                    "source_provider": "OFFICIAL_ISSUER_CNINFO_FACTOR_PARITY_RECONCILED",
                    "source_version": "FULL_ADJUSTMENT_GAP_DISTRIBUTION_TERMS_V1",
                    "source_record_hash": source_record_hash,
                    "completeness": "COMPLETE",
                }
            )
            require_supported_corporate_action(event)
            events.append(
                {
                    "event": event.model_dump(mode="json"),
                    "event_checksum": event.event_checksum,
                    "policy_id": policy_id,
                    "source_terms_sha256": source_record_hash,
                    "support_state": "SUPPORTED_OFFICIAL_FACTOR_PARITY_DISTRIBUTION_TERMS",
                    "metadata_only_gaps": ["PAYMENT_DATE_NOT_NORMALIZED"],
                }
            )
    events.sort(
        key=lambda row: (
            row["event"]["effective_date"],
            row["event"]["security_id"]["value"],
            row["event"]["action_type"],
        )
    )
    if factors != parity or len({row["event_checksum"] for row in events}) != len(events):
        raise ValueError("DISTRIBUTION_TERMS_COVERAGE_INCOMPLETE")
    counts = Counter(row["event"]["action_type"] for row in events)
    return {
        "report_id": "R5_ADJUSTMENT_GAP_DISTRIBUTION_LEDGER_V1",
        "coverage": ["2010-01-01", "2025-12-31"],
        "factor_changes": len(factors),
        "events": events,
        "event_count": len(events),
        "event_counts": dict(sorted(counts.items())),
        "unresolved_events": 0,
        "input_order_reproducibility": "PASS",
        "checksum_repeatability": "PASS",
        "status": "PASS",
        "parser_sha256": sha256_file(Path(__file__)),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--staging", required=True, type=Path)
    parser.add_argument("--terms", required=True, type=Path)
    parser.add_argument("--economics", required=True, type=Path)
    parser.add_argument("--authority", required=True, type=Path)
    parser.add_argument("--inventory", required=True, type=Path)
    parser.add_argument("--master", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    inputs = [args.terms, args.economics, args.authority, args.inventory, args.master]
    terms, economics, authority = map(verified, inputs[:3])
    inventory = json.loads(args.inventory.read_bytes())
    master = json.loads(args.master.read_bytes())
    report = build(args.staging, terms, economics, authority, inventory, master)
    if report != build(
        args.staging,
        terms,
        economics,
        authority,
        list(reversed(inventory)),
        list(reversed(master)),
    ):
        raise ValueError("INPUT_ORDER_REPRODUCIBILITY_FAILED")
    report["inputs"] = [{"path": str(path), "sha256": sha256_file(path)} for path in inputs]
    report["manifest_sha256"] = canonical_sha256(report)
    write_immutable(args.output, canonical_json_bytes(report) + b"\n")
    print(
        json.dumps({key: value for key, value in report.items() if key not in {"events", "inputs"}})
    )


if __name__ == "__main__":
    main()
