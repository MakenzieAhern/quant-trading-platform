"""Bounded R5 coverage controls, never ingestion or source promotion."""

import argparse
import json
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from scripts.probe_raw_failover import tencent_url
from scripts.reconcile_sse_cninfo import fetch, save
from scripts.stage_akshare_pilot import raw_url


def requests(symbol: str) -> dict[str, str]:
    primary = urlsplit(raw_url("SSE", symbol))
    params = dict(parse_qsl(primary.query))
    params.update(beg="20100101", end="20101231")
    secondary = urlsplit(tencent_url("SSE", symbol, 2023))
    secondary_params = dict(parse_qsl(secondary.query))
    secondary_params.update(
        _var="kline_day2010", param=f"sh{symbol},day,2010-01-01,2011-12-31,640,"
    )
    return {
        "Eastmoney": urlunsplit(primary._replace(query=urlencode(params))),
        "Tencent": urlunsplit(secondary._replace(query=urlencode(secondary_params))),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    results = []
    # Official cached SSE exit register:600553 listed2002-08-22, exited2011-02-18.
    # 600000 is the surviving transport/coverage control; selection precedes requests.
    for symbol in ("600000", "600553"):
        for provider, url in requests(symbol).items():
            row = dict(symbol=symbol, provider=provider, requested_year=2010, url=url)
            try:
                raw = fetch(args.output, f"{provider}-{symbol}-2010.json", url)
                value = json.loads(raw.decode().split("=", 1)[-1])
                if provider == "Eastmoney":
                    bars = (value.get("data") or {}).get("klines", [])
                    dates = [bar.split(",")[0] for bar in bars]
                else:
                    bars = (value.get("data") or {}).get("sh" + symbol, {}).get("day", [])
                    dates = [bar[0] for bar in bars]
                row.update(
                    returned_rows=len(bars),
                    target_rows=sum(d.startswith("2010-") for d in dates),
                    first_date=min(dates, default=None),
                    last_date=max(dates, default=None),
                )
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
                dict(status="COVERAGE_PROBE_ONLY_NOT_ACCEPTED", results=results),
            )
            print(json.dumps(row), flush=True)


if __name__ == "__main__":
    main()
