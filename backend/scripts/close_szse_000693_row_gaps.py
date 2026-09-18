"""Close 000693's bounded pre-2010 suspended-listing row gaps from issuer notices."""

import argparse
import json
from collections import Counter
from pathlib import Path

from scripts.reconcile_sse_cninfo import canonical, save, sha

BASE_SHA = "5c54e94fc10e35d16c37257aab22afdb47046f6a416418134eab42d17e9ae713"
SECURITY_ID = "CN-A:SZSE:000693"
SUSPENDED_FROM = "2007-05-23"
FIRST_TRADING_DAY = "2014-01-10"
SOURCES = {
    "000693-2013-08-05-pause-history.pdf": (
        "f83c030ba792fac391deadec4957614971b6a38a4980992ec4c79d4b3f6726d7",
        "https://static.cninfo.com.cn/finalpage/2013-08-05/62900545.PDF",
    ),
    "000693-2014-01-10-restoration.pdf": (
        "777a0cbdcb83a3e5c3d1d69918b5d772696e0d9881352d2ff6ac1679f13cb012",
        "https://static.cninfo.com.cn/finalpage/2014-01-10/63471125.PDF",
    ),
}


def close_report(base: dict, evidence: list[dict], expected_rows: int = 461) -> dict:
    if base["report_version"] != "SZSE_OFFICIAL_ROW_GAPS_V1":
        raise ValueError("WRONG_BASE_REPORT")
    rows = base["unresolved_rows"]
    matched = [row for row in rows if row["security_id"] == SECURITY_ID]
    if len(matched) != expected_rows or any(
        row["reason"] != "NO_MATCHING_HALT_SOURCE"
        or not SUSPENDED_FROM <= row["date"] < FIRST_TRADING_DAY
        for row in matched
    ):
        raise ValueError("000693_BOUNDARY_OR_COUNT_CHANGED")
    remaining = [row for row in rows if row["security_id"] != SECURITY_ID]
    counts = Counter(base["classification_counts"])
    counts["NO_MATCHING_HALT_SOURCE"] -= len(matched)
    counts["OFFICIAL_PRE2010_LISTING_SUSPENSION"] += len(matched)
    if min(counts.values()) < 0 or sum(counts.values()) != base["missing_rows"]:
        raise ValueError("MISSING_ROW_CONSERVATION_FAILED")
    report = {
        **base,
        "report_version": "SZSE_OFFICIAL_ROW_GAPS_V2",
        "parser_sha256": sha(Path(__file__).read_bytes()),
        "base_report_sha256": BASE_SHA,
        "base_manifest_sha256": base["manifest_sha256"],
        "classification_counts": dict(sorted(counts.items())),
        "unresolved_rows": remaining,
        "unresolved_symbols": dict(
            sorted(Counter(row["security_id"].split(":")[-1] for row in remaining).items())
        ),
        "unresolved_by_year": dict(sorted(Counter(row["date"][:4] for row in remaining).items())),
        "official_000693_interval": {
            "security_id": SECURITY_ID,
            "suspended_from": SUSPENDED_FROM,
            "first_trading_day": FIRST_TRADING_DAY,
            "source_absent_rows_closed": len(matched),
            "evidence": evidence,
        },
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
    evidence = []
    for filename, (expected_sha, url) in SOURCES.items():
        path = args.evidence_root / filename
        receipt = json.loads(path.with_name(filename + ".meta.json").read_bytes())
        if (
            sha(path.read_bytes()) != expected_sha
            or receipt["sha256"] != expected_sha
            or receipt["url"] != url
            or receipt["http_status"] != 200
            or not receipt["retrieved_at_utc"].endswith("+00:00")
        ):
            raise ValueError(f"OFFICIAL_EVIDENCE_CHANGED:{filename}")
        evidence.append(
            {"url": url, "sha256": expected_sha, "retrieved_at_utc": receipt["retrieved_at_utc"]}
        )
    report = close_report(base, evidence)
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
