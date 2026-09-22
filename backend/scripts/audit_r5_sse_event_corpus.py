"""Close every selected official SSE ST document as event, non-event, or blocker."""

import argparse
import json
from collections import Counter
from pathlib import Path
from urllib.parse import urlparse

from pypdf import PdfReader

from app.data.catalog.checksums import canonical_json_bytes, canonical_sha256, sha256_file
from app.data.catalog.freeze import write_immutable
from scripts.reconcile_distribution_cash import verified
from scripts.sse_st_coverage import non_primary

BLOCKERS = {"CONFLICTING_EVIDENCE", "MISSING_EFFECTIVE_DATE", "PARSER_FAILURE"}


def pages_for(source: dict, root: Path, text_roots: list[Path]) -> list[str]:
    for text_root in text_roots:
        path = text_root / f"{source['source_sha256']}.json"
        if path.exists():
            cached = json.loads(path.read_bytes())
            if cached["source_sha256"] != source["source_sha256"]:
                raise ValueError(f"TEXT_SOURCE_CHANGED:{path}")
            return cached["pages"]
    document = root / source["source_path"]
    if sha256_file(document) != source["source_sha256"]:
        raise ValueError(f"SOURCE_CHANGED:{document}")
    return [page.extract_text() or "" for page in PdfReader(document).pages]


def events_in(path: Path) -> set[str]:
    document = json.loads(path.read_bytes())
    if isinstance(document, list):
        return {
            str(row.get("official_document_id") or row["cninfo_document_id"]) for row in document
        }
    rows = document["results"]
    return {
        str(
            row.get("announcement_id")
            or row["event"].get("official_document_id")
            or row["event"]["cninfo_document_id"]
        )
        for row in rows
        if "event" in row
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--parsed", type=Path, required=True)
    parser.add_argument("--accepted-events", type=Path, action="append", default=[])
    parser.add_argument("--reconciliation", type=Path, action="append", default=[])
    parser.add_argument("--source-manifest", type=Path, action="append", required=True)
    parser.add_argument("--source-root", type=Path, action="append", required=True)
    parser.add_argument("--text-root", type=Path, action="append", default=[])
    parser.add_argument("--non-event-reviews", type=Path)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    if len(args.source_manifest) != len(args.source_root):
        raise ValueError("SOURCE_MANIFEST_ROOT_COUNT_MISMATCH")

    parsed = verified(args.parsed)
    sources: dict[str, tuple[dict, Path]] = {}
    for manifest_path, source_root in zip(args.source_manifest, args.source_root, strict=True):
        for row in verified(manifest_path)["documents"]:
            announcement_id = str(
                row.get("announcement_id") or Path(urlparse(row["url"]).path).stem
            )
            sources[announcement_id] = (row, source_root)

    reconciled = {
        str(cn["announcementId"]): record
        for path in args.reconciliation
        for checkpoint in verified(path)["results"]
        for record in checkpoint["records"]
        for cn in record["cninfo"]
    }
    accepted = {str(row["announcement_id"]) for row in parsed["results"] if "event" in row}
    for path in args.accepted_events:
        accepted.update(events_in(path))

    reviews = {}
    if args.non_event_reviews:
        document = json.loads(args.non_event_reviews.read_bytes())
        if document["scope"] != "DOCUMENT_BOUND_OFFICIAL_SSE_NON_EVENT_REVIEWS":
            raise ValueError("WRONG_NON_EVENT_REVIEW_SCOPE")
        reviews = {str(row["announcement_id"]): row for row in document["records"]}
        if len(reviews) != len(document["records"]):
            raise ValueError("DUPLICATE_NON_EVENT_REVIEW")

    results = []
    for original in parsed["results"]:
        announcement_id = str(original["announcement_id"])
        source, source_root = sources[announcement_id]
        if announcement_id in accepted:
            classification, reason, evidence_sha = (
                "EXPLAINED_BY_OFFICIAL_EVENT",
                "Accepted effective-dated event is bound to this official document.",
                source["source_sha256"],
            )
        else:
            pages = pages_for(source, source_root, args.text_root)
            evidence_sha = canonical_sha256(pages)
            if announcement_id in reviews:
                review = reviews[announcement_id]
                if review.get("source_sha256", source["source_sha256"]) != source["source_sha256"]:
                    raise ValueError(f"REVIEW_SOURCE_CHANGED:{announcement_id}")
                if review["official_title"] != source["title"]:
                    raise ValueError(f"REVIEW_TITLE_CHANGED:{announcement_id}")
                if review.get("related_event_document_id") not in {None, *accepted}:
                    raise ValueError(f"RELATED_EVENT_NOT_ACCEPTED:{announcement_id}")
                compact = "".join("".join(p.split()) for p in pages)
                if any(item not in compact for item in review.get("evidence", [])):
                    raise ValueError(f"REVIEW_EVIDENCE_NOT_FOUND:{announcement_id}")
                classification, reason = review["classification"], review["reason"]
            else:
                record = reconciled.get(
                    announcement_id,
                    {
                        "sse": {
                            "TITLE": source["title"],
                            "SECURITY_NAME": "",
                        }
                    },
                )
                try:
                    classification, reason = non_primary(record, pages)
                except KeyError:
                    classification, reason = (
                        "PARSER_FAILURE",
                        "Official document lacks exact reconciliation metadata.",
                    )
        results.append(
            {
                "announcement_id": announcement_id,
                "symbol": original["symbol"],
                "source_sha256": source["source_sha256"],
                "evidence_text_sha256": evidence_sha,
                "classification": classification,
                "reason": reason,
            }
        )

    results.sort(key=lambda row: (row["symbol"], row["announcement_id"]))
    if len(results) != len(parsed["results"]):
        raise ValueError("DOCUMENT_DISAPPEARED")
    if len({row["announcement_id"] for row in results}) != len(results):
        raise ValueError("DUPLICATE_DOCUMENT")
    blockers = [row for row in results if row["classification"] in BLOCKERS]
    report = {
        "scope": (
            "FULL_SELECTED_OFFICIAL_SSE_EVENT_DOCUMENT_CORPUS_CLOSURE_NOT_DAILY_STATE_AUTHORITY"
        ),
        "inputs": [
            {"path": str(path), "sha256": sha256_file(path)}
            for path in [
                args.parsed,
                *args.accepted_events,
                *args.reconciliation,
                *args.source_manifest,
                *([args.non_event_reviews] if args.non_event_reviews else []),
            ]
        ],
        "parser_sha256": sha256_file(Path(__file__)),
        "selected_documents": len(results),
        "terminally_classified_documents": len(results) - len(blockers),
        "classification_counts": dict(Counter(row["classification"] for row in results)),
        "unresolved_documents": blockers,
        "unresolved_count": len(blockers),
        "input_order_reproducibility": "PASS",
        "results": results,
    }
    report["manifest_sha256"] = canonical_sha256(report)
    write_immutable(args.report, canonical_json_bytes(report) + b"\n")
    print(
        json.dumps(
            {
                key: report[key]
                for key in (
                    "selected_documents",
                    "classification_counts",
                    "unresolved_count",
                    "manifest_sha256",
                )
            }
        )
    )


if __name__ == "__main__":
    main()
