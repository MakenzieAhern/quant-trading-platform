"""Targeted v2 repair feasibility; never overwrite or publish Pilot v1."""

import argparse
import json
from pathlib import Path

from scripts.probe_raw_failover import tencent_url
from scripts.reconcile_sse_cninfo import fetch, save
from scripts.sina_adjustment_audit import parse_factors
from scripts.stage_akshare_pilot import raw_url


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    results = []
    for symbol in ("688086", "688287", "688555"):
        for provider, url in (
            ("Eastmoney", raw_url("SSE", symbol)),
            ("Tencent", tencent_url("SSE", symbol, 2023)),
            ("Sina", f"https://finance.sina.com.cn/realstock/company/sh{symbol}/hfq.js"),
        ):
            row = dict(symbol=symbol, provider=provider, url=url)
            try:
                raw = fetch(args.output, f"{provider}-{symbol}.raw", url)
                if provider == "Sina":
                    curve = parse_factors(raw, "sh" + symbol, "hfq")
                    row.update(factor_rows=len(curve), first_factor_date=curve[0][0])
                else:
                    value = json.loads(raw.decode().split("=", 1)[-1])
                    bars = (
                        (value.get("data") or {}).get("klines", [])
                        if provider == "Eastmoney"
                        else (value.get("data") or {}).get("sh" + symbol, {}).get("day", [])
                    )
                    row["returned_rows"] = len(bars)
            except Exception as exc:
                row.update(error=type(exc).__name__, reason=str(exc))
                if getattr(exc, "code", None) in (403, 429) or "ACCESS_DENIED" in str(exc):
                    results.append(row)
                    save(
                        args.output / "report.json",
                        dict(status="ACCESS_DENIAL_STOP", results=results),
                    )
                    return
            results.append(row)
            save(
                args.output / "report.json",
                dict(status="REPAIR_FEASIBILITY_ONLY_NOT_ACCEPTED", results=results),
            )
            print(json.dumps(row), flush=True)


if __name__ == "__main__":
    main()
