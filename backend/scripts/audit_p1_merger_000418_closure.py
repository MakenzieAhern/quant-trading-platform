"""Close the one P1 official-source request backed by the audited 000418 chain."""

import argparse
import json
from pathlib import Path

from app.data.catalog.checksums import canonical_json_bytes, canonical_sha256, sha256_file
from app.data.catalog.freeze import write_immutable
from scripts.audit_p1_public_fact_requirements import verified
from scripts.reconcile_merger_implementation_batch import event_from_review

EVENT = "MERGER_NEW:000418:000333"


def close(
    requirements: dict, audit: dict, fixture: dict, fixture_sha: str, event_id: str = EVENT
) -> dict:
    case = fixture["case"]
    if event_id != f"MERGER_NEW:{case['parent']}:{case['successor']}":
        raise ValueError("P1_MERGER_EVENT_ID_MISMATCH")
    matches = [row for row in requirements["documents"] if row.get("affected_events") == [event_id]]
    if len(matches) != 1 or matches[0]["priority"] != "P1":
        raise ValueError("P1_MERGER_REQUIREMENT_NOT_UNIQUE")
    event = event_from_review(case)
    if (
        audit["event_checksum"] != event.event_checksum
        or audit["review_sha256"] != fixture_sha
        or audit["scope"] != case["scope"]
        or not audit["source_bytes_verified"]
        or not audit["source_terms_verified"]
        or audit["input_order_reproducibility"] != "PASS"
        or audit["full_census_certified"]
        or audit["full_dataset_created"]
    ):
        raise ValueError("P1_MERGER_SOURCE_AUDIT_NOT_ACCEPTED")
    return {
        "closed": [
            {
                "document_id": matches[0]["document_id"],
                "affected_events": [event_id],
                "source_audit_manifest_sha256": audit["manifest_sha256"],
                "event_checksum": event.event_checksum,
            }
        ],
        "new_economic_events_created": 0,
        "inventory_admitted": False,
        "full_census_certified": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("requirements", "audit", "fixture", "output"):
        parser.add_argument("--" + name, required=True, type=Path)
    parser.add_argument("--event", default=EVENT)
    parser.add_argument("--revision", type=int, choices=(1, 2), default=1)
    args = parser.parse_args()
    requirements, audit = (verified(path) for path in (args.requirements, args.audit))
    fixture = json.loads(args.fixture.read_bytes())
    report = close(requirements, audit, fixture, sha256_file(args.fixture), args.event)
    report.update(
        report_version=f"P1_MERGER_{fixture['case']['parent']}_OFFICIAL_SOURCE_CLOSURE_V{args.revision}",
        parser_sha256=sha256_file(Path(__file__)),
        input_sha256s={
            name: sha256_file(path)
            for name, path in (
                ("requirements", args.requirements),
                ("audit", args.audit),
                ("fixture", args.fixture),
            )
        },
        input_order_reproducibility="PASS",
    )
    report["manifest_sha256"] = canonical_sha256(report)
    write_immutable(args.output, canonical_json_bytes(report) + b"\n")
    print(json.dumps({key: value for key, value in report.items() if key != "closed"}))


if __name__ == "__main__":
    main()
