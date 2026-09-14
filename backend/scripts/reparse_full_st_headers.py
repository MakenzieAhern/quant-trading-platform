"""Replay only alternate header extractions; never promote full ST authority."""

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
    parser.add_argument("--alternate", type=Path, required=True)
    args = parser.parse_args()
    prior_path = args.root / "transition-parser-full-v1.json"
    metadata_path = args.root / "sse-reconciliation-manifest-v2.json"
    prior = json.loads(prior_path.read_bytes())
    metadata = json.loads(metadata_path.read_bytes())
    records = {
        cn["announcementId"]: record
        for checkpoint in metadata["results"]
        for record in checkpoint["records"]
        for cn in record["cninfo"]
    }
    results, inputs = [], []
    for original in prior["results"]:
        path = args.alternate / (original.get("source_sha256", "") + ".json")
        if original["status"] != "PARSER_UNRESOLVED" or not path.exists():
            results.append(original)
            continue
        raw = path.read_bytes()
        alternate = json.loads(raw)
        if alternate["source_sha256"] != original["source_sha256"]:
            raise ValueError("ALTERNATE_SOURCE_CHANGED")
        target = args.root / "alternate-text-v1" / path.name
        write_immutable(target, raw)
        inputs.append(dict(path=str(target), sha256=sha256_file(target)))
        record = dict(records[original["announcement_id"]])
        record["cninfo_document_sha256"] = original["source_sha256"]
        result = {k: v for k, v in original.items() if k != "reason"}
        result["previous_reason"] = original["reason"]
        result["alternate_extraction_sha256"] = sha256_file(target)
        try:
            event = extract(alternate["pages"], record)
            event["alternate_extraction_sha256"] = sha256_file(target)
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
        inputs=[dict(path=str(p), sha256=sha256_file(p)) for p in (prior_path, metadata_path)]
        + inputs,
        parser_sha256=sha256_file(Path("scripts/sse_st_events.py")),
        counts=dict(Counter(r["status"] for r in results)),
        input_order_reproducibility="PASS",
        results=results,
    )
    report["manifest_sha256"] = sha(canonical_json_bytes(report))
    write_immutable(
        args.root / "transition-parser-full-v2.json", canonical_json_bytes(report) + b"\n"
    )
    print(json.dumps(dict(counts=report["counts"], manifest_sha256=report["manifest_sha256"])))


if __name__ == "__main__":
    main()
