"""Close P1 issuer notices explicitly distributing preferred shares, not ordinary A."""

import argparse
import json
import re
from pathlib import Path

from app.data.catalog.checksums import canonical_json_bytes, canonical_sha256, sha256_file
from app.data.catalog.freeze import write_immutable
from scripts.audit_p1_public_fact_requirements import verified


def preferred_only(title: str, pages: list[str]) -> bool:
    return bool(
        re.search(r"优先股|光大优3", title)
        and not re.search(r"A股|普通股", title)
        and re.search(r"优先股|光大优3", "\n".join(pages))
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--closure", type=Path, required=True)
    parser.add_argument("--triage", type=Path, required=True)
    parser.add_argument("--primary-cash", type=Path, required=True)
    parser.add_argument("--source-manifest", type=Path, required=True)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    closure, triage, cash, sources = (
        verified(path)
        for path in (args.closure, args.triage, args.primary_cash, args.source_manifest)
    )
    already_cash = {row["event"]["source_url"] for row in cash["events"]}
    by_id = {row["document_id"]: row for row in triage["documents"]}
    by_url = {row["url"]: row for row in sources["documents"]}
    if (
        len(by_id) != len(triage["documents"])
        or len(by_url) != len(sources["documents"])
        or len({row["document_id"] for row in closure["remaining_cash_documents"]})
        != len(closure["remaining_cash_documents"])
    ):
        raise ValueError("P1_PREFERRED_SOURCE_IDENTITY_AMBIGUOUS")
    excluded = []
    for requirement in closure["remaining_cash_documents"]:
        if requirement["url"] in already_cash:
            continue
        row = by_id[requirement["document_id"]]
        if not re.search(r"优先股|光大优3", requirement["title"]):
            continue
        source = by_url[requirement["url"]]
        pdf = args.source_root / source["source_path"]
        cache = args.source_root / "batch-v1/text" / f"{source['source_sha256']}.json"
        if (
            source["retrieval_status"] != "PASS"
            or source["issuer"] != requirement["issuer"]
            or source["title"] != requirement["title"]
            or source["source_sha256"] != row["source_sha256"]
            or sha256_file(pdf) != source["source_sha256"]
            or sha256_file(cache) != row["text_cache_sha256"]
        ):
            raise ValueError("P1_PREFERRED_NOTICE_SOURCE_CHANGED")
        extracted = json.loads(cache.read_bytes())
        if extracted["source_sha256"] != source["source_sha256"]:
            raise ValueError("P1_PREFERRED_NOTICE_TEXT_CHANGED")
        if preferred_only(requirement["title"], extracted["pages"]):
            excluded.append(
                {
                    "document_id": requirement["document_id"],
                    "affected_events": requirement["affected_events"],
                    "issuer": requirement["issuer"],
                    "title": requirement["title"],
                    "url": requirement["url"],
                    "source_sha256": source["source_sha256"],
                    "text_cache_sha256": sha256_file(cache),
                    "classification": "PREFERRED_SHARE_NOTICE_OUTSIDE_ORDINARY_A_SCOPE",
                }
            )
    excluded.sort(key=lambda row: row["document_id"])
    report = {
        "report_version": "P1_PREFERRED_INSTRUMENT_NOTICE_SCOPE_V1",
        "parser_sha256": sha256_file(Path(__file__)),
        "input_sha256s": {
            name: sha256_file(path)
            for name, path in (
                ("closure", args.closure),
                ("triage", args.triage),
                ("primary_cash", args.primary_cash),
                ("source_manifest", args.source_manifest),
            )
        },
        "excluded_documents": len(excluded),
        "excluded_facts": sum(len(row["affected_events"]) for row in excluded),
        "excluded": excluded,
        "ordinary_a_cash_events_created": 0,
        "input_order_reproducibility": "PASS",
    }
    report["manifest_sha256"] = canonical_sha256(report)
    write_immutable(args.output, canonical_json_bytes(report) + b"\n")
    print(json.dumps({key: value for key, value in report.items() if key != "excluded"}))


if __name__ == "__main__":
    main()
