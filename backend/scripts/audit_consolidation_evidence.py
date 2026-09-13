"""Verify retained source bytes and separate consolidation/surrender receipts."""

import argparse
import json
from pathlib import Path

from app.data.catalog.checksums import canonical_json_bytes, canonical_sha256, sha256_file
from app.data.catalog.freeze import write_immutable
from app.domain.markets.consolidations import ShareConsolidationEvent
from app.domain.markets.surrenders import MandatoryPartialShareSurrenderEvent
from scripts.audit_demerger_evidence import verify_sources


def audit(consolidation, surrender, root, catalog):
    matrix = json.loads(catalog.read_bytes())
    expected = "3784d6817fb7ab30081e57d9693bc1ac7adbfbaccebe200e2903e7021d8a0352"
    if sha256_file(catalog) != expected:
        raise ValueError("FROZEN_POLICY_CATALOG_CHANGED")
    if not consolidation.effective_date < surrender.application_date:
        raise ValueError("EVENT_SEQUENCE_CONTRADICTED")
    if consolidation.security_id != surrender.security_id:
        raise ValueError("EVENT_SECURITY_MISMATCH")
    receipts = []
    for event in (consolidation, surrender):
        event.require_supported()
        if event.convention_approval_sha256 != matrix["approval_sha256"]:
            raise ValueError("APPROVAL_MISMATCH")
        sources = (*event.sources, *event.confirmation_sources)
        documents = []
        for source in sources:
            name = source.document.split(";", 1)[0]
            documents.append(
                dict(
                    path=name,
                    url=source.url,
                    sha256=source.sha256,
                    published_on=source.published_on.isoformat(),
                    retrieved_at_utc=source.retrieved_at.isoformat(),
                )
            )
        verified = verify_sources({"documents": documents}, sources, root)
        reversed_event = event.model_copy(
            update={
                key: tuple(reversed(getattr(event, key)))
                for key in ("sources", "confirmation_sources")
            }
        )
        assert event.event_checksum == reversed_event.event_checksum
        receipts.append(
            dict(
                event_checksum=event.event_checksum,
                policy=event.policy,
                effective_date=event.effective_date.isoformat(),
                documents=verified,
            )
        )
    body = dict(
        parser_version="CONSOLIDATION_EVIDENCE_V1",
        policy_catalog_file_sha256=expected,
        source_bytes_verified=True,
        input_order_reproducibility="PASS",
        events=receipts,
        full_census_certified=False,
        surrender_separate_record_date="NOT_INVENTED",
        fractional_source_finding=(
            "Official plan references ChinaClear guide, but actual holder allocation is not "
            "reconstructed; approved research fallback explicitly applied."
        ),
    )
    return {**body, "manifest_sha256": canonical_sha256(body)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("consolidation", "surrender", "root", "catalog", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    report = audit(
        ShareConsolidationEvent.model_validate_json(args.consolidation.read_bytes()),
        MandatoryPartialShareSurrenderEvent.model_validate_json(args.surrender.read_bytes()),
        args.root,
        args.catalog,
    )
    write_immutable(args.output, canonical_json_bytes(report) + b"\n")
    print(json.dumps(report))
