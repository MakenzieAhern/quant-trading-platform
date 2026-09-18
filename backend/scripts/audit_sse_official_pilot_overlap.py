"""Read-only raw-bar parity check between SSE public charts and frozen Pilot v2."""

import argparse
import json
from decimal import Decimal
from pathlib import Path

import pyarrow.parquet as pq

from scripts.reconcile_sse_cninfo import save, sha

PRICES = ("raw_open", "raw_high", "raw_low", "raw_close")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--pilot", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    collection = json.loads((args.source_root / "full-collection-report.json").read_bytes())
    sources = {row["symbol"]: row for row in collection["results"]}
    if len(sources) != len(collection["results"]):
        raise ValueError("duplicate SSE source symbol")
    summary = {
        "status": "PILOT_OVERLAP_ONLY_NOT_FULL_RAW_AUTHORITY",
        "source_collection_sha256": sha(
            (args.source_root / "full-collection-report.json").read_bytes()
        ),
        "pilot_manifest_sha256": sha((args.pilot / "manifest.json").read_bytes()),
        "pilot_partitions": 0,
        "compared_bars": 0,
        "price_mismatch": 0,
        "volume_beyond_100_shares": 0,
        "amount_beyond_100_yuan": 0,
        "volume_official_higher": 0,
        "amount_official_higher": 0,
        "pilot_day_missing_from_official": 0,
        "official_day_missing_from_pilot": 0,
        "missing_source_symbols": [],
        "examples": [],
    }
    for partition in sorted((args.pilot / "SSE").glob("*/raw.parquet")):
        symbol = partition.parent.name
        summary["pilot_partitions"] += 1
        source = sources.get(symbol)
        source_path = args.source_root / f"{symbol}.json"
        if not source or not source.get("source_sha256") or not source_path.exists():
            summary["missing_source_symbols"].append(symbol)
            continue
        source_bytes = source_path.read_bytes()
        if sha(source_bytes) != source["source_sha256"]:
            raise ValueError(f"official SSE source checksum changed: {symbol}")
        payload = json.loads(source_bytes)
        if payload.get("code") != symbol:
            raise ValueError(f"official SSE response code changed: {symbol}")
        official = {}
        for bar in payload["kline"]:
            day = str(bar[0])
            if "20230101" <= day <= "20240731":
                key = f"{day[:4]}-{day[4:6]}-{day[6:]}"
                if key in official:
                    raise ValueError(f"duplicate official SSE bar: {symbol} {key}")
                official[key] = bar
        pilot = pq.read_table(
            partition,
            columns=["trading_date", *PRICES, "volume", "amount"],
        ).to_pylist()
        pilot_days = set()
        for row in pilot:
            day = row["trading_date"]
            if day in pilot_days:
                raise ValueError(f"duplicate frozen Pilot bar: {symbol} {day}")
            pilot_days.add(day)
            bar = official.get(day)
            if bar is None:
                summary["pilot_day_missing_from_official"] += 1
                if len(summary["examples"]) < 20:
                    summary["examples"].append([symbol, day, "PILOT_DAY_NOT_OFFICIAL"])
                continue
            summary["compared_bars"] += 1
            mismatched = any(
                Decimal(str(bar[i + 1])) != Decimal(row[name]) for i, name in enumerate(PRICES)
            )
            volume_gap = Decimal(str(bar[5])) - Decimal(row["volume"])
            amount_gap = Decimal(str(bar[6])) - Decimal(row["amount"])
            summary["price_mismatch"] += mismatched
            summary["volume_beyond_100_shares"] += abs(volume_gap) > 100
            summary["amount_beyond_100_yuan"] += abs(amount_gap) > 100
            summary["volume_official_higher"] += volume_gap > 100
            summary["amount_official_higher"] += amount_gap > 100
            if (mismatched or abs(volume_gap) > 100 or abs(amount_gap) > 100) and len(
                summary["examples"]
            ) < 20:
                summary["examples"].append(
                    [symbol, day, "FIELD_GAP", str(volume_gap), str(amount_gap)]
                )
        summary["official_day_missing_from_pilot"] += len(official.keys() - pilot_days)
    save(args.output, summary)
    print(
        f"compared={summary['compared_bars']} price_mismatch={summary['price_mismatch']} "
        f"volume_scope_gap={summary['volume_beyond_100_shares']} "
        f"amount_scope_gap={summary['amount_beyond_100_yuan']}",
        flush=True,
    )


if __name__ == "__main__":
    main()
