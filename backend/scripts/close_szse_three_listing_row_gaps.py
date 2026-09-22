"""Reconcile three SZSE no-row histories to official suspended-listing bounds."""

import argparse
import json
from collections import Counter
from pathlib import Path

from scripts.reconcile_sse_cninfo import canonical, save, sha

BASE_SHA = "9f42a73d16e70d9665fd9966718c93a131aa0789cc81a7ad4d259a478232c1b1"
CLOSURES = {
    "000038": {
        "suspended_from": "2007-05-22",
        "first_trading_day": "2013-02-08",
        "expected_rows": 241,
        "sources": [
            (
                "000038-2013-02-01-restoration.pdf",
                "87c793d029956f2ed8eef76fc6b2fa694c3f9eeb6e9bbb1b3d29f8d0fb42819e",
                "https://static.cninfo.com.cn/finalpage/2013-02-01/62092809.PDF",
                [2, 48],
            )
        ],
    },
    "000670": {
        "suspended_from": "2007-05-25",
        "first_trading_day": "2013-02-08",
        "expected_rows": 217,
        "sources": [
            (
                "000670-2013-02-01-sponsor.pdf",
                "821212968e539e36968d0a0c482a2aa54f97cb395ba09c2ae6ae223b40b02ac2",
                "https://static.cninfo.com.cn/finalpage/2013-02-01/62092765.PDF",
                [23],
            ),
            (
                "000670-2014-08-29-halfyear.pdf",
                "eff0ffdd292adf2bd326db32ebf1ab2b193feb777bde5064e815ebe1f9e7db8e",
                "https://static.cninfo.com.cn/finalpage/2014-08-29/1200184709.PDF",
                [52],
            ),
        ],
    },
    "000719": {
        "suspended_from": "2008-01-31",
        "first_trading_day": "2011-12-02",
        "expected_rows": 225,
        "sources": [
            (
                "000719-2013-04-23-sponsor.pdf",
                "fafbe34c9b634b1a279f3d6481a0ef8af9774b1ad57bed00ef6450937c4be3eb",
                "https://static.cninfo.com.cn/finalpage/2013-04-23/62402633.PDF",
                [1],
            ),
            (
                "000719-2014-04-15-annual.pdf",
                "460822249cda1bb81bdbb9ad9eaf4978f172956881e8655601da5ce746083515",
                "https://static.cninfo.com.cn/finalpage/2014-04-15/63838946.PDF",
                [81],
            ),
        ],
    },
}


def close_report(base: dict, closures: dict) -> dict:
    if base["report_version"] != "SZSE_OFFICIAL_ROW_GAPS_V3":
        raise ValueError("WRONG_BASE_REPORT")
    counts = Counter(base["classification_counts"])
    evidence = []
    for symbol, item in sorted(closures.items()):
        security_id = f"CN-A:SZSE:{symbol}"
        matched = [r for r in base["unresolved_rows"] if r["security_id"] == security_id]
        if len(matched) != item["expected_rows"] or any(
            r["reason"] != "NO_MATCHING_HALT_SOURCE"
            or not item["suspended_from"] <= r["date"] < item["first_trading_day"]
            for r in matched
        ):
            raise ValueError(f"SOURCE_INTERVAL_OR_COUNT_CHANGED:{symbol}")
        counts["NO_MATCHING_HALT_SOURCE"] -= len(matched)
        counts["OFFICIAL_PRE2010_LISTING_SUSPENSION"] += len(matched)
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
        "report_version": "SZSE_OFFICIAL_ROW_GAPS_V4",
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
            *evidence,
        ],
        "closure_scope": "SOURCE_ABSENCE_ONLY_NOT_EXECUTION_AUTHORITY",
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
            receipt = json.loads(path.with_name(filename + ".meta.json").read_bytes())
            if (
                not path.read_bytes().startswith(b"%PDF-")
                or sha(path.read_bytes()) != expected_sha
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
