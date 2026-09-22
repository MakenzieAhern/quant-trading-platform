"""Resume dated factor-baseline checks for exits absent from Pilot; no full authority claim."""

import argparse
import json
from pathlib import Path

from scripts.reconcile_sse_cninfo import fetch, save, sha
from scripts.sina_adjustment_audit import factor_at, parse_factors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lifecycles", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    rows = json.loads(args.lifecycles.read_bytes())
    targets = sorted(
        (
            r
            for r in rows
            if r["delisting_date"] and "2010-01-01" <= r["delisting_date"] < "2023-01-01"
        ),
        key=lambda r: (r["delisting_date"], r["security_id"]),
    )
    results = []
    for row in targets:
        symbol = ("sh" if row["exchange"] == "SSE" else "sz") + row["symbol"]
        result = dict(
            security_id=row["security_id"],
            listing_date=row["listing_date"],
            delisting_date=row["delisting_date"],
        )
        try:
            raw = fetch(
                args.output,
                symbol + "-hfq.js",
                f"https://finance.sina.com.cn/realstock/company/{symbol}/hfq.js",
            )
            curve = parse_factors(raw, symbol, "hfq")
            result.update(
                source_sha256=sha(raw),
                rows=len(curve),
                baseline=str(factor_at(curve, max("2010-01-01", row["listing_date"]))),
                status="BASELINE_PRESENT_NOT_AUTHORITY_ACCEPTANCE",
            )
        except (ValueError, RuntimeError, OSError) as exc:
            result.update(status="UNRESOLVED", error=f"{type(exc).__name__}: {exc}")
        results.append(result)
        save(
            args.output / "exit-factor-report.json",
            dict(
                requested_start="2010-01-01",
                source_master_sha256=sha(args.lifecycles.read_bytes()),
                targets=len(targets),
                checked=len(results),
                results=results,
                status="SOURCE_PROBE_ONLY_NOT_ACCEPTED",
            ),
        )
        print(json.dumps(result), flush=True)
        if result["status"] == "UNRESOLVED":
            break  # Resolve this concrete source gap before expanding acquisition.


if __name__ == "__main__":
    main()
