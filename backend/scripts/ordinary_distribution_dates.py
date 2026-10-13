"""Source-proven date replacements for isolated successors, never financial admission."""

from __future__ import annotations

import json
import re
import unicodedata
from copy import deepcopy
from io import BytesIO
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field
from pypdf import PdfReader

from app.data.catalog.checksums import canonical_json_bytes, verified_file_bytes
from app.domain.markets.corporate_actions import CorporateAction, CorporateActionType
from scripts.distribution_payment_terms import cash_payment_date
from scripts.full_dataset_build_inputs import FilePin
from scripts.retained_bonus_terms import same_day_listing

VERSION = "ORDINARY_DISTRIBUTION_DATES_V1"


class DateItem(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    event_checksum: str = Field(pattern=r"^[0-9a-f]{64}$")
    source_pdf: FilePin
    source_title: str = Field(min_length=1)


class DateInventory(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    version: Literal["ORDINARY_DISTRIBUTION_DATES_V1"]
    items: tuple[DateItem, ...] = Field(min_length=1)


def require(condition: bool, reason: str) -> None:
    if not condition:
        raise ValueError(f"ORDINARY_DATES_{reason}")


def source_path(pin: FilePin, manifest_path: Path) -> Path:
    path = manifest_path.parent / pin.path
    require(not any(part.is_symlink() for part in (path, *path.parents)), "SOURCE_PATH_ALIASED")
    return path.resolve(strict=True)


def date_source_pins(payload: Any, manifest_path: Path) -> dict[Path, str]:
    inventory = DateInventory.model_validate(payload)
    require(
        len({item.event_checksum for item in inventory.items}) == len(inventory.items),
        "DUPLICATE_TARGET",
    )
    pins: dict[Path, str] = {}
    for item in inventory.items:
        path = source_path(item.source_pdf, manifest_path)
        require(path not in pins or pins[path] == item.source_pdf.sha256, "CONFLICTING_PIN")
        pins[path] = item.source_pdf.sha256
    return pins


def normalize_ordinary_dates(
    rows: list[dict[str, Any]], payload: Any, manifest_path: Path
) -> list[dict[str, Any]]:
    inventory = DateInventory.model_validate(payload)
    pins = date_source_pins(payload, manifest_path)
    pages_by_path = {
        path: [
            page.extract_text() or ""
            for page in PdfReader(BytesIO(verified_file_bytes(path, digest))).pages
        ]
        for path, digest in pins.items()
    }
    by_checksum: dict[str, list[int]] = {}
    for index, row in enumerate(rows):
        by_checksum.setdefault(row["event_checksum"], []).append(index)
    result = deepcopy(rows)
    for item in sorted(inventory.items, key=lambda item: item.event_checksum):
        matches = by_checksum.get(item.event_checksum, [])
        require(len(matches) == 1, "TARGET_NOT_UNIQUE")
        index = matches[0]
        row = rows[index]
        require(row["event_kind"] == "CORPORATE_ACTION", "UNSUPPORTED_KIND")
        event = CorporateAction.model_validate_json(row["event_json"])
        _, exchange, symbol = str(event.security_id).split(":")
        require(exchange == "SZSE", "UNSUPPORTED_EXCHANGE")
        require(
            event.action_type
            in {CorporateActionType.CASH_DIVIDEND, CorporateActionType.BONUS_SHARE},
            "UNSUPPORTED_ACTION",
        )
        before = event.model_dump(mode="json")
        expected = {
            "security_id": str(event.security_id),
            "action_type": before["action_type"],
            "application_date": before["effective_date"],
            "effective_date": before["effective_date"],
            "ex_date": before["ex_date"],
            "cash_per_share": before["cash_per_share"],
            "share_ratio": before["share_ratio"],
            "source_document_sha256": before["source_document_sha256"],
            "source_url": before["source_url"],
            "event_checksum": event.event_checksum,
        }
        require(all(row.get(key) == value for key, value in expected.items()), "ROW_IDENTITY")
        require(event.event_checksum == item.event_checksum, "EVENT_CHECKSUM")
        require(event.source_document_sha256 == item.source_pdf.sha256, "SOURCE_IDENTITY")
        require(
            bool(
                re.fullmatch(
                    r"https://static\.cninfo\.com\.cn/finalpage/\d{4}-\d{2}-\d{2}/[0-9]+\.PDF",
                    event.source_url or "",
                )
            ),
            "OFFICIAL_SOURCE_REQUIRED",
        )
        require(
            event.record_date is not None
            and event.ex_date is not None
            and event.effective_date == event.ex_date
            and event.announcement_date is not None
            and event.announcement_date <= event.record_date < event.ex_date,
            "EVENT_DATES",
        )
        pages = pages_by_path[source_path(item.source_pdf, manifest_path)]
        compact_title = re.sub(r"\s+", "", unicodedata.normalize("NFKC", item.source_title))
        compact_source_title = re.sub(
            r"\s+", "", unicodedata.normalize("NFKC", event.source_document or "")
        )
        heading = (
            r"证券代码:"
            + re.escape(symbol)
            + r"证券简称:[\u4e00-\u9fffA-Za-z*]{1,20}公告编号:[0-9]{4}-[0-9]+"
            + r"[\u4e00-\u9fff]{2,80}股份有限公司"
            + re.escape(compact_title)
            + r"(?=本公司|重要提示|[一二三四五六七八九十]+、)"
        )
        require(
            bool(pages)
            and compact_title == compact_source_title
            and re.match(heading, re.sub(r"\s+", "", unicodedata.normalize("NFKC", pages[0])))
            is not None,
            "TITLE_NOT_IN_SOURCE",
        )
        cash = event.action_type is CorporateActionType.CASH_DIVIDEND
        field = "payment_date" if cash else "listing_date"
        require(before[field] is None, "DATE_ALREADY_PRESENT")
        parser = cash_payment_date if cash else same_day_listing
        derived = parser(
            pages,
            symbol,
            item.source_title,
            str(event.record_date),
            str(event.ex_date),
        )
        # Date metadata must not imply support for delayed entitlement accounting.
        require(derived == str(event.ex_date), "DELAYED_DATE_REQUIRES_SEPARATE_ACCOUNTING")
        updated = CorporateAction.model_validate({**before, field: derived})
        after = updated.model_dump(mode="json")
        require({key for key in before if before[key] != after[key]} == {field}, "TERMS_CHANGED")
        acceptance = json.loads(row["acceptance_json"])
        require(
            isinstance(acceptance, dict) and "date_normalization" not in acceptance,
            "PRIOR_REPLACEMENT",
        )
        result[index] = {
            **row,
            "event_checksum": updated.event_checksum,
            "event_json": canonical_json_bytes(after).decode(),
            "acceptance_json": canonical_json_bytes(
                {
                    "event_checksum": updated.event_checksum,
                    "date_normalization": {
                        "version": VERSION,
                        "original_event_checksum": item.event_checksum,
                        "event_checksum": updated.event_checksum,
                        "field": field,
                        "date": derived,
                        "source_pdf_sha256": item.source_pdf.sha256,
                        "source_title": item.source_title,
                        "financial_admission": False,
                    },
                    "original_acceptance": acceptance,
                }
            ).decode(),
        }
    require(len({row["event_checksum"] for row in result}) == len(result), "DUPLICATE_RESULT")
    return result
