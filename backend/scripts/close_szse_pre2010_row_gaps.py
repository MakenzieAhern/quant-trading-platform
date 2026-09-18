"""Close bounded SZSE pre-2010 suspended listings using archived issuer PDFs."""

import argparse
import json
from collections import Counter
from pathlib import Path

from scripts.reconcile_sse_cninfo import canonical, save, sha

BASE_SHA = "b9d8250bce1fa18362f7c81f78b302a14a5123907ee40499ccca973ef0940719"
CLOSURES = {
    "000403": {
        "suspended_from": "2007-04-27",
        "first_trading_day": "2013-02-08",
        "reasons": {"NO_MATCHING_HALT_SOURCE": 291},
        "file": "000403-2013-02-01-restoration.pdf",
        "sha256": "00b993988fff1d3e1a6bb2b15bf1072a4f34761ee2b672de368af319f1a33788",
        "url": "https://static.cninfo.com.cn/finalpage/2013-02-01/62092773.PDF",
    },
    "000498": {
        "suspended_from": "2008-05-16",
        "first_trading_day": "2013-02-08",
        "reasons": {"NO_MATCHING_HALT_SOURCE": 303},
        "file": "000498-2013-02-01-restoration.pdf",
        "sha256": "e8ab4b451aea1eb97e00ad0f85fdc5ea269d091ed7a537cf1fcd23b85a9a841b",
        "url": "https://static.cninfo.com.cn/finalpage/2013-02-01/62092873.PDF",
    },
    "000622": {
        "suspended_from": "2006-05-15",
        "first_trading_day": "2013-02-08",
        "reasons": {"NO_MATCHING_HALT_SOURCE": 303},
        "file": "000622-2013-02-01-restoration.pdf",
        "sha256": "f9755116574bcf0832f5c67dd6385a81e466553c4fb652abceb4bda8034f6e6a",
        "url": "https://static.cninfo.com.cn/finalpage/2013-02-01/62092904.PDF",
    },
    "000672": {
        "suspended_from": "2007-05-11",
        "first_trading_day": "2013-04-26",
        "reasons": {"NO_MATCHING_HALT_SOURCE": 279},
        "file": "000672-2013-04-19-restoration.pdf",
        "sha256": "9b312f854a97bd04a366a00b40c16967f636a200f21c8a4e4585e002373f2045",
        "url": "https://static.cninfo.com.cn/finalpage/2013-04-19/62385047.PDF",
    },
    "000688": {
        "suspended_from": "2007-05-23",
        "first_trading_day": "2013-04-26",
        "reasons": {"NO_MATCHING_HALT_SOURCE": 30, "UNKNOWN_RESUMPTION_NOT_CLOSED": 273},
        "file": "000688-2013-04-19-restoration.pdf",
        "sha256": "3484e0b1e743718dba043ae8ec2d4c7fea0f5a3cc372a48be66276b06d291b4b",
        "url": "https://static.cninfo.com.cn/finalpage/2013-04-19/62384991.PDF",
    },
    "000757": {
        "suspended_from": "2007-05-23",
        "first_trading_day": "2013-02-08",
        "reasons": {"NO_MATCHING_HALT_SOURCE": 248},
        "file": "000757-2013-02-01-restoration.pdf",
        "sha256": "8ce3a2cef4d1cb477d911d0cbe8fc37a28152b8ffc0ab51330ec7ac1c7038730",
        "url": "https://static.cninfo.com.cn/finalpage/2013-02-01/62092884.PDF",
    },
}


def close_report(base: dict, closures: dict = CLOSURES) -> dict:
    if base["report_version"] != "SZSE_OFFICIAL_ROW_GAPS_V2":
        raise ValueError("WRONG_BASE_REPORT")
    counts = Counter(base["classification_counts"])
    evidence = []
    for symbol, item in sorted(closures.items()):
        security_id = f"CN-A:SZSE:{symbol}"
        matched = [r for r in base["unresolved_rows"] if r["security_id"] == security_id]
        if Counter(r["reason"] for r in matched) != item["reasons"] or any(
            not item["suspended_from"] <= r["date"] < item["first_trading_day"] for r in matched
        ):
            raise ValueError(f"SOURCE_INTERVAL_OR_COUNT_CHANGED:{symbol}")
        counts.subtract(item["reasons"])
        counts["OFFICIAL_PRE2010_LISTING_SUSPENSION"] += len(matched)
        evidence.append(
            {
                "security_id": security_id,
                "suspended_from": item["suspended_from"],
                "first_trading_day": item["first_trading_day"],
                "source_absent_rows_closed": len(matched),
                "source_url": item["url"],
                "source_sha256": item["sha256"],
                "retrieved_at_utc": item["retrieved_at_utc"],
            }
        )
    remaining = [
        r for r in base["unresolved_rows"] if r["security_id"].split(":")[-1] not in closures
    ]
    if min(counts.values()) < 0 or sum(counts.values()) != base["missing_rows"]:
        raise ValueError("MISSING_ROW_CONSERVATION_FAILED")
    report = {
        **base,
        "report_version": "SZSE_OFFICIAL_ROW_GAPS_V3",
        "parser_sha256": sha(Path(__file__).read_bytes()),
        "base_report_sha256": BASE_SHA,
        "base_manifest_sha256": base["manifest_sha256"],
        "classification_counts": dict(sorted(counts.items())),
        "unresolved_rows": remaining,
        "unresolved_symbols": dict(
            sorted(Counter(r["security_id"].split(":")[-1] for r in remaining).items())
        ),
        "unresolved_by_year": dict(sorted(Counter(r["date"][:4] for r in remaining).items())),
        "additional_official_pre2010_intervals": evidence,
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
        path = args.evidence_root / item["file"]
        receipt = json.loads(path.with_name(item["file"] + ".meta.json").read_bytes())
        if (
            sha(path.read_bytes()) != item["sha256"]
            or receipt["sha256"] != item["sha256"]
            or receipt["url"] != item["url"]
            or receipt["http_status"] != 200
            or not receipt["retrieved_at_utc"].endswith("+00:00")
        ):
            raise ValueError(f"OFFICIAL_EVIDENCE_CHANGED:{symbol}")
        item["retrieved_at_utc"] = receipt["retrieved_at_utc"]
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
