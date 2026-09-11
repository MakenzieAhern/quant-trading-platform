"""Inventory explicit instrument evidence; never infer eligibility or type from a code."""

import argparse
import json
from collections import Counter
from pathlib import Path

from app.domain.markets.security import InstrumentClassification
from scripts.reconcile_sse_cninfo import canonical, save, sha
from scripts.stage_akshare_pilot import pilot_members


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
    members = pilot_members(staging)
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


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--staging", type=Path, required=True)
    parser.add_argument("--evidence", type=Path, required=True)
    args = parser.parse_args()
    audit(args.staging, args.evidence)
