"""Close URL-less P1 cash requests with another exact official issuer notice."""

import argparse
import json
import re
from collections import defaultdict
from datetime import date
from decimal import Decimal
from pathlib import Path

from app.data.catalog.checksums import canonical_json_bytes, canonical_sha256, sha256_file
from app.data.catalog.freeze import write_immutable
from scripts.audit_p1_cash_census_counterexamples import PRIMARY, SECONDARY
from scripts.audit_p1_public_fact_requirements import verified
from scripts.link_distribution_notices import notice_dates
from scripts.reconcile_distribution_cash import gross_cash

REQUIREMENT = "FINAL_IMPLEMENTATION_NOTICE_WITH_GROSS_ORDINARY_A_SHARE_CASH"
LEGACY_FINAL = re.compile(
    r"(?:分红派息公告|权益分派公告|利润分配实施的公告|权益分派的公告|"
    r"现金红利实施公告|权益派息实施公告|分红公告)$"
)
LEGACY_NOT_FINAL = re.compile(
    r"预案|提议|董事会|股东大会|调整|回购|提示|更正|修订|进展|实施后|停止转股"
)


def final_issuer_title(title: str) -> bool:
    return bool(
        not SECONDARY.search(title)
        and (
            PRIMARY.search(title)
            or (LEGACY_FINAL.search(title) and not LEGACY_NOT_FINAL.search(title))
        )
    )


def select(
    requirements,
    public,
    out_of_scope,
    cash,
    master,
    sources,
    *,
    final_title=final_issuer_title,
    historical_alias=False,
):
    known_ids = {row["document_id"] for row in public} | {
        row["document_id"] for row in out_of_scope
    }
    by_source = {row["url"]: row for row in sources}
    sources_by_symbol = defaultdict(list)
    for row in sources:
        sources_by_symbol[row["issuer"]].append(row)
    by_cash = defaultdict(list)
    by_symbol = defaultdict(list)
    by_stable_symbol = defaultdict(list)
    for row in cash:
        event = row["event"]
        by_cash[(event["security_id"]["value"], event["record_date"], event["ex_date"])].append(row)
    for row in master:
        by_symbol[row["symbol"]].append(row)
        if historical_alias:
            by_stable_symbol[row["security_id"].split(":")[-1]].append(row)
    selected = []
    for requirement in requirements:
        if (
            requirement["priority"] != "P1"
            or requirement["source_group"] != "CNINFO"
            or requirement["document_id"] in known_ids
            or requirement["known_urls"]
            or requirement["required_document_types"] != [REQUIREMENT]
            or len(requirement["affected_events"]) != 1
        ):
            continue
        parts = requirement["affected_events"][0].split(":")
        if len(parts) != 4 or parts[0] != "CASH":
            continue
        symbol, record, ex = parts[1:]
        active = [
            row
            for row in by_symbol[symbol]
            if row["effective_from"] <= record <= (row["effective_to"] or "2025-12-31")
            and row["instrument_type"] == "COMMON_A_SHARE"
        ]
        if not active and historical_alias:
            active = [
                row
                for row in by_stable_symbol[symbol]
                if row["effective_from"] <= record <= (row["effective_to"] or "2025-12-31")
                and row["instrument_type"] == "COMMON_A_SHARE"
                and row.get("code_transition_source_url")
                and row.get("code_transition_source_sha256")
            ]
        identities = {(row["security_id"], row["symbol"]) for row in active}
        if len(identities) != 1:
            continue
        sid, issuer_symbol = next(iter(identities))
        alias_evidence = {
            (row.get("code_transition_source_url"), row.get("code_transition_source_sha256"))
            for row in active
        }
        historical_code = sid.rsplit(":", 1)[-1] != symbol
        if (issuer_symbol != symbol or historical_code) and (
            len(alias_evidence) != 1 or not all(next(iter(alias_evidence)))
        ):
            continue
        peers = by_cash[(sid, record, ex)]
        if len(peers) != 1:
            continue
        accepted = peers[0]
        event = accepted["event"]
        same_source = event["source_provider"].startswith(
            "OFFICIAL_ISSUER_CNINFO_"
        ) and final_title(event["source_document"])
        if same_source:
            source = by_source.get(event["source_url"])
        else:
            candidates = [
                row
                for row in sources_by_symbol[issuer_symbol]
                if row["retrieval_status"] == "PASS"
                and row["published_on"] <= record
                and (date.fromisoformat(record) - date.fromisoformat(row["published_on"])).days
                <= 60
                and final_title(row["title"])
            ]
            if len(candidates) != 1:
                continue
            source = candidates[0]
        if not source or (
            source["retrieval_status"] != "PASS"
            or not source["url"].startswith("https://static.cninfo.com.cn/finalpage/")
            or source["issuer"] != issuer_symbol
            or not final_title(source["title"])
            or source["published_on"] > record
            or (
                same_source
                and (
                    source["title"] != event["source_document"]
                    or source["published_on"] != event["announcement_date"]
                    or source["source_sha256"] != event["source_document_sha256"]
                )
            )
        ):
            continue
        selected.append(
            {
                "document_id": requirement["document_id"],
                "affected_events": requirement["affected_events"],
                "security_id": sid,
                "issuer": issuer_symbol,
                **(
                    {
                        "official_code_transition_url": next(iter(alias_evidence))[0],
                        "official_code_transition_sha256": next(iter(alias_evidence))[1],
                        **(
                            {"requirement_stable_symbol": symbol} if issuer_symbol != symbol else {}
                        ),
                    }
                    if issuer_symbol != symbol or historical_code
                    else {}
                ),
                **({"requirement_historical_symbol": symbol} if historical_code else {}),
                "record_date": record,
                "ex_date": ex,
                "cash_per_share": event["cash_per_share"],
                "accepted_event_checksum": accepted["event_checksum"],
                "substitute_source_url": source["url"],
                "substitute_source_sha256": source["source_sha256"],
                "substitute_source_path": source["source_path"],
                "classification": (
                    "AUTHORITATIVE_OFFICIAL_SOURCE_SUBSTITUTION"
                    if same_source
                    else "INDEPENDENT_OFFICIAL_ISSUER_SOURCE_SUBSTITUTION"
                ),
            }
        )
    return sorted(selected, key=lambda row: row["document_id"])


def verify_terms(rows, staging: Path, source_root: Path, text_root: Path) -> list[dict]:
    accepted = []
    for row in rows:
        pdf = Path(row["substitute_source_path"])
        if not pdf.is_absolute():
            pdf = source_root / pdf
        pdf = pdf.resolve()
        cache = text_root / f"{row['substitute_source_sha256']}.json"
        if (
            not pdf.is_relative_to(staging.resolve())
            or sha256_file(pdf) != row["substitute_source_sha256"]
            or not cache.is_file()
        ):
            raise ValueError("P1_ORPHAN_OFFICIAL_PDF_CHANGED")
        extracted = json.loads(cache.read_bytes())
        if extracted["source_sha256"] != row["substitute_source_sha256"]:
            raise ValueError("P1_ORPHAN_TEXT_CACHE_CHANGED")
        try:
            amount = gross_cash(extracted["pages"], row["issuer"])
            records, ex_dates = notice_dates(extracted["pages"])
        except ValueError:
            continue
        if (
            amount == Decimal(row["cash_per_share"])
            and records == [row["record_date"]]
            and ex_dates == [row["ex_date"]]
        ):
            accepted.append(
                {
                    **{key: value for key, value in row.items() if key != "substitute_source_path"},
                    "substitute_text_cache_sha256": sha256_file(cache),
                }
            )
    return accepted


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--requirements", type=Path, required=True)
    parser.add_argument("--public-queue", type=Path, required=True)
    parser.add_argument("--public-reassessment", type=Path, required=True)
    parser.add_argument("--cash-ledger", type=Path, required=True)
    parser.add_argument("--master", type=Path, required=True)
    parser.add_argument("--source-manifest", type=Path, required=True)
    parser.add_argument("--staging", type=Path, required=True)
    parser.add_argument("--text-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    requirements, reassessment, cash, sources = (
        verified(path)
        for path in (
            args.requirements,
            args.public_reassessment,
            args.cash_ledger,
            args.source_manifest,
        )
    )
    public = json.loads(args.public_queue.read_bytes())
    master = json.loads(args.master.read_bytes())
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
    closed = verify_terms(
        candidates, args.staging, args.source_manifest.parent.parent, args.text_root
    )
    report = {
        "report_version": "P1_ORPHAN_OFFICIAL_CASH_FACT_SUBSTITUTION_V1",
        "parser_sha256": sha256_file(Path(__file__)),
        "gross_cash_parser_sha256": sha256_file(
            Path(__file__).with_name("reconcile_distribution_cash.py")
        ),
        "notice_date_parser_sha256": sha256_file(
            Path(__file__).with_name("link_distribution_notices.py")
        ),
        "input_sha256s": {
            name: sha256_file(path)
            for name, path in (
                ("requirements", args.requirements),
                ("public_queue", args.public_queue),
                ("public_reassessment", args.public_reassessment),
                ("cash_ledger", args.cash_ledger),
                ("master", args.master),
                ("source_manifest", args.source_manifest),
            )
        },
        "candidate_documents": len(candidates),
        "closed_documents": len(closed),
        "closed_facts": sum(len(row["affected_events"]) for row in closed),
        "closed": closed,
        "input_order_reproducibility": "PASS",
        "new_economic_events_created": 0,
    }
    report["manifest_sha256"] = canonical_sha256(report)
    write_immutable(args.output, canonical_json_bytes(report) + b"\n")
    print(json.dumps({key: value for key, value in report.items() if key != "closed"}))


if __name__ == "__main__":
    main()
