"""Bounded official SSE day-bar controls; no full-universe source promotion."""

import argparse
import json
from pathlib import Path

from scripts.reconcile_sse_cninfo import fetch, save

CONTROLS = ("600000", "600553", "688001")  # survivor, delisted, STAR
URL = "https://yunhq.sse.com.cn:32042/v1/sh1/dayk/{}?begin=-5000&end=-1&period=day"
REFERER = "https://www.sse.com.cn/assortment/stock/list/info/company/index.shtml?COMPANY_CODE={}"


def inspect(raw: bytes, symbol: str) -> dict[str, object]:
    value = json.loads(raw)
    if value.get("code") != symbol:
        raise ValueError("official SSE response code mismatch")
    bars = value.get("kline")
    if not isinstance(bars, list) or not bars:
        raise ValueError("empty official SSE day bars")
    dates = [bar[0] for bar in bars]
    if any(len(bar) != 7 for bar in bars) or dates != sorted(set(dates)):
        raise ValueError("malformed or duplicate official SSE day bars")
    target = [bar for bar in bars if 20100101 <= bar[0] <= 20251231]
    if symbol == "600000" and (not target or target[0][0] > 20100104):
        raise ValueError("survivor 2010 start is not covered")
    if symbol == "600553" and (not target or target[-1][0] > 20110218):
        raise ValueError("delisted control has impossible post-exit bars")
    return {
        "returned_rows": len(bars),
        "first_date": dates[0],
        "last_date": dates[-1],
        "target_rows_2010_2025": len(target),
        "target_first": target[0][0] if target else None,
        "target_last": target[-1][0] if target else None,
        "control_2023_04_10": next((bar for bar in target if bar[0] == 20230410), None),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = {"status": "BOUNDED_PROBE_ONLY_NOT_ACCEPTED", "controls": []}
    for symbol in CONTROLS:
        raw = fetch(
            args.output,
            symbol + ".json",
            URL.format(symbol),
            referer=REFERER.format(symbol),
        )
        result = {"symbol": symbol, **inspect(raw, symbol)}
        report["controls"].append(result)
        save(args.output / "report.json", report)
        print(f"{symbol}: {result['target_rows_2010_2025']} target bars", flush=True)


if __name__ == "__main__":
    main()
