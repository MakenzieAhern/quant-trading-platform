"""Reverify reviewed pass-through source bytes; no automatic PDF interpretation."""

import argparse
import json
from pathlib import Path

from app.data.catalog.checksums import canonical_json_bytes, canonical_sha256
from app.data.catalog.freeze import write_immutable
from app.domain.markets.pass_through import RestructuringBonusPassThroughEvent
from scripts.audit_demerger_evidence import verify_sources


def audit(review, event, staging):
    event.require_supported()
    if (
        review["policy"] != event.policy
        or review["basis_policy"] != event.basis_policy
        or review["approval_sha256"] != event.convention_approval_sha256
    ):
        raise ValueError("PASS_THROUGH_APPROVAL_MISMATCH")
    documents = verify_sources(review, (*event.sources, *event.confirmation_sources), staging)
    normalized = event.model_dump(mode="json")
    for key in ("sources", "confirmation_sources"):
        normalized[key].sort(key=lambda s: (s["sha256"], s["url"]))
    body = dict(
        parser_version="PASS_THROUGH_EVIDENCE_V1",
        review={**review, "documents": documents},
        event=normalized,
        event_checksum=event.event_checksum,
        source_bytes_verified=True,
        full_census_certified=False,
    )
    return {**body, "manifest_sha256": canonical_sha256(body)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for option in ("review", "event", "staging", "output"):
        parser.add_argument(f"--{option}", type=Path, required=True)
    args = parser.parse_args()
    review = json.loads(args.review.read_bytes())
    event = RestructuringBonusPassThroughEvent.model_validate_json(args.event.read_bytes())
    result = audit(review, event, args.staging)
    reverse = audit(
        {**review, "documents": list(reversed(review["documents"]))},
        event.model_copy(
            update={
                key: tuple(reversed(getattr(event, key)))
                for key in ("sources", "confirmation_sources")
            }
        ),
        args.staging,
    )
    if result != reverse:
        raise ValueError("INPUT_ORDER_REPRODUCIBILITY_FAILED")
    write_immutable(args.output, canonical_json_bytes(result) + b"\n")
    print(json.dumps({key: result[key] for key in ("event_checksum", "manifest_sha256")}))
