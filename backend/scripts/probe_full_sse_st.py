"""Reuse the retained 2009 SSE yearbook for starting risk-state evidence only."""

import argparse
import json
import re
import unicodedata
from collections import Counter
from pathlib import Path

from app.data.catalog.checksums import canonical_json_bytes, canonical_sha256, sha256_file
from app.data.catalog.freeze import write_immutable
from scripts.audit_full_master_baseline import active_codes
from scripts.szse_st_recovery import risk_state


def table_names(pages, kind):
    names = {}
    for page, text in enumerate(pages, 1):
        normalized = unicodedata.normalize("NFKC", text)
        compact = re.sub(r"\s+", "", normalized)
        selected = (
            "ListedCompaniesin2009" in compact and "上市公司基本信息" in compact
            if kind == "company"
            else "发行股本" in compact and "上年收盘" in compact
        )
        if not selected:
            continue
        for code, name in re.findall(
            r"(?m)^(6\d{5})\s+([A-Za-z*\u4e00-\u9fff\s]+?)\s+-?\d", normalized
        ):
            if code in names:
                raise ValueError("DUPLICATE_SSE_YEARBOOK_CODE")
            name = re.sub(r"\s+", "", name)
            names[code] = dict(name=name, source_page=page, status=risk_state(name))
    return names


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--staging", type=Path, required=True)
    parser.add_argument("--report", default="prestart-anchor-v1.json")
    args = parser.parse_args()
    root = args.staging / "full-master-sse-baseline-v1"
    pdf = root / "raw/sse-yearbook-2010.pdf"
    extracted_path = root / "master-text-2010.json"
    extracted = json.loads(extracted_path.read_bytes())
    snapshots = json.loads((root / "source-snapshot-manifest.json").read_bytes())
    source = next(s for s in snapshots["snapshots"] if s["raw_snapshot_filename"] == pdf.name)
    if sha256_file(pdf) != source["sha256"] or extracted["source_sha256"] != source["sha256"]:
        raise ValueError("SSE_YEARBOOK_SOURCE_CHANGED")
    master_path = args.staging / "full-code-transitions-v1/master-code-intervals.json"
    master = json.loads(master_path.read_bytes())
    if master["manifest_sha256"] != canonical_sha256(
        {k: v for k, v in master.items() if k != "manifest_sha256"}
    ):
        raise ValueError("SSE_MASTER_CHANGED")
    eligible = active_codes(master["records"], "SSE")
    if eligible != active_codes(list(reversed(master["records"])), "SSE"):
        raise ValueError("SSE_MASTER_ORDER_CHANGED")
    names = table_names(extracted["pages"], "company")
    prices = table_names(extracted["pages"], "price")
    anchors, conflicts = [], []
    for code in sorted(eligible):
        evidence = names.get(code)
        secondary = prices.get(code)
        if evidence and secondary and evidence["status"] != secondary["status"]:
            conflicts.append(code)
        anchors.append(
            dict(
                symbol=code,
                status=evidence["status"] if evidence else "UNKNOWN",
                as_of="2009-12-31",
                source=evidence,
                trading_table=secondary,
            )
        )
    report = dict(
        parser_version="SSE_2009_PRESTART_RISK_ANCHOR_V1",
        parser_sha256=sha256_file(Path(__file__)),
        anchors=anchors,
        source=source,
        extraction_sha256=sha256_file(extracted_path),
        master_sha256=sha256_file(master_path),
        total=len(anchors),
        states=dict(sorted(Counter(a["status"] for a in anchors).items())),
        missing=sorted(eligible - names.keys()),
        conflicts=conflicts,
        price_table_corroborated=len(eligible & prices.keys()),
        paused_company_table_only=sorted(eligible - prices.keys()),
        noneligible_yearbook_codes=sorted(names.keys() - eligible),
        publication_date=None,
        scope="HISTORICAL_STATE_RECONSTRUCTION_NOT_DOCUMENT_AVAILABILITY_OR_TRADABILITY",
        full_sse_st_authority="PARTIAL_EVENT_CENSUS_PENDING",
        future_name_order_used=False,
        full_dataset_created=False,
    )
    report["manifest_sha256"] = canonical_sha256(report)
    write_immutable(
        args.staging / "full-sse-st-v1" / args.report,
        canonical_json_bytes(report) + b"\n",
    )
    print(json.dumps({k: v for k, v in report.items() if k not in {"anchors", "source"}}))


if __name__ == "__main__":
    main()
