"""Classify three SZSE no-row histories within official terminal listing suspensions."""

import argparse
import json
from collections import Counter
from pathlib import Path

from scripts.reconcile_sse_cninfo import canonical, save, sha

BASE_SHA = "e450c15f1ff3f3ddbc193106450f51b32bacb3975c0237633dc35b0984ef1b81"
CLOSURES = {
    "000594": {
        "suspended_from": "2014-07-17",
        "terminal_decision_on": "2015-05-21",
        "previous_reason": "UNKNOWN_RESUMPTION_NOT_CLOSED",
        "expected_rows": 37,
        "sources": [
            (
                "000594-2014-07-16-pause.pdf",
                "afcb4083241d9e4a5f83bfd9f5f03c4441aa5f9ebf843a4f2144df97ec21ff9a",
                "https://static.cninfo.com.cn/finalpage/2014-07-16/1200056400.PDF",
                [1],
            ),
            (
                "000594-2015-05-23-termination.pdf",
                "19a88351949005b389769c10a6b09a1c5da3cb789b57bbba6f8b3af0c485a5f6",
                "https://static.cninfo.com.cn/finalpage/2015-05-23/1201050497.PDF",
                [1],
            ),
        ],
    },
    "000787": {
        "suspended_from": "2007-05-24",
        "terminal_decision_on": "2012-12-31",
        "delisted_on": "2013-02-08",
        "previous_reason": "NO_MATCHING_HALT_SOURCE",
        "expected_rows": 114,
        "sources": [
            (
                "000787-2012-06-05-progress.pdf",
                "0c29d413f0d8345387e8804cc8cdf14c0ca81d27e0c27e7478061ea79a08dd63",
                "https://static.cninfo.com.cn/finalpage/2012-06-05/61088317.PDF",
                [1],
            ),
            (
                "000787-2013-02-07-delisting.pdf",
                "65af7790110fa47928b07010106c85f3363f58c59bd8e964c6859fc764bdb13a",
                "https://static.cninfo.com.cn/finalpage/2013-02-07/62119656.PDF",
                [1],
            ),
        ],
    },
    "000805": {
        "suspended_from": "2006-05-15",
        "terminal_decision_on": "2012-12-31",
        "delisted_on": "2013-03-27",
        "previous_reason": "NO_MATCHING_HALT_SOURCE",
        "expected_rows": 212,
        "sources": [
            (
                "000805-2006-05-12-pause.pdf",
                "529332a50231dda2efc965cd887a7ef12d1778217a3c4e63bc7944d8fe35c9ee",
                "https://static.cninfo.com.cn/finalpage/2006-05-12/17064741.PDF",
                [1],
            ),
            (
                "000805-2013-02-01-vote.pdf",
                "8e05048b627b33266b9a66c5fadb3e3c4d69f672ed44873d0aece83f9f92f97d",
                "https://static.cninfo.com.cn/finalpage/2013-02-01/62092767.PDF",
                [2],
            ),
            (
                "000805-2013-03-26-delisting.pdf",
                "43085dd6f37ade095b56fa630447260f327a90803da56e276faf66bfba52578e",
                "https://static.cninfo.com.cn/finalpage/2013-03-26/62270416.PDF",
                [1],
            ),
        ],
    },
}


def close_report(base: dict, closures: dict) -> dict:
    if base["report_version"] != "SZSE_OFFICIAL_ROW_GAPS_V6":
        raise ValueError("WRONG_BASE_REPORT")
    counts = Counter(base["classification_counts"])
    evidence = []
    for symbol, item in sorted(closures.items()):
        security_id = f"CN-A:SZSE:{symbol}"
        matched = [r for r in base["unresolved_rows"] if r["security_id"] == security_id]
        interval_end = item.get("delisted_on", item["terminal_decision_on"])
        if (
            len(matched) != item["expected_rows"]
            or not item["suspended_from"] < interval_end
            or any(
                r["reason"] != item["previous_reason"]
                or not item["suspended_from"] <= r["date"] < interval_end
                for r in matched
            )
        ):
            raise ValueError(f"SOURCE_INTERVAL_OR_COUNT_CHANGED:{symbol}")
        counts[item["previous_reason"]] -= len(matched)
        counts["OFFICIAL_TERMINAL_LISTING_SUSPENSION"] += len(matched)
        evidence.append(
            {
                "security_id": security_id,
                "suspended_from": item["suspended_from"],
                "terminal_decision_on": item["terminal_decision_on"],
                "delisted_on": item.get("delisted_on"),
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
        "report_version": "SZSE_OFFICIAL_ROW_GAPS_V7",
        "parser_sha256": sha(Path(__file__).read_bytes()),
        "base_report_sha256": BASE_SHA,
        "base_manifest_sha256": base["manifest_sha256"],
        "classification_counts": dict(sorted(counts.items())),
        "unresolved_rows": remaining,
        "unresolved_symbols": dict(
            sorted(Counter(r["security_id"].split(":")[-1] for r in remaining).items())
        ),
        "unresolved_by_year": dict(sorted(Counter(r["date"][:4] for r in remaining).items())),
        "additional_official_terminal_intervals": evidence,
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
            pdf = path.read_bytes()
            receipt = json.loads(path.with_name(filename + ".meta.json").read_bytes())
            if (
                not pdf.startswith(b"%PDF-")
                or sha(pdf) != expected_sha
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
