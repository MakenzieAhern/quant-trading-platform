"""Verify retained surrender evidence without promoting incomplete historical facts."""

import argparse
import json
from pathlib import Path

from app.data.catalog.checksums import canonical_json_bytes, canonical_sha256
from app.data.catalog.freeze import write_immutable
from app.domain.markets.surrenders import (
    PARTIAL_SURRENDER_POLICY,
    MandatoryPartialShareSurrenderEvent,
)
from scripts.audit_demerger_evidence import verify_sources


def audit(review, event, staging):
    if review["policy"] != PARTIAL_SURRENDER_POLICY:
        raise ValueError("PARTIAL_SURRENDER_POLICY_MISMATCH")
    documents = verify_sources(
        review, (*event.sources, *event.confirmation_sources, *event.boundary_sources), staging
    )
    convention = (
        event.research_effective_date is not None or event.research_fraction_rule is not None
    )
    if convention:
        event.require_supported()
        if review.get("convention_approval_sha256") != event.convention_approval_sha256:
            raise ValueError("CONVENTION_APPROVAL_RECEIPT_MISMATCH")
    normalized = event.model_dump(mode="json")
    for key in ("sources", "confirmation_sources", "boundary_sources"):
        normalized[key].sort(key=lambda s: (s["sha256"], s["url"]))
    gaps = []
    if event.effective_date is None:
        gaps.append("REGISTRY_EFFECTIVE_DATE_UNVERIFIED")
    if event.quantity_rounding_rule == "UNRESOLVED":
        gaps.append("SURRENDER_LEG_FRACTIONAL_ALLOCATION_UNVERIFIED")
    if event.consideration_type != "NONE" or event.consideration_value != 0:
        gaps.append("PARTIAL_SURRENDER_CONSIDERATION_POLICY_UNRESOLVED")
    body = dict(
        parser_version="PARTIAL_SURRENDER_EVIDENCE_V2",
        policy=PARTIAL_SURRENDER_POLICY,
        review={**review, "documents": documents},
        event=normalized,
        event_checksum=event.event_checksum,
        source_bytes_verified=True,
        unresolved_source_requirements=gaps,
        historical_event_admission="PARTIAL" if gaps else "ELIGIBLE_FOR_SEPARATE_DATASET_AUDIT",
        research_convention_admission="PASS_UNDER_APPROVED_CONVENTION"
        if convention
        else "NOT_USED",
        full_census_certified=False,
    )
    return {**body, "manifest_sha256": canonical_sha256(body)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("review", "event", "staging", "output"):
        parser.add_argument(f"--{name}", type=Path, required=True)
    args = parser.parse_args()
    review = json.loads(args.review.read_bytes())
    event = MandatoryPartialShareSurrenderEvent.model_validate_json(args.event.read_bytes())
    report = audit(review, event, args.staging)
    reverse = audit(
        {**review, "documents": list(reversed(review["documents"]))},
        event.model_copy(
            update={
                "sources": tuple(reversed(event.sources)),
                "confirmation_sources": tuple(reversed(event.confirmation_sources)),
                "boundary_sources": tuple(reversed(event.boundary_sources)),
            }
        ),
        args.staging,
    )
    if report != reverse:
        raise ValueError("INPUT_ORDER_REPRODUCIBILITY_FAILED")
    write_immutable(args.output, canonical_json_bytes(report) + b"\n")
    print(
        json.dumps(
            {
                k: report[k]
                for k in (
                    "event_checksum",
                    "manifest_sha256",
                    "historical_event_admission",
                    "unresolved_source_requirements",
                )
            }
        )
    )
