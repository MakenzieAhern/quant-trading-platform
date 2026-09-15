"""Replay unresolved cached extractions only; never promote full ST authority."""

import argparse
import json
from collections import Counter
from pathlib import Path

from app.data.catalog.checksums import canonical_json_bytes, sha256_file
from app.data.catalog.freeze import write_immutable
from scripts.reconcile_sse_cninfo import sha
from scripts.sse_st_events import extract, normalize


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--alternate", type=Path)
    parser.add_argument("--alternate-output", type=Path)
    parser.add_argument("--prior", default="transition-parser-full-v1.json")
    parser.add_argument("--report", default="transition-parser-full-v2.json")
    parser.add_argument("--subject-reviews", type=Path)
    args = parser.parse_args()
    prior_path = args.root / args.prior
    metadata_path = args.root / "sse-reconciliation-manifest-v2.json"
    prior = json.loads(prior_path.read_bytes())
    metadata = json.loads(metadata_path.read_bytes())
    source_path = args.root / "transition-pdfs-v1/source-manifest.json"
    source_manifest = json.loads(source_path.read_bytes())
    for document in (prior, metadata, source_manifest):
        body = {k: v for k, v in document.items() if k != "manifest_sha256"}
        if document["manifest_sha256"] != sha(canonical_json_bytes(body)):
            raise ValueError("INPUT_MANIFEST_CHANGED")
    sources = {r["announcement_id"]: r for r in source_manifest["documents"]}
    records = {
        cn["announcementId"]: record
        for checkpoint in metadata["results"]
        for record in checkpoint["records"]
        for cn in record["cninfo"]
    }
    results, inputs = [], []
    reviews = {}
    if args.subject_reviews:
        review = json.loads(args.subject_reviews.read_bytes())
        if review["scope"] != "DOCUMENT_BOUND_TITLE_EQUIVALENCE_ONLY_NOT_EVENT_ACCEPTANCE":
            raise ValueError("WRONG_SUBJECT_REVIEW_SCOPE")
        reviews = {r["announcement_id"]: r for r in review["records"]}
        if len(reviews) != len(review["records"]):
            raise ValueError("DUPLICATE_SUBJECT_REVIEW")
        inputs.append(
            dict(path=str(args.subject_reviews), sha256=sha256_file(args.subject_reviews))
        )
    for original in prior["results"]:
        filename = original.get("source_sha256", "") + ".json"
        path = (args.alternate or args.root / "alternate-text-v1") / filename
        if not args.alternate and not path.exists():
            path = args.root / "batch-v1/text" / filename
        if original["status"] != "PARSER_UNRESOLVED" or not path.exists():
            results.append(original)
            continue
        raw = path.read_bytes()
        alternate = json.loads(raw)
        if alternate["source_sha256"] != original["source_sha256"]:
            raise ValueError("ALTERNATE_SOURCE_CHANGED")
        source = sources[original["announcement_id"]]
        if sha256_file(args.root / source["source_path"]) != original["source_sha256"]:
            raise ValueError("PDF_SOURCE_CHANGED")
        target = (
            (args.alternate_output or args.root / "alternate-text-v1") / path.name
            if args.alternate
            else path
        )
        if args.alternate:
            write_immutable(target, raw)
        inputs.append(dict(path=str(target), sha256=sha256_file(target)))
        record = dict(records[original["announcement_id"]])
        record["cninfo_document_sha256"] = original["source_sha256"]
        if original["announcement_id"] in reviews:
            record["pdf_subject_review"] = reviews[original["announcement_id"]]
        result = {k: v for k, v in original.items() if k != "reason"}
        result["previous_reason"] = original["reason"]
        result["extraction_sha256"] = sha256_file(target)
        try:
            event = extract(alternate["pages"], record)
            event["extraction_sha256"] = sha256_file(target)
            event["retrieved_at_utc"] = source["retrieved_at_utc"]
            event["event_sha256"] = sha(canonical_json_bytes(event))
            result.update(
                event=event,
                status="PARSED_TRANSITION_REQUIRES_LIFECYCLE_AND_COVERAGE_REVIEW",
            )
        except ValueError as exc:
            result["reason"] = str(exc)
        results.append(result)
    assert len(results) == len(prior["results"])
    events = [r["event"] for r in results if "event" in r]
    assert normalize(events) == normalize(list(reversed(events)))
    assert all(r in results for r in prior["results"] if "event" in r)
    report = dict(
        scope="FULL_SELECTED_SSE_TRANSITIONS_NOT_COMPLETE_CENSUS",
        accepted_events=0,
        inputs=[
            dict(path=str(p), sha256=sha256_file(p))
            for p in (prior_path, metadata_path, source_path)
        ]
        + inputs,
        parser_sha256=sha256_file(Path("scripts/sse_st_events.py")),
        matcher_sha256=sha256_file(Path("scripts/reconcile_sse_cninfo.py")),
        counts=dict(Counter(r["status"] for r in results)),
        input_order_reproducibility="PASS",
        results=results,
    )
    report["manifest_sha256"] = sha(canonical_json_bytes(report))
    write_immutable(args.root / args.report, canonical_json_bytes(report) + b"\n")
    print(json.dumps(dict(counts=report["counts"], manifest_sha256=report["manifest_sha256"])))


if __name__ == "__main__":
    main()
