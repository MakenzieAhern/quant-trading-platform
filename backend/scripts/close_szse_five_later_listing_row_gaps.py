"""Close five SZSE 2010-plus listing-suspension no-row histories."""

import argparse
import json
from collections import Counter
from pathlib import Path

from scripts.reconcile_sse_cninfo import canonical, save, sha

BASE_SHA = "8b286641b05ab550b1e25b154b2f179d181c10c2718532435addee588dcbaea2"
CLOSURES = {
    "000545": {
        "suspended_from": "2012-05-07",
        "first_trading_day": "2013-07-26",
        "expected_rows": 132,
        "sources": [
            (
                "000545-2014-02-12-sponsor.pdf",
                "2dcb04114d6ed4ca1112a5b50263bebce727a0a389605649a34edb0ead3dc1a6",
                "https://static.cninfo.com.cn/finalpage/2014-02-12/63561114.PDF",
                [3, 4],
            )
        ],
    },
    "000722": {
        "suspended_from": "2010-05-10",
        "first_trading_day": "2012-06-15",
        "expected_rows": 78,
        "sources": [
            (
                "000722-2012-06-06-restoration.pdf",
                "accc06e1282be736e9d02b7f5e6eb126a5cd38c9073e22f3f74f1fc4f7aaf1c8",
                "https://static.cninfo.com.cn/finalpage/2012-06-06/61096742.PDF",
                [9],
            )
        ],
    },
    "000751": {
        "suspended_from": "2013-05-08",
        "first_trading_day": "2014-08-06",
        "expected_rows": 145,
        "sources": [
            (
                "000751-2013-05-03-pause.pdf",
                "ab033cbc85ee6fe1d2b8d12dedd9ef08c56404b7379bd5c49339bc0f88eeddaa",
                "https://static.cninfo.com.cn/finalpage/2013-05-03/62452294.PDF",
                [1],
            ),
            (
                "000751-2014-08-06-restoration.pdf",
                "f396244bea77c282b35d25cb3d7fe02a9d604037912c5c0e690e62ce28acb522",
                "https://static.cninfo.com.cn/finalpage/2014-08-06/1200100623.PDF",
                [1],
            ),
        ],
    },
    "000831": {
        "suspended_from": "2011-03-24",
        "first_trading_day": "2013-02-08",
        "expected_rows": 78,
        "sources": [
            (
                "000831-2015-04-17-sponsor.pdf",
                "12915839ccec7b9e577fcd86f00a31f8cedb7212b17fe8cdcfadbecc97fadd02",
                "https://static.cninfo.com.cn/finalpage/2015-04-17/1200842338.PDF",
                [2],
            )
        ],
    },
    "002506": {
        "suspended_from": "2014-05-28",
        "first_trading_day": "2015-08-12",
        "expected_rows": 72,
        "sources": [
            (
                "002506-2014-10-30-quarterly.pdf",
                "d36c2f1a2d7144754f7be589748dc84f27b2116815739fefd7811c092f27b43c",
                "https://static.cninfo.com.cn/finalpage/2014-10-30/1200354078.PDF",
                [7],
            ),
            (
                "002506-2015-08-12-restoration.pdf",
                "94bbbb2b3c6478cd3d6579b4313bf8621f86974a192228475a56b1991263d933",
                "https://static.cninfo.com.cn/finalpage/2015-08-12/1201424146.PDF",
                [1],
            ),
        ],
    },
}


def close_report(base: dict, closures: dict) -> dict:
    if base["report_version"] != "SZSE_OFFICIAL_ROW_GAPS_V5":
        raise ValueError("WRONG_BASE_REPORT")
    counts = Counter(base["classification_counts"])
    evidence = []
    for symbol, item in sorted(closures.items()):
        security_id = f"CN-A:SZSE:{symbol}"
        matched = [r for r in base["unresolved_rows"] if r["security_id"] == security_id]
        if (
            len(matched) != item["expected_rows"]
            or item["suspended_from"] < "2010-01-01"
            or any(
                r["reason"] != "UNKNOWN_RESUMPTION_NOT_CLOSED"
                or not item["suspended_from"] <= r["date"] < item["first_trading_day"]
                for r in matched
            )
        ):
            raise ValueError(f"SOURCE_INTERVAL_OR_COUNT_CHANGED:{symbol}")
        counts["UNKNOWN_RESUMPTION_NOT_CLOSED"] -= len(matched)
        counts["OFFICIAL_2010PLUS_LISTING_SUSPENSION"] += len(matched)
        evidence.append(
            {
                "security_id": security_id,
                "suspended_from": item["suspended_from"],
                "first_trading_day": item["first_trading_day"],
                "source_absent_rows_closed": len(matched),
                "evidence": item["evidence"],
            }
        )
    remaining = [
        r for r in base["unresolved_rows"] if r["security_id"].split(":")[-1] not in closures
    ]
    if min(counts.values()) < 0 or sum(counts.values()) != base["missing_rows"]:
        raise ValueError("MISSING_ROW_CONSERVATION_FAILED")
    report = {
        **base,
        "report_version": "SZSE_OFFICIAL_ROW_GAPS_V6",
        "parser_sha256": sha(Path(__file__).read_bytes()),
        "base_report_sha256": BASE_SHA,
        "base_manifest_sha256": base["manifest_sha256"],
        "classification_counts": dict(sorted(counts.items())),
        "unresolved_rows": remaining,
        "unresolved_symbols": dict(
            sorted(Counter(r["security_id"].split(":")[-1] for r in remaining).items())
        ),
        "unresolved_by_year": dict(sorted(Counter(r["date"][:4] for r in remaining).items())),
        "additional_official_2010plus_intervals": [
            *base["additional_official_2010plus_intervals"],
            *evidence,
        ],
    }
    report.pop("manifest_sha256")
    report["manifest_sha256"] = sha(canonical(report))
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-report", type=Path, required=True)
    parser.add_argument("--evidence-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    raw = args.base_report.read_bytes()
    if sha(raw) != BASE_SHA:
        raise ValueError("AUDITED_BASE_REPORT_CHANGED")
    base = json.loads(raw)
    if (
        sha(canonical({k: v for k, v in base.items() if k != "manifest_sha256"}))
        != base["manifest_sha256"]
    ):
        raise ValueError("BASE_MANIFEST_CHANGED")
    closures = json.loads(json.dumps(CLOSURES))
    for symbol, item in closures.items():
        evidence = []
        for filename, expected_sha, url, pages in item["sources"]:
            path = args.evidence_root / filename
            raw_pdf = path.read_bytes()
            receipt = json.loads(path.with_name(filename + ".meta.json").read_bytes())
            if (
                not raw_pdf.startswith(b"%PDF-")
                or sha(raw_pdf) != expected_sha
                or receipt["sha256"] != expected_sha
                or receipt["url"] != url
                or receipt["http_status"] != 200
                or not receipt["retrieved_at_utc"].endswith("+00:00")
            ):
                raise ValueError(f"OFFICIAL_EVIDENCE_CHANGED:{symbol}:{filename}")
            evidence.append(
                {
                    "url": url,
                    "sha256": expected_sha,
                    "retrieved_at_utc": receipt["retrieved_at_utc"],
                    "pdf_pages": pages,
                }
            )
        item["evidence"] = evidence
    report = close_report(base, closures)
    save(args.output, report)
    print(
        json.dumps(
            {
                "classification_counts": report["classification_counts"],
                "unresolved_rows": len(report["unresolved_rows"]),
                "manifest_sha256": report["manifest_sha256"],
            }
        )
    )


if __name__ == "__main__":
    main()
