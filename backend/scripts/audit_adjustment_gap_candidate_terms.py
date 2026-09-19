"""Parse retained issuer notices for exact adjustment-gap dates and terms without acceptance."""

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path

import pymupdf

from app.data.catalog.checksums import canonical_json_bytes, canonical_sha256, sha256_file
from app.data.catalog.freeze import write_immutable
from scripts.link_distribution_notices import notice_dates
from scripts.reconcile_cash_gap_candidates import is_final_implementation_document
from scripts.reconcile_distribution_cash import gross_cash, normalized_document
from scripts.retained_bonus_terms import retained_ratio


def classify_document(document: dict, pages: list[str]) -> dict:
    outcome = {
        "issuer": document["issuer"],
        "title": document["title"],
        "url": document["url"],
        "source_sha256": document["source_sha256"],
    }
    text = normalized_document(pages)
    if not is_final_implementation_document(document["title"], text):
        return {**outcome, "status": "NOT_FINAL_IMPLEMENTATION_DOCUMENT"}
    records, ex_dates = notice_dates(pages)
    affected = set(document["affected_factor_changes"])
    matched = [event for event in affected if event.rsplit(":", 1)[-1] in ex_dates]
    if len(records) != 1 or len(ex_dates) != 1 or not matched:
        return {
            **outcome,
            "status": "NOTICE_DATES_NOT_UNIQUE_OR_FACTOR_MISMATCH",
            "record_dates": records,
            "ex_dates": ex_dates,
        }
    terms = {}
    failures = {}
    for name, parser in (("cash_per_share", gross_cash), ("bonus_share_ratio", retained_ratio)):
        try:
            terms[name] = str(parser(pages, document["issuer"]))
        except ValueError as exc:
            failures[name] = str(exc)
    if not terms:
        return {
            **outcome,
            "status": "EXACT_DATE_NO_SUPPORTED_TERMS",
            "record_date": records[0],
            "ex_date": ex_dates[0],
            "term_failures": failures,
        }
    return {
        **outcome,
        "status": "EXACT_DATE_OFFICIAL_TERMS_CANDIDATE",
        "record_date": records[0],
        "ex_date": ex_dates[0],
        **terms,
        "term_failures": failures,
        "matched_factor_changes": sorted(matched),
    }


def cache_index(staging: Path) -> dict[str, Path]:
    paths = sorted(
        staging.glob("**/text*/*.json"),
        key=lambda path: ("text-pymupdf" not in path.parts, str(path)),
    )
    result = {}
    for path in paths:
        if len(path.stem) == 64:
            result.setdefault(path.stem, path)
    return result


def pages_for(
    staging: Path, document: dict, caches: dict[str, Path]
) -> tuple[list[str] | None, dict]:
    source_sha = document["source_sha256"]
    cache = caches.get(source_sha)
    if cache:
        extracted = json.loads(cache.read_bytes())
        if extracted["source_sha256"] != source_sha:
            raise ValueError("TEXT_CACHE_SOURCE_CHANGED")
        return extracted["pages"], {
            "text_source": "RETAINED_EXTRACTION_CACHE",
            "text_path": cache.relative_to(staging).as_posix(),
            "text_sha256": sha256_file(cache),
        }
    pdf = staging / document["source_path"]
    try:
        with pymupdf.open(pdf) as source:
            pages = [page.get_text() for page in source]
    except pymupdf.FileDataError:
        return None, {
            "text_source": "SOURCE_BYTES_NOT_PARSEABLE_AS_PDF",
            "text_path": None,
            "text_sha256": None,
        }
    return pages, {
        "text_source": "DETERMINISTIC_PYMUPDF_FALLBACK",
        "text_path": None,
        "text_sha256": canonical_sha256(pages),
    }


def audit(staging: Path, documents: list[dict], caches: dict[str, Path]) -> dict:
    outcomes = []
    for document in sorted(documents, key=lambda row: (row["url"], row["source_sha256"])):
        pdf = staging / document["source_path"]
        if sha256_file(pdf) != document["source_sha256"]:
            raise ValueError("OFFICIAL_SOURCE_CHANGED")
        pages, receipt = pages_for(staging, document, caches)
        if pages is None:
            outcomes.append(
                {
                    "issuer": document["issuer"],
                    "title": document["title"],
                    "url": document["url"],
                    "source_sha256": document["source_sha256"],
                    "status": "OFFICIAL_SOURCE_PDF_UNREADABLE",
                    **receipt,
                }
            )
            continue
        outcomes.append({**classify_document(document, pages), **receipt})
    by_factor = defaultdict(list)
    for row in outcomes:
        if row["status"] == "EXACT_DATE_OFFICIAL_TERMS_CANDIDATE":
            signature = {
                key: row.get(key)
                for key in ("record_date", "ex_date", "cash_per_share", "bonus_share_ratio")
            }
            for event in row["matched_factor_changes"]:
                by_factor[event].append({**signature, "source_sha256": row["source_sha256"]})
    all_factors = {event for document in documents for event in document["affected_factor_changes"]}
    factor_results = []
    for event in sorted(all_factors):
        evidence = by_factor.get(event, [])
        signatures = {
            canonical_sha256({k: v for k, v in row.items() if k != "source_sha256"})
            for row in evidence
        }
        factor_results.append(
            {
                "factor_change": event,
                "status": (
                    "NO_EXACT_OFFICIAL_TERMS_CANDIDATE"
                    if not evidence
                    else "UNIQUE_EXACT_OFFICIAL_TERMS_CANDIDATE"
                    if len(signatures) == 1
                    else "CONFLICTING_EXACT_OFFICIAL_TERMS_CANDIDATES"
                ),
                "evidence": evidence,
            }
        )
    return {
        "report_id": "FULL_ADJUSTMENT_GAP_OFFICIAL_TERMS_V1",
        "status": "CANDIDATE_TERMS_ONLY_NO_EVENT_OR_AUTHORITY_ACCEPTANCE",
        "documents": outcomes,
        "document_statuses": dict(sorted(Counter(row["status"] for row in outcomes).items())),
        "factor_results": factor_results,
        "factor_statuses": dict(sorted(Counter(row["status"] for row in factor_results).items())),
        "source_documents": len(documents),
        "factor_changes": len(factor_results),
        "dataset_created": False,
        "limitations": [
            "Candidate terms are not CorporateAction events and are not admitted to any ledger.",
            "Correction precedence, registry allocation, lifecycle and full census remain "
            "separate.",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--staging", type=Path, required=True)
    parser.add_argument("--inventory", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    documents = json.loads(args.inventory.read_bytes())
    caches = cache_index(args.staging)
    report = audit(args.staging, documents, caches)
    if report != audit(args.staging, list(reversed(documents)), caches):
        raise ValueError("INPUT_ORDER_CHANGED")
    report.update(
        input_order_reproducibility="PASS",
        inputs=[{"path": str(args.inventory), "sha256": sha256_file(args.inventory)}],
        parser_sha256=sha256_file(Path(__file__)),
    )
    report["manifest_sha256"] = canonical_sha256(report)
    write_immutable(args.output, canonical_json_bytes(report) + b"\n")
    print(
        json.dumps(
            {
                key: report[key]
                for key in (
                    "status",
                    "source_documents",
                    "factor_changes",
                    "document_statuses",
                    "factor_statuses",
                    "manifest_sha256",
                )
            }
        )
    )


if __name__ == "__main__":
    main()
