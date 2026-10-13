"""Verify a narrow official aggregate-text correction, never financial admission."""

from __future__ import annotations

import json
import re
from datetime import UTC, date, datetime, time, timedelta
from decimal import Decimal, InvalidOperation
from io import BytesIO
from pathlib import Path
from typing import Any, Literal
from zoneinfo import ZoneInfo

from pydantic import BaseModel, ConfigDict, Field
from pypdf import PdfReader

from app.data.catalog.checksums import canonical_json_bytes, verified_file_bytes
from app.domain.markets.identifiers import SecurityId
from scripts.audit_p1_cash_corrections import normalized, unchanged_except_cash_aggregate
from scripts.full_dataset_build_inputs import FilePin
from scripts.link_distribution_notices import notice_dates
from scripts.reconcile_distribution_cash import issuer_code_matches
from scripts.retained_bonus_terms import retained_ratio

EXTENSION = "cash_aggregate_corrections"
CNINFO_INDEX = "https://www.cninfo.com.cn/new/hisAnnouncement/query"
CNINFO_PDF = re.compile(
    r"https://static\.cninfo\.com\.cn/finalpage/(\d{4}-\d{2}-\d{2})/([0-9]+)\.PDF"
)


class CorrectionItem(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    security_id: str
    record_date: str
    ex_date: str
    original_pdf: FilePin
    correction_pdf: FilePin
    correction_receipt: FilePin
    official_index: FilePin
    official_index_receipt: FilePin


class CorrectionInventory(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    version: Literal["CASH_AGGREGATE_CORRECTIONS_V1"]
    parent_inventory: FilePin
    items: list[CorrectionItem] = Field(min_length=1)


def require(condition: bool, reason: str) -> None:
    if not condition:
        raise ValueError(f"CASH_CORRECTION_{reason}")


def inventory_content(value: dict[str, Any]) -> dict[str, Any]:
    rows = value.get("records")
    if not isinstance(rows, list) or not rows or any(not isinstance(row, dict) for row in rows):
        raise ValueError("CASH_CORRECTION_INVALID_PARENT_RECORDS")
    return {**value, "records": sorted(rows, key=canonical_json_bytes)}


def utc_receipt(value: Any) -> datetime:
    require(isinstance(value, str), "INVALID_RETRIEVAL_TIME")
    parsed = datetime.fromisoformat(value)
    require(parsed.utcoffset() == timedelta(0), "RETRIEVAL_NOT_UTC")
    return parsed.astimezone(UTC)


def publication(value: Any) -> datetime:
    require(
        type(value) is int and 0 < value < 253402300800000,
        "INVALID_PUBLICATION_MILLISECONDS",
    )
    return datetime(1970, 1, 1, tzinfo=UTC) + timedelta(milliseconds=value)


def notice_number(page: str, symbol: str) -> str:
    require(issuer_code_matches(page, symbol), "ISSUER_HEADER_MISMATCH")
    header = re.search(r"公告编号:?([0-9]{4}-[0-9]+)", normalized(page)[:200])
    require(header is not None, "NOTICE_NUMBER_MISSING")
    if header is None:  # Narrow the type without assertions, including under python -O.
        raise ValueError("CASH_CORRECTION_NOTICE_NUMBER_MISSING")
    return header[1]


def correction_frame(original: str, correction: str, terms: dict[str, Any]) -> dict[str, str]:
    """Only the reviewed full-page layout; extra prose may change economic terms."""
    header = re.match(
        r"证券代码:(?P<symbol>[0-9]{6})证券简称:(?P<short>[\u4e00-\u9fffA-Za-z*]{1,20})"
        r"公告编号:(?P<notice>[0-9]{4}-[0-9]+)"
        r"(?P<issuer>[\u4e00-\u9fff]{2,80}股份有限公司)"
        r"(?P<title>[0-9]{4}年度权益分派实施公告)",
        normalized(original),
    )
    require(header is not None, "UNSUPPORTED_ORIGINAL_HEADER")
    if header is None:
        raise ValueError("CASH_CORRECTION_UNSUPPORTED_ORIGINAL_HEADER")
    values = header.groupdict()
    issuer = re.escape(values["issuer"])
    dated = r"[0-9]{4}年[0-9]{1,2}月[0-9]{1,2}日"
    prefix = (
        re.escape(f"证券代码:{values['symbol']}证券简称:{values['short']}公告编号:")
        + r"(?P<notice>[0-9]{4}-[0-9]+)"
        + issuer
        + r"更正公告本公司及董事会全体成员保证信息披露的内容真实、准确、完整,"
        r"没有虚假记载、误导性陈述或重大遗漏。"
        + issuer
        + r"于(?P<cited_date>"
        + dated
        + r")公告的文件,公告编号:?"
        + re.escape(values["notice"])
        + "《"
        + issuer
        + re.escape(values["title"])
        + r"》,公告第(?:一|1)页,二、利润分配及转增股本方案的共计派发股利金额"
        r"由于笔误出现错误。原文:"
    )
    tail = (
        r"本公司对上述更正给投资者带来的不便深表歉意,并将认真汲取教训,"
        r"切实履行好信息披露义务,不断提高信息披露质量。特此公告。"
        + issuer
        + r"董事会(?P<signed_date>"
        + dated
        + r")"
    )
    frame = re.fullmatch(
        prefix
        + re.escape(terms["original_paragraph"])
        + "现更正为:"
        + re.escape(terms["corrected_paragraph"])
        + tail,
        normalized(correction),
    )
    require(frame is not None, "UNSUPPORTED_FULL_DOCUMENT")
    if frame is None:
        raise ValueError("CASH_CORRECTION_UNSUPPORTED_FULL_DOCUMENT")
    return {**values, **frame.groupdict()}


def load_cash_corrections(
    gaps: dict[str, Any], inventory_path: Path
) -> tuple[list[dict[str, Any]], dict[Path, str]]:
    if EXTENSION not in gaps:
        return [], {}
    extension = CorrectionInventory.model_validate(gaps[EXTENSION])
    root = inventory_path.resolve(strict=True).parent
    pins: dict[Path, str] = {}
    consumed: dict[Path, bytes] = {}
    resolved: dict[Path, Path] = {}

    def read(pin: FilePin) -> bytes:
        declared_path = root / pin.path
        if declared_path not in resolved:
            resolved[declared_path] = declared_path.resolve(strict=True)
        path = resolved[declared_path]
        require(path not in pins or pins[path] == pin.sha256, "CONFLICTING_FILE_PIN")
        if path not in consumed:
            pins[path] = pin.sha256
            consumed[path] = verified_file_bytes(path, pin.sha256)
        return consumed[path]

    def document(pin: FilePin) -> dict[str, Any]:
        value = json.loads(read(pin))
        if not isinstance(value, dict):
            raise ValueError("CASH_CORRECTION_JSON_OBJECT_REQUIRED")
        return value

    parent = document(extension.parent_inventory)
    require(EXTENSION not in parent, "NESTED_PARENT")
    require(
        canonical_json_bytes(inventory_content(parent))
        == canonical_json_bytes(
            inventory_content({key: value for key, value in gaps.items() if key != EXTENSION})
        ),
        "PARENT_INVENTORY_CHANGED",
    )
    proofs = []
    identities = set()
    for item in extension.items:
        sid = str(SecurityId(value=item.security_id))
        _, exchange, symbol = sid.split(":")
        require(exchange in {"SSE", "SZSE"}, "UNSUPPORTED_EXCHANGE")
        record_day, ex_day = date.fromisoformat(item.record_date), date.fromisoformat(item.ex_date)
        require(
            record_day.isoformat() == item.record_date
            and ex_day.isoformat() == item.ex_date
            and record_day <= ex_day,
            "INVALID_EVENT_DATES",
        )
        identity = sid, item.record_date, item.ex_date
        require(identity not in identities, "DUPLICATE_EVENT")
        identities.add(identity)
        matching = [
            row
            for row in parent["records"]
            if (row.get("security_id"), row.get("record_date"), row.get("ex_date")) == identity
        ]
        require(len(matching) == 1, "PARENT_EVENT_NOT_UNIQUE")
        gap = matching[0]
        require(gap.get("source_sha256") == item.original_pdf.sha256, "ORIGINAL_SOURCE_PIN")
        original_url = gap.get("source_url")
        require(isinstance(original_url, str), "ORIGINAL_URL")
        original_address = CNINFO_PDF.fullmatch(original_url)
        require(original_address is not None, "ORIGINAL_URL")

        original_pages = [
            page.extract_text() or "" for page in PdfReader(BytesIO(read(item.original_pdf))).pages
        ]
        correction_pages = [
            page.extract_text() or ""
            for page in PdfReader(BytesIO(read(item.correction_pdf))).pages
        ]
        require(bool(original_pages) and len(correction_pages) == 1, "UNSUPPORTED_PAGE_LAYOUT")
        old_notice = notice_number(original_pages[0], symbol)
        new_notice = notice_number(correction_pages[0], symbol)
        introduction = normalized(correction_pages[0]).split("原文:", 1)[0]
        require(
            old_notice != new_notice
            and "更正公告" in introduction
            and re.search(r"公告编号:?" + re.escape(old_notice) + r"(?![0-9])", introduction)
            is not None
            and re.search(r"公告第(?:一|1)页", introduction) is not None
            and "笔误" in introduction,
            "ORIGINAL_NOTICE_REFERENCE",
        )
        terms = unchanged_except_cash_aggregate(correction_pages)
        require(terms is not None, "NOT_AGGREGATE_ONLY")
        if terms is None:
            raise ValueError("CASH_CORRECTION_NOT_AGGREGATE_ONLY")
        require(
            normalized(original_pages[0]).count(str(terms["original_paragraph"])) == 1,
            "ORIGINAL_PARAGRAPH_NOT_ON_FIRST_PAGE",
        )
        frame = correction_frame(original_pages[0], correction_pages[0], terms)
        require(
            notice_dates(original_pages) == ([item.record_date], [item.ex_date]),
            "ORIGINAL_EVENT_DATES",
        )
        for declared, parsed in (
            ("declared_shares", "base_shares"),
            ("declared_gross_cash_per_share", "cash_per_share"),
            ("declared_total", "original_aggregate"),
            ("derived_exact_total", "corrected_aggregate"),
        ):
            try:
                require(isinstance(gap[declared], str), "DECLARED_TERMS_MUST_BE_STRINGS")
                amount = Decimal(gap[declared])
                agrees = amount.is_finite() and amount == Decimal(str(terms[parsed]))
            except (KeyError, TypeError, InvalidOperation):
                agrees = False
            require(agrees, "DECLARED_TERMS_MISMATCH")

        receipt = document(item.correction_receipt)
        index = document(item.official_index)
        index_receipt = document(item.official_index_receipt)
        correction_url = receipt.get("url")
        if not isinstance(correction_url, str):
            raise ValueError("CASH_CORRECTION_CORRECTION_URL")
        correction_address = CNINFO_PDF.fullmatch(correction_url)
        require(correction_address is not None, "CORRECTION_URL")
        require(
            receipt.get("http_status") == 200
            and receipt.get("sha256") == item.correction_pdf.sha256
            and index_receipt.get("http_status") == 200
            and index_receipt.get("sha256") == item.official_index.sha256
            and index_receipt.get("url") == CNINFO_INDEX,
            "RECEIPT_MISMATCH",
        )
        rows = index.get("announcements")
        if not isinstance(rows, list) or any(not isinstance(row, dict) for row in rows):
            raise ValueError("CASH_CORRECTION_INDEX_ROWS")
        require(
            all(
                isinstance(row.get("announcementId"), str)
                and re.fullmatch(r"[0-9]+", row["announcementId"])
                for row in rows
            ),
            "INVALID_ANNOUNCEMENT_ID",
        )
        require(
            len({row.get("announcementId") for row in rows}) == len(rows),
            "DUPLICATE_ANNOUNCEMENT",
        )
        selected = []
        for address, url in (
            (original_address, original_url),
            (correction_address, correction_url),
        ):
            if address is None:
                raise ValueError("CASH_CORRECTION_DOCUMENT_URL")
            matches = [row for row in rows if str(row.get("announcementId")) == address[2]]
            require(len(matches) == 1, "OFFICIAL_ANNOUNCEMENT_MISSING")
            row = matches[0]
            require(
                row.get("secCode") == symbol
                and row.get("adjunctType") == "PDF"
                and "https://static.cninfo.com.cn/" + str(row.get("adjunctUrl")) == url,
                "OFFICIAL_DOCUMENT_IDENTITY",
            )
            selected.append(row)
        old_row, new_row = selected
        org = old_row.get("orgId")
        params = index_receipt.get("params")
        require(
            isinstance(org, str)
            and bool(re.fullmatch(r"[0-9]+", org))
            and new_row.get("orgId") == org
            and isinstance(params, dict)
            and params.get("stock") == f"{symbol},{org}"
            and params.get("column") == exchange.lower()
            and old_row.get("announcementTitle") == frame["title"]
            and new_row.get("announcementTitle") == "更正公告",
            "OFFICIAL_ISSUER_QUERY",
        )
        old_published, published = (publication(row.get("announcementTime")) for row in selected)
        retrieved = utc_receipt(receipt.get("retrieved_at_utc"))
        index_retrieved = utc_receipt(index_receipt.get("retrieved_at_utc"))
        record_start = datetime.combine(record_day, time(), ZoneInfo("Asia/Shanghai"))
        require(
            old_published <= published < record_start
            and published <= retrieved <= datetime.now(UTC)
            and published <= index_retrieved <= datetime.now(UTC),
            "PUBLICATION_OR_RETRIEVAL_ORDER",
        )
        if original_address is None or correction_address is None:
            raise ValueError("CASH_CORRECTION_DOCUMENT_URL")
        local_day = published.astimezone(ZoneInfo("Asia/Shanghai")).date()
        original_day = old_published.astimezone(ZoneInfo("Asia/Shanghai")).date()
        cited_day = date(*map(int, re.findall(r"[0-9]+", frame["cited_date"])))
        require(
            correction_address[1] == local_day.isoformat()
            and original_address[1] == original_day.isoformat()
            and frame["signed_date"] == f"{local_day.year}年{local_day.month}月{local_day.day}日"
            and cited_day <= original_day,
            "CORRECTION_SIGNED_DATE",
        )
        proofs.append(
            {
                "security_id": sid,
                "record_date": item.record_date,
                "ex_date": item.ex_date,
                "source_sha256": item.original_pdf.sha256,
                "source_url": original_url,
                **terms,
                "bonus_share_ratio": str(retained_ratio(original_pages, symbol)),
                "correction_url": correction_url,
                "correction_sha256": item.correction_pdf.sha256,
                "published_at": published.isoformat(),
                "original_published_at": old_published.isoformat(),
                "retrieved_at_utc": retrieved.isoformat(),
                "official_org_id": org,
                "original_notice_number": old_notice,
                "correction_notice_number": new_notice,
            }
        )
    return sorted(
        proofs, key=lambda row: (row["security_id"], row["record_date"], row["ex_date"])
    ), pins
