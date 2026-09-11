"""Small immutable operational probe; no ingestion or authority promotion."""

import argparse
import json
import time
from pathlib import Path
from urllib.parse import urlencode

from scripts.reconcile_sse_cninfo import fetch, save
from scripts.stage_akshare_pilot import pilot_members, raw_url

# Fixed before requests: four boards, plus two exited lifecycle controls.
SAMPLE = ("600000", "000001", "688001", "300750", "600070", "300336")
TENCENT_SAMPLE = ("600000", "000001", "688008", "300750", "600070", "300336", "000732", "603125")
TENCENT_ENDPOINT = "https://proxy.finance.qq.com/ifzqgtimg/appstock/app/newfqkline/get"


def tencent_url(exchange: str, symbol: str, year: int) -> str:
    raw_url(exchange, symbol)  # Reuse identity validation, not primary data semantics.
    if year not in {2023, 2024}:
        raise ValueError("OUTSIDE_PILOT_REQUEST_YEARS")
    code = ("sh" if exchange == "SSE" else "sz") + symbol
    return (
        TENCENT_ENDPOINT
        + "?"
        + urlencode(
            {
                "_var": f"kline_day{year}",
                "param": f"{code},day,{year}-01-01,{year + 1}-12-31,640,",
                "r": "0.8205512681390605",
            }
        )
    )


def candidate(staging: Path, output: Path) -> None:
    if (output / "access-denial-stop.json").exists():
        return
    members = {r["symbol"]: r for r in pilot_members(staging)}
    for repeat in (1, 2):
        for symbol in TENCENT_SAMPLE:
            for year in (2023, 2024):
                name = f"{symbol}-{year}-{repeat}.json"
                meta_path = output / (name + ".meta.json")
                if meta_path.exists():
                    continue
                url = tencent_url(members[symbol]["exchange"], symbol, year)
                try:
                    raw = fetch(output, name, url)
                    print(name, len(raw), flush=True)
                except Exception as exc:
                    save(
                        output / (name + ".failure.json"),
                        dict(error_type=type(exc).__name__, reason=str(exc)),
                    )
                    print(name, type(exc).__name__, flush=True)
                    if getattr(exc, "code", None) in {403, 429} or "ACCESS_DENIED" in str(exc):
                        save(
                            output / "access-denial-stop.json",
                            dict(
                                error_type=type(exc).__name__,
                                reason=str(exc),
                                http_status=getattr(exc, "code", None),
                                request=url,
                            ),
                        )
                        return
                time.sleep(2)


def primary_status(results: list[dict]) -> str:
    if any(r.get("http_status") == 429 for r in results):
        return "PRIMARY_RATE_LIMITED"
    if sum(r.get("error_type") == "RemoteDisconnected" for r in results) > len(results) / 2:
        return "PRIMARY_SYSTEMIC_TRANSPORT_FAILURE"
    successes = sum(r.get("valid_raw") is True for r in results)
    if successes == len(results) and results:
        return "PRIMARY_HEALTHY"
    return "PRIMARY_DEGRADED" if successes else "UNKNOWN"


def run(staging: Path, output: Path) -> None:
    report_path = output / "report.json"
    if report_path.exists():
        previous = json.loads(report_path.read_bytes())
        if previous["status"] != "RUNNING" or any(
            r.get("http_status") in {403, 429} or "ACCESS_DENIED" in r.get("reason", "")
            for r in previous["results"]
        ):
            return
    members = {r["symbol"]: r for r in pilot_members(staging)}
    results = []
    for symbol in SAMPLE:
        member = members[symbol]
        name = f"{symbol}.json"
        metadata = output / (name + ".meta.json")
        result = dict(security_id=member["security_id"], member=member)
        # A completed probe is immutable, including failed/timeout slots.
        if metadata.exists():
            record = json.loads(metadata.read_bytes())
            result.update(record)
            result["error_type"] = record.get("error")
            if not record.get("error"):
                raw = fetch(output, name, raw_url(member["exchange"], symbol))
                data = json.loads(raw).get("data")
                result["valid_raw"] = bool(data and data.get("klines"))
        else:
            try:
                raw = fetch(output, name, raw_url(member["exchange"], symbol))
                data = json.loads(raw).get("data")
                result["valid_raw"] = bool(data and data.get("klines"))
            except Exception as exc:
                result.update(
                    error_type=type(exc).__name__,
                    reason=str(exc),
                    http_status=getattr(exc, "code", None),
                )
            result.update(json.loads(metadata.read_bytes()))
        results.append(result)
        save(output / "report.json", dict(results=results, status="RUNNING"))
        print(symbol, result.get("error_type", "HTTP_RESPONSE"), flush=True)
        if result.get("http_status") in {403, 429} or "ACCESS_DENIED" in result.get("reason", ""):
            break
        time.sleep(2)
    save(output / "report.json", dict(results=results, status=primary_status(results)))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--staging", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--candidate", action="store_true")
    args = parser.parse_args()
    (candidate if args.candidate else run)(args.staging, args.output)
