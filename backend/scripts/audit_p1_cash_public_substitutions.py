"""Reconcile cached official issuer PDFs to unresolved exchange cash facts via OCR."""

from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from datetime import date, timedelta
from decimal import Decimal
from importlib.metadata import version
from pathlib import Path

from app.data.catalog.checksums import canonical_json_bytes, canonical_sha256, sha256_file
from app.data.catalog.freeze import write_immutable
from scripts.link_distribution_notices import notice_dates
from scripts.reconcile_distribution_cash import gross_cash

VERSION = "P1_CASH_PUBLIC_SUBSTITUTION_OCR_V1"
TARGET_TYPE = "FINAL_IMPLEMENTATION_NOTICE_WITH_GROSS_ORDINARY_A_SHARE_CASH"
TARGET = re.compile(r"(\d{6}) (\d{4}-\d{2}-\d{2})\.\.(\d{4}-\d{2}-\d{2})")


def verified(path: Path) -> dict:
    value = json.loads(path.read_bytes())
    expected = value.pop("manifest_sha256")
    if canonical_sha256(value) != expected:
        raise ValueError(f"INPUT_MANIFEST_CHANGED:{path}")
    value["manifest_sha256"] = expected
    return value


def candidates(rows: list[dict], symbol: str, record_date: str) -> list[dict]:
    boundary = date.fromisoformat(record_date)
    return sorted(
        (
            row
            for row in rows
            if row["issuer"] == symbol
            and boundary - timedelta(days=30) <= date.fromisoformat(row["published_on"]) <= boundary
        ),
        key=lambda row: (row["published_on"], row["url"]),
    )


def exchange_cash(sse: dict, szse: dict) -> dict[tuple[str, str, str], set[Decimal]]:
    result: dict[tuple[str, str, str], set[Decimal]] = defaultdict(set)
    for group in sse["groups"]:
        if group["key"][0] != "dividend":
            continue
        for evidence in group["evidence"]:
            row = evidence["normalized"]
            result[row["source_symbol"], row["record_date"], row["ex_date"]].add(
                Decimal(row["amount"])
            )
    for row in szse["rows"]:
        if row["symbol"].startswith(("0", "3")) and row["raw_cells"][5].strip():
            amount = Decimal(row["raw_cells"][5])
            if amount > 0:
                result[row["symbol"], row["record_date"], row["ex_date"]].add(amount)
    return result


def classify(
    pages: list[str], symbol: str, record_date: str, ex_date: str, amounts: set[Decimal]
) -> dict:
    try:
        records, ex_dates = notice_dates(pages)
        date_error = None
    except ValueError as exc:
        records, ex_dates, date_error = [], [], str(exc)
    try:
        amount = gross_cash(pages, symbol)
        cash_error = None
    except ValueError as exc:
        amount, cash_error = None, str(exc)
    exact_dates = records == [record_date] and ex_dates == [ex_date]
    if exact_dates and amount is not None and {amount} == amounts:
        status = "EXACTLY_CORROBORATED"
    elif ((record_date in records or ex_date in ex_dates) and records and ex_dates) or (
        exact_dates and amount is not None
    ):
        status = "OFFICIAL_SOURCE_CONFLICT"
    else:
        status = "TEMPORAL_BOUNDARY_AMBIGUITY"
    return {
        "classification": status,
        "parsed_record_dates": records,
        "parsed_ex_dates": ex_dates,
        "date_parser_error": date_error,
        "parsed_cash_per_share": str(amount) if amount is not None else None,
        "cash_parser_error": cash_error,
    }


def ocr_pages(
    pdf: Path, cache: Path, source_sha256: str, runtime: dict, engine
) -> tuple[list[str], str]:
    if cache.exists():
        value = json.loads(cache.read_bytes())
        if value["source_sha256"] != source_sha256 or value["runtime"] != runtime:
            raise ValueError("OCR_CACHE_IDENTITY_CHANGED")
        return value["pages"], sha256_file(cache)

    import numpy as np
    from pypdfium2 import PdfDocument

    pages = []
    for page in PdfDocument(pdf):
        output = engine(np.array(page.render(scale=2.5).to_pil()))
        pages.append("\n".join(output.txts or []))
    value = {
        "parser_version": VERSION,
        "source_sha256": source_sha256,
        "runtime": runtime,
        "pages": pages,
        "event_acceptance": "NOT_PERFORMED",
    }
    write_immutable(cache, canonical_json_bytes(value) + b"\n")
    return pages, sha256_file(cache)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--requirements", type=Path, required=True)
    parser.add_argument("--metadata", type=Path, required=True)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--source-manifest", type=Path, required=True)
    parser.add_argument("--sse-audit", type=Path, required=True)
    parser.add_argument("--szse-audit", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    args = parser.parse_args()

    import rapidocr
    from rapidocr import RapidOCR

    inputs = [
        args.requirements,
        args.metadata,
        args.source_manifest,
        args.sse_audit,
        args.szse_audit,
    ]
    requirements, metadata, sources, sse, szse = map(verified, inputs)
    metadata_rows = [row for year in metadata["results"] for row in year.get("documents", [])]
    source_rows = {}
    for row in sources["documents"]:
        if row["retrieval_status"] != "PASS":
            continue
        key = row["url"]
        if key in source_rows and source_rows[key]["source_sha256"] != row["source_sha256"]:
            raise ValueError("CONFLICTING_SOURCE_SNAPSHOTS")
        source_rows[key] = row
    amounts = exchange_cash(sse, szse)
    models = sorted((Path(rapidocr.__file__).parent / "models").glob("*.onnx"))
    runtime = {
        "render_scale": "2.5",
        "rapidocr_version": version("rapidocr"),
        "onnxruntime_version": version("onnxruntime"),
        "pypdfium2_version": version("pypdfium2"),
        "models": [{"name": p.name, "sha256": sha256_file(p)} for p in models],
    }
    engine = RapidOCR()

    targets = []
    for row in requirements["documents"]:
        if row["priority"] != "P1" or TARGET_TYPE not in row["required_document_types"]:
            continue
        match = TARGET.match(row["expected_filename_or_title"])
        if not match:
            raise ValueError("CASH_REQUIREMENT_IDENTITY_INVALID")
        symbol, record_date, ex_date = match.groups()
        targets.append((row, symbol, record_date, ex_date))

    results = []
    for number, (requirement, symbol, record_date, ex_date) in enumerate(targets, 1):
        key = symbol, record_date, ex_date
        if key not in amounts:
            raise ValueError(f"EXCHANGE_CASH_FACT_MISSING:{key}")
        evidence = []
        for candidate in candidates(metadata_rows, symbol, record_date):
            source = source_rows.get(candidate["url"])
            if not source:
                evidence.append({**candidate, "classification": "MISSING"})
                continue
            pdf = (args.source_root / source["source_path"]).resolve()
            if (
                not pdf.is_relative_to(args.source_root.resolve())
                or sha256_file(pdf) != source["source_sha256"]
            ):
                raise ValueError("SOURCE_CHECKSUM_MISMATCH")
            cache = args.output_root / "ocr" / f"{source['source_sha256']}.json"
            pages, cache_sha256 = ocr_pages(pdf, cache, source["source_sha256"], runtime, engine)
            evidence.append(
                {
                    **candidate,
                    "source_sha256": source["source_sha256"],
                    "retrieved_at_utc": source["retrieved_at_utc"],
                    "ocr_cache_sha256": cache_sha256,
                    **classify(pages, symbol, record_date, ex_date, amounts[key]),
                }
            )
        exact = [row for row in evidence if row["classification"] == "EXACTLY_CORROBORATED"]
        conflicts = [row for row in evidence if row["classification"] == "OFFICIAL_SOURCE_CONFLICT"]
        if exact:
            classification = "EXACTLY_CORROBORATED"
        elif conflicts:
            classification = "OFFICIAL_SOURCE_CONFLICT"
        elif evidence:
            classification = "TEMPORAL_BOUNDARY_AMBIGUITY"
        else:
            classification = "MISSING"
        results.append(
            {
                "document_id": requirement["document_id"],
                "affected_events": requirement["affected_events"],
                "symbol": symbol,
                "record_date": record_date,
                "ex_date": ex_date,
                "exchange_cash_per_share": sorted(str(value) for value in amounts[key]),
                "classification": classification,
                "evidence": evidence,
            }
        )
        print(number, len(targets), symbol, record_date, classification, flush=True)

    results.sort(key=lambda row: (row["symbol"], row["record_date"], row["document_id"]))
    classifications = {
        name: sum(row["classification"] == name for row in results)
        for name in (
            "EXACTLY_CORROBORATED",
            "SINGLE_OFFICIAL_SOURCE",
            "OFFICIAL_SOURCE_CONFLICT",
            "TEMPORAL_BOUNDARY_AMBIGUITY",
            "MISSING",
        )
    }
    report = {
        "report_version": VERSION,
        "search_window_days": 30,
        "runtime": runtime,
        "inputs": [{"path": str(path), "sha256": sha256_file(path)} for path in inputs],
        "requirements": len(results),
        "classifications": classifications,
        "resolved_by_official_substitution": classifications["EXACTLY_CORROBORATED"],
        "unresolved": len(results) - classifications["EXACTLY_CORROBORATED"],
        "results": results,
        "input_order_reproducibility": "PASS",
        "full_dataset_created": False,
        "limitations": [
            "OCR_IS_ACCEPTED_ONLY_WHEN_ISSUER_DATES_AND_GROSS_CASH_MATCH_EXCHANGE_FACTS_EXACTLY",
            "SEARCH_WINDOW_SELECTS_CANDIDATES_ONLY_AND_NEVER_SUPPLIES_EVENT_DATES",
        ],
    }
    report["manifest_sha256"] = canonical_sha256(report)
    output = args.output_root / "p1-cash-public-substitution-v1.json"
    write_immutable(output, canonical_json_bytes(report) + b"\n")
    print(json.dumps({k: v for k, v in report.items() if k not in {"results", "inputs"}}))


if __name__ == "__main__":
    main()
