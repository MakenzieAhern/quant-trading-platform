"""Identify no-holder-award notices without closing their other P1 facts."""

import argparse
import json
import re
from pathlib import Path

from app.data.catalog.checksums import canonical_json_bytes, canonical_sha256, sha256_file
from app.data.catalog.freeze import write_immutable
from scripts.audit_p1_public_fact_requirements import verified
from scripts.triage_p1_remaining_distribution_docs import diagnose

NO_SHARES = re.compile(
    r"(?:本次|前述|转增|股票).{0,80}不向原股东分配|向原股东分配导致股份增加数为0"
)
NO_CASH = ("不涉及现金红利", "现金红利为0", "不涉及现金分红")
POSITIVE_CASH = re.compile(r"每10股派[1-9]|每股派发现金红利[1-9]")


def classify(requirements: list[dict], triage: list[dict], texts: dict[str, str]) -> list[dict]:
    by_id = {row["document_id"]: row for row in triage}
    findings = []
    for item in requirements:
        document_id = item["document_id"]
        title = item["title"]
        if not all(token in title for token in ("资本公积", "转增", "实施")):
            continue
        row = by_id[document_id]
        text = texts.get(document_id, "")
        match = NO_SHARES.search(text)
        cash = next((term for term in NO_CASH if term in text), None)
        if (
            row["candidate_class"] != "NEITHER"
            or row["cash_candidate_per_share"] is not None
            or row["bonus_candidate_per_share"] is not None
            or row["preferred_instrument_marker"]
            or not match
            or not cash
            or POSITIVE_CASH.search(text)
        ):
            continue
        findings.append(
            {
                "document_id": document_id,
                "affected_events": item["affected_events"],
                "issuer": item["issuer"],
                "title": title,
                "published_on": item["published_on"],
                "url": item["url"],
                "source_sha256": row["source_sha256"],
                "text_cache_sha256": row["text_cache_sha256"],
                "no_original_holder_shares_evidence": match.group(),
                "no_cash_dividend_evidence": cash,
                "classification": "NO_ORIGINAL_HOLDER_BONUS_OR_CASH_DIVIDEND_IN_THIS_NOTICE",
            }
        )
    return sorted(findings, key=lambda row: row["document_id"])


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("queue", "triage", "base", "prior", "source-manifest", "source-root", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    queue = json.loads(args.queue.read_bytes())
    triage, base, prior, sources = (
        verified(path) for path in (args.triage, args.base, args.prior, args.source_manifest)
    )
    queue_ids = {row["document_id"] for row in queue}
    base_by_id = {row["document_id"]: row for row in base["remaining_cash_documents"]}
    prior_ids = {row["document_id"] for row in prior["closed"]}
    if (
        len(queue_ids) != len(queue)
        or len(base_by_id) != len(base["remaining_cash_documents"])
        or queue_ids != base_by_id.keys() - prior_ids
        or {row["document_id"] for row in triage["documents"]} != queue_ids
        or triage["source_requirements_sha256"] != sha256_file(args.queue)
        or triage["source_manifest_sha256"] != sha256_file(args.source_manifest)
    ):
        raise ValueError("RESTRUCTURING_INPUT_QUEUE_CHANGED")
    by_id = {row["document_id"]: row for row in sources["documents"]}
    texts = {}
    for item in queue:
        title = item["title"]
        if not all(token in title for token in ("资本公积", "转增", "实施")):
            continue
        source = by_id[item["document_id"]]
        row = next(row for row in triage["documents"] if row["document_id"] == item["document_id"])
        pdf = args.source_root / source["source_path"]
        cache = args.source_root / "batch-v1/text" / f"{source['source_sha256']}.json"
        if (
            source["retrieval_status"] != "PASS"
            or any(source[key] != item[key] for key in ("issuer", "title", "published_on", "url"))
            or source["source_sha256"] != row["source_sha256"]
            or sha256_file(pdf) != row["source_sha256"]
            or sha256_file(cache) != row["text_cache_sha256"]
        ):
            raise ValueError(f"RESTRUCTURING_OFFICIAL_SOURCE_CHANGED:{item['document_id']}")
        extracted = json.loads(cache.read_bytes())
        parsed = diagnose(extracted["pages"], item["issuer"])
        if extracted["source_sha256"] != row["source_sha256"] or any(
            parsed[key] != row[key]
            for key in (
                "candidate_class",
                "cash_candidate_per_share",
                "bonus_candidate_per_share",
                "record_dates",
                "ex_dates",
                "preferred_instrument_marker",
            )
        ):
            raise ValueError(f"RESTRUCTURING_REPARSE_CHANGED:{item['document_id']}")
        texts[item["document_id"]] = re.sub(r"\s+", "", "".join(extracted["pages"]))
    findings = classify(queue, triage["documents"], texts)
    if findings != classify(list(reversed(queue)), list(reversed(triage["documents"])), texts):
        raise ValueError("INPUT_ORDER_CHANGED")
    if len(findings) != 48:
        raise ValueError(f"RESTRUCTURING_SOURCE_SCOPE_CHANGED:{len(findings)}")
    report = {
        "report_version": "P1_RESTRUCTURING_NON_ENTITLEMENT_DIAGNOSTIC_V2",
        "status": "NEGATIVE_ENTITLEMENT_FACT_ONLY_P1_DOCUMENTS_REMAIN_OPEN",
        "parser_sha256": sha256_file(Path(__file__)),
        "input_sha256s": {
            name: sha256_file(path)
            for name, path in (
                ("queue", args.queue),
                ("triage", args.triage),
                ("base", args.base),
                ("prior", args.prior),
                ("source_manifest", args.source_manifest),
            )
        },
        "negative_entitlement_documents": len(findings),
        "negative_entitlement_candidate_facts": sum(
            len(row["affected_events"]) for row in findings
        ),
        "p1_documents_closed": 0,
        "p1_facts_closed": 0,
        "findings": findings,
        "input_order_reproducibility": "PASS",
        "new_economic_events_created": 0,
        "remaining_restructuring_reference_price_and_other_corporate_actions": "OPEN",
    }
    report["manifest_sha256"] = canonical_sha256(report)
    write_immutable(args.output, canonical_json_bytes(report) + b"\n")
    print(json.dumps({key: value for key, value in report.items() if key != "findings"}))


if __name__ == "__main__":
    main()
