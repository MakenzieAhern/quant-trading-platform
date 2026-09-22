"""Close the 301262 cash fact using the issuer notice and official SZSE factbook."""

import argparse
import json
import re
import unicodedata
from pathlib import Path

import pymupdf

from app.data.catalog.checksums import canonical_json_bytes, canonical_sha256, sha256_file
from app.data.catalog.freeze import write_immutable
from scripts.audit_p1_public_fact_requirements import verified

EVENT = "CNINFO:1218122069"
DOCUMENT_ID = "OFFICIAL_DOCUMENT:5fac202af7a8c2c69f0fe48a212c720bbf0569a0884f49021d2c7853ec5cd18d"
NOTICE_URL = "https://static.cninfo.com.cn/finalpage/2023-10-24/1218122069.PDF"
NOTICE_SHA = "af26edcd6277bc7212d9d43e9208650e119c33be27698f86a9457647b523d4c9"
FACTBOOK_FILE = "szse-yearbook-verified-2023.pdf"
FACTBOOK_URL = "https://docs.static.szse.cn/www/market/periodical/year/W020240814360443176703.pdf"
FACTBOOK_SHA = "954a719859b3767ffa3ed4d1ca3b50803549bcaca6366925a194d27f12be0bb4"


def compact(value: str) -> str:
    return re.sub(r"\s+", "", unicodedata.normalize("NFKC", value))


def close(requirements, queue, cash_sources, factbook_sources, notice_text, factbook_text):
    requirement = [row for row in requirements["documents"] if row["document_id"] == DOCUMENT_ID]
    queued = [row for row in queue if row["document_id"] == DOCUMENT_ID]
    notice = [row for row in cash_sources["documents"] if row.get("url") == NOTICE_URL]
    factbook = [
        row
        for row in factbook_sources["snapshots"]
        if row.get("raw_snapshot_filename") == FACTBOOK_FILE
    ]
    if (
        len(requirement) != 1
        or requirement[0]["priority"] != "P1"
        or requirement[0]["affected_events"] != [EVENT]
        or len(queued) != 1
        or queued[0]["affected_events"] != [EVENT]
    ):
        raise ValueError("P1_301262_REQUIREMENT_CHANGED")
    if (
        len(notice) != 1
        or notice[0]["source_sha256"] != NOTICE_SHA
        or notice[0]["retrieval_status"] != "PASS"
        or notice[0]["published_on"] != "2023-10-24"
    ):
        raise ValueError("P1_301262_NOTICE_RECEIPT_CHANGED")
    if (
        len(factbook) != 1
        or factbook[0]["sha256"] != FACTBOOK_SHA
        or factbook[0]["source_url"] != FACTBOOK_URL
        or factbook[0]["http_status"] != 200
    ):
        raise ValueError("P1_301262_FACTBOOK_RECEIPT_CHANGED")
    notice_text, factbook_text = compact(notice_text), compact(factbook_text)
    if not all(
        term in notice_text
        for term in (
            "证券代码:301262",
            "每10股派发现金红利8.500000元",
            "本次权益分派股权登记日为:2023年10月30日",
            "除权除息日为:2023年10年31日",
            "现金红利将于2023年10月31日",
        )
    ):
        raise ValueError("P1_301262_NOTICE_TERMS_CHANGED")
    if "301262海看股份0354450000.0010/31/202310派8.5元(含税)" not in factbook_text:
        raise ValueError("P1_301262_FACTBOOK_TERMS_CHANGED")
    row = {
        "document_id": DOCUMENT_ID,
        "affected_events": [EVENT],
        "classification": "ISSUER_DATE_TYPO_REPAIRED_BY_INTERNAL_PAYMENT_AND_SZSE_FACTBOOK",
        "security_id": "CN-A:SZSE:301262",
        "announcement_date": "2023-10-24",
        "record_date": "2023-10-30",
        "ex_date": "2023-10-31",
        "cash_per_share": "0.85",
        "accounting_effective_date": "2023-10-31",
        "point_in_time_use": "ACCOUNTING_ONLY_RETROSPECTIVE_SOURCE_NOT_SIGNAL_INPUT",
        "issuer_notice": {
            "url": NOTICE_URL,
            "sha256": NOTICE_SHA,
            "retrieved_at_utc": notice[0]["retrieved_at_utc"],
            "printed_malformed_ex_date": "2023-10-31_WITH_YEAR_MONTH_UNIT_TYPO",
            "internally_confirmed_cash_payment_date": "2023-10-31",
        },
        "official_exchange_factbook": {
            "url": FACTBOOK_URL,
            "sha256": FACTBOOK_SHA,
            "retrieved_at_utc": factbook[0]["retrieved_at"],
            "fact_year": 2023,
        },
    }
    row["fact_checksum"] = canonical_sha256(row)
    return {
        "closed": [row],
        "closed_facts": 1,
        "new_economic_events_created": 0,
        "future_source_used_as_strategy_signal": False,
        "input_order_reproducibility": "PASS",
        "full_census_certified": False,
        "full_dataset_created": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--requirements", required=True, type=Path)
    parser.add_argument("--cash-queue", required=True, type=Path)
    parser.add_argument("--cash-source-manifest", required=True, type=Path)
    parser.add_argument("--cash-source-root", required=True, type=Path)
    parser.add_argument("--factbook-manifest", required=True, type=Path)
    parser.add_argument("--factbook", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    requirements = verified(args.requirements)
    queue = json.loads(args.cash_queue.read_bytes())
    cash_sources = verified(args.cash_source_manifest)
    factbook_sources = json.loads(args.factbook_manifest.read_bytes())
    notice = next(row for row in cash_sources["documents"] if row.get("url") == NOTICE_URL)
    notice_path = (args.cash_source_root / notice["source_path"]).resolve()
    if (
        not notice_path.is_relative_to(args.cash_source_root.resolve())
        or sha256_file(notice_path) != NOTICE_SHA
        or sha256_file(args.factbook) != FACTBOOK_SHA
    ):
        raise ValueError("P1_301262_SOURCE_BYTES_CHANGED")
    with pymupdf.open(notice_path) as document:
        notice_text = "".join(page.get_text() for page in document)
    with pymupdf.open(args.factbook) as document:
        factbook_text = document[1058].get_text()
    report = close(
        requirements,
        queue,
        cash_sources,
        factbook_sources,
        notice_text,
        factbook_text,
    )
    reversed_report = close(
        {**requirements, "documents": list(reversed(requirements["documents"]))},
        list(reversed(queue)),
        {**cash_sources, "documents": list(reversed(cash_sources["documents"]))},
        {**factbook_sources, "snapshots": list(reversed(factbook_sources["snapshots"]))},
        notice_text,
        factbook_text,
    )
    if report != reversed_report:
        raise ValueError("INPUT_ORDER_CHANGED")
    report.update(
        report_version="P1_301262_OFFICIAL_CASH_FACT_CLOSURE_V1",
        parser_sha256=sha256_file(Path(__file__)),
        input_sha256s={
            "requirements": sha256_file(args.requirements),
            "cash_queue": sha256_file(args.cash_queue),
            "cash_source_manifest": sha256_file(args.cash_source_manifest),
            "factbook_manifest": sha256_file(args.factbook_manifest),
        },
    )
    report["manifest_sha256"] = canonical_sha256(report)
    write_immutable(args.output, canonical_json_bytes(report) + b"\n")
    print(json.dumps({key: value for key, value in report.items() if key != "closed"}))


if __name__ == "__main__":
    main()
