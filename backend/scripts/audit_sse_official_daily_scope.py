"""Audit cached SSE day bars against the accepted calendar and symbol intervals."""

import argparse
import json
from decimal import Decimal
from pathlib import Path

from scripts.probe_sse_official_daily import REFERER, URL, inspect
from scripts.reconcile_sse_cninfo import canonical, save, sha

MASTER_SHA = "02f1a2bb145d1d9c98c4d9678bad687a8a4c4ece6f6419f12da939b66507b363"
CALENDAR_SHA = "622e812a0ab3142207ef8a381d18d38d92064415e7425563961a6a4d278ce1c4"


def within_interval(bar: list, row: dict, sessions: set[str]) -> bool:
    raw_day, raw_open, raw_high, raw_low, raw_close, volume, amount = bar
    digits = str(raw_day)
    day = f"{digits[:4]}-{digits[4:6]}-{digits[6:]}"
    if day not in sessions:
        raise ValueError(f"OFFICIAL_BAR_OUTSIDE_ACCEPTED_CALENDAR: {day}")
    open_, high, low, close, shares, yuan = map(
        lambda value: Decimal(str(value)),
        (raw_open, raw_high, raw_low, raw_close, volume, amount),
    )
    if not (0 < low <= min(open_, close) <= max(open_, close) <= high) or min(shares, yuan) < 0:
        raise ValueError(f"OFFICIAL_BAR_INVALID_OHLCV: {row['symbol']} {day}")
    return row["effective_from"] <= day and (
        row["effective_to"] is None or day <= row["effective_to"]
    )


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
    master = sorted(
        (
            row
            for row in json.loads(master_bytes)
            if row["exchange"] == "SSE" and row["instrument_type"] == "COMMON_A_SHARE"
        ),
        key=lambda row: (row["symbol"], row["effective_from"]),
    )
    sessions = set(json.loads(calendar_bytes)["sessions"])
    source_path = args.source_root / "full-collection-report.json"
    source_bytes = source_path.read_bytes()
    source = json.loads(source_bytes)
    if source["master_sha256"] != MASTER_SHA or source["expected_symbols"] != len(master):
        raise ValueError("SOURCE_COLLECTION_MASTER_CHANGED")
    if len(source["results"]) > len(master):
        raise ValueError("SOURCE_COLLECTION_EXCEEDS_MASTER")

    accepted_bars = quarantined_bars = 0
    quarantined_symbols = []
    failures = []
    no_target_bars = []
    for row, result in zip(master, source["results"], strict=False):
        if any(
            result[key] != row[key]
            for key in ("symbol", "security_id", "effective_from", "effective_to")
        ):
            raise ValueError("SOURCE_COLLECTION_ORDER_OR_IDENTITY_CHANGED")
        if result["status"] == "FAILED":
            failures.append(result)
            continue
        if result["status"] == "NO_TARGET_BARS":
            no_target_bars.append(row["symbol"])
        symbol = row["symbol"]
        path = args.source_root / f"{symbol}.json"
        raw = path.read_bytes()
        meta = json.loads(path.with_suffix(".json.meta.json").read_bytes())
        if (
            sha(raw) != result["source_sha256"]
            or meta["sha256"] != result["source_sha256"]
            or meta["url"] != URL.format(symbol)
            or meta["referer"] != REFERER.format(symbol)
            or not meta["retrieved_at_utc"].endswith("+00:00")
        ):
            raise ValueError(f"OFFICIAL_SOURCE_RECEIPT_CHANGED: {symbol}")
        if any(result[key] != value for key, value in inspect(raw, symbol).items()):
            raise ValueError(f"OFFICIAL_SOURCE_REPARSE_CHANGED: {symbol}")
        outside = 0
        for bar in json.loads(raw)["kline"]:
            if 20100101 <= bar[0] <= 20251231:
                if within_interval(bar, row, sessions):
                    accepted_bars += 1
                else:
                    outside += 1
        quarantined_bars += outside
        if outside:
            quarantined_symbols.append({"symbol": symbol, "outside_interval_bars": outside})
    report = {
        "status": (
            "COMPLETE_SOURCE_SNAPSHOT_SCOPE_NOT_RAW_AUTHORITY"
            if len(source["results"]) == len(master) and not failures
            else "PARTIAL_SOURCE_SCOPE_NOT_RAW_AUTHORITY"
        ),
        "report_version": "SSE_OFFICIAL_DAILY_SCOPE_V1",
        "parser_sha256": sha(Path(__file__).read_bytes()),
        "source_collection_sha256": sha(source_bytes),
        "master_sha256": MASTER_SHA,
        "calendar_sha256": CALENDAR_SHA,
        "audited_symbols": len(source["results"]) - len(failures),
        "expected_symbols": len(master),
        "in_interval_target_bars": accepted_bars,
        "quarantined_out_of_interval_bars": quarantined_bars,
        "quarantined_symbols": quarantined_symbols,
        "no_target_bar_symbols": no_target_bars,
        "transport_failures": failures,
        "raw_authority_promoted": False,
    }
    report["manifest_sha256"] = sha(canonical(report))
    save(args.output, report)
    print(
        json.dumps(
            {
                key: value
                for key, value in report.items()
                if key not in ("quarantined_symbols", "transport_failures")
            }
        )
    )


if __name__ == "__main__":
    main()
