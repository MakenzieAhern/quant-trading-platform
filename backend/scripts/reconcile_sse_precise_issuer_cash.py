"""Replace rounded SSE table cash amounts with exact retained issuer notice terms."""

import argparse
import json
from decimal import Decimal
from pathlib import Path

from app.data.catalog.checksums import canonical_json_bytes, canonical_sha256, sha256_file
from app.data.catalog.freeze import write_immutable
from app.domain.markets.corporate_actions import CorporateAction, require_supported_corporate_action
from scripts.audit_p1_public_fact_requirements import verified
from scripts.link_distribution_notices import notice_dates
from scripts.reconcile_distribution_cash import gross_cash
from scripts.reconcile_sse_cash_table_substitutions import distribution_class


def reconcile(previous, corrected, p1, cash, source_root):
    accepted = {
        (row["event"]["security_id"]["value"], row["event"]["ex_date"]): row
        for row in corrected["events"]
    }
    p1_keys = {
        (row["event"]["security_id"]["value"], row["event"]["ex_date"]) for row in p1["events"]
    }
    by_cash = {
        (row["event"]["security_id"]["value"], row["event"]["ex_date"]): row
        for row in cash["events"]
    }
    replacements = []
    for row in previous["events"]:
        old = row["event"]
        key = old["security_id"]["value"], old["ex_date"]
        if key in accepted or key in p1_keys:
            continue
        outcome = next(
            item
            for item in corrected["outcomes"]
            if item["security_id"] == key[0] and item["ex_date"] == key[1]
        )
        if outcome["status"] != "ISSUER_NOTICE_TABLE_CASH_AMOUNT_CONFLICT":
            raise ValueError("SSE_PRECISE_CASH_CONFLICT_NOT_ESTABLISHED")
        if by_cash[key]["event_checksum"] != row["event_checksum"]:
            raise ValueError("SSE_PRECISE_CASH_BASELINE_CHANGED")
        notice = row["evidence"]["issuer_notice"]
        pdf = source_root / notice["source_path"]
        cache = source_root / "batch-v1/text" / f"{notice['source_sha256']}.json"
        if (
            not notice["url"].startswith("https://static.cninfo.com.cn/finalpage/")
            or notice["retrieval_status"] != "PASS"
            or sha256_file(pdf) != notice["source_sha256"]
        ):
            raise ValueError("SSE_PRECISE_CASH_OFFICIAL_SOURCE_CHANGED")
        extracted = json.loads(cache.read_bytes())
        if extracted["source_sha256"] != notice["source_sha256"]:
            raise ValueError("SSE_PRECISE_CASH_EXTRACTION_CHANGED")
        pages = extracted["pages"]
        if distribution_class(pages) != "NON_DIFFERENTIATED":
            raise ValueError("SSE_PRECISE_CASH_INSTRUMENT_AMBIGUOUS")
        record_dates, ex_dates = notice_dates(pages)
        if record_dates != [old["record_date"]] or ex_dates != [old["ex_date"]]:
            raise ValueError("SSE_PRECISE_CASH_EFFECTIVE_DATES_CONFLICT")
        amount = gross_cash(pages, notice["issuer"])
        if amount == Decimal(old["cash_per_share"]):
            raise ValueError("SSE_PRECISE_CASH_NO_AMOUNT_DIFFERENCE")
        terms = {
            "security_id": key[0],
            "record_date": old["record_date"],
            "ex_date": old["ex_date"],
            "cash_per_share": str(amount),
            "source_sha256": notice["source_sha256"],
        }
        action = CorporateAction.model_validate(
            {
                "security_id": old["security_id"],
                "action_type": "CASH_DIVIDEND",
                "announcement_date": notice["published_on"],
                "effective_date": old["ex_date"],
                "record_date": old["record_date"],
                "ex_date": old["ex_date"],
                "cash_per_share": str(amount),
                "source_document": notice["title"],
                "source_url": notice["url"],
                "source_document_sha256": notice["source_sha256"],
                "retrieved_at": notice["retrieved_at_utc"],
                "source_provider": "OFFICIAL_ISSUER_CNINFO_PRIMARY_IMPLEMENTATION",
                "source_version": "SSE_PRECISE_ISSUER_CASH_OVER_ROUNDED_TABLE_V1",
                "source_record_hash": canonical_sha256(terms),
                "completeness": "COMPLETE",
            }
        )
        require_supported_corporate_action(action)
        replacements.append(
            {
                "event": action.model_dump(mode="json"),
                "event_checksum": action.event_checksum,
                "supersedes_event_checksum": row["event_checksum"],
                "source_terms_sha256": canonical_sha256(terms),
                "source_text_cache_sha256": sha256_file(cache),
                "old_sse_table_amount": old["cash_per_share"],
                "official_issuer_exact_amount": str(amount),
            }
        )
    return sorted(replacements, key=lambda row: row["event_checksum"])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--previous-sse", type=Path, required=True)
    parser.add_argument("--corrected-sse", type=Path, required=True)
    parser.add_argument("--p1-primary", type=Path, required=True)
    parser.add_argument("--cash-ledger", type=Path, required=True)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    previous, corrected, p1, cash = (
        verified(path)
        for path in (args.previous_sse, args.corrected_sse, args.p1_primary, args.cash_ledger)
    )
    events = reconcile(previous, corrected, p1, cash, args.source_root)
    if events != reconcile(
        {**previous, "events": list(reversed(previous["events"]))},
        corrected,
        p1,
        {**cash, "events": list(reversed(cash["events"]))},
        args.source_root,
    ):
        raise ValueError("INPUT_ORDER_CHANGED")
    report = {
        "report_version": "SSE_PRECISE_OFFICIAL_ISSUER_CASH_REPLACEMENTS_V1",
        "parser_sha256": sha256_file(Path(__file__)),
        "input_sha256s": {
            name: sha256_file(path)
            for name, path in (
                ("previous_sse", args.previous_sse),
                ("corrected_sse", args.corrected_sse),
                ("p1_primary", args.p1_primary),
                ("cash_ledger", args.cash_ledger),
            )
        },
        "replacements": len(events),
        "events": events,
        "input_order_reproducibility": "PASS",
        "full_cash_census_acceptance": "NOT_YET_REAUDITED",
    }
    report["manifest_sha256"] = canonical_sha256(report)
    write_immutable(args.output, canonical_json_bytes(report) + b"\n")
    print(json.dumps({key: value for key, value in report.items() if key != "events"}))


if __name__ == "__main__":
    main()
