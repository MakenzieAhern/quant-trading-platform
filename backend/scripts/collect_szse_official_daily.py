"""Checkpoint SZSE public daily stock exports for accepted 2010-2025 sessions."""

import argparse
import json
from pathlib import Path

from scripts.probe_szse_official_daily import inspect, request
from scripts.reconcile_sse_cninfo import fetch, save, sha


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--calendar", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--limit", type=int)
    args = parser.parse_args()
    if args.limit is not None and args.limit < 1:
        parser.error("--limit must be positive")
    calendar_bytes = args.calendar.read_bytes()
    calendar_sha = sha(calendar_bytes)
    if calendar_sha != "622e812a0ab3142207ef8a381d18d38d92064415e7425563961a6a4d278ce1c4":
        raise ValueError("accepted full-calendar checkpoint changed")
    days = json.loads(calendar_bytes)["sessions"]
    if len(days) != 3886 or days != sorted(set(days)):
        raise ValueError("accepted 2010-2025 trading sessions changed")
    report = {
        "status": "IN_PROGRESS_NOT_AUDITED",
        "calendar_sha256": calendar_sha,
        "expected_sessions": len(days),
        "results": [],
    }
    for index, day in enumerate(days[: args.limit], 1):
        result = {"date": day}
        try:
            url, catalog, referer = request(day)
            raw = fetch(args.output, day + ".xlsx", url, referer=referer)
            result.update(catalog=catalog, **inspect(raw, day, require_control=False))
            meta = json.loads((args.output / (day + ".xlsx.meta.json")).read_bytes())
            result["source_sha256"] = meta["sha256"]
            result["status"] = "SNAPSHOTTED_UNAUDITED"
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
            print(f"{index}/{len(days)} snapshotted", flush=True)
    complete = args.limit is None or args.limit >= len(days)
    failures = [r for r in report["results"] if r["status"] == "FAILED"]
    report["status"] = (
        "ACQUIRED_NOT_AUDITED" if complete and not failures else "PARTIAL_OR_FAILED_NOT_AUDITED"
    )
    report["failure_manifest"] = failures
    save(args.output / "full-collection-report.json", report)
    print(f"{len(report['results'])}/{len(days)}; failures={len(failures)}", flush=True)


if __name__ == "__main__":
    main()
