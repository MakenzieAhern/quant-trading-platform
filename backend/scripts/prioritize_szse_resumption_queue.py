"""Build a first-pass official-document queue without treating titles as facts."""

import argparse
import json
import re
from pathlib import Path

from app.data.catalog.checksums import canonical_json_bytes, canonical_sha256, sha256_file
from app.data.catalog.freeze import write_immutable

TITLE = re.compile(r"停牌|复牌|恢复交易")


def prioritize(
    queues: list[list[dict]],
    title: re.Pattern = TITLE,
    excluded: set[str] | None = None,
) -> tuple[list[dict], int]:
    all_rows = {}
    for queue in queues:
        for row in queue:
            previous = all_rows.get(row["url"])
            identity = ("issuer", "announcement_id", "title", "published_on")
            if previous and any(previous[key] != row[key] for key in identity):
                raise ValueError("CONFLICTING_CNINFO_DOCUMENT_IDENTITY")
            if previous:
                affected = previous["affected_suspensions"] + row["affected_suspensions"]
                previous["affected_suspensions"] = sorted({tuple(value) for value in affected})
            else:
                all_rows[row["url"]] = dict(row)
    selected = [
        row
        for row in all_rows.values()
        if title.search(row["title"]) and row["url"] not in (excluded or set())
    ]
    return sorted(selected, key=lambda row: (row["published_on"], row["url"])), len(all_rows)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--queue", type=Path, action="append", required=True)
    parser.add_argument("--title-pattern", default=TITLE.pattern)
    parser.add_argument("--exclude-queue", type=Path, action="append", default=[])
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    sources = [json.loads(path.read_bytes()) for path in args.queue]
    title = re.compile(args.title_pattern)
    excluded = {row["url"] for path in args.exclude_queue for row in json.loads(path.read_bytes())}
    selected, total = prioritize(sources, title, excluded)
    if (selected, total) != prioritize(
        [list(reversed(queue)) for queue in reversed(sources)], title, excluded
    ):
        raise ValueError("INPUT_ORDER_CHANGED")
    write_immutable(args.output, canonical_json_bytes(selected) + b"\n")
    report = {
        "parser_version": "SZSE_RESUMPTION_TITLE_PRIORITY_QUEUE_V2",
        "parser_sha256": sha256_file(Path(__file__)),
        "source_queue_sha256s": [sha256_file(path) for path in args.queue],
        "excluded_queue_sha256s": [sha256_file(path) for path in args.exclude_queue],
        "title_pattern": args.title_pattern,
        "all_document_leads": total,
        "first_pass_document_leads": len(selected),
        "deferred_document_leads": total - len(selected),
        "first_pass_queue_sha256": sha256_file(args.output),
        "input_order_reproducibility": "PASS",
        "acceptance": "TITLE_PRIORITIZATION_ONLY_NO_RESUMPTION_FACT_ACCEPTED",
    }
    report["manifest_sha256"] = canonical_sha256(report)
    write_immutable(args.report, canonical_json_bytes(report) + b"\n")
    print(json.dumps(report, sort_keys=True))


if __name__ == "__main__":
    main()
