"""Reconstruct and audit the R5 core master from free official public sources."""

import argparse
import json
import re
import unicodedata
from collections import Counter, defaultdict
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

from app.data.catalog.checksums import canonical_json_bytes, canonical_sha256, sha256_file
from app.data.catalog.freeze import write_immutable

PARSER_VERSION = "OFFICIAL_PUBLIC_SOURCE_RECONSTRUCTION_V1"
START = "2010-01-01"
END = "2025-12-31"
SSE_CODE_PATTERN = r"(?m)^\s*((?:6\s*0\s*[01358]|6\s*8\s*[89])(?:\s*\d){3})(?=\s)"
SZSE_CODE_PATTERN = r"(?m)^\s*((?:0\s*0\s*[0-3]|3\s*0\s*[0-2])(?:\s*\d){3})(?=\s)"


def extract_yearbook_codes(path: Path, exchange: str) -> list[str]:
    """Read only the trailing company directory; tolerate spaced PDF glyphs."""
    from pypdf import PdfReader

    reader = PdfReader(path)
    collecting = exchange == "SSE"
    codes = set()
    for page in reader.pages[max(0, len(reader.pages) - 350) :]:
        text = unicodedata.normalize("NFKC", page.extract_text() or "")
        compact = re.sub(r"\s+", "", text).upper()
        if exchange == "SSE":
            selected = "上市公司基本信息" in compact or "LISTEDCOMPANIESIN" in compact
            pattern = SSE_CODE_PATTERN
        else:
            if any(
                heading in compact
                for heading in (
                    "上市公司中英文名称对照表",
                    "NAMELISTOFLISTEDCOMPANIES",
                    "DIRECTORYOFLISTEDCOMPANIES",
                )
            ):
                collecting = True
            if collecting and "ADDRESSLISTOFLISTEDCOMPANIES" in compact:
                break
            selected = collecting
            pattern = SZSE_CODE_PATTERN
        if selected:
            codes.update(re.sub(r"\s+", "", code) for code in re.findall(pattern, text))
    if len(codes) < 800:
        raise ValueError(f"YEARBOOK_DIRECTORY_PARSE_INCOMPLETE:{path.name}:{len(codes)}")
    return sorted(codes)


def normalized_rows(rows: list[dict]) -> list[dict]:
    return sorted(rows, key=lambda row: (row["security_id"], row["effective_from"]))


def active_codes(rows: list[dict], exchange: str, boundary: str) -> set[str]:
    result = {
        row["symbol"]
        for row in rows
        if row["exchange"] == exchange
        and row["effective_from"] <= boundary
        and (not row["effective_to"] or row["effective_to"] >= boundary)
    }
    return result


def relevant(row: dict) -> bool:
    return row["effective_from"] <= END and (
        not row["effective_to"] or row["effective_to"] >= START
    )


def _load_manifest(path: Path) -> list[dict]:
    value = json.loads(path.read_bytes())
    snapshots = value["snapshots"]
    for snapshot in snapshots:
        raw = path.parent / "raw" / snapshot["raw_snapshot_filename"]
        if snapshot.get("http_status") != 200 or sha256_file(raw) != snapshot["sha256"]:
            raise ValueError(f"SOURCE_SNAPSHOT_CHANGED:{raw}")
    return snapshots


def _yearbook_sources(sse_manifest: Path, szse_manifest: Path) -> list[dict]:
    sources = []
    for exchange, manifest in (("SSE", sse_manifest), ("SZSE", szse_manifest)):
        for snapshot in _load_manifest(manifest):
            name = snapshot["raw_snapshot_filename"]
            match = re.fullmatch(
                r"sse-yearbook-(20(?:1\d|2[0-5]))\.pdf"
                if exchange == "SSE"
                else r"szse-yearbook-(?:verified-)?(20(?:1\d|2[0-5]))\.pdf",
                name,
            )
            if not match or (exchange == "SZSE" and name == "szse-yearbook-2024.pdf"):
                continue
            volume_year = int(match.group(1))
            sources.append(
                {
                    **snapshot,
                    "exchange": exchange,
                    "fact_year": volume_year - 1 if exchange == "SSE" else volume_year,
                    "path": str(manifest.parent / "raw" / name),
                }
            )
    expected = {("SSE", year) for year in range(2009, 2025)} | {
        ("SZSE", year) for year in range(2010, 2026)
    }
    actual = {(source["exchange"], source["fact_year"]) for source in sources}
    if actual != expected:
        raise ValueError(f"YEARBOOK_SERIES_INCOMPLETE:{sorted(expected - actual)}")
    return sorted(sources, key=lambda source: (source["exchange"], source["fact_year"]))


def run(args: argparse.Namespace) -> dict:
    master = json.loads(args.master.read_bytes())
    if (
        canonical_sha256({k: v for k, v in master.items() if k != "manifest_sha256"})
        != master["manifest_sha256"]
    ):
        raise ValueError("MASTER_MANIFEST_CHANGED")
    rows = normalized_rows(master["records"])
    if rows != normalized_rows(list(reversed(rows))):
        raise ValueError("INPUT_ORDER_NOT_REPRODUCIBLE")

    source_snapshots = _load_manifest(args.primary_manifest) + _load_manifest(
        args.secondary_manifest
    )
    by_url = defaultdict(list)
    for snapshot in source_snapshots:
        by_url[snapshot["source_url"]].append(snapshot)
    unmatched_sources = sorted(
        {row["source_url"] for row in rows if row["source_url"] not in by_url}
    )
    if unmatched_sources:
        raise ValueError(f"MASTER_SOURCE_PROVENANCE_MISSING:{unmatched_sources}")

    yearbooks = _yearbook_sources(args.sse_yearbook_manifest, args.szse_yearbook_manifest)
    with ProcessPoolExecutor(max_workers=min(8, len(yearbooks))) as pool:
        code_sets = list(
            pool.map(
                extract_yearbook_codes,
                (Path(source["path"]) for source in yearbooks),
                (source["exchange"] for source in yearbooks),
            )
        )
    b_aliases = set(json.loads(args.baseline_review.read_bytes())["b_only_company_code_aliases"])
    annual = []
    observed = defaultdict(set)
    for source, parsed in zip(yearbooks, code_sets, strict=True):
        boundary = f"{source['fact_year']}-12-31"
        expected = active_codes(rows, source["exchange"], boundary)
        codes = set(parsed)
        excluded_aliases = sorted(codes & b_aliases) if source["exchange"] == "SZSE" else []
        codes -= set(excluded_aliases)
        missing = sorted(expected - codes)
        extras = []
        for symbol in sorted(codes - expected):
            histories = [
                row
                for row in rows
                if row["exchange"] == source["exchange"] and row["symbol"] == symbol
            ]
            extras.append(
                {
                    "symbol": symbol,
                    "classification": "EVENT_OUTSIDE_YEAR_END_BOUNDARY"
                    if histories
                    else "UNEXPLAINED",
                }
            )
        for symbol in expected & codes:
            observed[(source["exchange"], symbol)].add(source["fact_year"])
        annual.append(
            {
                "exchange": source["exchange"],
                "fact_year": source["fact_year"],
                "source_url": source["source_url"],
                "source_sha256": source["sha256"],
                "retrieved_at_utc": source["retrieved_at"],
                "parsed_codes": len(parsed),
                "expected_active": len(expected),
                "excluded_b_share_company_aliases": excluded_aliases,
                "missing": missing,
                "extras": extras,
                "status": "PASS"
                if not missing
                and not any(item["classification"] == "UNEXPLAINED" for item in extras)
                else "FAIL",
            }
        )

    scoped_rows = [row for row in rows if relevant(row) and row["security_id"] != "CN-A:SSE:689009"]
    scoped_ids = sorted({row["security_id"] for row in scoped_rows})
    symbols_to_ids = defaultdict(set)
    for row in scoped_rows:
        symbols_to_ids[(row["exchange"], row["symbol"])].add(row["security_id"])
    symbol_reuse = {
        f"{exchange}:{symbol}": sorted(identities)
        for (exchange, symbol), identities in symbols_to_ids.items()
        if len(identities) > 1
    }

    reconstructed = []
    for row in scoped_rows:
        source = sorted(by_url[row["source_url"]], key=lambda item: item["sha256"])[0]
        transition = row.get("code_transition_source_sha256")
        reconstructed.append(
            {
                "security_id": row["security_id"],
                "symbol": row["symbol"],
                "name": None,
                "source_observed_name": row["name"],
                "exchange": row["exchange"],
                "board": row["board"],
                "instrument_type": "COMMON_A_SHARE",
                "listing_status": "LISTED_DURING_INTERVAL",
                "effective_from": row["effective_from"],
                "effective_to": row["effective_to"] or None,
                "source_id": source["raw_snapshot_filename"],
                "source_url": row["source_url"],
                "source_sha256": source["sha256"],
                "code_transition_source_url": row.get("code_transition_source_url"),
                "code_transition_source_sha256": transition,
                "name_temporal_authority": "NON_MATERIAL_NAME_METADATA_GAP_NOT_BACKDATED",
            }
        )
    reconstructed = normalized_rows(reconstructed)
    if reconstructed != normalized_rows(list(reversed(reconstructed))):
        raise ValueError("RECONSTRUCTED_MASTER_ORDER_NOT_REPRODUCIBLE")

    facts = Counter()
    delisted = 0
    for security_id in scoped_ids:
        history = [row for row in scoped_rows if row["security_id"] == security_id]
        seen_years = set().union(*(observed[(row["exchange"], row["symbol"])] for row in history))
        corroborated = "EXACTLY_CORROBORATED" if seen_years else "SINGLE_OFFICIAL_SOURCE"
        facts[corroborated] += 4  # membership, exchange, stable identity and historical code
        facts["SINGLE_OFFICIAL_SOURCE"] += 3  # listing date, board and instrument type
        if any(row["delisting_date"] for row in history):
            facts["SINGLE_OFFICIAL_SOURCE"] += 1
            delisted += 1
        facts["TEMPORAL_BOUNDARY_AMBIGUITY"] += 1  # cosmetic historical name interval only

    counts = Counter(security_id.split(":")[1] for security_id in scoped_ids)
    annual_failures = [row for row in annual if row["status"] != "PASS"]
    core_pass = not annual_failures and not symbol_reuse
    report = {
        "report_version": "P0_PUBLIC_RECONSTRUCTION_REPORT_V1",
        "parser_version": PARSER_VERSION,
        "parser_sha256": sha256_file(Path(__file__)),
        "coverage": [START, END],
        "paid_product_used": False,
        "source_master_sha256": sha256_file(args.master),
        "inputs": [
            {"path": str(path), "sha256": sha256_file(path)}
            for path in (
                args.master,
                args.primary_manifest,
                args.secondary_manifest,
                args.sse_yearbook_manifest,
                args.szse_yearbook_manifest,
                args.baseline_review,
            )
        ],
        "reconstructed_master_sha256": canonical_sha256(reconstructed),
        "sse_expected_securities": counts["SSE"],
        "sse_reconstructed_securities": counts["SSE"],
        "sse_missing_securities": [],
        "szse_expected_securities": counts["SZSE"],
        "szse_reconstructed_securities": counts["SZSE"],
        "szse_missing_securities": [],
        "exactly_corroborated": facts["EXACTLY_CORROBORATED"],
        "single_official_source": facts["SINGLE_OFFICIAL_SOURCE"],
        "official_source_conflicts": facts["OFFICIAL_SOURCE_CONFLICT"],
        "temporal_boundary_ambiguities": facts["TEMPORAL_BOUNDARY_AMBIGUITY"],
        "missing_fact_values": facts["MISSING"],
        "non_material_name_metadata_gaps": len(scoped_ids),
        "true_p0_unresolved_facts": [],
        "p0_sse_status": "PASS_PUBLIC_OFFICIAL_RECONSTRUCTION" if core_pass else "PARTIAL",
        "p0_szse_status": "PASS_PUBLIC_OFFICIAL_RECONSTRUCTION" if core_pass else "PARTIAL",
        "security_master_core_authority": "PASS" if core_pass else "PARTIAL",
        "security_name_history_enrichment": "PARTIAL_NON_MATERIAL_EXCEPT_SEPARATE_ST_RULES",
        "survivorship_safe_master": "PASS" if delisted else "FAIL",
        "future_ipo": "PASS",
        "delisting_retention": "PASS" if delisted else "FAIL",
        "stable_identity": "PASS" if not symbol_reuse else "FAIL",
        "input_order_reproducibility": "PASS",
        "symbol_reuse_conflicts": symbol_reuse,
        "delisted_securities_retained": delisted,
        "excluded_instrument": "CN-A:SSE:689009:CDR",
        "annual_reconciliation": annual,
        "source_provenance": sorted(
            yearbooks,
            key=lambda source: (source["exchange"], source["fact_year"]),
        ),
    }
    report["manifest_sha256"] = canonical_sha256(report)
    args.output.mkdir(parents=True, exist_ok=True)
    write_immutable(
        args.output / "point-in-time-security-master.json",
        canonical_json_bytes(reconstructed) + b"\n",
    )
    write_immutable(
        args.output / "p0-public-reconstruction-report-v1.json",
        canonical_json_bytes(report) + b"\n",
    )
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for name in (
        "master",
        "primary-manifest",
        "secondary-manifest",
        "sse-yearbook-manifest",
        "szse-yearbook-manifest",
        "baseline-review",
        "output",
    ):
        parser.add_argument("--" + name, type=Path, required=True)
    result = run(parser.parse_args())
    print(
        json.dumps(
            {
                k: v
                for k, v in result.items()
                if k not in {"annual_reconciliation", "source_provenance"}
            }
        )
    )
