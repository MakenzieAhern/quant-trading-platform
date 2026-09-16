"""Audit differentiated-cash issuer notices omitted by the ordinary cash parser."""

import argparse
import json
from collections import Counter, defaultdict
from decimal import Decimal
from pathlib import Path

from app.data.catalog.checksums import canonical_json_bytes, canonical_sha256, sha256_file
from app.data.catalog.freeze import write_immutable
from app.domain.markets.corporate_actions import CorporateAction, require_supported_corporate_action
from scripts.audit_p1_cash_census_counterexamples import PRIMARY, SECONDARY
from scripts.audit_p1_public_fact_requirements import verified
from scripts.link_distribution_notices import notice_dates
from scripts.reconcile_distribution_cash import differentiated_cash

POLICY = "DIFFERENTIATED_CASH_ORDINARY_PUBLIC_A_V1"


def decision(peers, record, amount):
    if not peers:
        return "NEW_OFFICIAL_ISSUER_EVENT"
    if (
        len(peers) == 1
        and peers[0]["event"]["record_date"] == record
        and Decimal(peers[0]["event"]["cash_per_share"]) == amount
    ):
        return "EXACT_ACCEPTED_EVENT"
    return "ACCEPTED_EVENT_CONFLICT"


def reconcile(triage, requirements, cash, master, sources, root):
    by_id = {row["document_id"]: row for row in requirements}
    by_url = {row["url"]: row for row in sources}
    peers = defaultdict(list)
    for row in cash:
        event = row["event"]
        peers[event["security_id"]["value"], event["ex_date"]].append(row)
    results, events = [], []
    for row in triage:
        if row["cash_parser_error"] != "DIFFERENTIATED_DISTRIBUTION_REQUIRES_REVIEW":
            continue
        requirement = by_id[row["document_id"]]
        source = by_url[row["url"]]
        result = {
            "document_id": row["document_id"],
            "url": row["url"],
            "source_sha256": row["source_sha256"],
        }
        pdf = Path(source["source_path"])
        if not pdf.is_absolute():
            pdf = root / pdf
        pdf = pdf.resolve()
        cache = root / "batch-v1/text" / f"{row['source_sha256']}.json"
        if (
            not pdf.is_relative_to(root.parent.resolve())
            or source["retrieval_status"] != "PASS"
            or source["issuer"] != requirement["issuer"]
            or source["title"] != requirement["title"]
            or source["published_on"] != requirement["published_on"]
            or source["source_sha256"] != row["source_sha256"]
            or sha256_file(pdf) != row["source_sha256"]
            or sha256_file(cache) != row["text_cache_sha256"]
        ):
            raise ValueError(f"DIFFERENTIATED_SOURCE_CHANGED:{row['document_id']}")
        extracted = json.loads(cache.read_bytes())
        if extracted["source_sha256"] != row["source_sha256"]:
            raise ValueError("DIFFERENTIATED_TEXT_CHANGED")
        if not PRIMARY.search(requirement["title"]) or SECONDARY.search(requirement["title"]):
            results.append({**result, "status": "NOT_PRIMARY_FINAL_NOTICE"})
            continue
        try:
            amount = differentiated_cash(
                extracted["pages"], requirement["issuer"], requirement["title"]
            )
            records, ex_dates = notice_dates(extracted["pages"])
        except ValueError as exc:
            results.append({**result, "status": str(exc)})
            continue
        if len(records) != 1 or len(ex_dates) != 1:
            results.append(
                {
                    **result,
                    "status": "DATES_NOT_UNIQUE",
                    "record_dates": records,
                    "ex_dates": ex_dates,
                }
            )
            continue
        record, ex = records[0], ex_dates[0]
        if record > "2025-12-31" and ex > "2025-12-31":
            results.append(
                {
                    **result,
                    "status": "BOTH_ENTITLEMENT_DATES_AFTER_PERIOD",
                    "record_date": record,
                    "ex_date": ex,
                }
            )
            continue
        if not requirement["published_on"] <= record < ex <= "2025-12-31":
            results.append(
                {
                    **result,
                    "status": "DATE_BOUNDARY_NOT_PRE_EFFECTIVE",
                    "record_date": record,
                    "ex_date": ex,
                }
            )
            continue
        members = {
            item["security_id"]
            for item in master
            if item["symbol"] == requirement["issuer"]
            and item["instrument_type"] == "COMMON_A_SHARE"
            and item["effective_from"] <= record < ex <= (item["effective_to"] or "2025-12-31")
        }
        if len(members) != 1:
            results.append({**result, "status": "MASTER_IDENTITY_UNRESOLVED"})
            continue
        sid = next(iter(members))
        status = decision(peers[sid, ex], record, amount)
        result.update(
            status=status,
            security_id=sid,
            record_date=record,
            ex_date=ex,
            cash_per_share=str(amount),
            text_cache_sha256=row["text_cache_sha256"],
        )
        results.append(result)
        if status != "NEW_OFFICIAL_ISSUER_EVENT":
            continue
        terms = {
            key: result[key]
            for key in ("security_id", "record_date", "ex_date", "cash_per_share", "source_sha256")
        }
        action = CorporateAction.model_validate(
            {
                "security_id": {"value": sid},
                "action_type": "CASH_DIVIDEND",
                "announcement_date": requirement["published_on"],
                "effective_date": ex,
                "record_date": record,
                "ex_date": ex,
                "cash_per_share": str(amount),
                "source_document": requirement["title"],
                "source_url": source["url"],
                "source_document_sha256": source["source_sha256"],
                "retrieved_at": source["retrieved_at_utc"],
                "source_provider": "OFFICIAL_ISSUER_CNINFO_DIFFERENTIATED_PUBLIC_A",
                "source_version": "P1_DIFFERENTIATED_CASH_NOTICE_V1",
                "source_record_hash": canonical_sha256(terms),
                "completeness": "COMPLETE",
            }
        )
        require_supported_corporate_action(action)
        events.append(
            {
                "event": action.model_dump(mode="json"),
                "event_checksum": action.event_checksum,
                "source_terms_sha256": canonical_sha256(terms),
                "source_text_cache_sha256": sha256_file(cache),
                "policy_id": POLICY,
                "holder_class": "ORDINARY_EXCHANGE_TRADABLE_A_SHARE_PUBLIC_HOLDER",
            }
        )
    return sorted(results, key=lambda item: item["document_id"]), sorted(
        events, key=lambda item: item["event_checksum"]
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    for name in (
        "triage",
        "closure",
        "cash-ledger",
        "master",
        "source-manifest",
        "source-root",
        "output",
    ):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    triage, closure, cash, sources = (
        verified(path)
        for path in (args.triage, args.closure, args.cash_ledger, args.source_manifest)
    )
    master = json.loads(args.master.read_bytes())
    if (
        triage["closure_sha256"] != sha256_file(args.closure)
        or triage["source_manifest_sha256"] != sha256_file(args.source_manifest)
        or closure["input_sha256s"]["master"] != sha256_file(args.master)
    ):
        raise ValueError("DIFFERENTIATED_INPUT_CHANGED")
    inputs = (
        triage["documents"],
        closure["remaining_cash_documents"],
        cash["events"],
        master,
        sources["documents"],
    )
    results, events = reconcile(*inputs, args.source_root)
    if (results, events) != reconcile(*(list(reversed(rows)) for rows in inputs), args.source_root):
        raise ValueError("INPUT_ORDER_CHANGED")
    report = {
        "report_version": "P1_DIFFERENTIATED_OFFICIAL_CASH_NOTICE_V1",
        "parser_sha256": sha256_file(Path(__file__)),
        "cash_parser_sha256": sha256_file(
            Path(__file__).with_name("reconcile_distribution_cash.py")
        ),
        "input_sha256s": {
            name: sha256_file(path)
            for name, path in (
                ("triage", args.triage),
                ("closure", args.closure),
                ("cash_ledger", args.cash_ledger),
                ("master", args.master),
                ("source_manifest", args.source_manifest),
            )
        },
        "candidate_documents": len(results),
        "classification_counts": dict(sorted(Counter(row["status"] for row in results).items())),
        "classifications": results,
        "accepted_events": len(events),
        "events": events,
        "input_order_reproducibility": "PASS",
        "full_cash_census_acceptance": "PARTIAL",
    }
    report["manifest_sha256"] = canonical_sha256(report)
    write_immutable(args.output, canonical_json_bytes(report) + b"\n")
    print(
        json.dumps(
            {
                key: value
                for key, value in report.items()
                if key not in {"events", "classifications"}
            }
        )
    )


if __name__ == "__main__":
    main()
