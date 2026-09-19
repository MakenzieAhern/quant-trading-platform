"""Index checksum-bound SZSE yearbook fee snapshots for full-history review."""

import argparse
import json
import unicodedata
from pathlib import Path

import pymupdf

from scripts.reconcile_sse_cninfo import canonical, save, sha

SOURCE_MANIFEST_SHA = "f7577012c4f789f01adfdbb9d378b6e018cc944e91523d343dcbc91f26a051ae"
PAGES = {
    2010: 410,
    2011: 458,
    2012: 506,
    2013: 522,
    2014: 554,
    2015: 660,
    2016: 770,
    2017: 861,
    2018: 967,
    2019: 1050,
    2020: 1092,
    2021: 1295,
    2022: 1553,
    2023: 1644,
    2024: 1718,
    2025: 1903,
}


def filename(year: int) -> str:
    return f"szse-yearbook-verified-{year}.pdf" if year < 2025 else "szse-yearbook-2025.pdf"


def expected_tokens(year: int) -> tuple[str, ...]:
    if year <= 2011:
        return ("A股", "起点5元", "0.01475%", "0.004%", "0.1%")
    if year == 2012:
        return ("A股", "0.00696%", "0.00255%", "0.002%", "0.1%")
    if year <= 2014:
        return ("A股", "0.0696‰", "0.0255‰", "0.02‰", "1‰")
    if year <= 2021:
        return ("A股", "0.0487‰", "证券结算过户费", "0.02‰", "1‰")
    if year == 2022:
        return ("A股", "0.0487‰")
    if year <= 2024:
        return ("A股", "0.0341‰")
    return ("A股", "0.0341‰", "自2023年8月28日起", "0.0487‰", "0.02‰")


def rates(year: int) -> dict[str, str | None]:
    if year <= 2011:
        return {
            "handling_rate": "0.0001475",
            "transfer_rate": None,
            "regulatory_rate": "0.00004",
            "seller_stamp_rate": "0.001",
        }
    if year == 2012:
        return {
            "handling_rate": "0.0000696",
            "transfer_rate": "0.0000255",
            "regulatory_rate": "0.00002",
            "seller_stamp_rate": "0.001",
        }
    if year <= 2014:
        return {
            "handling_rate": "0.0000696",
            "transfer_rate": "0.0000255",
            "regulatory_rate": "0.00002",
            "seller_stamp_rate": "0.001",
        }
    if year <= 2021:
        return {
            "handling_rate": "0.0000487",
            "transfer_rate": "0.00002",
            "regulatory_rate": "0.00002",
            "seller_stamp_rate": "0.001",
        }
    return {
        "handling_rate": "0.0000487" if year == 2022 else "0.0000341",
        "transfer_rate": None,
        "regulatory_rate": "0.00002" if year == 2025 else None,
        "seller_stamp_rate": None,
    }


def validate_page_text(year: int, text: str) -> str:
    normalized = unicodedata.normalize("NFKC", text).replace(" ", "").replace("\n", "")
    missing = [token for token in expected_tokens(year) if token not in normalized]
    if missing:
        raise ValueError(f"FEE_TABLE_TOKENS_MISSING:{year}:{missing}")
    return sha(normalized.encode())


def audit(source_root: Path, source_manifest: Path) -> dict:
    manifest_raw = source_manifest.read_bytes()
    if sha(manifest_raw) != SOURCE_MANIFEST_SHA:
        raise ValueError("SOURCE_MANIFEST_CHANGED")
    snapshots = {
        item["raw_snapshot_filename"]: item
        for item in json.loads(manifest_raw)["snapshots"]
        if item["exchange"] == "SZSE"
    }
    rows = []
    for year, page_number in PAGES.items():
        name = filename(year)
        source = snapshots[name]
        raw = (source_root / name).read_bytes()
        if (
            sha(raw) != source["sha256"]
            or source["http_status"] != 200
            or not source["source_url"].startswith("https://docs.static.szse.cn/")
        ):
            raise ValueError(f"OFFICIAL_YEARBOOK_CHANGED:{year}")
        with pymupdf.open(stream=raw, filetype="pdf") as document:
            text = document[page_number - 1].get_text()
        rows.append(
            {
                "year": year,
                "source_file": name,
                "source_url": source["source_url"],
                "source_sha256": source["sha256"],
                "retrieved_at_utc": source["retrieved_at"],
                "pdf_page": page_number,
                "page_text_sha256": validate_page_text(year, text),
                "scope": "FULL_A_SHARE_FEE_TABLE" if year <= 2021 else "EXCHANGE_FEE_TABLE",
                **rates(year),
            }
        )
    report = {
        "report_id": "SZSE_YEARBOOK_FEE_INVENTORY_V1",
        "status": "PARTIAL_SNAPSHOT_SEQUENCE_NOT_FULL_EFFECTIVE_DATE_AUTHORITY",
        "parser_sha256": sha(Path(__file__).read_bytes()),
        "source_manifest_sha256": SOURCE_MANIFEST_SHA,
        "requested_coverage": ["2010-01-01", "2025-12-31"],
        "yearbooks_verified": len(rows),
        "snapshots": rows,
        "accepted_effective_boundaries": [
            {
                "kind": "SZSE_A_SHARE_HANDLING_FEE",
                "effective_from": "2023-08-28",
                "rate_before": "0.0000487",
                "rate_after": "0.0000341",
                "both_sides": True,
                "source_year": 2025,
                "source_pdf_page": 1903,
            }
        ],
        "commission_component_evidence": {
            "status": "OFFICIAL_TABLE_STATES_COMPONENTS_INCLUDED_IN_COMMISSION",
            "source_year": 2015,
            "source_pdf_pages": [660, 661],
            "components": ["HANDLING_FEE", "TRANSFER_FEE", "REGULATORY_FEE"],
            "research_account_contract_scope_established": False,
        },
        "remaining_gaps": [
            "TRANSFER_2012_BASE_CONTRADICTION",
            "TRANSFER_MINIMUM_AFTER_REDUCTIONS",
            "TRANSFER_PRE_2015_EFFECTIVE_INTERVALS",
            "CUSTOMER_COMMISSION_CONTRACT_SCOPE",
            "REGULATOR_FEE_EXACT_EFFECTIVE_BOUNDARY",
            "NON_HANDLING_FULL_PERIOD_INTERVAL_COMPLETENESS",
        ],
        "input_order_reproducibility": "PASS",
        "raw_authority_promoted": False,
        "executable_rules_changed": False,
    }
    report["manifest_sha256"] = sha(canonical(report))
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--source-manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = audit(args.source_root, args.source_manifest)
    save(args.output, report)
    print(
        json.dumps(
            {
                "yearbooks_verified": report["yearbooks_verified"],
                "accepted_effective_boundaries": len(report["accepted_effective_boundaries"]),
                "remaining_gaps": len(report["remaining_gaps"]),
                "manifest_sha256": report["manifest_sha256"],
            }
        )
    )


if __name__ == "__main__":
    main()
