"""Rebind retained factor curves to the accepted full master; never certify economic parity."""

import argparse
import json
from collections import Counter, defaultdict
from datetime import UTC, date, datetime
from itertools import pairwise
from pathlib import Path

from app.data.catalog.checksums import sha256_file
from app.data.catalog.freeze import write_immutable
from app.domain.markets.corporate_actions import CorporateAction, require_supported_corporate_action
from scripts.audit_full_cash_ledger import verified
from scripts.reconcile_sse_cninfo import canonical, sha
from scripts.sina_adjustment_audit import factor_at, parse_factors

START, END = "2010-01-01", "2025-12-31"


def interval_key(row):
    symbol = row["symbol"]
    if not symbol.startswith(("sh", "sz")):
        symbol = {"SSE": "sh", "SZSE": "sz"}[row["exchange"]] + symbol
    start = max(START, row["effective_from"])
    end = min(END, row["effective_to"] or END)
    if start > end or any(date.fromisoformat(day).isoformat() != day for day in (start, end)):
        raise ValueError("INVALID_TARGET_INTERVAL")
    return row["security_id"], symbol, start, end


def inside(root, path):
    value = (root / path).resolve()
    if not value.is_relative_to(root.resolve()):
        raise ValueError("SOURCE_OUTSIDE_STAGING")
    return value


def source_curve(root, source, symbol):
    path = inside(root, source["path"])
    metadata_path = path.with_suffix(path.suffix + ".meta.json")
    metadata = json.loads(metadata_path.read_bytes())
    expected_url = f"https://finance.sina.com.cn/realstock/company/{symbol}/hfq.js"
    if (
        sha256_file(path) != source["sha256"]
        or metadata["sha256"] != source["sha256"]
        or source["url"] != expected_url
        or metadata["url"] != expected_url
        or metadata.get("error")
    ):
        raise ValueError("FACTOR_SOURCE_IDENTITY_OR_CHECKSUM_CHANGED")
    retrieved = datetime.fromisoformat(metadata["retrieved_at_utc"])
    if retrieved.utcoffset() is None:
        raise ValueError("NAIVE_SOURCE_TIMESTAMP")
    return parse_factors(path.read_bytes(), symbol, "hfq"), dict(
        path=path.relative_to(root.resolve()).as_posix(),
        sha256=source["sha256"],
        metadata_sha256=sha256_file(metadata_path),
        url=expected_url,
        retrieved_at_utc=retrieved.astimezone(UTC).isoformat(),
    )


def partition_curve(curve, start, end):
    baseline = max((row for row in curve if row[0] <= start), default=None)
    if baseline is None:
        raise ValueError("UNKNOWN_FACTOR_BASELINE")
    assert baseline[1] == factor_at(curve, start)

    def encode(rows):
        return [[day, str(value)] for day, value in rows]

    return dict(
        baseline=encode([baseline])[0],
        period_rows=encode([row for row in curve if start <= row[0] <= end]),
        prior_rows_not_used=encode([row for row in curve if row[0] < baseline[0]]),
        after_interval_rows_not_used=encode([row for row in curve if row[0] > end]),
        change_dates=[
            current[0]
            for previous, current in pairwise(curve)
            if start <= current[0] <= end and previous[1] != current[1]
        ],
    )


def supported_events(ledgers):
    events = {}
    for ledger in ledgers:
        rows = ledger.get("events", ledger.get("rows"))
        if rows is None:
            raise ValueError("SUPPORTED_EVENT_LEDGER_ROWS_MISSING")
        for row in rows:
            event = CorporateAction.model_validate(row["event"])
            require_supported_corporate_action(event)
            if event.action_type not in {
                "CASH_DIVIDEND",
                "BONUS_SHARE",
                "RIGHTS_RELATED_EVENT",
            }:
                raise ValueError("UNSUPPORTED_COMPARISON_LEDGER")
            if event.event_checksum != row["event_checksum"] or not event.ex_date:
                raise ValueError("EVENT_CHECKSUM_CHANGED")
            if "OFFICIAL" not in event.source_provider.upper():
                raise ValueError("NON_OFFICIAL_EVENT_LEDGER")
            events[event.event_checksum] = dict(
                security_id=event.security_id.value,
                ex_date=event.ex_date.isoformat(),
                action_type=event.action_type.value,
                event_checksum=event.event_checksum,
            )
    return [events[key] for key in sorted(events)]


def reversed_ledger(ledger):
    key = "events" if "events" in ledger else "rows"
    return dict(ledger, **{key: list(reversed(ledger[key]))})


def audit(root, master, inventory, missing, missing_root, ledgers):
    targets = {interval_key(row): row for row in master}
    if len(targets) != len(master) or any(
        row["instrument_type"] != "COMMON_A_SHARE" for row in master
    ):
        raise ValueError("MASTER_INTERVAL_IDENTITY_INVALID")
    sources = defaultdict(list)
    for row in inventory["results"]:
        sources[interval_key(row)].extend(row.get("sources", []))
    for row in missing["results"]:
        sources[interval_key(row)].append(
            dict(row["source"], path=(missing_root / (row["symbol"] + "-hfq.js")).as_posix())
        )
    if set(sources) != set(targets):
        raise ValueError("FACTOR_INVENTORY_MASTER_INTERVAL_MISMATCH")
    events = supported_events(ledgers)
    event_dates = defaultdict(list)
    for event in events:
        event_dates[event["security_id"], event["ex_date"]].append(event)
    results, changes, gaps, matched_dates = [], [], [], set()
    for (sid, symbol, start, end), references in sorted(sources.items()):
        variants, receipts = {}, {}
        for source in sorted(references, key=lambda item: item["path"]):
            curve, receipt = source_curve(root, source, symbol)
            partition = partition_curve(curve, start, end)
            scoped = {key: partition[key] for key in ("baseline", "period_rows", "change_dates")}
            digest = sha(canonical(scoped))
            variants[digest] = scoped
            receipts[receipt["path"]] = dict(
                receipt,
                in_interval_sha256=digest,
                prior_rows_not_used=partition["prior_rows_not_used"],
                after_interval_rows_not_used=partition["after_interval_rows_not_used"],
            )
        result = dict(
            security_id=sid,
            symbol=symbol,
            effective_from=start,
            effective_to=end,
            sources=[receipts[key] for key in sorted(receipts)],
            in_interval_variants=variants,
            status="RETAINED_CURVE_VERIFIED" if len(variants) == 1 else "UNRESOLVED_CURVE_CONFLICT",
        )
        results.append(result)
        if len(variants) != 1:
            gaps.append(dict(security_id=sid, symbol=symbol, reason=result["status"]))
            continue
        for day in next(iter(variants.values()))["change_dates"]:
            matches = event_dates.get((sid, day), [])
            changes.append(
                dict(
                    security_id=sid,
                    symbol=symbol,
                    effective_date=day,
                    status="SUPPORTED_EVENT_DATE_MATCH_ONLY"
                    if matches
                    else "NO_SUPPORTED_EVENT_DATE",
                    supported_events=matches,
                )
            )
            if matches:
                matched_dates.add((sid, day))
    unmatched = [
        event
        for event in events
        if START <= event["ex_date"] <= END
        and (event["security_id"], event["ex_date"]) not in matched_dates
    ]
    return dict(
        parser_version="FULL_ADJUSTMENT_RETAINED_INVENTORY_V1",
        requested_coverage=[START, END],
        status="PARTIAL_ECONOMIC_ALIGNMENT_AND_EVENT_COMPLETENESS_NOT_ESTABLISHED",
        authority_accepted=False,
        dataset_created=False,
        counts=dict(
            master_intervals=len(targets),
            securities=len({key[0] for key in targets}),
            verified_intervals=sum(row["status"] == "RETAINED_CURVE_VERIFIED" for row in results),
            unresolved_intervals=len(gaps),
            unique_source_files=len({s["path"] for row in results for s in row["sources"]}),
            supported_events=len(events),
            factor_change_dates=len(changes),
            change_date_statuses=dict(sorted(Counter(row["status"] for row in changes).items())),
            supported_events_without_factor_change=len(unmatched),
        ),
        intervals=results,
        factor_changes=changes,
        unresolved_intervals=gaps,
        supported_events_without_factor_change=unmatched,
        limitations=[
            "Date agreement is not numerical factor/economic-term parity.",
            "Cash and integer-bonus ledgers are partial; unmatched dates are gaps, "
            "not invalid events.",
            "Mergers, other share changes and fractional bonus policies are not reconciled.",
            "Frozen-vintage source curves do not establish historical publication availability.",
            "No raw reference prices, strategy, tradability, materialization or "
            "freeze is evaluated.",
        ],
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("staging", "master", "master-report", "inventory", "missing", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--ledger", type=Path, action="append", required=True)
    args = parser.parse_args()
    root = args.staging.resolve()
    master = json.loads(args.master.read_bytes())
    master_report = verified(args.master_report)
    if master_report["security_master_core_authority"] != "PASS" or master_report[
        "reconstructed_master_sha256"
    ] != sha(canonical(master)):
        raise ValueError("ACCEPTED_MASTER_CHANGED")
    inventory, missing = verified(args.inventory), verified(args.missing)
    ledger_paths = sorted(args.ledger)
    ledgers = [verified(path) for path in ledger_paths]
    missing_root = args.missing.parent.resolve().relative_to(root)
    report = audit(root, master, inventory, missing, missing_root, ledgers)
    replay = audit(
        root,
        list(reversed(master)),
        dict(inventory, results=list(reversed(inventory["results"]))),
        dict(missing, results=list(reversed(missing["results"]))),
        missing_root,
        [reversed_ledger(row) for row in reversed(ledgers)],
    )
    if report != replay:
        raise ValueError("INPUT_ORDER_CHANGED")
    report.update(
        input_order_reproducibility="PASS",
        checksum_repeatability="PASS",
        parser_sha256=sha256_file(Path(__file__)),
        inputs=[
            dict(path=str(path.relative_to(root)), sha256=sha256_file(path))
            for path in sorted(
                [args.master, args.master_report, args.inventory, args.missing, *ledger_paths]
            )
        ],
    )
    report["manifest_sha256"] = sha(canonical(report))
    write_immutable(args.output, canonical(report) + b"\n")
    print(json.dumps({key: report[key] for key in ("status", "counts", "manifest_sha256")}))


if __name__ == "__main__":
    main()
