"""Reconcile six more SZSE no-row histories to official listing-suspension bounds."""

import argparse
import json
from collections import Counter
from pathlib import Path

from scripts.reconcile_sse_cninfo import canonical, save, sha

BASE_SHA = "86905153277c0ca28ef26347fd86ca702a814e1d9664317d1357fe236cb5b847"
CLOSURES = {
    "000620": {
        "suspended_from": "2006-04-03",
        "first_trading_day": "2011-07-08",
        "expected_rows": 134,
        "previous_reason": "NO_MATCHING_HALT_SOURCE",
        "category": "OFFICIAL_PRE2010_LISTING_SUSPENSION",
        "sources": [
            (
                "000620-2011-07-01-restoration.pdf",
                "ebf6b026f25f8a3736284b955f56dae1b27554ba9469dc7cd9f09d8b9018cc0b",
                "https://static.cninfo.com.cn/finalpage/2011-07-01/59619412.PDF",
                [1, 8],
            )
        ],
    },
    "000657": {
        "suspended_from": "2010-04-09",
        "first_trading_day": "2013-02-08",
        "expected_rows": 150,
        "previous_reason": "UNKNOWN_RESUMPTION_NOT_CLOSED",
        "category": "OFFICIAL_2010PLUS_LISTING_SUSPENSION",
        "sources": [
            (
                "000657-2014-04-03-sponsor.pdf",
                "e878500a5c72bedf1f0bfa5b98e74d5f3b92c586ce3c636a07eb9a0e11e30630",
                "https://static.cninfo.com.cn/finalpage/2014-04-03/63786011.PDF",
                [1, 2],
            )
        ],
    },
    "000681": {
        "suspended_from": "2009-03-24",
        "first_trading_day": "2013-02-08",
        "expected_rows": 195,
        "previous_reason": "NO_MATCHING_HALT_SOURCE",
        "category": "OFFICIAL_PRE2010_LISTING_SUSPENSION",
        "sources": [
            (
                "000681-2014-01-29-annual.pdf",
                "eca6eaa87712f097e9d3dfa4d110e5e6d143b13e5fc977422cf71535f7e52e15",
                "https://static.cninfo.com.cn/finalpage/2014-01-29/63535891.PDF",
                [11],
            )
        ],
    },
    "000820": {
        "suspended_from": "2011-04-28",
        "first_trading_day": "2013-04-26",
        "expected_rows": 173,
        "previous_reason": "UNKNOWN_RESUMPTION_NOT_CLOSED",
        "category": "OFFICIAL_2010PLUS_LISTING_SUSPENSION",
        "sources": [
            (
                "000820-2013-04-19-restoration.pdf",
                "c78fc19ebf3c954a4dca128fd71745156dcf3df6f133a9442d601b90982cc0dc",
                "https://static.cninfo.com.cn/finalpage/2013-04-19/62385007.PDF",
                [1, 2],
            )
        ],
    },
    "000863": {
        "suspended_from": "2007-05-15",
        "first_trading_day": "2012-08-03",
        "expected_rows": 188,
        "previous_reason": "NO_MATCHING_HALT_SOURCE",
        "category": "OFFICIAL_PRE2010_LISTING_SUSPENSION",
        "sources": [
            (
                "000863-2013-05-10-sponsor.pdf",
                "50bdbadf0a1478911ec1fe5fc540aa70dee058d3251126d17885e0e9ffca41b1",
                "https://static.cninfo.com.cn/finalpage/2013-05-10/62475428.PDF",
                [1],
            )
        ],
    },
    "000981": {
        "suspended_from": "2009-03-03",
        "first_trading_day": "2011-08-26",
        "expected_rows": 172,
        "previous_reason": "NO_MATCHING_HALT_SOURCE",
        "category": "OFFICIAL_PRE2010_LISTING_SUSPENSION",
        "sources": [
            (
                "000981-2011-05-12-restructuring.pdf",
                "f1c7bfe2dbc473c174a8803432b2d01819318871bfb6b599aab0832de2681096",
                "https://static.cninfo.com.cn/finalpage/2011-05-12/59417301.PDF",
                [19],
            ),
            (
                "000981-2012-08-20-halfyear.pdf",
                "af46f97b0f73c73cd8444e8e48dd4d6cfefe501246dfabc71b400d1d4be7b56f",
                "https://static.cninfo.com.cn/finalpage/2012-08-20/61440794.PDF",
                [6],
            ),
        ],
    },
}


def close_report(base: dict, closures: dict) -> dict:
    if base["report_version"] != "SZSE_OFFICIAL_ROW_GAPS_V4":
        raise ValueError("WRONG_BASE_REPORT")
    counts = Counter(base["classification_counts"])
    pre2010, later = [], []
    for symbol, item in sorted(closures.items()):
        security_id = f"CN-A:SZSE:{symbol}"
        matched = [r for r in base["unresolved_rows"] if r["security_id"] == security_id]
        if len(matched) != item["expected_rows"] or any(
            r["reason"] != item["previous_reason"]
            or not item["suspended_from"] <= r["date"] < item["first_trading_day"]
            for r in matched
        ):
            raise ValueError(f"SOURCE_INTERVAL_OR_COUNT_CHANGED:{symbol}")
        if item["category"] not in {
            "OFFICIAL_PRE2010_LISTING_SUSPENSION",
            "OFFICIAL_2010PLUS_LISTING_SUSPENSION",
        } or (item["suspended_from"] < "2010-01-01") != (
            item["category"] == "OFFICIAL_PRE2010_LISTING_SUSPENSION"
        ):
            raise ValueError(f"WRONG_LISTING_SUSPENSION_CATEGORY:{symbol}")
        counts[item["previous_reason"]] -= len(matched)
        counts[item["category"]] += len(matched)
        evidence = {
            "security_id": security_id,
            "suspended_from": item["suspended_from"],
            "first_trading_day": item["first_trading_day"],
            "source_absent_rows_closed": len(matched),
            "evidence": item["evidence"],
        }
        (pre2010 if item["suspended_from"] < "2010-01-01" else later).append(evidence)
    remaining = [
        r for r in base["unresolved_rows"] if r["security_id"].split(":")[-1] not in closures
    ]
    if min(counts.values()) < 0 or sum(counts.values()) != base["missing_rows"]:
        raise ValueError("MISSING_ROW_CONSERVATION_FAILED")
    report = {
        **base,
        "report_version": "SZSE_OFFICIAL_ROW_GAPS_V5",
        "parser_sha256": sha(Path(__file__).read_bytes()),
        "base_report_sha256": BASE_SHA,
        "base_manifest_sha256": base["manifest_sha256"],
        "classification_counts": dict(sorted(counts.items())),
        "unresolved_rows": remaining,
        "unresolved_symbols": dict(
            sorted(Counter(r["security_id"].split(":")[-1] for r in remaining).items())
        ),
        "unresolved_by_year": dict(sorted(Counter(r["date"][:4] for r in remaining).items())),
        "additional_official_pre2010_intervals": [
            *base["additional_official_pre2010_intervals"],
            *pre2010,
        ],
        "additional_official_2010plus_intervals": later,
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
