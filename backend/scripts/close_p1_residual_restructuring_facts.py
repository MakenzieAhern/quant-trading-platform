"""Close residual restructuring distribution facts under the approved holder policy."""

import argparse
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

from app.data.catalog.checksums import canonical_json_bytes, canonical_sha256, sha256_file
from app.data.catalog.freeze import write_immutable
from app.domain.markets.corporate_actions import CorporateAction, require_supported_corporate_action
from scripts.audit_p1_public_fact_requirements import verified
from scripts.reconcile_retained_bonus_fraction_policy import (
    APPROVAL_SHA256,
    POLICY_ID,
    restructuring_holder_ratio,
)

RESTRUCTURING = re.compile(r"重整|资本公积")
PRIMARY_TITLE = re.compile(r"权益分派实施(?:的)?公告|重整计划.*转增股本事项?实施(?:的)?公告")


def classify(groups: dict[str, list[dict]], prior: list[dict]) -> tuple[list[dict], list[dict]]:
    prior_by_issuer = defaultdict(list)
    for row in prior:
        prior_by_issuer[row["issuer"]].append(row)
    closed, events = [], []
    for issuer, rows in sorted(groups.items()):
        positive = []
        zero = []
        for row in rows:
            try:
                ratio = restructuring_holder_ratio(row["pages"])
            except ValueError:
                continue
            (positive if ratio else zero).append((row, ratio))
        if positive:
            primary = min(
                positive,
                key=lambda item: (
                    not bool(PRIMARY_TITLE.search(item[0]["title"])),
                    item[0]["published_on"],
                    item[0]["document_id"],
                ),
            )
            source, ratio = primary
            records, ex_dates = source["record_dates"], source["ex_dates"]
            if len(records) != 1 or len(ex_dates) != 1:
                raise ValueError(f"RESTRUCTURING_ENTITLEMENT_DATES_UNRESOLVED:{issuer}")
            listing_token = (
                f"上市日为{int(ex_dates[0][:4])}年{int(ex_dates[0][5:7])}月{int(ex_dates[0][8:])}日"
            )
            listing_date = (
                ex_dates[0] if any(listing_token in row["text"] for row in rows) else None
            )
            event = CorporateAction.model_validate(
                {
                    "security_id": {"value": source["security_id"]},
                    "action_type": "BONUS_SHARE",
                    "announcement_date": source["published_on"],
                    "effective_date": ex_dates[0],
                    "record_date": records[0],
                    "ex_date": ex_dates[0],
                    "listing_date": listing_date,
                    "share_ratio": str(ratio),
                    "source_document": source["title"],
                    "source_url": source["url"],
                    "source_document_sha256": source["source_sha256"],
                    "retrieved_at": source["retrieved_at_utc"],
                    "source_provider": "OFFICIAL_ISSUER_CNINFO",
                    "source_version": "RESIDUAL_RESTRUCTURING_HOLDER_POLICY_V1",
                    "source_record_hash": canonical_sha256(
                        {
                            "document_id": source["document_id"],
                            "record_date": records[0],
                            "ex_date": ex_dates[0],
                            "share_ratio": str(ratio),
                        }
                    ),
                    "completeness": "COMPLETE",
                }
            )
            require_supported_corporate_action(event)
            events.append(
                {
                    "event": event.model_dump(mode="json"),
                    "event_checksum": event.event_checksum,
                    "policy_id": POLICY_ID,
                    "classification": "ORDINARY_HOLDER_RESTRUCTURING_ENTITLEMENT",
                    "actual_tradability": (
                        "CONFIRMED_ON_EX_DATE" if event.listing_date else "NOT_EVIDENCED"
                    ),
                }
            )
            evidence = source
            classification = "OFFICIAL_ORDINARY_HOLDER_RESTRUCTURING_ENTITLEMENT"
        else:
            evidence = min(
                (row for row, _ in zero),
                key=lambda row: (row["published_on"], row["document_id"]),
                default=None,
            )
            if evidence is None and prior_by_issuer[issuer]:
                evidence = min(
                    prior_by_issuer[issuer],
                    key=lambda row: (row["published_on"], row["document_id"]),
                )
            if evidence is None:
                raise ValueError(f"RESTRUCTURING_HOLDER_ENTITLEMENT_UNRESOLVED:{issuer}")
            classification = "OFFICIAL_NO_ORIGINAL_HOLDER_ENTITLEMENT"
        for row in rows:
            closed.append(
                {
                    "document_id": row["document_id"],
                    "affected_events": row["affected_events"],
                    "issuer": issuer,
                    "classification": classification,
                    "holder_ratio": str(ratio) if positive else "0",
                    "source_sha256": row["source_sha256"],
                    "evidence_document_id": evidence["document_id"],
                    "evidence_source_sha256": evidence["source_sha256"],
                    "accounting_policy_id": POLICY_ID,
                }
            )
    return sorted(closed, key=lambda row: row["document_id"]), sorted(
        events, key=lambda row: row["event"]["security_id"]["value"]
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    for name in (
        "queue",
        "triage",
        "prior",
        "source-manifest",
        "source-root",
        "master",
        "policy",
        "output",
    ):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    queue = json.loads(args.queue.read_bytes())
    triage, prior, sources = (
        verified(path) for path in (args.triage, args.prior, args.source_manifest)
    )
    master = json.loads(args.master.read_bytes())
    policy = json.loads(args.policy.read_bytes())
    if (
        triage["source_requirements_sha256"] != sha256_file(args.queue)
        or triage["source_manifest_sha256"] != sha256_file(args.source_manifest)
        or policy["lineage"]["retained_bonus_fraction_approval_sha256"] != APPROVAL_SHA256
        or not any(row.get("policy_id") == POLICY_ID for row in policy["policies"])
    ):
        raise ValueError("RESIDUAL_RESTRUCTURING_INPUT_CHANGED")
    triage_by_id = {row["document_id"]: row for row in triage["documents"]}
    sources_by_id = {row["document_id"]: row for row in sources["documents"]}
    groups = defaultdict(list)
    for requirement in queue:
        if not RESTRUCTURING.search(requirement["title"]):
            continue
        row, source = (
            triage_by_id[requirement["document_id"]],
            sources_by_id[requirement["document_id"]],
        )
        cache = args.source_root / "batch-v1/text" / f"{source['source_sha256']}.json"
        extracted = json.loads(cache.read_bytes())
        identities = {
            item["security_id"]
            for item in master["records"]
            if item["symbol"] == requirement["issuer"]
            and item["effective_from"]
            <= requirement["published_on"]
            <= (item["effective_to"] or "9999-12-31")
        }
        if (
            source["retrieval_status"] != "PASS"
            or source["source_sha256"] != row["source_sha256"]
            or sha256_file(cache) != row["text_cache_sha256"]
            or extracted["source_sha256"] != row["source_sha256"]
            or len(identities) != 1
        ):
            raise ValueError(f"RESIDUAL_RESTRUCTURING_SOURCE_CHANGED:{requirement['document_id']}")
        groups[requirement["issuer"]].append(
            {
                **requirement,
                **row,
                "security_id": next(iter(identities)),
                "retrieved_at_utc": source["retrieved_at_utc"],
                "pages": extracted["pages"],
                "text": re.sub(r"\s+", "", "".join(extracted["pages"])),
            }
        )
    result = classify(groups, prior["closed"])
    reversed_result = classify(
        {issuer: list(reversed(rows)) for issuer, rows in reversed(list(groups.items()))},
        list(reversed(prior["closed"])),
    )
    if result != reversed_result:
        raise ValueError("RESIDUAL_RESTRUCTURING_INPUT_ORDER_CHANGED")
    closed, events = result
    report = {
        "report_version": "P1_RESIDUAL_RESTRUCTURING_FACT_CLOSURE_V2",
        "parser_sha256": sha256_file(Path(__file__)),
        "input_sha256s": {
            name: sha256_file(path)
            for name, path in (
                ("queue", args.queue),
                ("triage", args.triage),
                ("prior", args.prior),
                ("source_manifest", args.source_manifest),
                ("master", args.master),
                ("policy", args.policy),
            )
        },
        "closed_documents": len(closed),
        "closed_facts": sum(len(row["affected_events"]) for row in closed),
        "classifications": dict(sorted(Counter(row["classification"] for row in closed).items())),
        "new_economic_events_created": len(events),
        "closed": closed,
        "events": events,
        "input_order_reproducibility": "PASS",
        "full_dataset_created": False,
    }
    report["manifest_sha256"] = canonical_sha256(report)
    write_immutable(args.output, canonical_json_bytes(report) + b"\n")
    print(
        json.dumps({key: value for key, value in report.items() if key not in {"closed", "events"}})
    )


if __name__ == "__main__":
    main()
