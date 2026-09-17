"""Recount disjoint official P1 fact closures from immutable source reports."""

import argparse
import json
from pathlib import Path

from app.data.catalog.checksums import canonical_json_bytes, canonical_sha256, sha256_file
from app.data.catalog.freeze import write_immutable
from scripts.audit_p1_public_fact_requirements import verified

REPORTS = {
    "base": "p1-accepted-cash-fact-closure-v1.json",
    "preferred": "p1-preferred-share-scope-v1.json",
    "matched": "p1-matched-official-cash-facts-v2.json",
    "out_of_period": "p1-out-of-period-cash-v3.json",
    "primary": "p1-primary-cash-notice-ledger-v4.json",
    "orphan_issuer": "p1-orphan-cash-gap-substitutions-v4.json",
    "orphan_exchange": "p1-orphan-exchange-dated-cash-v10.json",
    "sse_st": "p1-official-sse-st-fact-closure-v1.json",
    "differentiated": "p1-differentiated-cash-notice-ledger-v7.json",
    "correction": "p1-correction-cash-facts-v5.json",
    "proposal": "p1-nonfinal-proposal-scope-v3.json",
    "precise": "p1-precise-sse-cash-v1.json",
    "derivative": "p1-derivative-notice-scope-v3.json",
    "retained_cash": "p1-retained-full-cash-source-closure-v9.json",
}


def recount(reports):
    base = reports["base"]
    cash = {row["document_id"]: row for row in base["remaining_cash_documents"]}
    if len(cash) != len(base["remaining_cash_documents"]):
        raise ValueError("BASE_CASH_DOCUMENT_IDS_NOT_UNIQUE")
    by_url = {row["url"]: row for row in cash.values()}
    if len(by_url) != len(cash):
        raise ValueError("BASE_CASH_URLS_NOT_UNIQUE")
    closed = {}

    def add(kind, rows, *, require_cash):
        for row in rows:
            document_id = row["document_id"]
            if document_id in closed:
                raise ValueError(f"DUPLICATE_P1_CLOSURE:{document_id}")
            if require_cash != (document_id in cash):
                raise ValueError(f"P1_CLOSURE_WRONG_FAMILY:{document_id}")
            events = row["affected_events"]
            if not events or len(events) != len(set(events)):
                raise ValueError(f"P1_CLOSURE_FACTS_NOT_UNIQUE:{document_id}")
            closed[document_id] = {
                "document_id": document_id,
                "closure": kind,
                "affected_events": events,
            }

    for kind, field in (
        ("preferred", "excluded"),
        ("matched", "closed"),
        ("out_of_period", "excluded"),
    ):
        add(kind, reports[kind][field], require_cash=True)
    primary = []
    for row in reports["primary"]["events"]:
        source_url = row["event"]["source_url"]
        if source_url not in by_url:
            raise ValueError(f"PRIMARY_NOT_IN_BASE_CASH:{source_url}")
        primary.append(by_url[source_url])
    add("primary", primary, require_cash=True)
    for kind in ("orphan_issuer", "orphan_exchange", "sse_st"):
        add(kind, reports[kind]["closed"], require_cash=False)
    differentiated = [
        cash[row["document_id"]]
        for row in reports["differentiated"]["classifications"]
        if row["status"]
        in (
            "EXACT_ACCEPTED_EVENT",
            "SUPERSEDED_BY_OFFICIAL_CORRECTION",
            "BOTH_ENTITLEMENT_DATES_AFTER_PERIOD",
        )
    ]
    add("differentiated", differentiated, require_cash=True)
    add("correction", reports["correction"]["closed"], require_cash=True)
    add("proposal", reports["proposal"]["closed"], require_cash=True)
    add("precise", reports["precise"]["closed"], require_cash=True)
    add("derivative", reports["derivative"]["closed"], require_cash=True)
    add("retained_cash", reports["retained_cash"]["closed"], require_cash=False)
    rows = sorted(closed.values(), key=lambda row: row["document_id"])
    closed_facts = sum(len(row["affected_events"]) for row in rows)
    unresolved_cash = len(cash) - sum(row["document_id"] in cash for row in rows)
    unresolved_documents = base["p1_unestablished_unique_documents"] - len(rows)
    unresolved_facts = base["p1_true_missing_source_facts"] - closed_facts
    if unresolved_cash < 0 or unresolved_documents < 0 or unresolved_facts < 0:
        raise ValueError("P1_CLOSURE_EXCEEDS_BASELINE")
    substitutions = (
        len(reports["orphan_issuer"]["closed"])
        + len(reports["orphan_exchange"]["closed"])
        + len(reports["sse_st"]["closed"])
        + sum(
            row["classification"] == "STRONGER_ACCEPTED_OFFICIAL_NOTICE_SUBSTITUTION"
            for row in reports["matched"]["closed"]
        )
        + sum(
            row["status"] == "SUPERSEDED_BY_OFFICIAL_CORRECTION"
            for row in reports["differentiated"]["classifications"]
        )
        + len(reports["correction"]["closed"])
        + len(reports["precise"]["closed"])
        + len(reports["retained_cash"]["closed"])
    )
    return {
        "closed_documents": len(rows),
        "closed_facts": closed_facts,
        "p1_raw_requirements": base["p1_raw_requirements"],
        "p1_facts_already_established": base["p1_raw_requirements"] - unresolved_facts,
        "p1_resolved_by_official_substitution": substitutions,
        "p1_true_missing_source_facts": unresolved_facts,
        "p1_unresolved_unique_documents": unresolved_documents,
        "p1_unresolved_cash_documents": unresolved_cash,
        "p1_unresolved_other_documents": unresolved_documents - unresolved_cash,
        "closed": rows,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    paths = {name: args.report_root / filename for name, filename in REPORTS.items()}
    reports = {name: verified(path) for name, path in paths.items()}
    result = recount(reports)
    if result != recount(
        {
            name: dict(
                report,
                **{
                    field: list(reversed(report[field]))
                    for field in (
                        "remaining_cash_documents",
                        "excluded",
                        "closed",
                        "events",
                        "classifications",
                    )
                    if isinstance(report.get(field), list)
                },
            )
            for name, report in reports.items()
        }
    ):
        raise ValueError("INPUT_ORDER_CHANGED")
    result.update(
        report_version="P1_CUMULATIVE_OFFICIAL_FACT_CLOSURE_V24",
        parser_sha256=sha256_file(Path(__file__)),
        input_sha256s={name: sha256_file(path) for name, path in paths.items()},
        input_order_reproducibility="PASS",
    )
    result["manifest_sha256"] = canonical_sha256(result)
    write_immutable(args.output, canonical_json_bytes(result) + b"\n")
    print(json.dumps({key: value for key, value in result.items() if key != "closed"}))


if __name__ == "__main__":
    main()
