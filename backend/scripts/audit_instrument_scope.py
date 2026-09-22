"""Inventory explicit instrument evidence; never infer eligibility or type from a code."""

import argparse
import json
from collections import Counter
from pathlib import Path

from app.domain.markets.identifiers import InstrumentType
from app.domain.markets.security import InstrumentClassification
from scripts.reconcile_sse_cninfo import canonical, save, sha
from scripts.stage_akshare_pilot import candidate_members, scope_members, verify_scope_sources


def inventory(members: list[dict], facts: list[InstrumentClassification]) -> list[dict]:
    by_id = {str(item.security_id): item for item in facts}
    member_ids = {item["security_id"] for item in members}
    if (
        len(by_id) != len(facts)
        or len(member_ids) != len(members)
        or not by_id.keys() <= member_ids
    ):
        raise ValueError("DUPLICATE_OR_OUT_OF_MASTER_CLASSIFICATION")
    return [
        dict(
            security_id=row["security_id"],
            exchange=row["exchange"],
            symbol=row["symbol"],
            listing_date=row["listing_date"],
            delisting_date=row["delisting_date"],
            instrument_type=(
                by_id[row["security_id"]].instrument_type.value
                if row["security_id"] in by_id
                else "UNCLASSIFIED"
            ),
            classification=(
                by_id[row["security_id"]].model_dump(mode="json")
                if row["security_id"] in by_id
                else None
            ),
            eligibility_changed=False,
        )
        for row in sorted(members, key=lambda item: item["security_id"])
    ]


def audit(staging: Path, evidence: Path) -> dict:
    facts = []
    for item in json.loads((evidence / "classifications.json").read_bytes()):
        fact = InstrumentClassification.model_validate(item["classification"])
        path = (evidence / item["snapshot"]).resolve()
        if (
            not path.is_relative_to(evidence.resolve())
            or sha(path.read_bytes()) != fact.source_document_sha256
        ):
            raise ValueError("CLASSIFICATION_SNAPSHOT_CHANGED")
        meta = json.loads(path.with_suffix(path.suffix + ".meta.json").read_bytes())
        if meta["url"] != fact.source_url or meta["sha256"] != fact.source_document_sha256:
            raise ValueError("CLASSIFICATION_PROVENANCE_CHANGED")
        facts.append(fact)
    members = candidate_members(staging)
    rows = inventory(members, facts)
    if rows != inventory(members[::-1], facts[::-1]):
        raise ValueError("INPUT_ORDER_FAILURE")
    save(evidence / "instrument-inventory.json", rows)
    report = dict(
        pilot_instrument_scope="AMBIGUOUS_REQUIRES_HUMAN_DECISION",
        total_master_securities=len(rows),
        exchange_counts=dict(sorted(Counter(row["exchange"] for row in rows).items())),
        evidence_counts=dict(sorted(Counter(row["instrument_type"] for row in rows).items())),
        confirmed_nonordinary_symbols=[
            row["symbol"]
            for row in rows
            if row["instrument_type"] not in {"COMMON_STOCK", "UNCLASSIFIED"}
        ],
        instrument_inventory_sha256=sha(canonical(rows)),
        input_order_reproducibility="PASS",
        exclusions_applied=0,
        eligibility_changed=False,
        note=(
            "UNCLASSIFIED is missing explicit type evidence, not ordinary stock and not an "
            "exclusion. Prior master coverage PASS did not certify instrument scope."
        ),
    )
    save(evidence / "instrument-scope-audit.json", report)
    print(json.dumps(report))
    return report


def approved_audit(staging: Path, evidence: Path) -> dict:
    records = json.loads((evidence / "approved-classifications.json").read_bytes())
    facts = [InstrumentClassification.model_validate(r["classification"]) for r in records]
    for record in records:
        fact = InstrumentClassification.model_validate(record["classification"])
        if not any(
            s["sha256"] == fact.source_document_sha256 and s["source_url"] == fact.source_url
            for s in record["sources"]
        ):
            raise ValueError("CLASSIFICATION_PRIMARY_SOURCE_NOT_ATTACHED")
    verify_scope_sources(staging, records)
    members = candidate_members(staging)
    admitted = scope_members(members, facts)
    if admitted != scope_members(members[::-1], facts[::-1]):
        raise ValueError("SCOPE_INPUT_ORDER_FAILURE")
    admitted_ids = {r["security_id"] for r in admitted}
    rows = inventory(members, facts)
    excluded = []
    for row in rows:
        row["pilot_eligibility"] = (
            "IN_SCOPE" if row["security_id"] in admitted_ids else "OUT_OF_SCOPE"
        )
        row["eligibility_changed"] = row["security_id"] not in admitted_ids
        if row["eligibility_changed"]:
            excluded.append(
                dict(
                    **row,
                    status="AUTHORITATIVELY_OUT_OF_SCOPE_INSTRUMENT",
                    reason="HUMAN_APPROVED_ORDINARY_A_SHARE_SCOPE",
                    market_data_required=False,
                )
            )
    save(evidence / "approved-instrument-inventory.json", rows)
    save(evidence / "out-of-scope-instruments.json", excluded)
    counts = Counter(row["instrument_type"] for row in rows)
    report = dict(
        status="PASS",
        pilot_instrument_scope="ORDINARY_A_SHARE_EQUITIES_ONLY",
        total_master_securities=len(members),
        post_scope_filter_securities=len(admitted),
        counts={kind.value: counts[kind.value] for kind in InstrumentType},
        unclassified_securities=counts["UNCLASSIFIED"],
        exclusions=len(excluded),
        input_order_reproducibility="PASS",
        classifications_sha256=sha((evidence / "approved-classifications.json").read_bytes()),
        inventory_sha256=sha(canonical(rows)),
        exclusions_sha256=sha(canonical(excluded)),
        scope_is_methodology_not_provider_exclusion=True,
        original_master_preserved=True,
        dataset_publication_authorized=False,
        temporal_evidence_basis=(
            "Explicit original A-listing register fields on nonmixed venues; "
            "dated original IPO notices on the mixed STAR stock/CDR venue. Retrieval dates are "
            "not substituted for historical effective dates or invented publication dates."
        ),
    )
    save(evidence / "approved-scope-manifest.json", report)
    print(json.dumps(report))
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--staging", type=Path, required=True)
    parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument("--approved", action="store_true")
    args = parser.parse_args()
    (approved_audit if args.approved else audit)(args.staging, args.evidence)
