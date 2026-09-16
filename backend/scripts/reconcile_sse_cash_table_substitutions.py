"""Accept exact SSE cash rows only when an issuer notice says non-differentiated."""

import argparse
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

from app.data.catalog.checksums import canonical_json_bytes, canonical_sha256, sha256_file
from app.data.catalog.freeze import write_immutable
from app.domain.markets.corporate_actions import CorporateAction, require_supported_corporate_action
from scripts.reconcile_distribution_cash import normalized_document, verified

POLICY = "SSE_GROSS_A_TABLE_PLUS_EXPLICIT_NON_DIFFERENTIATED_NOTICE_V1"


def distribution_class(pages):
    text = re.sub(r"\s+", "", normalized_document(pages))
    found = {value for value in ("是", "否") if f"差异化分红送转:{value}" in text}
    return {"是": "DIFFERENTIATED", "否": "NON_DIFFERENTIATED"}.get(
        next(iter(found)) if len(found) == 1 else "", "CONFLICT" if found else "UNMARKED"
    )


def raw_sources(root):
    sources = defaultdict(list)
    for receipt in sorted(root.glob("dividend-*.json.meta.json")):
        metadata = json.loads(receipt.read_bytes())
        raw = Path(str(receipt).removesuffix(".meta.json"))
        if (
            metadata.get("http_status") != 200
            or not metadata.get("url", "").startswith("https://query.sse.com.cn/")
            or sha256_file(raw) != metadata.get("sha256")
        ):
            raise ValueError("SSE_TABLE_SOURCE_CHANGED")
        payload = json.loads(raw.read_bytes())
        rows = [*payload.get("pageHelp", {}).get("data", []), *payload.get("result", [])]
        source = {
            "url": metadata["url"],
            "source_sha256": metadata["sha256"],
            "retrieved_at_utc": metadata["retrieved_at_utc"],
            "source_path": str(raw),
        }
        for row in rows:
            sources[canonical_sha256(row)].append(source)
    return {
        key: sorted(value, key=lambda item: (item["url"], item["source_sha256"]))[0]
        for key, value in sources.items()
    }


def reconcile(root, gaps, groups, master, documents, sources, superseded=frozenset()):
    intervals = defaultdict(list)
    for row in master:
        intervals[row["security_id"]].append(row)
    audited = {}
    for group in groups:
        if group["key"][0] != "dividend" or group["status"] != "CANDIDATE_NOT_ACCEPTED":
            continue
        terms = {canonical_sha256(item["normalized"]) for item in group["evidence"]}
        if len(terms) == 1:
            row = group["evidence"][0]
            audited[
                (
                    row["normalized"]["source_symbol"],
                    row["normalized"]["record_date"],
                    row["normalized"]["ex_date"],
                )
            ] = row

    by_event = defaultdict(list)
    for document in documents:
        if document["retrieval_status"] != "PASS" or "实施" not in document["title"]:
            continue
        source = root / document["source_path"]
        cache = root / "batch-v1/text" / f"{document['source_sha256']}.json"
        if sha256_file(source) != document["source_sha256"] or not cache.exists():
            raise ValueError("ISSUER_NOTICE_SOURCE_CHANGED")
        extracted = json.loads(cache.read_bytes())
        if extracted["source_sha256"] != document["source_sha256"]:
            raise ValueError("ISSUER_NOTICE_EXTRACTION_CHANGED")
        classification = distribution_class(extracted["pages"])
        for event in document["affected_events"]:
            if event.startswith("CASH:") and len(event.split(":")) == 4:
                by_event[tuple(event.split(":")[1:])].append((classification, document))

    events, outcomes = [], []
    for gap in gaps:
        if not gap["security_id"].startswith("CN-A:SSE:"):
            continue
        members = [
            row
            for row in intervals[gap["security_id"]]
            if row["instrument_type"] == "COMMON_A_SHARE"
            and row["effective_from"] <= gap["record_date"] <= gap["ex_date"]
            and gap["ex_date"] <= (row["effective_to"] or "2025-12-31")
        ]
        if len(members) != 1:
            raise ValueError("SSE_CASH_LIFECYCLE_UNRESOLVED")
        key = (members[0]["symbol"], gap["record_date"], gap["ex_date"])
        candidates = by_event.get(key, [])
        classes = {item[0] for item in candidates}
        outcome = {
            "security_id": gap["security_id"],
            "symbol": key[0],
            "record_date": key[1],
            "ex_date": key[2],
        }
        if "DIFFERENTIATED" in classes or "CONFLICT" in classes:
            outcome["status"] = "DIFFERENTIATED_OR_CONFLICTING_NOTICE"
        elif "NON_DIFFERENTIATED" not in classes:
            outcome["status"] = "NO_EXPLICIT_NON_DIFFERENTIATED_NOTICE"
        elif key not in audited:
            outcome["status"] = "NO_UNCONFLICTED_SSE_TABLE_ROW"
        else:
            notices = sorted(
                (
                    document
                    for classification, document in candidates
                    if classification == "NON_DIFFERENTIATED"
                    and document["published_on"] <= gap["record_date"]
                ),
                key=lambda row: (row["published_on"], row["url"], row["source_sha256"]),
            )
            evidence = audited[key]
            table = sources.get(canonical_sha256(evidence["raw_row"]))
            if not notices:
                outcome["status"] = "NOTICE_AFTER_RECORD_DATE"
            elif table is None:
                outcome["status"] = "SSE_TABLE_RECEIPT_NOT_FOUND"
            elif (gap["security_id"], gap["ex_date"], "CASH_DIVIDEND") in superseded:
                outcome["status"] = "SUPERSEDED_BY_PRECISE_ISSUER_NOTICE"
            else:
                notice = notices[0]
                combined = {
                    "policy_id": POLICY,
                    "sse_table": {
                        "normalized": evidence["normalized"],
                        "raw_row": evidence["raw_row"],
                        "source": table,
                    },
                    "issuer_notice": notice,
                }
                action = CorporateAction.model_validate(
                    {
                        "security_id": {"value": gap["security_id"]},
                        "action_type": "CASH_DIVIDEND",
                        "announcement_date": notice["published_on"],
                        "effective_date": gap["ex_date"],
                        "record_date": gap["record_date"],
                        "ex_date": gap["ex_date"],
                        "cash_per_share": evidence["normalized"]["amount"],
                        "source_document": (
                            "SSE official distribution table with issuer "
                            "non-differentiated implementation notice"
                        ),
                        "source_url": table["url"],
                        "source_document_sha256": table["source_sha256"],
                        "retrieved_at": table["retrieved_at_utc"],
                        "source_provider": "OFFICIAL_SSE_TABLE_CNINFO_NOTICE_COMPOSITE",
                        "source_version": POLICY,
                        "source_record_hash": canonical_sha256(combined),
                        "completeness": "COMPLETE",
                    }
                )
                require_supported_corporate_action(action)
                events.append(
                    {
                        "event": action.model_dump(mode="json"),
                        "event_checksum": action.event_checksum,
                        "policy_id": POLICY,
                        "support_state": "AUTHORITATIVE_OFFICIAL_SOURCE_SUBSTITUTION",
                        "metadata_only_gaps": ["PAYMENT_DATE_NOT_NORMALIZED"],
                        "source_terms_sha256": canonical_sha256(combined),
                        "evidence": combined,
                    }
                )
                outcome["status"] = "ACCEPTED_OFFICIAL_SUBSTITUTION"
        outcomes.append(outcome)
    return sorted(events, key=lambda row: row["event_checksum"]), sorted(
        outcomes, key=lambda row: (row["security_id"], row["record_date"], row["ex_date"])
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--source-manifest", type=Path, action="append", required=True)
    parser.add_argument("--coverage", type=Path, required=True)
    parser.add_argument("--sse-audit", type=Path, required=True)
    parser.add_argument("--master", type=Path, required=True)
    parser.add_argument("--sse-root", type=Path, required=True)
    parser.add_argument("--accepted", type=Path, action="append", default=[])
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    source_manifests = [verified(path) for path in args.source_manifest]
    coverage, audit = map(verified, (args.coverage, args.sse_audit))
    master = json.loads(args.master.read_bytes())
    sources = raw_sources(args.sse_root)
    accepted = [verified(path) for path in args.accepted]
    superseded = {
        (
            row["event"]["security_id"]["value"],
            row["event"]["ex_date"],
            row["event"]["action_type"],
        )
        for ledger in accepted
        for row in ledger["events"]
    }
    documents = sorted(
        {
            (row["url"], row["source_sha256"]): row
            for manifest in source_manifests
            for row in manifest["documents"]
        }.values(),
        key=lambda row: (row["url"], row["source_sha256"]),
    )
    values = reconcile(
        args.root,
        coverage["unresolved_events"],
        audit["groups"],
        master,
        documents,
        sources,
        superseded,
    )
    reversed_values = reconcile(
        args.root,
        list(reversed(coverage["unresolved_events"])),
        list(reversed(audit["groups"])),
        list(reversed(master)),
        list(reversed(documents)),
        sources,
        superseded,
    )
    if values != reversed_values:
        raise ValueError("INPUT_ORDER_CHANGED")
    events, outcomes = values
    report = {
        "parser_version": "SSE_OFFICIAL_TABLE_CASH_SUBSTITUTION_V1",
        "parser_sha256": sha256_file(Path(__file__)),
        "policy_id": POLICY,
        "inputs": [
            {"path": str(path), "sha256": sha256_file(path)}
            for path in (
                *args.source_manifest,
                args.coverage,
                args.sse_audit,
                args.master,
                *args.accepted,
            )
        ],
        "outcome_counts": dict(sorted(Counter(row["status"] for row in outcomes).items())),
        "accepted_events": len(events),
        "outcomes": outcomes,
        "events": events,
        "input_order_reproducibility": "PASS",
        "full_dataset_created": False,
    }
    report["manifest_sha256"] = canonical_sha256(report)
    write_immutable(args.output, canonical_json_bytes(report) + b"\n")
    print(
        json.dumps(
            {key: value for key, value in report.items() if not isinstance(value, list)},
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
