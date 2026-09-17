"""Audit one original designated-paper issuer notice against official SSE facts."""

import argparse
import hashlib
import json
import re
import unicodedata
from decimal import Decimal
from pathlib import Path

import pymupdf

from app.data.catalog.checksums import canonical_json_bytes, canonical_sha256, sha256_file
from app.data.catalog.freeze import write_immutable
from scripts.audit_p1_public_fact_requirements import verified
from scripts.link_distribution_notices import notice_dates
from scripts.reconcile_distribution_cash import gross_cash

DOCUMENT_ID = "OFFICIAL_DOCUMENT:df1ded9ee9019044db75001e50eac5619ee9ce5abf34106ea831d98f1ad0fb16"
EVENT_ID = "CASH:600337:2011-06-13:2011-06-14"
TITLE = "美克国际家具股份有限公司2010年度利润分配实施公告"
SOURCES = {
    "sse": (
        "600337-2011-06-08-p001.json",
        "https://query.sse.com.cn/security/stock/queryCompanyBulletinNew.do?",
    ),
    "issuer_designation": (
        "600337-2010-annual-report.pdf",
        "https://static.cninfo.com.cn/finalpage/2011-04-09/59242490.PDF",
    ),
    "issuer_notice": (
        "2011-06-08-stcn-D005.pdf",
        "https://epaper.stcn.com/paper/zqsb/page/1/2011-06-08/D005/1301307475377565.pdf",
    ),
}


def source(root, name):
    filename, url = SOURCES[name]
    path = root / filename
    meta_path = root / f"{filename}.meta.json"
    meta = json.loads(meta_path.read_bytes())
    if (
        not (meta["url"].startswith(url) if name == "sse" else meta["url"] == url)
        or meta.get("error")
        or meta["http_status"] != 200
        or sha256_file(path) != meta["sha256"]
    ):
        raise ValueError(f"SOURCE_RECEIPT_INVALID:{name}")
    return path, {
        "url": meta["url"],
        "sha256": meta["sha256"],
        "receipt_sha256": sha256_file(meta_path),
        "retrieved_at_utc": meta["retrieved_at_utc"],
    }


def issuer_block(page_text):
    text = re.sub(r"\s+", "", unicodedata.normalize("NFKC", page_text))
    headings = list(re.finditer(r"证券代码:\d{6}", text))
    matches = [index for index, heading in enumerate(headings) if heading[0] == "证券代码:600337"]
    if len(matches) != 1 or matches[0] + 1 >= len(headings):
        raise ValueError("ISSUER_PAGE_BOUNDARY_NOT_UNIQUE")
    index = matches[0]
    block = text[headings[index].start() : headings[index + 1].start()]
    if not all(
        marker in block
        for marker in (
            TITLE,
            "编号:临2011-022",
            "美克国际家具股份有限公司董事会",
            "2010年度不进行公积金转增股本",
        )
    ):
        raise ValueError("ISSUER_NOTICE_IDENTITY_OR_FINALITY_MISSING")
    return block


def audit(root, requirements, retained, cash):
    request = [row for row in requirements["documents"] if row["document_id"] == DOCUMENT_ID]
    rejected = [row for row in retained["rejected"] if row["document_id"] == DOCUMENT_ID]
    accepted = [
        row
        for row in cash["events"]
        if row["event"]["security_id"]["value"] == "CN-A:SSE:600337"
        and row["event"]["record_date"] == "2011-06-13"
        and row["event"]["ex_date"] == "2011-06-14"
    ]
    if (
        len(request) != 1
        or request[0]["affected_events"] != [EVENT_ID]
        or len(rejected) != 1
        or len(accepted) != 1
        or accepted[0]["event"]["cash_per_share"] != "0.05"
    ):
        raise ValueError("P1_REQUIREMENT_OR_ACCEPTED_EVENT_CHANGED")

    sse_path, sse_receipt = source(root, "sse")
    annual_path, annual_receipt = source(root, "issuer_designation")
    notice_path, notice_receipt = source(root, "issuer_notice")
    sse = json.loads(sse_path.read_bytes())
    rows = [
        row
        for group in sse["pageHelp"]["data"]
        for row in group
        if row["SECURITY_CODE"] == "600337" and row["SSEDATE"] == "2011-06-08"
    ]
    if len(rows) != 1 or rows[0]["TITLE"] != "美克股份2010年度利润分配实施公告":
        raise ValueError("SSE_ISSUER_NOTICE_INDEX_NOT_UNIQUE")
    with pymupdf.open(annual_path) as annual:
        designation = re.sub(r"\s+", "", unicodedata.normalize("NFKC", annual[3].get_text()))
    if not all(
        token in designation
        for token in ("美克国际家具股份有限公司", "公司选定的信息披露报纸名称", "《证券时报》")
    ):
        raise ValueError("ISSUER_DESIGNATED_DISCLOSURE_MEDIUM_NOT_EVIDENCED")
    with pymupdf.open(notice_path) as notice:
        if len(notice) != 1:
            raise ValueError("NEWSPAPER_PAGE_COUNT_CHANGED")
        block = issuer_block(notice[0].get_text())
    amount = gross_cash([block], "600337", {Decimal("0.05")}, trusted_issuer=True)
    records, ex_dates = notice_dates([block])
    if (
        amount != Decimal("0.05")
        or records != ["2011-06-13"]
        or ex_dates != ["2011-06-14"]
        or "现金红利发放日:2011年6月20日" not in block
        or "股东美克投资集团有限公司、香港博伊西家具有限公司的现金红利由公司直接发放" not in block
        or "其他股东的现金红利委托中国证券登记结算公司上海分公司" not in block
    ):
        raise ValueError("ISSUER_FINAL_CASH_OR_HOLDER_TERMS_NOT_UNIQUE")
    return {
        "report_version": "P1_ORIGINAL_DESIGNATED_DISCLOSURE_CASH_V2",
        "classification": "OFFICIAL_ISSUER_ORIGINAL_DESIGNATED_PAPER_SSE_INDEX_CORROBORATED",
        "closed": [
            {
                "document_id": DOCUMENT_ID,
                "affected_events": [EVENT_ID],
                "accepted_event_checksum": accepted[0]["event_checksum"],
                "gross_cash_per_share": str(amount),
                "record_date": records[0],
                "ex_date": ex_dates[0],
                "payment_date": "2011-06-20",
                "holder_terms": "TWO_NAMED_DIRECT_PAYEES_OTHER_REGISTERED_HOLDERS_CSDC_SSE",
                "issuer_notice_block_sha256": hashlib.sha256(block.encode()).hexdigest(),
            }
        ],
        "sources": {
            "sse_publication_index": {
                **sse_receipt,
                "announced_pdf_url": "https://static.sse.com.cn" + rows[0]["URL"],
            },
            "issuer_annual_designation": annual_receipt,
            "original_issuer_notice": notice_receipt,
        },
        "sse_pdf_bytes_verified": False,
        "new_economic_events_created": 0,
        "input_order_reproducibility": "PASS",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("root", "requirements", "retained", "cash", "output"):
        parser.add_argument(f"--{name}", type=Path, required=True)
    args = parser.parse_args()
    inputs = {name: verified(getattr(args, name)) for name in ("requirements", "retained", "cash")}
    body = audit(args.root, inputs["requirements"], inputs["retained"], inputs["cash"])
    reversed_body = audit(
        args.root,
        {
            **inputs["requirements"],
            "documents": list(reversed(inputs["requirements"]["documents"])),
        },
        {**inputs["retained"], "rejected": list(reversed(inputs["retained"]["rejected"]))},
        {**inputs["cash"], "events": list(reversed(inputs["cash"]["events"]))},
    )
    if body != reversed_body:
        raise ValueError("INPUT_ORDER_CHANGED")
    body["input_sha256s"] = {
        name: sha256_file(getattr(args, name)) for name in ("requirements", "retained", "cash")
    }
    body["parser_sha256"] = sha256_file(Path(__file__))
    body["cash_parser_sha256"] = sha256_file(
        Path(__file__).with_name("reconcile_distribution_cash.py")
    )
    body["date_parser_sha256"] = sha256_file(
        Path(__file__).with_name("link_distribution_notices.py")
    )
    body["manifest_sha256"] = canonical_sha256(body)
    write_immutable(args.output, canonical_json_bytes(body) + b"\n")
    print(json.dumps({key: value for key, value in body.items() if key != "closed"}))


if __name__ == "__main__":
    main()
