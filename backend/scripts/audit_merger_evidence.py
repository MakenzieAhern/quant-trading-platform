"""Reconcile reviewed merger facts with retained official bytes; not a full census."""

import argparse
import json
from pathlib import Path

from app.data.catalog.checksums import canonical_json_bytes, canonical_sha256, sha256_file
from app.data.catalog.freeze import write_immutable
from app.domain.markets.mergers import MERGER_POLICY, MergerEvent
from scripts.audit_demerger_evidence import verify_sources


def audit(review, event, staging):
    if review["policy"] != MERGER_POLICY:
        raise ValueError("MERGER_POLICY_MISMATCH")
    event.require_supported()
    documents = verify_sources(review, (*event.sources, *event.activation_sources), staging)
    normalized = event.model_dump(mode="json")
    normalized["sources"].sort(key=lambda s: (s["sha256"], s["url"]))
    normalized["activation_sources"].sort(key=lambda s: (s["sha256"], s["url"]))
    body = dict(
        parser_version="MERGER_EVIDENCE_V2_ZERO_WHOLE",
        policy=MERGER_POLICY,
        review={**review, "documents": documents},
        event=normalized,
        event_checksum=event.event_checksum,
        source_bytes_verified=True,
        full_census_certified=False,
    )
    return {**body, "manifest_sha256": canonical_sha256(body)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("review", "event", "staging", "output"):
        parser.add_argument(f"--{name}", type=Path, required=True)
    args = parser.parse_args()
    review = json.loads(args.review.read_bytes())
    event = MergerEvent.model_validate_json(args.event.read_bytes())
    report = audit(review, event, args.staging)
    reverse = audit(
        {**review, "documents": list(reversed(review["documents"]))},
        event.model_copy(
            update={
                "sources": tuple(reversed(event.sources)),
                "activation_sources": tuple(reversed(event.activation_sources)),
            }
        ),
        args.staging,
    )
    if report != reverse:
        raise ValueError("INPUT_ORDER_REPRODUCIBILITY_FAILED")
    write_immutable(args.output, canonical_json_bytes(report) + b"\n")
    print(
        json.dumps(
            dict(
                event_checksum=event.event_checksum,
                manifest_sha256=report["manifest_sha256"],
                file_sha256=sha256_file(args.output),
                documents_verified=len(review["documents"]),
            )
        )
    )
