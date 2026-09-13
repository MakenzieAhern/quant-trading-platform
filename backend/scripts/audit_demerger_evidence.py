"""Reverify reviewed original bytes and publish a deterministic event/source receipt.

This does not infer PDF semantics, certify a full census, or authorize a study.
"""

import argparse
import json
from pathlib import Path

from app.data.catalog.checksums import canonical_json_bytes, canonical_sha256, sha256_file
from app.data.catalog.freeze import write_immutable
from app.domain.markets.demergers import DEMERGER_POLICY, DemergerEvent


def verify_sources(review, sources, staging):
    documents = sorted(review["documents"], key=lambda d: d["path"])
    if len({d["path"] for d in documents}) != len(documents):
        raise ValueError("DUPLICATE_SOURCE_PATH")
    for document in documents:
        path = (staging / document["path"]).resolve()
        if not path.is_relative_to(staging.resolve()):
            raise ValueError("SOURCE_OUTSIDE_STAGING")
        meta = json.loads(path.with_suffix(path.suffix + ".meta.json").read_bytes())
        if meta.get("error") or meta.get("http_status") != 200:
            raise ValueError("SOURCE_RETRIEVAL_NOT_ACCEPTED")
        if any(meta[k] != document[k] for k in ("url", "sha256", "retrieved_at_utc")):
            raise ValueError("SOURCE_RECEIPT_MISMATCH")
        if sha256_file(path) != document["sha256"] or not path.read_bytes().startswith(b"%PDF"):
            raise ValueError("SOURCE_BYTES_MISMATCH")
    for source in sources:
        matches = [d for d in documents if d["sha256"] == source.sha256]
        if len(matches) != 1 or (
            matches[0]["url"] != source.url
            or matches[0]["published_on"] != source.published_on.isoformat()
            or matches[0]["retrieved_at_utc"] != source.retrieved_at.isoformat()
        ):
            raise ValueError("EVENT_SOURCE_NOT_RECONCILED")
    return documents


def audit(review, event, staging):
    if review["policy"] != DEMERGER_POLICY:
        raise ValueError("DEMERGER_POLICY_MISMATCH")
    event.require_supported()
    documents = verify_sources(
        review, (event.conversion_source, *event.allocation_sources), staging
    )
    normalized = event.model_dump(mode="json")
    normalized["successors"].sort(key=lambda s: s["security_id"]["value"])
    normalized["allocation_sources"].sort(key=lambda s: s["sha256"])
    body = dict(
        parser_version="DEMERGER_EVIDENCE_V1",
        policy=DEMERGER_POLICY,
        review={**review, "documents": documents},
        event=normalized,
        event_checksum=event.event_checksum,
        source_bytes_verified=True,
        full_census_certified=False,
    )
    return {**body, "manifest_sha256": canonical_sha256(body)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--review", type=Path, required=True)
    parser.add_argument("--event", type=Path, required=True)
    parser.add_argument("--staging", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    review = json.loads(args.review.read_bytes())
    event = DemergerEvent.model_validate_json(args.event.read_bytes())
    report = audit(review, event, args.staging)
    reverse = audit(
        {**review, "documents": list(reversed(review["documents"]))},
        event.model_copy(
            update={
                "successors": tuple(reversed(event.successors)),
                "allocation_sources": tuple(reversed(event.allocation_sources)),
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
                "event_checksum": event.event_checksum,
                "manifest_sha256": report["manifest_sha256"],
                "file_sha256": sha256_file(args.output),
                "documents_verified": len(review["documents"]),
            }
        )
    )
