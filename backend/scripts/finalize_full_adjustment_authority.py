"""Close full adjustment authority by partitioning every retained factor change."""

import argparse
import json
from decimal import Decimal, localcontext
from pathlib import Path

from app.data.catalog.checksums import canonical_json_bytes, canonical_sha256, sha256_file
from app.data.catalog.freeze import write_immutable
from app.domain.markets.corporate_actions import CorporateAction, CorporateActionType
from scripts.audit_adjustment_factor_economics import sse_pre_closes, szse_pre_closes
from scripts.build_cash_gap_queue import verified


def factor_id(row: dict) -> str:
    return f"FACTOR:{row['security_id']}:{row['effective_date']}"


def partition_factor_changes(universe: set[str], groups: dict[str, set[str]]) -> list[dict]:
    owners = {}
    for classification, events in sorted(groups.items()):
        for event in events:
            if event in owners:
                raise ValueError(f"DUPLICATE_FACTOR_CLASSIFICATION:{event}")
            owners[event] = classification
    if set(owners) != universe:
        missing = sorted(universe - set(owners))
        extra = sorted(set(owners) - universe)
        raise ValueError(f"FACTOR_PARTITION_MISMATCH:missing={missing}:extra={extra}")
    return [{"factor_change": event, "classification": owners[event]} for event in sorted(owners)]


def official_cash_overlay(event_row: dict, pre_close: Decimal) -> dict:
    action = CorporateAction.model_validate(event_row["event"])
    if action.event_checksum != event_row["event_checksum"]:
        raise ValueError("CASH_EVENT_CHECKSUM_CHANGED")
    if action.action_type is not CorporateActionType.CASH_DIVIDEND or action.cash_per_share <= 0:
        raise ValueError("UNSUPPORTED_MISSING_FACTOR_EVENT")
    if pre_close <= action.cash_per_share:
        raise ValueError("INVALID_OFFICIAL_CASH_OVERLAY")
    with localcontext() as context:
        context.prec = 50
        factor_step = pre_close / (pre_close - action.cash_per_share)
    return {
        "security_id": action.security_id.value,
        "effective_date": action.ex_date.isoformat(),
        "action_type": action.action_type.value,
        "cash_per_share": str(action.cash_per_share),
        "raw_pre_close": str(pre_close),
        "factor_step": str(factor_step),
        "composition": "MULTIPLY_PROVIDER_FACTOR_FROM_EFFECTIVE_DATE_FORWARD",
        "event_checksum": action.event_checksum,
        "source_url": action.source_url,
        "source_sha256": action.source_document_sha256,
        "status": "OFFICIAL_MISSING_PROVIDER_FACTOR_OVERLAY_PASS",
    }


def require_pass_rows(report: dict, expected_status: str | None = None) -> set[str]:
    if expected_status and report["status"] != expected_status:
        raise ValueError(f"REQUIRED_AUDIT_NOT_PASS:{report['report_id']}")
    rows = report["rows"]
    if any("PASS" not in row["status"] for row in rows):
        raise ValueError(f"FACTOR_AUDIT_CONFLICT:{report['report_id']}")
    return {row["factor_change"] for row in rows}


def audit(
    inventory: dict,
    routing: dict,
    economics: dict,
    residual: dict,
    special: dict,
    remaining: dict,
    cash_ledger: dict,
    pre_closes: dict[tuple[str, str], Decimal],
) -> dict:
    changes = {factor_id(row): row for row in inventory["factor_changes"]}
    if len(changes) != inventory["counts"]["factor_change_dates"]:
        raise ValueError("FACTOR_CHANGE_IDENTITY_COLLISION")
    matched = {
        event
        for event, row in changes.items()
        if row["status"] == "SUPPORTED_EVENT_DATE_MATCH_ONLY"
    }
    unmatched = set(changes) - matched
    routes = {factor_id(row): row for row in routing["rows"]}
    if set(routes) != unmatched:
        raise ValueError("ROUTING_SCOPE_CHANGED")

    bonus_pass = {
        event
        for event, row in routes.items()
        if row["route"] == "RETAINED_OFFICIAL_BONUS_SOURCE_DATE"
        and row["factor_economic_alignment_status"] == "OFFICIAL_BONUS_FACTOR_ALIGNMENT_PASS"
    }
    bonus_conflicts = {
        event
        for event, row in routes.items()
        if row["route"] == "RETAINED_OFFICIAL_BONUS_SOURCE_DATE"
        and row["factor_economic_alignment_status"] == "OFFICIAL_BONUS_FACTOR_ALIGNMENT_CONFLICT"
    }
    no_bonus_date = {
        event for event, row in routes.items() if row["route"] == "NO_RETAINED_OFFICIAL_BONUS_DATE"
    }

    economic = require_pass_rows(economics)
    residual_events = require_pass_rows(residual, "OFFICIAL_RESIDUAL_MECHANICS_IN_SCOPE_PASS")
    special_events = require_pass_rows(special, "OFFICIAL_SPECIAL_MECHANICS_FACTOR_ALIGNMENT_PASS")
    remaining_events = require_pass_rows(remaining, "OFFICIAL_REMAINING_MECHANICS_PASS")
    if special_events != bonus_conflicts:
        raise ValueError("SPECIAL_MECHANICS_SCOPE_CHANGED")
    if economic | residual_events | remaining_events != no_bonus_date:
        raise ValueError("NO_BONUS_DATE_MECHANICS_SCOPE_CHANGED")

    classifications = partition_factor_changes(
        set(changes),
        {
            "OFFICIAL_EVENT_DATE_BOUND_PROVIDER_FACTOR": matched,
            "OFFICIAL_BONUS_ORACLE_FACTOR_PARITY": bonus_pass,
            "OFFICIAL_SPECIAL_MECHANICS_FACTOR_PARITY": special_events,
            "OFFICIAL_GROSS_TERMS_FACTOR_PARITY": economic,
            "OFFICIAL_RESIDUAL_MECHANICS_FACTOR_PARITY": residual_events,
            "OFFICIAL_REMAINING_MECHANICS_FACTOR_PARITY": remaining_events,
        },
    )

    ledger = {row["event_checksum"]: row for row in cash_ledger["events"]}
    deferred = {
        (
            row["factor_change"].removeprefix("FACTOR:").rsplit(":", 1)[0],
            row["official_ex_date"],
        ): row
        for row in remaining["rows"]
        if row.get("official_ex_date")
    }
    deferred_rows, overlays = [], []
    for item in inventory["supported_events_without_factor_change"]:
        event_row = ledger.get(item["event_checksum"])
        if event_row is None:
            raise ValueError("UNBOUND_SUPPORTED_EVENT_WITHOUT_FACTOR_CHANGE")
        action = CorporateAction.model_validate(event_row["event"])
        if action.event_checksum != item["event_checksum"]:
            raise ValueError("SUPPORTED_EVENT_CHECKSUM_CHANGED")
        key = (item["security_id"], item["ex_date"])
        if row := deferred.get(key):
            deferred_rows.append(
                {
                    **item,
                    "provider_factor_change": row["factor_change"],
                    "status": row["status"],
                }
            )
            continue
        symbol = item["security_id"].rsplit(":", 1)[-1]
        pre_close = pre_closes.get((symbol, item["ex_date"]))
        if pre_close is None:
            raise ValueError("OFFICIAL_RAW_PRE_CLOSE_MISSING_FOR_OVERLAY")
        overlays.append(official_cash_overlay(event_row, pre_close))

    return {
        "report_id": "FULL_ADJUSTMENT_AUTHORITY_V1",
        "status": "PASS_OFFICIAL_EVENT_BOUND_PROVIDER_FACTORS_WITH_CASH_OVERLAYS",
        "adjustment_authority": "PASS_FOR_FULL_DATASET",
        "authority_accepted": True,
        "requested_coverage": inventory["requested_coverage"],
        "provider_factor_change_dates": len(changes),
        "factor_change_classifications": classifications,
        "factor_change_counts": {
            name: len(events)
            for name, events in sorted(
                {
                    "OFFICIAL_EVENT_DATE_BOUND_PROVIDER_FACTOR": matched,
                    "OFFICIAL_BONUS_ORACLE_FACTOR_PARITY": bonus_pass,
                    "OFFICIAL_SPECIAL_MECHANICS_FACTOR_PARITY": special_events,
                    "OFFICIAL_GROSS_TERMS_FACTOR_PARITY": economic,
                    "OFFICIAL_RESIDUAL_MECHANICS_FACTOR_PARITY": residual_events,
                    "OFFICIAL_REMAINING_MECHANICS_FACTOR_PARITY": remaining_events,
                }.items()
            )
        },
        "unresolved_factor_changes": 0,
        "supported_events_without_same_date_provider_factor": len(
            inventory["supported_events_without_factor_change"]
        ),
        "provider_deferred_factor_events": sorted(
            deferred_rows, key=lambda row: (row["security_id"], row["ex_date"])
        ),
        "official_cash_overlay_events": sorted(
            overlays, key=lambda row: (row["security_id"], row["effective_date"])
        ),
        "unresolved_supported_events": 0,
        "dataset_created": False,
        "dataset_frozen": False,
        "limitations": [
            "Provider factors are feature-series normalization only and never create cash, "
            "share entitlements, or portfolio corporate actions.",
            "Three official cash events absent from the provider curve require the persisted "
            "forward multiplier overlays in this report during Full Dataset materialization.",
            "Frozen-vintage provider factors do not prove historical publication availability.",
        ],
    }


def reverse_rows(report: dict, key: str = "rows") -> dict:
    return dict(report, **{key: list(reversed(report[key]))})


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    for name in (
        "inventory",
        "routing",
        "economics",
        "residual",
        "special",
        "remaining",
        "cash-ledger",
        "szse-root",
        "szse-report",
        "sse-root",
        "sse-report",
        "output",
    ):
        parser.add_argument(f"--{name}", type=Path, required=True)
    args = parser.parse_args()
    inventory, routing, economics, residual, special, remaining, cash_ledger = map(
        verified,
        (
            args.inventory,
            args.routing,
            args.economics,
            args.residual,
            args.special,
            args.remaining,
            args.cash_ledger,
        ),
    )
    deferred = {
        (row["factor_change"].removeprefix("FACTOR:").rsplit(":", 1)[0], row["official_ex_date"])
        for row in remaining["rows"]
        if row.get("official_ex_date")
    }
    overlay_requests = {
        (row["security_id"].rsplit(":", 1)[-1], row["ex_date"])
        for row in inventory["supported_events_without_factor_change"]
        if (row["security_id"], row["ex_date"]) not in deferred
    }
    szse_report = json.loads(args.szse_report.read_bytes())
    sse_report = json.loads(args.sse_report.read_bytes())
    pre_closes = {
        **szse_pre_closes(
            args.szse_root,
            szse_report,
            {item for item in overlay_requests if item[0].startswith(("0", "3"))},
        ),
        **sse_pre_closes(
            args.sse_root,
            sse_report,
            {item for item in overlay_requests if not item[0].startswith(("0", "3"))},
        ),
    }
    reports = (inventory, routing, economics, residual, special, remaining, cash_ledger)
    report = audit(*reports, pre_closes)
    replay = audit(
        reverse_rows(inventory, "factor_changes"),
        reverse_rows(routing),
        reverse_rows(economics),
        reverse_rows(residual),
        reverse_rows(special),
        reverse_rows(remaining),
        reverse_rows(cash_ledger, "events"),
        pre_closes,
    )
    if report != replay:
        raise ValueError("INPUT_ORDER_CHANGED")
    inputs = (
        args.inventory,
        args.routing,
        args.economics,
        args.residual,
        args.special,
        args.remaining,
        args.cash_ledger,
        args.szse_report,
        args.sse_report,
    )
    report.update(
        input_order_reproducibility="PASS",
        checksum_repeatability="PASS",
        inputs=[{"path": str(path), "sha256": sha256_file(path)} for path in inputs],
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
                    "adjustment_authority",
                    "provider_factor_change_dates",
                    "factor_change_counts",
                    "unresolved_factor_changes",
                    "supported_events_without_same_date_provider_factor",
                    "unresolved_supported_events",
                    "manifest_sha256",
                )
            }
        )
    )


if __name__ == "__main__":
    main()
