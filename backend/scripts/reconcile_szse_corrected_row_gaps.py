"""Reapply checksum-bound official listing intervals after SZSE date normalization."""

import argparse
import json
from collections import Counter
from pathlib import Path

from scripts.audit_szse_official_row_gaps import SOURCE_REPORT_SHA
from scripts.reconcile_sse_cninfo import canonical, save, sha

PRIOR_SHA = "b44fe8de96244136055a090c03f71644aed226b0c23f99643af1873b05d7ec89"


def close_report(base: dict, prior: dict, base_sha: str) -> dict:
    if (
        base["report_version"] != "SZSE_OFFICIAL_ROW_GAPS_V1"
        or prior["report_version"] != "SZSE_OFFICIAL_ROW_GAPS_V7"
        or base["source_collection_sha256"] != SOURCE_REPORT_SHA
        or base["missing_rows"] != prior["missing_rows"]
        or base["raw_authority_promoted"]
    ):
        raise ValueError("AUDIT_INPUT_CHANGED")
    intervals = [("OFFICIAL_PRE2010_LISTING_SUSPENSION", prior["official_000693_interval"])]
    intervals += [
        ("OFFICIAL_PRE2010_LISTING_SUSPENSION", item)
        for item in prior["additional_official_pre2010_intervals"]
    ]
    intervals += [
        ("OFFICIAL_2010PLUS_LISTING_SUSPENSION", item)
        for item in prior["additional_official_2010plus_intervals"]
    ]
    intervals += [
        ("OFFICIAL_TERMINAL_LISTING_SUSPENSION", item)
        for item in prior["additional_official_terminal_intervals"]
    ]
    by_id = {}
    for category, item in intervals:
        security_id = item["security_id"]
        end = (
            item.get("first_trading_day")
            or item.get("delisted_on")
            or item.get("terminal_decision_on")
        )
        if security_id in by_id or not item["suspended_from"] < end:
            raise ValueError(f"OFFICIAL_INTERVAL_CONFLICT:{security_id}")
        by_id[security_id] = (category, item, end)
    counts = Counter(base["classification_counts"])
    closed = Counter()
    remaining = []
    for row in base["unresolved_rows"]:
        match = by_id.get(row["security_id"])
        if match and match[1]["suspended_from"] <= row["date"] < match[2]:
            counts[row["reason"]] -= 1
            counts[match[0]] += 1
            closed[row["security_id"]] += 1
        else:
            remaining.append(row)
    if (
        min(counts.values()) < 0
        or sum(counts.values()) != base["missing_rows"]
        or Counter(r["reason"] for r in remaining)
        != {
            k: counts[k]
            for k in ("NO_MATCHING_HALT_SOURCE", "UNKNOWN_RESUMPTION_NOT_CLOSED")
            if counts[k]
        }
    ):
        raise ValueError("MISSING_ROW_CONSERVATION_FAILED")
    evidence = [
        {
            **{k: v for k, v in item.items() if k != "source_absent_rows_closed"},
            "prior_closed_rows": item["source_absent_rows_closed"],
            "corrected_closed_rows": closed[item["security_id"]],
            "classification": category,
        }
        for category, item in intervals
    ]
    report = {
        "report_version": "SZSE_OFFICIAL_ROW_GAPS_CORRECTED_V2",
        "status": "PARTIAL_SOURCE_PRESENCE_NOT_RAW_AUTHORITY",
        "parser_sha256": sha(Path(__file__).read_bytes()),
        "corrected_base_report_sha256": base_sha,
        "corrected_base_manifest_sha256": base["manifest_sha256"],
        "superseded_v7_report_sha256": PRIOR_SHA,
        "superseded_v7_manifest_sha256": prior["manifest_sha256"],
        "date_normalization_defect": "SLASH_FORMAT_RESUMPTION_DATE_LEXICAL_COMPARISON",
        "missing_rows": base["missing_rows"],
        "classification_counts": dict(sorted(counts.items())),
        "official_intervals": evidence,
        "unresolved_rows": remaining,
        "unresolved_symbols": dict(
            sorted(Counter(r["security_id"].split(":")[-1] for r in remaining).items())
        ),
        "unresolved_by_year": dict(sorted(Counter(r["date"][:4] for r in remaining).items())),
        "raw_authority_promoted": False,
    }
    report["manifest_sha256"] = sha(canonical(report))
    return report


def verify_evidence(report: dict, root: Path) -> None:
    receipts = {}
    for path in sorted(root.glob("*.pdf.meta.json")):
        meta = json.loads(path.read_bytes())
        if meta.get("sha256"):
            if meta["url"] in receipts and receipts[meta["url"]][1]["sha256"] != meta["sha256"]:
                raise ValueError("CONFLICTING_OFFICIAL_RECEIPTS")
            receipts[meta["url"]] = (Path(str(path).removesuffix(".meta.json")), meta)
    for interval in report["official_intervals"]:
        evidence = interval.get("evidence") or [
            {
                "url": interval["source_url"],
                "sha256": interval["source_sha256"],
                "retrieved_at_utc": interval["retrieved_at_utc"],
            }
        ]
        for item in evidence:
            path, meta = receipts[item["url"]]
            raw = path.read_bytes()
            if (
                not raw.startswith(b"%PDF-")
                or sha(raw) != item["sha256"]
                or meta["sha256"] != item["sha256"]
                or meta["http_status"] != 200
                or meta["retrieved_at_utc"] != item["retrieved_at_utc"]
            ):
                raise ValueError(f"OFFICIAL_INTERVAL_EVIDENCE_CHANGED:{interval['security_id']}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corrected-base", type=Path, required=True)
    parser.add_argument("--prior-report", type=Path, required=True)
    parser.add_argument("--evidence-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    base_raw, prior_raw = args.corrected_base.read_bytes(), args.prior_report.read_bytes()
    base, prior = json.loads(base_raw), json.loads(prior_raw)
    if sha(prior_raw) != PRIOR_SHA:
        raise ValueError("AUDITED_PRIOR_REPORT_CHANGED")
    for report in (base, prior):
        if (
            sha(canonical({k: v for k, v in report.items() if k != "manifest_sha256"}))
            != report["manifest_sha256"]
        ):
            raise ValueError("REPORT_MANIFEST_CHANGED")
    from scripts import audit_szse_official_row_gaps as audit

    if base["parser_sha256"] != sha(Path(audit.__file__).read_bytes()):
        raise ValueError("CORRECTED_AUDIT_PARSER_CHANGED")
    report = close_report(base, prior, sha(base_raw))
    verify_evidence(report, args.evidence_root)
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
