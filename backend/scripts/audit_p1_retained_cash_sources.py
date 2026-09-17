"""Close stale P1 cash requests using retained final issuer PDFs and exchange dates."""

import argparse
import json
import re
from collections import Counter
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

from app.data.catalog.checksums import canonical_json_bytes, canonical_sha256, sha256_file
from app.data.catalog.freeze import write_immutable
from scripts.audit_full_cash_ledger import official_targets
from scripts.audit_p1_cash_census_counterexamples import SECONDARY
from scripts.audit_p1_orphan_cash_facts import REQUIREMENT, final_issuer_title, select
from scripts.audit_p1_orphan_exchange_dates import classify_dates
from scripts.audit_p1_public_fact_requirements import verified
from scripts.link_distribution_notices import notice_dates
from scripts.reconcile_distribution_cash import gross_cash

PROVIDERS = {
    "OFFICIAL_ISSUER_CNINFO_EXCHANGE_DATED",
    "OFFICIAL_ISSUER_CNINFO_EXCHANGE_RECONCILED",
    "OFFICIAL_ISSUER_CNINFO_PRIMARY_IMPLEMENTATION",
}
FINAL_VARIANT = re.compile(r"(?:实施(?:的)?公告|实施方案|实施报告|派发.*(?:股息|股利).*公告)$")
NONFINAL_VARIANT = re.compile(r"董事会|股东大会|预案|决议|停牌|提示")


def retained_final_title(title):
    return final_issuer_title(title) or bool(
        FINAL_VARIANT.search(title)
        and not SECONDARY.search(title)
        and not NONFINAL_VARIANT.search(title)
    )


def eligible(requirements, excluded, cash):
    by_key = {}
    for accepted in cash:
        event = accepted["event"]
        key = (
            event["security_id"]["value"].split(":")[-1],
            event["record_date"],
            event["ex_date"],
        )
        by_key.setdefault(key, []).append(accepted)
    rows, events = [], []
    for row in sorted(requirements, key=lambda item: item["document_id"]):
        if (
            row["priority"] != "P1"
            or row["document_id"] in excluded
            or row["required_document_types"] != [REQUIREMENT]
            or row["known_urls"]
            or len(row["affected_events"]) != 1
        ):
            continue
        parts = row["affected_events"][0].split(":")
        if len(parts) != 4 or parts[0] != "CASH":
            continue
        matches = by_key.get(tuple(parts[1:]), [])
        if len(matches) == 1 and matches[0]["event"]["source_provider"] in PROVIDERS:
            rows.append(row)
            events.append(matches[0])
    return rows, events


def retained_sources(staging, events):
    keys = {(row["event"]["source_url"], row["event"]["source_document_sha256"]) for row in events}
    found = {}
    for manifest in sorted(staging.rglob("source-manifest.json")):
        data = json.loads(manifest.read_bytes())
        if not isinstance(data, dict):
            continue
        for doc in data.get("documents", []):
            key = doc.get("url"), doc.get("source_sha256")
            if key not in keys or doc.get("retrieval_status") != "PASS":
                continue
            if key in found:
                earlier = found[key][1]
                if any(
                    doc[field] != earlier[field] for field in ("issuer", "title", "published_on")
                ):
                    raise ValueError(f"CONFLICTING_OFFICIAL_RECEIPTS:{key[0]}")
                continue
            verified(manifest)
            found[key] = (manifest, doc)
    source_docs = []
    by_url = {}
    for (url, sha), (manifest, doc) in sorted(found.items()):
        if url in by_url and by_url[url] != sha:
            raise ValueError(f"CONFLICTING_OFFICIAL_SOURCE_BYTES:{url}")
        by_url[url] = sha
        source_docs.append(
            {
                **doc,
                "source_path": str((manifest.parents[1] / doc["source_path"]).resolve()),
            }
        )
    return found, source_docs


def exchange_amount_matches(amount, targets):
    return any(
        amount == target
        or amount.quantize(Decimal(1).scaleb(target.as_tuple().exponent), rounding=ROUND_HALF_UP)
        == target
        for target in targets
    )


def exchange_resolves_year_conflict(row, records, ex_dates, published_on):
    if (len(records), len(ex_dates)) != (1, 1):
        return False
    expected = row["record_date"], row["ex_date"]
    parsed = records[0], ex_dates[0]
    return (
        published_on <= expected[0] < expected[1]
        and any(actual != target for actual, target in zip(parsed, expected, strict=True))
        and all(
            actual[5:] == target[5:] and (actual == target or actual < published_on)
            for actual, target in zip(parsed, expected, strict=True)
        )
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in (
        "requirements",
        "reassessment",
        "base",
        "prior",
        "cash-ledger",
        "master",
        "instruments",
        "sse-audit",
        "szse-audit",
        "staging",
        "output",
    ):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    requirements, reassessment, base, prior, cash, instruments, sse, szse = (
        verified(path)
        for path in (
            args.requirements,
            args.reassessment,
            args.base,
            args.prior,
            args.cash_ledger,
            args.instruments,
            args.sse_audit,
            args.szse_audit,
        )
    )
    master = json.loads(args.master.read_bytes())
    excluded = (
        {row["document_id"] for row in reassessment["out_of_scope_cninfo_documents"]}
        | {row["document_id"] for row in base["accepted_cash_matches"]}
        | {row["document_id"] for row in prior["closed"]}
    )
    requests, events = eligible(requirements["documents"], excluded, cash["events"])
    if (requests, events) != eligible(
        list(reversed(requirements["documents"])), excluded, list(reversed(cash["events"]))
    ):
        raise ValueError("INPUT_ORDER_CHANGED")
    found, source_docs = retained_sources(args.staging, events)
    selected = select(
        requests, [], [], events, master, source_docs, final_title=retained_final_title
    )
    if selected != select(
        list(reversed(requests)),
        [],
        [],
        list(reversed(events)),
        master,
        source_docs,
        final_title=retained_final_title,
    ):
        raise ValueError("SOURCE_INPUT_ORDER_CHANGED")
    instrument_types = {
        row["classification"]["security_id"]["value"]: row["classification"]["instrument_type"]
        for row in instruments["classifications"]
    }
    targets, _ = official_targets(master, instrument_types, sse, szse)
    closed = []
    selected_ids = {row["document_id"] for row in selected}
    rejected = [
        {"document_id": row["document_id"], "reason": "SOURCE_TITLE_OR_MASTER_UNMATCHED"}
        for row in requests
        if row["document_id"] not in selected_ids
    ]
    for row in selected:
        key = row["security_id"], row["record_date"], row["ex_date"]
        reason = None
        if key not in targets:
            reason = "NO_EXACT_OFFICIAL_EXCHANGE_TARGET"
        else:
            source_key = row["substitute_source_url"], row["substitute_source_sha256"]
            manifest, doc = found[source_key]
            source_root = manifest.parents[1]
            pdf = (source_root / doc["source_path"]).resolve()
            cache = source_root / "batch-v1/text" / f"{doc['source_sha256']}.json"
            if (
                not pdf.is_relative_to(args.staging.resolve())
                or sha256_file(pdf) != doc["source_sha256"]
                or not cache.is_file()
            ):
                raise ValueError(f"RETAINED_OFFICIAL_SOURCE_CHANGED:{row['document_id']}")
            extracted = json.loads(cache.read_bytes())
            if extracted["source_sha256"] != doc["source_sha256"]:
                raise ValueError(f"RETAINED_OFFICIAL_TEXT_CHANGED:{row['document_id']}")
            try:
                amount = gross_cash(
                    extracted["pages"], row["issuer"], targets[key], trusted_issuer=True
                )
                records, ex_dates = notice_dates(extracted["pages"])
            except ValueError as exc:
                reason = str(exc)
            else:
                classification = classify_dates(row, records, ex_dates)
                if classification is None and exchange_resolves_year_conflict(
                    row, records, ex_dates, doc["published_on"]
                ):
                    classification = "OFFICIAL_EXCHANGE_RESOLVED_SOURCE_YEAR_CONFLICT"
                if amount != Decimal(row["cash_per_share"]):
                    reason = "ISSUER_CASH_AMOUNT_CONFLICT"
                elif not exchange_amount_matches(amount, targets[key]):
                    reason = "ISSUER_EXCHANGE_AMOUNT_CONFLICT"
                elif classification is None:
                    reason = "ISSUER_DATE_CONFLICT"
                else:
                    closed.append(
                        {
                            **{k: v for k, v in row.items() if k != "substitute_source_path"},
                            "classification": classification,
                            "issuer_notice_record_dates": records,
                            "issuer_notice_ex_dates": ex_dates,
                            "official_exchange_amounts": sorted(
                                str(value) for value in targets[key]
                            ),
                            "source_manifest_sha256": sha256_file(manifest),
                            "source_text_sha256": sha256_file(cache),
                        }
                    )
        if reason:
            rejected.append({"document_id": row["document_id"], "reason": reason})
    if len(closed) + len(rejected) != len(requests):
        raise ValueError("RETAINED_P1_CANDIDATES_NOT_PARTITIONED")
    report = {
        "report_version": "P1_RETAINED_OFFICIAL_FULL_CASH_SOURCE_CLOSURE_V4",
        "candidate_documents": len(requests),
        "selected_documents": len(selected),
        "closed_documents": len(closed),
        "closed_facts": sum(len(row["affected_events"]) for row in closed),
        "classification_counts": dict(
            sorted(Counter(row["classification"] for row in closed).items())
        ),
        "rejected_counts": dict(sorted(Counter(row["reason"] for row in rejected).items())),
        "rejected": rejected,
        "closed": closed,
        "input_sha256s": {
            name: sha256_file(getattr(args, name))
            for name in (
                "requirements",
                "reassessment",
                "base",
                "prior",
                "cash_ledger",
                "master",
                "instruments",
                "sse_audit",
                "szse_audit",
            )
        },
        "source_manifest_sha256s": {
            str(path): sha256_file(path) for path in sorted({item[0] for item in found.values()})
        },
        "parser_sha256": sha256_file(Path(__file__)),
        "cash_parser_sha256": sha256_file(
            Path(__file__).with_name("reconcile_distribution_cash.py")
        ),
        "date_parser_sha256": sha256_file(Path(__file__).with_name("link_distribution_notices.py")),
        "input_order_reproducibility": "PASS",
        "closed_source_checksum_verified": True,
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
