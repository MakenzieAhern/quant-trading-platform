"""Close cash-source gaps with exact issuer amount plus official exchange dates."""

import argparse
import json
from collections import Counter
from decimal import Decimal
from pathlib import Path

from app.data.catalog.checksums import canonical_json_bytes, canonical_sha256, sha256_file
from app.data.catalog.freeze import write_immutable
from scripts.audit_full_cash_ledger import official_targets
from scripts.audit_p1_orphan_cash_facts import select
from scripts.audit_p1_public_fact_requirements import verified
from scripts.link_distribution_notices import notice_dates
from scripts.reconcile_distribution_cash import differentiated_cash, gross_cash


def classify_dates(
    row: dict, records: list[str], ex_dates: list[str], *, differentiated: bool = False
) -> str | None:
    if differentiated and records == [row["record_date"]] and ex_dates == [row["ex_date"]]:
        return "DIFFERENTIATED_PUBLIC_A_EXACT_ISSUER_DATES"
    if (
        (not records or records == [row["record_date"]])
        and (not ex_dates or ex_dates == [row["ex_date"]])
        and (not records or not ex_dates)
    ):
        result = "OFFICIAL_ISSUER_AMOUNT_PLUS_OFFICIAL_EXCHANGE_DATES"
        return "DIFFERENTIATED_PUBLIC_A_" + result if differentiated else result
    if (
        row["record_date"] in records
        and row["ex_date"] in ex_dates
        and (len(records) > 1 or len(ex_dates) > 1)
    ):
        result = "OFFICIAL_EXCHANGE_DISAMBIGUATED_ISSUER_DATE_SET"
        return "DIFFERENTIATED_PUBLIC_A_" + result if differentiated else result
    return None


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--requirements", type=Path, required=True)
    parser.add_argument("--public-queue", type=Path, required=True)
    parser.add_argument("--public-reassessment", type=Path, required=True)
    parser.add_argument("--cash-ledger", type=Path, required=True)
    parser.add_argument("--master", type=Path, required=True)
    parser.add_argument("--instruments", type=Path, required=True)
    parser.add_argument("--sse-audit", type=Path, required=True)
    parser.add_argument("--szse-audit", type=Path, required=True)
    parser.add_argument("--source-manifest", type=Path, required=True)
    parser.add_argument("--text-root", type=Path, required=True)
    parser.add_argument("--strict-report", type=Path, required=True)
    parser.add_argument("--staging", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    requirements, reassessment, cash, instruments, sse, szse, sources, strict = (
        verified(path)
        for path in (
            args.requirements,
            args.public_reassessment,
            args.cash_ledger,
            args.instruments,
            args.sse_audit,
            args.szse_audit,
            args.source_manifest,
            args.strict_report,
        )
    )
    public = json.loads(args.public_queue.read_bytes())
    master = json.loads(args.master.read_bytes())
    for name, path in (
        ("requirements", args.requirements),
        ("public_queue", args.public_queue),
        ("public_reassessment", args.public_reassessment),
        ("cash_ledger", args.cash_ledger),
        ("master", args.master),
        ("source_manifest", args.source_manifest),
    ):
        if strict["input_sha256s"][name] != sha256_file(path):
            raise ValueError("P1_STRICT_SOURCE_INPUT_CHANGED")
    closed_ids = {row["document_id"] for row in strict["closed"]}
    instrument_types = {
        row["classification"]["security_id"]["value"]: row["classification"]["instrument_type"]
        for row in instruments["classifications"]
    }
    targets, _ = official_targets(master, instrument_types, sse, szse)
    inputs = (
        requirements["documents"],
        public,
        reassessment["out_of_scope_cninfo_documents"],
        cash["events"],
        master,
        sources["documents"],
    )
    candidates = select(*inputs)
    if candidates != select(*(list(reversed(rows)) for rows in inputs)):
        raise ValueError("INPUT_ORDER_CHANGED")
    source_titles = {row["url"]: row["title"] for row in sources["documents"]}
    if len(source_titles) != len(sources["documents"]):
        raise ValueError("DUPLICATE_OFFICIAL_SOURCE_URL")
    reversed_targets, _ = official_targets(
        list(reversed(master)),
        instrument_types,
        {**sse, "groups": list(reversed(sse["groups"]))},
        {**szse, "rows": list(reversed(szse["rows"]))},
    )
    if targets != reversed_targets:
        raise ValueError("EXCHANGE_INPUT_ORDER_CHANGED")
    closed, rejected = [], []
    for row in candidates:
        if row["document_id"] in closed_ids:
            continue
        rejection = {
            "document_id": row["document_id"],
            "substitute_source_url": row["substitute_source_url"],
            "substitute_source_sha256": row["substitute_source_sha256"],
        }
        key = row["security_id"], row["record_date"], row["ex_date"]
        if key not in targets:
            rejected.append({**rejection, "reason": "NO_EXACT_OFFICIAL_EXCHANGE_TARGET"})
            continue
        pdf = Path(row["substitute_source_path"])
        if not pdf.is_absolute():
            pdf = args.source_manifest.parent.parent / pdf
        pdf = pdf.resolve()
        cache = args.text_root / f"{row['substitute_source_sha256']}.json"
        if (
            not pdf.is_relative_to(args.staging.resolve())
            or sha256_file(pdf) != row["substitute_source_sha256"]
            or not cache.is_file()
        ):
            raise ValueError("P1_COMPOSITE_OFFICIAL_SOURCE_CHANGED")
        extracted = json.loads(cache.read_bytes())
        if extracted["source_sha256"] != row["substitute_source_sha256"]:
            raise ValueError("P1_COMPOSITE_TEXT_CACHE_CHANGED")
        differentiated = False
        try:
            amount = gross_cash(extracted["pages"], row["issuer"])
        except ValueError as exc:
            if str(exc) != "DIFFERENTIATED_DISTRIBUTION_REQUIRES_REVIEW":
                rejected.append({**rejection, "reason": str(exc)})
                continue
            try:
                amount = differentiated_cash(
                    extracted["pages"],
                    row["issuer"],
                    source_titles[row["substitute_source_url"]],
                )
            except ValueError as policy_error:
                rejected.append({**rejection, "reason": str(policy_error)})
                continue
            differentiated = True
        try:
            records, ex_dates = notice_dates(extracted["pages"])
        except ValueError as exc:
            rejected.append({**rejection, "reason": str(exc)})
            continue
        classification = classify_dates(row, records, ex_dates, differentiated=differentiated)
        if amount != Decimal(row["cash_per_share"]):
            rejected.append({**rejection, "reason": "ISSUER_CASH_AMOUNT_CONFLICT"})
            continue
        if classification is None:
            rejected.append(
                {
                    **rejection,
                    "reason": "ISSUER_DATE_CONFLICT",
                    "official_exchange_record_date": row["record_date"],
                    "official_exchange_ex_date": row["ex_date"],
                    "issuer_record_dates": records,
                    "issuer_ex_dates": ex_dates,
                }
            )
            continue
        closed.append(
            {
                **{key: value for key, value in row.items() if key != "substitute_source_path"},
                "substitute_text_cache_sha256": sha256_file(cache),
                "issuer_notice_record_dates": records,
                "issuer_notice_ex_dates": ex_dates,
                "official_exchange_amounts": sorted(str(amount) for amount in targets[key]),
                "classification": classification,
                **(
                    {"holder_policy": "DIFFERENTIATED_CASH_ORDINARY_PUBLIC_A_V1"}
                    if differentiated
                    else {}
                ),
            }
        )
    if len(candidates) != len(closed_ids) + len(closed) + len(rejected):
        raise ValueError("P1_CANDIDATE_CLASSIFICATION_INCOMPLETE")
    report = {
        "report_version": "P1_ORPHAN_CASH_OFFICIAL_COMPOSITE_DATES_V2",
        "parser_sha256": sha256_file(Path(__file__)),
        "cash_parser_sha256": sha256_file(
            Path(__file__).with_name("reconcile_distribution_cash.py")
        ),
        "date_parser_sha256": sha256_file(Path(__file__).with_name("link_distribution_notices.py")),
        "exchange_parser_sha256": sha256_file(
            Path(__file__).with_name("audit_full_cash_ledger.py")
        ),
        "input_sha256s": {
            name: sha256_file(path)
            for name, path in (
                ("requirements", args.requirements),
                ("public_queue", args.public_queue),
                ("public_reassessment", args.public_reassessment),
                ("cash_ledger", args.cash_ledger),
                ("master", args.master),
                ("instruments", args.instruments),
                ("sse_audit", args.sse_audit),
                ("szse_audit", args.szse_audit),
                ("source_manifest", args.source_manifest),
                ("strict_report", args.strict_report),
            )
        },
        "closed_documents": len(closed),
        "closed_facts": sum(len(row["affected_events"]) for row in closed),
        "rejected_documents": len(rejected),
        "rejected_counts": dict(sorted(Counter(row["reason"] for row in rejected).items())),
        "rejected": rejected,
        "classification_counts": dict(
            sorted(Counter(row["classification"] for row in closed).items())
        ),
        "closed": closed,
        "source_checksum_repeatability": "PASS",
        "input_order_reproducibility": "PASS",
        "new_economic_events_created": 0,
    }
    report["manifest_sha256"] = canonical_sha256(report)
    write_immutable(args.output, canonical_json_bytes(report) + b"\n")
    print(
        json.dumps(
            {key: value for key, value in report.items() if key not in {"closed", "rejected"}}
        )
    )


if __name__ == "__main__":
    main()
