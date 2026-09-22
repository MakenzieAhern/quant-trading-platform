"""Checkpoint SSE public day bars for the accepted 2010-2025 master codes."""

import argparse
import json
from pathlib import Path

from scripts.probe_sse_official_daily import REFERER, URL, inspect
from scripts.reconcile_sse_cninfo import fetch, save, sha


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--master", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--limit", type=int)
    args = parser.parse_args()
    if args.limit is not None and args.limit < 1:
        parser.error("--limit must be positive")
    master_bytes = args.master.read_bytes()
    master_sha = sha(master_bytes)
    if master_sha != "02f1a2bb145d1d9c98c4d9678bad687a8a4c4ece6f6419f12da939b66507b363":
        raise ValueError("accepted P0 master checksum changed")
    records = sorted(
        (
            row
            for row in json.loads(master_bytes)
            if row["exchange"] == "SSE" and row["instrument_type"] == "COMMON_A_SHARE"
        ),
        key=lambda row: (row["symbol"], row["effective_from"]),
    )
    if len(records) != 2405 or len({row["security_id"] for row in records}) != 2403:
        raise ValueError("accepted P0 SSE symbol/identity census changed")
    report = {
        "status": "IN_PROGRESS_NOT_AUDITED",
        "master_sha256": master_sha,
        "expected_symbols": len(records),
        "results": [],
    }
    for index, row in enumerate(records[: args.limit], 1):
        symbol = row["symbol"]
        result = {
            "symbol": symbol,
            "security_id": row["security_id"],
            "effective_from": row["effective_from"],
            "effective_to": row["effective_to"],
        }
        try:
            raw = fetch(
                args.output,
                symbol + ".json",
                URL.format(symbol),
                referer=REFERER.format(symbol),
            )
            result.update(inspect(raw, symbol))
            meta = json.loads((args.output / (symbol + ".json.meta.json")).read_bytes())
            result["source_sha256"] = meta["sha256"]
            result["status"] = (
                "SNAPSHOTTED_UNAUDITED" if result["target_rows_2010_2025"] else "NO_TARGET_BARS"
            )
        except Exception as exc:
            result.update(status="FAILED", error=type(exc).__name__, reason=str(exc))
            if getattr(exc, "code", None) in (403, 429) or "ACCESS_DENIED" in str(exc):
                report["results"].append(result)
                report["status"] = "ACCESS_DENIAL_STOP"
                save(args.output / "full-collection-report.json", report)
                raise SystemExit(2) from exc
        report["results"].append(result)
        if index % 25 == 0:
            save(args.output / "full-collection-report.json", report)
            print(f"{index}/{len(records)} snapshotted", flush=True)
    complete = args.limit is None or args.limit >= len(records)
    failures = [r for r in report["results"] if r["status"] == "FAILED"]
    no_target_bars = [r for r in report["results"] if r["status"] == "NO_TARGET_BARS"]
    report["status"] = (
        "ACQUIRED_NOT_AUDITED"
        if complete and not failures and not no_target_bars
        else "PARTIAL_OR_GAPPED_NOT_AUDITED"
    )
    report["failure_manifest"] = failures
    report["no_target_bars"] = no_target_bars
    save(args.output / "full-collection-report.json", report)
    print(
        f"{len(report['results'])}/{len(records)}; transport_failures={len(failures)}; "
        f"no_target_bars={len(no_target_bars)}",
        flush=True,
    )


if __name__ == "__main__":
    main()
