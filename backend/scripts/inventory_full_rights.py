"""Replay preserved all-company rights pages and explicit official claim review.

This is a coverage oracle, not a full-history dataset or automatic authority promotion.
"""

import argparse
import json
from collections import Counter
from decimal import Decimal
from pathlib import Path

from app.data.catalog.checksums import canonical_json_bytes, canonical_sha256, sha256_file
from app.data.catalog.freeze import write_immutable
from app.domain.markets import CorporateAction, SecurityId


def normalize(row, source, review=None):
    code, exchange = row["SECUCODE"].split(".")
    if exchange not in {"SH", "SZ"} or not code.isdigit() or len(code) != 6:
        raise ValueError("unsupported rights security identity")
    sid = f"CN-A:{'SSE' if exchange == 'SH' else 'SZSE'}:{code}"
    fields = {
        "announcement_date": "FIRST_NOTICE_DATE",
        "record_date": "EQUITY_RECORD_DATE",
        "ex_date": "EX_DIVIDEND_DATE",
        "subscription_start_date": "PAY_START_DATE",
        "subscription_end_date": "PAY_END_DATE",
        "listing_date": "LISTING_DATE",
    }
    values = {key: (row[name][:10] if row.get(name) else None) for key, name in fields.items()}
    values.update(
        security_id=SecurityId(value=sid),
        action_type="RIGHTS_RELATED_EVENT",
        effective_date=values["ex_date"],
        subscription_deadline=None,  # A vendor window is not verified payment-deadline evidence.
        subscription_price=str(row["ISSUE_PRICE"]) if row.get("ISSUE_PRICE") is not None else None,
        share_ratio=str(Decimal(str(row["PLACING_RATIO"])) / 10)
        if row.get("PLACING_RATIO") is not None
        else None,
        eligible_share_basis=None,  # TOTAL_SHARES_BEFORE can include H shares; never substitute.
        source_provider="Eastmoney-coverage-oracle",
        source_version="RPT_IPO_ALLOTMENT",
        source_record_hash=canonical_sha256(row),
        source_document="RPT_IPO_ALLOTMENT raw row",
        source_url=source["url"],
        source_document_sha256=source["sha256"],
        retrieved_at=source["retrieved_at_utc"],
        completeness="PARTIAL",
    )
    if review:
        for key, expected in review["checks"].items():
            field = "share_ratio" if key == "ratio" else key
            actual = (
                (row.get("LISTING_DATE") or "")[:10]
                if key == "new_share_listing_date"
                else values[field]
            )
            equal = (
                Decimal(actual) == Decimal(expected)
                if key in {"ratio", "subscription_price"}
                else actual == expected
            )
            if not equal:
                raise ValueError(f"OFFICIAL_RIGHTS_TERM_MISMATCH:{sid}:{key}")
        values.update(review["verified_event_fields"])
    source_issues = []
    if (
        values["announcement_date"]
        and values["ex_date"]
        and values["announcement_date"] > values["ex_date"]
    ):
        source_issues.append("SOURCE_ANNOUNCEMENT_AFTER_EX_DATE")
        values["announcement_date"] = None
        values["completeness"] = "PARTIAL"
    action = CorporateAction.model_validate(values)
    return dict(
        event_id=f"{sid}:{values['record_date']}",
        event=action.model_dump(mode="json"),
        event_checksum=action.event_checksum,
        source_row_sha256=canonical_sha256(row),
        source_total_capital_not_eligible_basis=row.get("TOTAL_SHARES_BEFORE"),
        source_reported_listing_date=row.get("LISTING_DATE"),
        source_reported_announcement_date=row.get("FIRST_NOTICE_DATE"),
        source_issues=source_issues,
        classification="SUPPORTED_STANDARD_EVENT" if not action.rights_issues() else "UNRESOLVED",
        safety_classification=None
        if not action.rights_issues()
        else "RIGHTS_EVENT_UNSUPPORTED_VARIANT",
        issues=action.rights_issues(),
        official_review=review,
        point_in_time_admission="NOT_ADMITTED_FULL_AUTHORITY_PENDING",
    )


def inventory(pages, review):
    rows = []
    for payload, source in pages:
        if not payload.get("success"):
            raise ValueError("provider response failed")
        for row in payload["result"]["data"]:
            dates = [
                str(row[k])[:10]
                for k in (
                    "EQUITY_RECORD_DATE",
                    "PAY_START_DATE",
                    "PAY_END_DATE",
                    "EX_DIVIDEND_DATE",
                    "LISTING_DATE",
                )
                if row.get(k)
            ]
            # Include lifecycle overlap, including prior-year records with in-period listing.
            if not dates or (min(dates) <= "2025-12-31" and max(dates) >= "2010-01-01"):
                key = row["SECUCODE"] + ":" + (row.get("EQUITY_RECORD_DATE") or "UNKNOWN")[:10]
                rows.append(normalize(row, source, review.get(key)))
    counts = {page[0]["result"]["count"] for page in pages}
    expected_pages = {page[0]["result"]["pages"] for page in pages}
    all_ids = [row["FINANCE_CODE"] for page, _ in pages for row in page["result"]["data"]]
    if (
        len(counts) != 1
        or counts != {len(all_ids)}
        or len(all_ids) != len(set(all_ids))
        or expected_pages != {len(pages)}
    ):
        raise ValueError("incomplete or inconsistent provider pagination")
    rows.sort(key=lambda row: row["event_id"])
    if len({row["event_id"] for row in rows}) != len(rows):
        raise ValueError("duplicate economic rights event requires reconciliation")
    statuses = Counter(row["classification"] for row in rows)
    return dict(
        requested_coverage=["2010-01-01", "2025-12-31"],
        inventory_scope="ALL_IDENTIFIED_PROVIDER_EVENTS_NOT_COMPLETE_EXCHANGE_CENSUS",
        source_pagination="PASS",
        rights_events_total=len(rows),
        securities_with_rights_events=len({row["event"]["security_id"]["value"] for row in rows}),
        events_with_complete_terms=statuses["SUPPORTED_STANDARD_EVENT"],
        events_with_incomplete_terms=statuses["UNRESOLVED"],
        supported_standard_events=statuses["SUPPORTED_STANDARD_EVENT"],
        unsupported_variants=sum(
            row["event"]["rights_variant"] not in (None, "ORDINARY_NON_TRADABLE") for row in rows
        ),
        unresolved_events=statuses["UNRESOLVED"],
        rows=rows,
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sources", type=Path, required=True)
    parser.add_argument("--review", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    pages = []
    for name in ("eastmoney-allotments.json", "eastmoney-allotments-page-2.json"):
        path = args.sources / name
        meta = json.loads(path.with_suffix(".json.meta.json").read_bytes())
        if sha256_file(path) != meta["sha256"]:
            raise ValueError("source checksum mismatch")
        pages.append((json.loads(path.read_bytes(), parse_float=str), meta))
    review = json.loads(args.review.read_bytes())
    for claim in review["sources"]:
        if sha256_file(args.sources / claim["path"]) != claim["sha256"]:
            raise ValueError("reviewed official evidence checksum mismatch")
    result = inventory(pages, review["events"])
    reversed_pages = [
        (
            {**page, "result": {**page["result"], "data": list(reversed(page["result"]["data"]))}},
            meta,
        )
        for page, meta in reversed(pages)
    ]
    if result != inventory(reversed_pages, review["events"]):
        raise ValueError("input order changed inventory")
    result.update(
        parser_version="RIGHTS_INVENTORY_V1",
        parser_sha256=sha256_file(Path(__file__)),
        event_model_sha256=sha256_file(
            Path(__file__).parents[1] / "app/domain/markets/corporate_actions.py"
        ),
        review_sha256=sha256_file(args.review),
        source_pages=[m for _, m in pages],
        input_order_reproducibility="PASS",
        acquisition="REUSED_SNAPSHOTS_NO_NETWORK",
    )
    result["manifest_sha256"] = canonical_sha256(result)
    write_immutable(args.output, canonical_json_bytes(result) + b"\n")
    print(
        json.dumps({k: v for k, v in result.items() if k not in {"rows", "source_pages"}}, indent=2)
    )


if __name__ == "__main__":
    main()
