"""Accept exact official primary cash notices omitted or rounded by exchange tables."""

import argparse
import json
from collections import defaultdict
from decimal import Decimal
from pathlib import Path

from app.data.catalog.checksums import canonical_json_bytes, canonical_sha256, sha256_file
from app.data.catalog.freeze import write_immutable
from app.domain.markets.corporate_actions import CorporateAction, require_supported_corporate_action
from scripts.audit_p1_cash_census_counterexamples import crosscheck
from scripts.audit_p1_public_fact_requirements import verified
from scripts.triage_p1_remaining_distribution_docs import diagnose

ACCEPTABLE = {"NO_ACCEPTED_EX_DATE_EVENT", "ACCEPTED_EX_DATE_TERM_CONFLICT"}


def reconcile(findings, triage, requirements, cash, master, sources, root):
    by_id = {row["document_id"]: row for row in triage}
    by_requirement = {row["document_id"]: row for row in requirements}
    by_url = {row["url"]: row for row in sources}
    by_security = defaultdict(list)
    by_ex_date = defaultdict(list)
    for row in master:
        by_security[row["security_id"]].append(row)
    for row in cash:
        event = row["event"]
        by_ex_date[(event["security_id"]["value"], event["ex_date"])].append(row)
    accepted = []
    for finding in findings:
        if finding["finding"] not in ACCEPTABLE:
            continue
        row = by_id[finding["document_id"]]
        requirement = by_requirement[finding["document_id"]]
        source = by_url[finding["url"]]
        pdf = root / source["source_path"]
        cache = root / "batch-v1/text" / f"{source['source_sha256']}.json"
        if (
            source["retrieval_status"] != "PASS"
            or not source["url"].startswith("https://static.cninfo.com.cn/finalpage/")
            or source["issuer"] != requirement["issuer"]
            or source["published_on"] != requirement["published_on"]
            or source["title"] != requirement["title"]
            or requirement["url"] != finding["url"]
            or requirement["title"] != finding["title"]
            or source["source_sha256"] != finding["source_sha256"]
            or sha256_file(pdf) != source["source_sha256"]
            or sha256_file(cache) != row["text_cache_sha256"]
        ):
            raise ValueError("P1_PRIMARY_CASH_SOURCE_CHANGED")
        extracted = json.loads(cache.read_bytes())
        if extracted["source_sha256"] != source["source_sha256"]:
            raise ValueError("P1_PRIMARY_CASH_TEXT_CHANGED")
        parsed = diagnose(extracted["pages"], requirement["issuer"])
        if (
            parsed["preferred_instrument_marker"]
            or parsed["cash_candidate_per_share"] is None
            or parsed["record_dates"] != [finding["record_date"]]
            or parsed["ex_dates"] != [finding["ex_date"]]
            or Decimal(parsed["cash_candidate_per_share"])
            != Decimal(finding["cash_candidate_per_share"])
        ):
            raise ValueError("P1_PRIMARY_CASH_TERMS_CHANGED")
        sid, record, ex = (
            finding["security_id"],
            finding["record_date"],
            finding["ex_date"],
        )
        members = [
            item
            for item in by_security[sid]
            if item["instrument_type"] == "COMMON_A_SHARE"
            and item["effective_from"] <= record <= ex
            and ex <= (item["effective_to"] or "2025-12-31")
        ]
        if (
            len(members) != 1
            or requirement["published_on"] > record
            or not "2010-01-01" <= ex <= "2025-12-31"
        ):
            raise ValueError("P1_PRIMARY_CASH_LIFECYCLE_UNRESOLVED")
        peers = by_ex_date[(sid, ex)]
        if (finding["finding"] == "NO_ACCEPTED_EX_DATE_EVENT") != (len(peers) == 0):
            raise ValueError("P1_PRIMARY_CASH_LEDGER_STATE_CHANGED")
        if finding["finding"] == "ACCEPTED_EX_DATE_TERM_CONFLICT" and (
            len(peers) != 1 or peers[0]["event"]["record_date"] != record
        ):
            raise ValueError("P1_PRIMARY_CASH_CONFLICT_NOT_UNIQUE")
        terms = {
            "security_id": sid,
            "record_date": record,
            "ex_date": ex,
            "cash_per_share": str(Decimal(finding["cash_candidate_per_share"])),
            "source_sha256": source["source_sha256"],
        }
        action = CorporateAction.model_validate(
            {
                "security_id": {"value": sid},
                "action_type": "CASH_DIVIDEND",
                "announcement_date": requirement["published_on"],
                "effective_date": ex,
                "record_date": record,
                "ex_date": ex,
                "cash_per_share": terms["cash_per_share"],
                "source_document": requirement["title"],
                "source_url": source["url"],
                "source_document_sha256": source["source_sha256"],
                "retrieved_at": source["retrieved_at_utc"],
                "source_provider": "OFFICIAL_ISSUER_CNINFO_PRIMARY_IMPLEMENTATION",
                "source_version": "P1_PRIMARY_CASH_NOTICE_RECONCILIATION_V1",
                "source_record_hash": canonical_sha256(terms),
                "completeness": "COMPLETE",
            }
        )
        require_supported_corporate_action(action)
        accepted.append(
            {
                "event": action.model_dump(mode="json"),
                "event_checksum": action.event_checksum,
                "source_terms_sha256": canonical_sha256(terms),
                "source_text_cache_sha256": sha256_file(cache),
                "reconciles": finding["finding"],
                "supersedes_event_checksum": peers[0]["event_checksum"] if peers else None,
            }
        )
    return sorted(accepted, key=lambda row: row["event_checksum"])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--counterexamples", type=Path, required=True)
    parser.add_argument("--triage", type=Path, required=True)
    parser.add_argument("--closure", type=Path, required=True)
    parser.add_argument("--cash-ledger", type=Path, required=True)
    parser.add_argument("--master", type=Path, required=True)
    parser.add_argument("--source-manifest", type=Path, required=True)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    counterexamples, triage, closure, cash, sources = (
        verified(path)
        for path in (
            args.counterexamples,
            args.triage,
            args.closure,
            args.cash_ledger,
            args.source_manifest,
        )
    )
    master = json.loads(args.master.read_bytes())
    if (
        sha256_file(args.cash_ledger) != counterexamples["input_sha256s"]["cash_ledger"]
        or sha256_file(args.master) != counterexamples["input_sha256s"]["master"]
        or crosscheck(
            triage["documents"], closure["remaining_cash_documents"], cash["events"], master
        )
        != counterexamples["findings"]
    ):
        raise ValueError("P1_PRIMARY_CASH_CROSSCHECK_CHANGED")
    inputs = (
        counterexamples["findings"],
        triage["documents"],
        closure["remaining_cash_documents"],
        cash["events"],
        master,
        sources["documents"],
    )
    events = reconcile(*inputs, args.source_root)
    if events != reconcile(*(list(reversed(rows)) for rows in inputs), args.source_root):
        raise ValueError("INPUT_ORDER_CHANGED")
    if len(
        {(row["event"]["security_id"]["value"], row["event"]["ex_date"]) for row in events}
    ) != len(events):
        raise ValueError("DUPLICATE_P1_PRIMARY_CASH_EVENT")
    report = {
        "report_version": "P1_PRIMARY_OFFICIAL_CASH_NOTICE_LEDGER_V2",
        "parser_sha256": sha256_file(Path(__file__)),
        "input_sha256s": {
            name: sha256_file(path)
            for name, path in (
                ("counterexamples", args.counterexamples),
                ("triage", args.triage),
                ("closure", args.closure),
                ("cash_ledger", args.cash_ledger),
                ("master", args.master),
                ("source_manifest", args.source_manifest),
            )
        },
        "accepted_primary_notice_events": len(events),
        "missing_exchange_census_events": sum(
            row["supersedes_event_checksum"] is None for row in events
        ),
        "precise_issuer_notice_corrections": sum(
            row["supersedes_event_checksum"] is not None for row in events
        ),
        "events": events,
        "input_order_reproducibility": "PASS",
        "full_cash_census_acceptance": "NOT_YET_REAUDITED",
    }
    report["manifest_sha256"] = canonical_sha256(report)
    write_immutable(args.output, canonical_json_bytes(report) + b"\n")
    print(
        json.dumps({key: value for key, value in report.items() if key != "events"}, sort_keys=True)
    )


if __name__ == "__main__":
    main()
