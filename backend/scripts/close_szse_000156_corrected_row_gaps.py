"""Close 000156 source-absence dates with a checksum-bound official suspension history."""

import argparse
import json
from collections import Counter
from pathlib import Path

from scripts.reconcile_sse_cninfo import canonical, save, sha

BASE_SHA = "23038aa4068abddaf475ba027c3afa78e0a0bd4e1424337f3ee045eea1f3982b"
PDF_SHA = "807f2d79b15e88af65ea5ed0e0083704305795ea05f9b07a9606b4e8d6026110"
PDF_URL = "https://disc.static.szse.cn/disc/disk02/finalpage/2020-11-04/469619a9-fd8e-48e3-99c4-e5719feeb1d5.PDF"
SECURITY_ID = "CN-A:SZSE:000156"
START = "2006-04-13"
END = "2012-10-19"


def close_report(base: dict, evidence: dict, expected_rows: int = 665) -> dict:
    if (
        base["report_version"] != "SZSE_OFFICIAL_ROW_GAPS_CORRECTED_V2"
        or base["raw_authority_promoted"]
    ):
        raise ValueError("WRONG_BASE_REPORT")
    if any(i["security_id"] == SECURITY_ID for i in base["official_intervals"]):
        raise ValueError("DUPLICATE_OFFICIAL_INTERVAL")
    matched = [r for r in base["unresolved_rows"] if r["security_id"] == SECURITY_ID]
    if (
        len(matched) != expected_rows
        or len({r["date"] for r in matched}) != expected_rows
        or any(
            r["reason"] != "NO_MATCHING_HALT_SOURCE" or not START <= r["date"] < END
            for r in matched
        )
    ):
        raise ValueError("SOURCE_INTERVAL_OR_COUNT_CHANGED:000156")
    counts = Counter(base["classification_counts"])
    counts["NO_MATCHING_HALT_SOURCE"] -= len(matched)
    counts["OFFICIAL_PRE2010_LISTING_SUSPENSION"] += len(matched)
    remaining = [r for r in base["unresolved_rows"] if r["security_id"] != SECURITY_ID]
    if min(counts.values()) < 0 or sum(counts.values()) != base["missing_rows"]:
        raise ValueError("MISSING_ROW_CONSERVATION_FAILED")
    report = {
        **base,
        "report_version": "SZSE_OFFICIAL_ROW_GAPS_CORRECTED_V3",
        "parser_sha256": sha(Path(__file__).read_bytes()),
        "base_report_sha256": BASE_SHA,
        "base_manifest_sha256": base["manifest_sha256"],
        "classification_counts": dict(sorted(counts.items())),
        "official_intervals": [
            *base["official_intervals"],
            {
                "security_id": SECURITY_ID,
                "suspended_from": START,
                "first_trading_day": END,
                "corrected_closed_rows": len(matched),
                "classification": "OFFICIAL_PRE2010_LISTING_SUSPENSION",
                "evidence_temporality": "RETROSPECTIVE_2020_ISSUER_REPORT_NOT_SIGNAL_INPUT",
                "evidence": [evidence],
            },
        ],
        "unresolved_rows": remaining,
        "unresolved_symbols": dict(
            sorted(Counter(r["security_id"].split(":")[-1] for r in remaining).items())
        ),
        "unresolved_by_year": dict(sorted(Counter(r["date"][:4] for r in remaining).items())),
        "raw_authority_promoted": False,
    }
    report.pop("manifest_sha256")
    report["manifest_sha256"] = sha(canonical(report))
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-report", type=Path, required=True)
    parser.add_argument("--official-pdf", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    base_raw = args.base_report.read_bytes()
    base = json.loads(base_raw)
    if (
        sha(base_raw) != BASE_SHA
        or sha(canonical({k: v for k, v in base.items() if k != "manifest_sha256"}))
        != base["manifest_sha256"]
    ):
        raise ValueError("AUDITED_BASE_REPORT_CHANGED")
    pdf_raw = args.official_pdf.read_bytes()
    receipt = json.loads(
        args.official_pdf.with_name(args.official_pdf.name + ".meta.json").read_bytes()
    )
    if (
        not pdf_raw.startswith(b"%PDF-")
        or sha(pdf_raw) != PDF_SHA
        or receipt["sha256"] != PDF_SHA
        or receipt["url"] != PDF_URL
        or receipt["http_status"] != 200
        or not receipt["retrieved_at_utc"].endswith("+00:00")
    ):
        raise ValueError("OFFICIAL_EVIDENCE_CHANGED:000156")
    evidence = {
        "url": PDF_URL,
        "sha256": PDF_SHA,
        "retrieved_at_utc": receipt["retrieved_at_utc"],
        "pdf_pages": [93, 94],
    }
    report = close_report(base, evidence)
    save(args.output, report)
    print(
        json.dumps(
            {
                "classification_counts": report["classification_counts"],
                "unresolved_rows": len(report["unresolved_rows"]),
                "unresolved_symbols": len(report["unresolved_symbols"]),
                "manifest_sha256": report["manifest_sha256"],
            }
        )
    )


if __name__ == "__main__":
    main()
