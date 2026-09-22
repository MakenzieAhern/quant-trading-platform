"""Audit cached SZSE daily XLSX against accepted point-in-time A-share membership."""

import argparse
import json
import warnings
from decimal import Decimal
from io import BytesIO
from pathlib import Path

from openpyxl import load_workbook

from scripts.probe_szse_official_daily import HEADERS, request
from scripts.reconcile_sse_cninfo import canonical, save, sha

MASTER_SHA = "02f1a2bb145d1d9c98c4d9678bad687a8a4c4ece6f6419f12da939b66507b363"
CALENDAR_SHA = "622e812a0ab3142207ef8a381d18d38d92064415e7425563961a6a4d278ce1c4"


def number(value: object) -> Decimal:
    return Decimal(str(value).replace(",", ""))


def validate_traded_row(row: tuple) -> bool:
    volume, amount = number(row[9]), number(row[10])
    if volume < 0 or amount < 0 or (volume == 0 and amount != 0):
        raise ValueError("OFFICIAL_SZSE_NEGATIVE_OR_UNPAIRED_TURNOVER")
    if volume == 0:
        return False
    open_, high, low, close = map(number, row[4:8])
    if not (0 < low <= min(open_, close) <= max(open_, close) <= high):
        raise ValueError("OFFICIAL_SZSE_INVALID_OHLC")
    return True


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--master", type=Path, required=True)
    parser.add_argument("--calendar", type=Path, required=True)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    master_bytes, calendar_bytes = args.master.read_bytes(), args.calendar.read_bytes()
    if sha(master_bytes) != MASTER_SHA or sha(calendar_bytes) != CALENDAR_SHA:
        raise ValueError("ACCEPTED_MASTER_OR_CALENDAR_CHANGED")
    master = [
        row
        for row in json.loads(master_bytes)
        if row["exchange"] == "SZSE" and row["instrument_type"] == "COMMON_A_SHARE"
    ]
    sessions = json.loads(calendar_bytes)["sessions"]
    report_path = args.source_root / "full-collection-report.json"
    collection_bytes = report_path.read_bytes()
    collection = json.loads(collection_bytes)
    if collection["calendar_sha256"] != CALENDAR_SHA or collection["expected_sessions"] != len(
        sessions
    ):
        raise ValueError("SOURCE_COLLECTION_CALENDAR_CHANGED")
    if len(collection["results"]) > len(sessions):
        raise ValueError("SOURCE_COLLECTION_EXCEEDS_CALENDAR")

    totals = {
        "source_stock_rows": 0,
        "point_in_time_a_share_rows": 0,
        "a_share_traded_rows": 0,
        "a_share_zero_turnover_rows": 0,
        "active_master_without_stock_row": 0,
        "unmatched_a_prefix_candidates": 0,
    }
    failures, unmatched_examples = [], []
    for day, result in zip(sessions, collection["results"], strict=False):
        if result["date"] != day:
            raise ValueError("SOURCE_COLLECTION_SESSION_ORDER_CHANGED")
        if result["status"] == "FAILED":
            failures.append(result)
            continue
        url, catalog, referer = request(day)
        path = args.source_root / f"{day}.xlsx"
        raw = path.read_bytes()
        meta = json.loads(path.with_suffix(".xlsx.meta.json").read_bytes())
        if (
            sha(raw) != result["source_sha256"]
            or meta["sha256"] != result["source_sha256"]
            or meta["url"] != url
            or meta["referer"] != referer
            or result["catalog"] != catalog
            or not meta["retrieved_at_utc"].endswith("+00:00")
        ):
            raise ValueError(f"OFFICIAL_SZSE_SOURCE_RECEIPT_CHANGED: {day}")
        active = {
            row["symbol"]: row["security_id"]
            for row in master
            if row["effective_from"] <= day
            and (row["effective_to"] is None or day <= row["effective_to"])
        }
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", message="Workbook contains no default style")
            workbook = load_workbook(BytesIO(raw), read_only=True, data_only=True)
        sheet = workbook.active
        sheet.reset_dimensions()
        rows = sheet.values
        if tuple(next(rows)) != HEADERS:
            raise ValueError(f"OFFICIAL_SZSE_COLUMNS_CHANGED: {day}")
        codes = set()
        control = None
        for row in rows:
            symbol = row[1]
            if row[0] != day or not isinstance(symbol, str) or symbol in codes:
                raise ValueError(f"OFFICIAL_SZSE_DATE_OR_CODE_CHANGED: {day}")
            codes.add(symbol)
            if symbol == "000001":
                control = dict(zip(HEADERS, row, strict=True))
            if symbol in active:
                totals["point_in_time_a_share_rows"] += 1
                totals[
                    "a_share_traded_rows"
                    if validate_traded_row(row)
                    else "a_share_zero_turnover_rows"
                ] += 1
            elif symbol.startswith(("000", "001", "002", "003", "300", "301")):
                totals["unmatched_a_prefix_candidates"] += 1
                if len(unmatched_examples) < 30:
                    unmatched_examples.append({"date": day, "symbol": symbol, "name": row[2]})
        if (
            len(codes) != result["rows"]
            or len(codes) != result["unique_codes"]
            or control != result["control_000001"]
        ):
            raise ValueError(f"OFFICIAL_SZSE_REPARSE_CHANGED: {day}")
        totals["source_stock_rows"] += len(codes)
        totals["active_master_without_stock_row"] += len(active.keys() - codes)
    report = {
        "report_version": "SZSE_OFFICIAL_DAILY_SCOPE_V1",
        "status": (
            "COMPLETE_SOURCE_SNAPSHOT_SCOPE_NOT_RAW_AUTHORITY"
            if len(collection["results"]) == len(sessions) and not failures
            else "PARTIAL_SOURCE_SCOPE_NOT_RAW_AUTHORITY"
        ),
        "parser_sha256": sha(Path(__file__).read_bytes()),
        "source_collection_sha256": sha(collection_bytes),
        "master_sha256": MASTER_SHA,
        "calendar_sha256": CALENDAR_SHA,
        "audited_sessions": len(collection["results"]) - len(failures),
        "expected_sessions": len(sessions),
        **totals,
        "unmatched_a_prefix_examples": unmatched_examples,
        "transport_failures": failures,
        "active_without_row_not_inferred_suspended": True,
        "all_methods_volume_amount_not_auction_only_authority": True,
        "raw_authority_promoted": False,
    }
    report["manifest_sha256"] = sha(canonical(report))
    save(args.output, report)
    print(
        json.dumps(
            {
                key: value
                for key, value in report.items()
                if key not in ("unmatched_a_prefix_examples", "transport_failures")
            }
        )
    )


if __name__ == "__main__":
    main()
