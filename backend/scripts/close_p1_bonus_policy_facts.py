"""Close exact ordinary-holder bonus P1 source facts after accounting approval."""

import argparse
import json
from pathlib import Path

from app.data.catalog.checksums import canonical_json_bytes, canonical_sha256, sha256_file
from app.data.catalog.freeze import write_immutable
from scripts.audit_p1_public_fact_requirements import verified

APPROVAL_SHA256 = "26bf7dafd15bf2eca4476b2dfeaa09b5fc95ee90dbe2769637ae9a21bfa603e5"
POLICY_ID = "CN_A_RETAINED_BONUS_FRACTIONAL_SHARE_POLICY_V1"


def close(rows: list[dict]) -> list[dict]:
    closed = []
    for row in rows:
        if (
            row["candidate_class"] != "BONUS_ONLY"
            or row["classification"] != "EXACT_OFFICIAL_BONUS_SOURCE_TERMS_ACCOUNTING_PENDING"
            or not row["affected_events"]
        ):
            raise ValueError(f"P1_BONUS_FACT_NOT_CLOSABLE:{row['document_id']}")
        closed.append(
            {
                "document_id": row["document_id"],
                "affected_events": row["affected_events"],
                "security_id": row["security_id"],
                "record_date": row["record_date"],
                "ex_date": row["ex_date"],
                "bonus_ratio": row["bonus_ratio"],
                "source_sha256": row["source_sha256"],
                "exchange_evidence_sha256": row["exchange_evidence_sha256"],
                "classification": "EXACT_OFFICIAL_BONUS_SOURCE_FACT_POLICY_CLOSED",
                "accounting_policy_id": POLICY_ID,
                "tradability_authority_scope": "SEPARATE_FULL_DATASET_GATE",
            }
        )
    return sorted(closed, key=lambda row: row["document_id"])


def close_differentiated(
    rows: list[dict], zero_cash_rows: list[dict], requirements: list[dict]
) -> list[dict]:
    zero_cash = {row["document_id"]: row for row in zero_cash_rows}
    by_id = {row["document_id"]: row for row in requirements}
    if len(zero_cash) != len(zero_cash_rows) or len(by_id) != len(requirements):
        raise ValueError("P1_DIFFERENTIATED_BONUS_IDENTITY_NOT_UNIQUE")
    closed = []
    for row in rows:
        requirement = by_id[row["document_id"]]
        corroboration = zero_cash.get(row["document_id"])
        if row["status"] == "EXPLICIT_ZERO_CASH_BONUS_SOURCE_TERMS_ACCOUNTING_PENDING":
            if not row["cash_explicitly_zero"]:
                raise ValueError("P1_DIFFERENTIATED_BONUS_ZERO_CASH_CHANGED")
        elif not (
            row["status"] == "CASH_OR_IDENTITY_NOT_CLOSED"
            and corroboration
            and corroboration["classification"]
            == "OFFICIAL_ZERO_CASH_CORROBORATED_ACCOUNTING_PENDING"
            and all(
                corroboration[key] == row[key]
                for key in ("security_id", "record_date", "ex_date", "bonus_ratio")
            )
        ):
            raise ValueError(f"P1_DIFFERENTIATED_BONUS_NOT_CLOSABLE:{row['document_id']}")
        closed.append(
            {
                "document_id": row["document_id"],
                "affected_events": requirement["affected_events"],
                "security_id": row["security_id"],
                "record_date": row["record_date"],
                "ex_date": row["ex_date"],
                "bonus_ratio": row["bonus_ratio"],
                "source_sha256": row["source_sha256"],
                "exchange_evidence_sha256": row["exchange_evidence_sha256"],
                "classification": "DIFFERENTIATED_OFFICIAL_BONUS_SOURCE_FACT_POLICY_CLOSED",
                "accounting_policy_id": POLICY_ID,
                "tradability_authority_scope": "SEPARATE_FULL_DATASET_GATE",
            }
        )
    return sorted(closed, key=lambda row: row["document_id"])


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-terms", type=Path, required=True)
    parser.add_argument("--differentiated", type=Path, required=True)
    parser.add_argument("--zero-cash", type=Path, required=True)
    parser.add_argument("--queue", type=Path, required=True)
    parser.add_argument("--policy", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    source = verified(args.source_terms)
    differentiated = verified(args.differentiated)
    zero_cash = verified(args.zero_cash)
    queue = json.loads(args.queue.read_bytes())
    policy = json.loads(args.policy.read_bytes())
    policies = {row["class"]: row for row in policy["policies"]}
    if (
        source["corroborated_documents"] != len(source["corroborated"])
        or policy["revision"] != 3
        or policy["lineage"]["retained_bonus_fraction_approval_sha256"] != APPROVAL_SHA256
        or policies["RETAINED_BONUS_FRACTION"]["policy_id"] != POLICY_ID
        or differentiated["candidate_documents"] != len(differentiated["classified"])
        or zero_cash["baseline_sha256"] != sha256_file(args.differentiated)
        or zero_cash["classification"]
        != "22_OF_22_ZERO_CASH_SOURCE_TERMS_CORROBORATED_ACCOUNTING_PENDING"
    ):
        raise ValueError("P1_BONUS_POLICY_INPUT_CHANGED")
    closed = close(source["corroborated"]) + close_differentiated(
        differentiated["classified"], zero_cash["rows"], queue
    )
    closed.sort(key=lambda row: row["document_id"])
    replay = close(list(reversed(source["corroborated"]))) + close_differentiated(
        list(reversed(differentiated["classified"])),
        list(reversed(zero_cash["rows"])),
        list(reversed(queue)),
    )
    replay.sort(key=lambda row: row["document_id"])
    if closed != replay:
        raise ValueError("P1_BONUS_POLICY_INPUT_ORDER_CHANGED")
    report = {
        "report_version": "P1_OFFICIAL_BONUS_POLICY_CLOSURE_V2",
        "parser_sha256": sha256_file(Path(__file__)),
        "input_sha256s": {
            "source_terms": sha256_file(args.source_terms),
            "differentiated": sha256_file(args.differentiated),
            "zero_cash": sha256_file(args.zero_cash),
            "queue": sha256_file(args.queue),
            "policy": sha256_file(args.policy),
        },
        "human_approval_sha256": APPROVAL_SHA256,
        "accounting_policy_id": POLICY_ID,
        "closed_documents": len(closed),
        "closed_facts": sum(len(row["affected_events"]) for row in closed),
        "closed": closed,
        "input_order_reproducibility": "PASS",
        "new_economic_events_created": 0,
        "event_admission_scope": "SOURCE_FACT_ONLY_TRADABILITY_REMAINS_SEPARATE",
        "full_dataset_created": False,
    }
    report["manifest_sha256"] = canonical_sha256(report)
    write_immutable(args.output, canonical_json_bytes(report) + b"\n")
    print(json.dumps({key: value for key, value in report.items() if key != "closed"}))


if __name__ == "__main__":
    main()
