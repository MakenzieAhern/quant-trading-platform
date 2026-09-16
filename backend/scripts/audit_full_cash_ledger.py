"""Merge accepted cash events and audit full-range official exchange coverage."""

import argparse
import json
import re
from collections import Counter, defaultdict
from decimal import Decimal
from pathlib import Path

from app.data.catalog.checksums import canonical_json_bytes, canonical_sha256, sha256_file
from app.data.catalog.freeze import write_immutable
from app.domain.markets.corporate_actions import CorporateAction, require_supported_corporate_action
from scripts.reconcile_distribution_cash import accepted_event_key, accepted_event_terms

START, END = "2010-01-01", "2025-12-31"


def verified(path):
    value = json.loads(path.read_bytes())
    if value["manifest_sha256"] != canonical_sha256(
        {key: item for key, item in value.items() if key != "manifest_sha256"}
    ):
        raise ValueError("INPUT_MANIFEST_CHANGED")
    return value


def merge_events(baseline, additions):
    rows = {}
    for row in baseline:
        key = accepted_event_key(row)
        if key in rows:
            raise ValueError("DUPLICATE_BASELINE_CASH_EVENT")
        rows[key] = row
    for row in sorted(
        (row for ledger in additions for row in ledger),
        key=lambda row: (accepted_event_key(row), canonical_sha256(row)),
    ):
        key = accepted_event_key(row)
        if key in rows and accepted_event_terms(row) != accepted_event_terms(rows[key]):
            prior_title = rows[key]["event"].get("source_document", "")
            current_title = row["event"].get("source_document", "")
            obsolete = r"调整.*(?:转股|回购).*价格"
            if re.search(obsolete, prior_title) and not re.search(obsolete, current_title):
                rows[key] = row
                continue
            raise ValueError("CONFLICTING_ACCEPTED_CASH_EVENT")
        rows.setdefault(key, row)
    return [rows[key] for key in sorted(rows)]


def security_at(master, instruments, exchange, symbol, record_date, ex_date):
    rows = [
        row
        for row in master
        if row["symbol"] == symbol
        and row["instrument_type"] == "COMMON_A_SHARE"
        and row["effective_from"] <= record_date <= ex_date
        and ex_date <= (row["effective_to"] or END)
    ]
    stable_id = f"CN-A:{exchange}:{symbol}"
    if not rows:
        rows = [
            row
            for row in master
            if row["security_id"] == stable_id
            and row["instrument_type"] == "COMMON_A_SHARE"
            and row["effective_from"] <= record_date <= ex_date
            and ex_date <= (row["effective_to"] or END)
        ]
    if not rows and stable_id in instruments and instruments[stable_id] != "COMMON_A_SHARE":
        return None
    if len(rows) != 1:
        raise ValueError("CASH_TARGET_LIFECYCLE_UNRESOLVED")
    return rows[0]["security_id"]


def official_targets(master, instruments, sse, szse):
    targets = defaultdict(set)
    excluded = []
    for group in sse["groups"]:
        if group["key"][0] != "dividend":
            continue
        for evidence in group["evidence"]:
            row = evidence["normalized"]
            if START <= row["ex_date"] <= END:
                sid = security_at(
                    master,
                    instruments,
                    "SSE",
                    row["source_symbol"],
                    row["record_date"],
                    row["ex_date"],
                )
                if sid is None:
                    excluded.append((row["source_symbol"], row["record_date"], row["ex_date"]))
                    continue
                targets[(sid, row["record_date"], row["ex_date"])].add(Decimal(row["amount"]))
    for row in szse["rows"]:
        amount = row["raw_cells"][5].strip()
        if (
            row["symbol"].startswith(("0", "3"))
            and amount
            and Decimal(amount) > 0
            and START <= row["ex_date"] <= END
        ):
            sid = security_at(
                master,
                instruments,
                "SZSE",
                row["symbol"],
                row["record_date"],
                row["ex_date"],
            )
            if sid is None:
                excluded.append((row["symbol"], row["record_date"], row["ex_date"]))
                continue
            targets[(sid, row["record_date"], row["ex_date"])].add(Decimal(amount))
    return targets, sorted(set(excluded))


def validate_event(row):
    event = CorporateAction.model_validate(row["event"])
    require_supported_corporate_action(event)
    if event.event_checksum != row["event_checksum"] or event.action_type != "CASH_DIVIDEND":
        raise ValueError("ACCEPTED_CASH_EVENT_CHANGED")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--master", type=Path, required=True)
    parser.add_argument("--instruments", type=Path, required=True)
    parser.add_argument("--sse-audit", type=Path, required=True)
    parser.add_argument("--szse-audit", type=Path, required=True)
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--addition", type=Path, action="append", default=[])
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    master = json.loads(args.master.read_bytes())
    instruments, sse, szse, baseline = map(
        verified, (args.instruments, args.sse_audit, args.szse_audit, args.baseline)
    )
    instrument_types = {
        row["classification"]["security_id"]["value"]: row["classification"]["instrument_type"]
        for row in instruments["classifications"]
    }
    addition_paths = sorted(args.addition, key=str)
    additions = [verified(path) for path in addition_paths]
    events = merge_events(baseline["events"], [ledger["events"] for ledger in additions])
    if events != merge_events(
        baseline["events"], [ledger["events"] for ledger in reversed(additions)]
    ):
        raise ValueError("INPUT_ORDER_CHANGED")
    for row in events:
        validate_event(row)

    targets, out_of_scope = official_targets(master, instrument_types, sse, szse)
    accepted = {
        (
            row["event"]["security_id"]["value"],
            row["event"]["record_date"],
            row["event"]["ex_date"],
        ): row
        for row in events
        if START <= row["event"]["ex_date"] <= END
    }
    if len(accepted) != sum(START <= row["event"]["ex_date"] <= END for row in events):
        raise ValueError("DUPLICATE_ACCEPTED_CASH_DATE")
    gaps = [
        dict(
            security_id=key[0],
            record_date=key[1],
            ex_date=key[2],
            exchange_amounts=sorted(str(amount) for amount in amounts),
        )
        for key, amounts in sorted(targets.items())
        if key not in accepted
    ]
    extras = [
        dict(security_id=key[0], record_date=key[1], ex_date=key[2])
        for key in sorted(accepted.keys() - targets.keys())
    ]
    report = dict(
        parser_version="FULL_CASH_LEDGER_COVERAGE_V1",
        parser_sha256=sha256_file(Path(__file__)),
        coverage=[START, END],
        inputs=[
            dict(path=str(path), sha256=sha256_file(path))
            for path in [
                args.master,
                args.instruments,
                args.sse_audit,
                args.szse_audit,
                args.baseline,
                *addition_paths,
            ]
        ],
        official_cash_events=len(targets),
        accepted_events=len(events),
        accepted_in_range=len(accepted),
        covered_official_cash_events=len(targets.keys() & accepted.keys()),
        unresolved_official_cash_events=len(gaps),
        unresolved_by_ex_year=dict(sorted(Counter(row["ex_date"][:4] for row in gaps).items())),
        accepted_not_in_current_exchange_census=len(extras),
        out_of_scope_exchange_cash_rows=len(out_of_scope),
        out_of_scope_exchange_events=[
            dict(symbol=row[0], record_date=row[1], ex_date=row[2]) for row in out_of_scope
        ],
        unresolved_events=gaps,
        accepted_outside_current_exchange_census=extras,
        events=events,
        input_order_reproducibility="PASS",
        checksum_repeatability="PASS",
        full_dataset_created=False,
        full_dataset_frozen=False,
    )
    report["manifest_sha256"] = canonical_sha256(report)
    write_immutable(args.output, canonical_json_bytes(report) + b"\n")
    print(
        json.dumps(
            {key: value for key, value in report.items() if not isinstance(value, list)},
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
