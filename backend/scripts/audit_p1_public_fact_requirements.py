"""Reduce P1 source requests to facts applicable to the official ordinary-A master."""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

from app.data.catalog.checksums import canonical_json_bytes, canonical_sha256, sha256_file
from app.data.catalog.freeze import write_immutable

VERSION = "P1_PUBLIC_FACT_REASSESSMENT_V1"
CNINFO = "https://static.cninfo.com.cn/finalpage/"


def verified(path: Path) -> dict:
    value = json.loads(path.read_bytes())
    expected = value.pop("manifest_sha256")
    if canonical_sha256(value) != expected:
        raise ValueError(f"INPUT_MANIFEST_CHANGED:{path}")
    value["manifest_sha256"] = expected
    return value


def acquired_urls(roots: list[Path]) -> set[str]:
    found = set()
    for root in roots:
        for receipt in root.rglob("*.pdf.meta.json"):
            meta = json.loads(receipt.read_bytes())
            pdf = Path(str(receipt).removesuffix(".meta.json"))
            if meta.get("http_status") == 200 and pdf.exists():
                if sha256_file(pdf) != meta["sha256"]:
                    raise ValueError(f"SOURCE_CHECKSUM_MISMATCH:{pdf}")
                found.add(meta["url"])
    return found


def run(
    requirements_v1: Path,
    requirements_v2: Path,
    master_path: Path,
    p0_report_path: Path,
    queue_path: Path,
    report_path: Path,
    source_roots: list[Path],
) -> dict:
    v1, v2, p0 = map(verified, (requirements_v1, requirements_v2, p0_report_path))
    master = json.loads(master_path.read_bytes())
    if canonical_sha256(master) != p0["reconstructed_master_sha256"]:
        raise ValueError("P0_MASTER_CHANGED")
    ordinary_symbols = {
        row["symbol"] for row in master if row["instrument_type"] == "COMMON_A_SHARE"
    }
    v1_by_url: dict[str, list[dict]] = defaultdict(list)
    for item in v1["required_source_items"]:
        if item.get("known_url"):
            v1_by_url[item["known_url"]].append(item)

    p1 = [row for row in v2["documents"] if row["priority"] == "P1"]
    yearbooks = [
        row
        for row in p1
        if row["required_document_types"] == ["OFFICIAL_SZSE_STATISTICAL_YEARBOOK"]
    ]
    known_years = {
        row["fact_year"]
        for row in p0["annual_reconciliation"]
        if row["exchange"] == "SZSE" and row["status"] == "PASS"
    }
    if len(yearbooks) != 4 or any(row["years"][0] not in known_years for row in yearbooks):
        raise ValueError("P1_YEARBOOK_FACT_NOT_ESTABLISHED")

    in_scope, out_of_scope = [], []
    for doc in p1:
        urls = [url for url in doc["known_urls"] if url.startswith(CNINFO)]
        if not urls:
            continue
        items = v1_by_url[urls[0]]
        issuers = {item["security"] for item in items}
        titles = {item["event"] for item in items}
        if len(issuers) != 1 or len(titles) != 1:
            raise ValueError(f"CNINFO_SOURCE_IDENTITY_CONFLICT:{urls[0]}")
        target = in_scope if next(iter(issuers)) in ordinary_symbols else out_of_scope
        target.append((doc, items[0]))

    queue = [
        {
            "affected_events": doc["affected_events"],
            "document_id": doc["document_id"],
            "issuer": item["security"],
            "published_on": item["range"],
            "queue_type": "+".join(doc["required_document_types"]),
            "title": item["event"],
            "url": doc["known_urls"][0],
        }
        for doc, item in in_scope
    ]
    queue.sort(key=lambda row: (row["queue_type"], row["published_on"], row["url"]))
    acquired = acquired_urls(source_roots)
    resolved_ids = {row["document_id"] for row in yearbooks} | {
        row["document_id"] for row, _ in out_of_scope
    }
    unresolved = [row for row in p1 if row["document_id"] not in resolved_ids]
    raw = sum(row["affected_event_count"] for row in p1)
    established = sum(row["affected_event_count"] for row in yearbooks) + sum(
        row["affected_event_count"] for row, _ in out_of_scope
    )
    acquired_required = sum(bool(set(row["known_urls"]) & acquired) for row in unresolved)
    report = {
        "report_version": VERSION,
        "p1_raw_requirements": raw,
        "p1_facts_already_established": established,
        "p1_resolved_by_official_substitution": 0,
        "p1_true_missing_source_facts": raw - established,
        "p1_true_new_documents_required": len(unresolved) - acquired_required,
        "p1_unique_documents": len(p1),
        "p1_directly_resolved_yearbook_facts": sum(
            row["affected_event_count"] for row in yearbooks
        ),
        "p1_non_applicable_out_of_scope_facts": sum(
            row["affected_event_count"] for row, _ in out_of_scope
        ),
        "p1_unresolved_unique_documents": len(unresolved),
        "p1_in_scope_public_cninfo_documents": len(in_scope),
        "p1_acquired_required_documents": acquired_required,
        "p1_public_cninfo_documents_still_to_acquire": sum(
            row["url"] not in acquired for row in queue
        ),
        "p1_other_documents_still_required": len(unresolved) - len(in_scope),
        "out_of_scope_cninfo_documents": [
            {
                "document_id": doc["document_id"],
                "issuer": item["security"],
                "reason": "NOT_IN_OFFICIAL_ORDINARY_A_SECURITY_MASTER",
                "url": doc["known_urls"][0],
            }
            for doc, item in sorted(out_of_scope, key=lambda row: row[0]["document_id"])
        ],
        "queue_sha256": canonical_sha256(queue),
        "inputs": [
            {"path": str(path), "sha256": sha256_file(path)}
            for path in (requirements_v1, requirements_v2, master_path, p0_report_path)
        ],
        "limitations": [
            "ACQUIRED_SOURCE_BYTES_DO_NOT_ESTABLISH_EVENT_FACTS_UNTIL_PARSED_AND_RECONCILED",
            "OUT_OF_SCOPE_CLASSIFICATION_USES_THE_ACCEPTED_PUBLIC_OFFICIAL_ORDINARY_A_MASTER",
        ],
    }
    report["manifest_sha256"] = canonical_sha256(report)
    write_immutable(queue_path, canonical_json_bytes(queue) + b"\n")
    write_immutable(report_path, canonical_json_bytes(report) + b"\n")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--requirements-v1", type=Path, required=True)
    parser.add_argument("--requirements-v2", type=Path, required=True)
    parser.add_argument("--master", type=Path, required=True)
    parser.add_argument("--p0-report", type=Path, required=True)
    parser.add_argument("--queue", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--source-root", type=Path, action="append", default=[])
    args = parser.parse_args()
    report = run(
        args.requirements_v1,
        args.requirements_v2,
        args.master,
        args.p0_report,
        args.queue,
        args.output,
        args.source_root,
    )
    print(json.dumps({k: v for k, v in report.items() if not isinstance(v, list)}))


if __name__ == "__main__":
    main()
