"""Recover two bounded bonus source gaps from retained official CNINFO notices."""

import argparse
import json
from collections import Counter
from datetime import date
from decimal import Decimal
from pathlib import Path

from app.data.catalog.checksums import canonical_json_bytes, canonical_sha256, sha256_file
from app.data.catalog.freeze import write_immutable
from app.domain.markets.corporate_actions import CorporateAction, require_supported_corporate_action
from scripts.audit_p1_retained_cash_sources import issuer_body_finality
from scripts.link_distribution_notices import notice_dates
from scripts.reconcile_distribution_cash import verified
from scripts.retained_bonus_terms import retained_ratio

TARGETS = {
    ("603315", "2016-06-06", "2016-06-07"),
    ("603889", "2016-04-18", "2016-04-19"),
}


def select_sources(results, documents):
    unresolved = {
        (row["symbol"], row["record_date"], row["ex_date"]): row
        for row in results
        if row["status"] == "UNRESOLVED_TERMS_OR_LIFECYCLE"
        and not row["evidence"]
        and not row["unresolved_documents"]
    }
    if set(unresolved) != TARGETS:
        raise ValueError("BONUS_SOURCE_GAP_SET_CHANGED")
    selected = {}
    for key, row in unresolved.items():
        matches = [
            doc
            for doc in documents
            if doc.get("issuer") == key[0]
            and doc.get("retrieval_status") == "PASS"
            and doc.get("url", "").startswith("https://static.cninfo.com.cn/finalpage/")
            and doc.get("published_on", "") <= key[1]
            and (date.fromisoformat(key[1]) - date.fromisoformat(doc["published_on"])).days <= 15
            and doc.get("source_sha256")
        ]
        if len(matches) != 1:
            raise ValueError(f"BONUS_OFFICIAL_SOURCE_NOT_UNIQUE:{key[0]}")
        selected[key] = (row, matches[0])
    return selected


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("prior", "source-manifest", "staging", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    prior, source = verified(args.prior), verified(args.source_manifest)
    for item in prior["inputs"]:
        if sha256_file(Path(item["path"])) != item["sha256"]:
            raise ValueError("PRIOR_BONUS_INPUT_CHANGED")
    selected = select_sources(prior["results"], source["documents"])
    if selected != select_sources(
        list(reversed(prior["results"])), list(reversed(source["documents"]))
    ):
        raise ValueError("BONUS_SOURCE_INPUT_ORDER_CHANGED")
    bonus = args.staging / "full-bonus-inventory-v1"
    oracle = verified(bonus / "source-oracle-v1.json")
    boundary = verified(bonus / "listing-boundary-check-v2.json")
    master = verified(args.staging / "full-code-transitions-v1/master-code-intervals.json")
    instruments = verified(
        args.staging / "full-instrument-scope-v1/classification-manifest-v3.json"
    )
    by_oracle = {(row["symbol"], row["record_date"], row["ex_date"]): row for row in oracle["rows"]}
    by_boundary = {(row["symbol"], row["ex_date"]): row for row in boundary["rows"]}
    ordinary = {
        row["classification"]["security_id"]["value"]
        for row in instruments["classifications"]
        if row["classification"]["instrument_type"] == "COMMON_A_SHARE"
    }
    source_root = args.source_manifest.parent.parent
    replacements, accepted, receipts = {}, [], []
    for key, (original, doc) in sorted(selected.items()):
        symbol, record, ex = key
        ratio = Decimal(original["ratio"])
        oracle_row = by_oracle[key]
        schedule = by_boundary[symbol, ex]
        if (
            {Decimal(item["ratio"]) for item in oracle_row["evidence"]} != {ratio}
            or oracle_row["ratio_consistency"] != "SINGLE_DISPLAYED_RATIO"
            or schedule["status"] != "NEXT_ACCEPTED_SESSION"
        ):
            raise ValueError(f"BONUS_OFFICIAL_ORACLE_OR_SCHEDULE_CONFLICT:{symbol}")
        pdf = (source_root / doc["source_path"]).resolve()
        cache = source_root / "batch-v1/text" / f"{doc['source_sha256']}.json"
        if (
            not pdf.is_relative_to(args.staging.resolve())
            or sha256_file(pdf) != doc["source_sha256"]
            or not cache.is_file()
        ):
            raise ValueError(f"BONUS_OFFICIAL_SOURCE_BYTES_CHANGED:{symbol}")
        extracted = json.loads(cache.read_bytes())
        finality = issuer_body_finality(doc["title"], extracted["pages"])
        if (
            extracted["source_sha256"] != doc["source_sha256"]
            or not finality
            or retained_ratio(extracted["pages"], symbol) != ratio
            or notice_dates(extracted["pages"]) != ([record], [ex])
        ):
            raise ValueError(f"BONUS_OFFICIAL_TERMS_CHANGED:{symbol}")
        members = [
            member
            for member in master["records"]
            if member["symbol"] == symbol
            and member["security_id"] in ordinary
            and member["effective_from"] <= record < ex <= (member["effective_to"] or "2025-12-31")
            and member["listing_date"] <= record
            and schedule["next_session"] <= (member["delisting_date"] or "2025-12-31")
        ]
        if len(members) != 1:
            raise ValueError(f"BONUS_STABLE_ID_NOT_UNIQUE:{symbol}")
        result = {
            **original,
            "evidence": [doc],
            "unresolved_documents": [],
            "status": "EXACT_INTEGER_RETAINED_BONUS",
        }
        action = CorporateAction.model_validate(
            dict(
                security_id={"value": members[0]["security_id"]},
                action_type="BONUS_SHARE",
                announcement_date=doc["published_on"],
                effective_date=ex,
                record_date=record,
                ex_date=ex,
                listing_date=schedule["next_session"],
                share_ratio=str(ratio),
                source_document=doc["title"],
                source_url=doc["url"],
                source_document_sha256=doc["source_sha256"],
                retrieved_at=doc["retrieved_at_utc"],
                source_provider="OFFICIAL_ISSUER_CNINFO_EXCHANGE_RECONCILED",
                source_version="INTEGER_RETAINED_BONUS_SUPPLEMENT_V1",
                source_record_hash=canonical_sha256(result),
                completeness="COMPLETE",
            )
        )
        require_supported_corporate_action(action)
        replacements[key] = result
        accepted.append(
            dict(
                event=action.model_dump(mode="json"),
                event_checksum=action.event_checksum,
                policy_id="BASIS_CONSERVED_RETAINED_BONUS",
                support_state="SUPPORTED_FOR_INTEGER_HOLDINGS_NEXT_SESSION_SCHEDULE",
                source_oracle_evidence_sha256=oracle_row["evidence_sha256"],
                scheduled_listing_not_actual_tradability=True,
                accounting_scope="INTEGER_HOLDINGS_NO_FRACTION_NEXT_SESSION_SCHEDULE",
            )
        )
        receipts.append(
            dict(
                symbol=symbol,
                source_url=doc["url"],
                source_sha256=doc["source_sha256"],
                text_cache_sha256=sha256_file(cache),
                issuer_body_finality_marker=finality,
                oracle_evidence_sha256=oracle_row["evidence_sha256"],
                scheduled_listing_date=schedule["next_session"],
            )
        )
    results = [
        replacements.get((row["symbol"], row["record_date"], row["ex_date"]), row)
        for row in prior["results"]
    ]
    events = sorted(
        [*prior["events"], *accepted],
        key=lambda row: (
            row["event"]["security_id"]["value"],
            row["event"]["record_date"],
            row["event"]["ex_date"],
        ),
    )
    report = {
        **{key: value for key, value in prior.items() if key != "manifest_sha256"},
        "results": results,
        "events": events,
        "accepted_events": len(events),
        "counts": dict(Counter(row["status"] for row in results)),
        "inputs": [
            *prior["inputs"],
            {"path": str(args.prior), "sha256": sha256_file(args.prior)},
            {"path": str(args.source_manifest), "sha256": sha256_file(args.source_manifest)},
        ],
        "parser_sha256": sha256_file(Path(__file__)),
        "source_finality_parser_sha256": sha256_file(
            Path(__file__).with_name("audit_p1_retained_cash_sources.py")
        ),
        "supplemental_official_source_receipts": receipts,
        "full_dataset_created": False,
    }
    if report["counts"] != {
        "EXACT_INTEGER_RETAINED_BONUS": 278,
        "UNRESOLVED_TERMS_OR_LIFECYCLE": 10,
    }:
        raise ValueError("BONUS_SUPPLEMENT_COUNTS_CHANGED")
    report["manifest_sha256"] = canonical_sha256(report)
    write_immutable(args.output, canonical_json_bytes(report) + b"\n")
    print(
        json.dumps(
            {
                key: value
                for key, value in report.items()
                if key not in {"results", "events", "inputs"}
            }
        )
    )


if __name__ == "__main__":
    main()
