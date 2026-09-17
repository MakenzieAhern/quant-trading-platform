"""Close only source-bound P1 requests whose cash and bonus legs share one official PDF."""

import argparse
import json
import re
from collections import Counter
from decimal import Decimal
from pathlib import Path

import pymupdf

from app.data.catalog.checksums import canonical_json_bytes, canonical_sha256, sha256_file
from app.data.catalog.freeze import write_immutable
from app.domain.markets.corporate_actions import CorporateAction, require_supported_corporate_action
from scripts.audit_full_cash_ledger import official_targets
from scripts.audit_p1_orphan_exchange_dates import classify_dates
from scripts.audit_p1_public_fact_requirements import verified
from scripts.audit_p1_retained_cash_sources import (
    exchange_amount_matches,
    issuer_body_finality,
    retained_final_title,
    retained_sources,
)
from scripts.link_distribution_notices import notice_dates
from scripts.reconcile_distribution_cash import gross_cash
from scripts.retained_bonus_terms import retained_ratio

DUAL_TYPES = [
    "FINAL_BONUS_OR_CONVERSION_IMPLEMENTATION_NOTICE",
    "FINAL_IMPLEMENTATION_NOTICE_WITH_GROSS_ORDINARY_A_SHARE_CASH",
]


def normalized_dates(pages, date):
    return [index + 1 for index, page in enumerate(pages) if date in re.sub(r"\s+", "", page)]


def corroborate_603023_listing(staging, original_pages):
    if normalized_dates(original_pages, "2016年6月16日") != [1] or normalized_dates(
        original_pages, "2016年4月16日"
    ) != [3]:
        raise ValueError("603023_ORIGINAL_LISTING_DATE_CONFLICT_CHANGED")
    root = staging / "full-distribution-notices-v1/targeted-603023-v1"
    pdf = root / "603023-2016-halfyear-revised.pdf"
    receipt = pdf.with_name(pdf.name + ".meta.json")
    metadata = root / "cninfo-603023-2016-halfyear-metadata.json"
    metadata_receipt = metadata.with_name(metadata.name + ".meta.json")
    meta = json.loads(receipt.read_bytes())
    metadata_meta = json.loads(metadata_receipt.read_bytes())
    announcements = json.loads(metadata.read_bytes())["announcements"]
    url = "https://static.cninfo.com.cn/finalpage/2016-09-02/1202669225.PDF"
    if (
        meta["url"] != url
        or meta["http_status"] != 200
        or meta["sha256"] != sha256_file(pdf)
        or metadata_meta["url"] != "https://www.cninfo.com.cn/new/hisAnnouncement/query"
        or metadata_meta["http_status"] != 200
        or metadata_meta["sha256"] != sha256_file(metadata)
        or not any(
            row["secCode"] == "603023"
            and row["announcementId"] == "1202669225"
            and row["announcementTitle"] == "2016年半年度报告(修订版)"
            and row["announcementTime"] == 1472745600000
            and row["adjunctUrl"] == "finalpage/2016-09-02/1202669225.PDF"
            for row in announcements
        )
    ):
        raise ValueError("603023_RETROSPECTIVE_OFFICIAL_SOURCE_CHANGED")
    with pymupdf.open(pdf) as document:
        pages = [page.get_text() for page in document]
    phrase = "新增无限售条件流通股份上市日为2016年6月16日"
    if normalized_dates(pages, phrase) != [15, 21, 61]:
        raise ValueError("603023_RETROSPECTIVE_LISTING_DATE_NOT_CORROBORATED")
    return {
        "official_source_url": url,
        "official_pdf_sha256": meta["sha256"],
        "receipt_sha256": sha256_file(receipt),
        "metadata_sha256": sha256_file(metadata),
        "metadata_receipt_sha256": sha256_file(metadata_receipt),
        "published_on": "2016-09-02",
        "confirmed_listing_date": "2016-06-16",
        "page_numbers": [15, 21, 61],
        "role": "RETROSPECTIVE_AUDIT_ONLY_NOT_POINT_IN_TIME_SIGNAL",
    }


def event_index(rows):
    indexed = {}
    for row in rows:
        event = CorporateAction.model_validate(row["event"])
        require_supported_corporate_action(event)
        if event.event_checksum != row["event_checksum"]:
            raise ValueError("ACCEPTED_EVENT_CHECKSUM_CHANGED")
        key = (str(event.security_id).split(":")[-1], str(event.record_date), str(event.ex_date))
        if key in indexed:
            raise ValueError("DUPLICATE_ACCEPTED_EVENT_KEY")
        indexed[key] = row
    return indexed


def dual_candidates(requirements, closed, cash, bonus):
    candidates = []
    for row in sorted(requirements, key=lambda item: item["document_id"]):
        if row["priority"] != "P1" or row["required_document_types"] != DUAL_TYPES:
            continue
        if len(row["affected_events"]) != 2:
            raise ValueError("DUAL_REQUIREMENT_FACT_COUNT_CHANGED")
        facts = {
            name: tuple(fact.split(":")[1:])
            for fact in row["affected_events"]
            for name in [fact.split(":")[0]]
        }
        if row["known_urls"] or set(facts) != {"BONUS", "CASH"} or facts["BONUS"] != facts["CASH"]:
            raise ValueError("DUAL_REQUIREMENT_IDENTITY_CHANGED")
        if row["document_id"] in closed:
            raise ValueError("DUAL_REQUIREMENT_ALREADY_CLOSED")
        key = facts["BONUS"]
        candidates.append((row, key, cash.get(key), bonus.get(key)))
    return candidates


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in (
        "requirements",
        "prior",
        "cash",
        "bonus",
        "master",
        "instruments",
        "sse",
        "szse",
        "staging",
        "output",
    ):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    requirements, prior, cash, bonus, instruments, sse, szse = (
        verified(getattr(args, name))
        for name in ("requirements", "prior", "cash", "bonus", "instruments", "sse", "szse")
    )
    master = json.loads(args.master.read_bytes())
    ordinary = {
        row["classification"]["security_id"]["value"]: row["classification"]["instrument_type"]
        for row in instruments["classifications"]
    }
    targets, _ = official_targets(master, ordinary, sse, szse)
    oracle_path = args.staging / "full-bonus-inventory-v1/source-oracle-v1.json"
    oracle = verified(oracle_path)
    if not any(
        item["path"] == str(oracle_path) and item["sha256"] == sha256_file(oracle_path)
        for item in bonus["inputs"]
    ):
        raise ValueError("BONUS_ORACLE_INPUT_CHANGED")
    oracle_by_key = {
        (row["symbol"], row["record_date"], row["ex_date"]): row for row in oracle["rows"]
    }
    if len(oracle_by_key) != len(oracle["rows"]):
        raise ValueError("DUPLICATE_BONUS_ORACLE_KEY")
    cash_events, bonus_events = event_index(cash["events"]), event_index(bonus["events"])
    closed_ids = {row["document_id"] for row in prior["closed"]}
    candidates = dual_candidates(requirements["documents"], closed_ids, cash_events, bonus_events)
    if candidates != dual_candidates(
        list(reversed(requirements["documents"])), closed_ids, cash_events, bonus_events
    ):
        raise ValueError("INPUT_ORDER_CHANGED")
    matched_cash = [cash_row for _, _, cash_row, bonus_row in candidates if cash_row and bonus_row]
    found, _ = retained_sources(args.staging, matched_cash)
    accepted, rejected = [], []
    for row, key, cash_row, bonus_row in candidates:
        reason = None
        if not cash_row or not bonus_row:
            reason = "ACCEPTED_CASH_OR_BONUS_LEG_MISSING"
        else:
            cash_event, bonus_event = cash_row["event"], bonus_row["event"]
            sid = cash_event["security_id"]["value"]
            source_key = cash_event["source_url"], cash_event["source_document_sha256"]
            target_key = sid, key[1], key[2]
            oracle_row = oracle_by_key.get(key)
            if (
                sid != bonus_event["security_id"]["value"]
                or cash_event["action_type"] != "CASH_DIVIDEND"
                or bonus_event["action_type"] != "BONUS_SHARE"
                or cash_event["announcement_date"] != bonus_event["announcement_date"]
                or ordinary.get(sid) != "COMMON_A_SHARE"
                or source_key != (bonus_event["source_url"], bonus_event["source_document_sha256"])
                or not source_key[0].startswith("https://static.cninfo.com.cn/finalpage/")
                or source_key not in found
                or target_key not in targets
                or not oracle_row
                or oracle_row["evidence_sha256"] != bonus_row["source_oracle_evidence_sha256"]
                or {Decimal(item["ratio"]) for item in oracle_row["evidence"]}
                != {Decimal(bonus_event["share_ratio"])}
            ):
                reason = "DUAL_SOURCE_OR_AUTHORITY_MISMATCH"
            else:
                manifest, source = found[source_key]
                source_root = manifest.parents[1]
                pdf = (source_root / source["source_path"]).resolve()
                cache = source_root / "batch-v1/text" / f"{source['source_sha256']}.json"
                if (
                    not pdf.is_relative_to(args.staging.resolve())
                    or sha256_file(pdf) != source["source_sha256"]
                    or not cache.is_file()
                ):
                    raise ValueError("DUAL_SOURCE_BYTES_CHANGED")
                extracted = json.loads(cache.read_bytes())
                if extracted["source_sha256"] != source["source_sha256"]:
                    raise ValueError("DUAL_TEXT_CACHE_CHANGED")
                pages = extracted["pages"]
                if not (
                    retained_final_title(source["title"])
                    or issuer_body_finality(source["title"], pages)
                ):
                    reason = "NO_FINAL_IMPLEMENTATION_EVIDENCE"
                else:
                    try:
                        amount = gross_cash(pages, key[0], targets[target_key], trusted_issuer=True)
                        ratio = retained_ratio(pages, key[0])
                        record_dates, ex_dates = notice_dates(pages)
                    except ValueError as exc:
                        reason = str(exc)
                    else:
                        date_classification = classify_dates(
                            {"record_date": key[1], "ex_date": key[2]},
                            record_dates,
                            ex_dates,
                        )
                        if (
                            amount != Decimal(cash_event["cash_per_share"])
                            or not exchange_amount_matches(amount, targets[target_key])
                            or ratio != Decimal(bonus_event["share_ratio"])
                            or date_classification is None
                            or not source["published_on"] <= key[1] < key[2]
                        ):
                            reason = "DUAL_ISSUER_TERMS_OR_DATES_DISAGREE"
                        else:
                            listing_audit = None
                            if sid == "CN-A:SSE:603023":
                                try:
                                    listing_audit = corroborate_603023_listing(args.staging, pages)
                                except ValueError as exc:
                                    reason = str(exc)
                            if reason:
                                rejected.append(
                                    {"document_id": row["document_id"], "reason": reason}
                                )
                                continue
                            closed = {
                                "document_id": row["document_id"],
                                "affected_events": row["affected_events"],
                                "classification": "SAME_OFFICIAL_ISSUER_PDF_CASH_AND_BONUS",
                                "security_id": sid,
                                "record_date": key[1],
                                "ex_date": key[2],
                                "official_source_url": source_key[0],
                                "official_pdf_sha256": source_key[1],
                                "text_cache_sha256": sha256_file(cache),
                                "source_manifest_sha256": sha256_file(manifest),
                                "cash_event_checksum": cash_row["event_checksum"],
                                "bonus_event_checksum": bonus_row["event_checksum"],
                                "cash_per_share": str(amount),
                                "bonus_ratio": str(ratio),
                                "issuer_date_classification": date_classification,
                                "issuer_notice_record_dates": record_dates,
                                "issuer_notice_ex_dates": ex_dates,
                                "exchange_cash_targets": sorted(
                                    str(value) for value in targets[target_key]
                                ),
                                "bonus_oracle_evidence_sha256": oracle_row["evidence_sha256"],
                            }
                            if listing_audit:
                                closed["retrospective_listing_audit"] = listing_audit
                            accepted.append(closed)
        if reason:
            rejected.append({"document_id": row["document_id"], "reason": reason})
    report = {
        "report_version": "P1_OFFICIAL_DUAL_DISTRIBUTION_SOURCE_CLOSURE_V7",
        "candidate_documents": len(candidates),
        "closed_documents": len(accepted),
        "closed_facts": sum(len(row["affected_events"]) for row in accepted),
        "rejected_counts": dict(sorted(Counter(row["reason"] for row in rejected).items())),
        "rejected": rejected,
        "closed": accepted,
        "input_sha256s": {
            name: sha256_file(getattr(args, name))
            for name in (
                "requirements",
                "prior",
                "cash",
                "bonus",
                "master",
                "instruments",
                "sse",
                "szse",
            )
        },
        "oracle_sha256": sha256_file(oracle_path),
        "parser_sha256": sha256_file(Path(__file__)),
        "cash_parser_sha256": sha256_file(
            Path(__file__).with_name("reconcile_distribution_cash.py")
        ),
        "bonus_parser_sha256": sha256_file(Path(__file__).with_name("retained_bonus_terms.py")),
        "date_parser_sha256": sha256_file(Path(__file__).with_name("link_distribution_notices.py")),
        "input_order_reproducibility": "PASS",
        "new_economic_events_created": 0,
    }
    report["manifest_sha256"] = canonical_sha256(report)
    write_immutable(args.output, canonical_json_bytes(report) + b"\n")
    print(
        json.dumps(
            {key: value for key, value in report.items() if key not in {"closed", "rejected"}}
        )
    )


if __name__ == "__main__":
    main()
