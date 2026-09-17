"""Out-scope official proposals with no final distribution terms or dates."""

import argparse
import json
import re
from datetime import date
from decimal import Decimal
from pathlib import Path

from app.data.catalog.checksums import canonical_json_bytes, canonical_sha256, sha256_file
from app.data.catalog.freeze import write_immutable
from scripts.audit_p1_public_fact_requirements import verified
from scripts.triage_p1_remaining_distribution_docs import diagnose

PROPOSAL_TITLE = re.compile(
    r"提议.*(?:分红|利润分配)|拟实施.*中期分红|"
    r"授权(?:公司)?董事会.*(?:中期分红|中期利润分配)"
)
MIDTERM_TITLE = re.compile(r"实施\d{4}年(?:度)?中期分红")
NO_DISTRIBUTION_TITLE = re.compile(r"(?:拟不实施.*利润分配|不实施.*中期现金分红)")
DEFERRED_TITLE = re.compile(r"推迟.*利润分配实施")
CONDITIONAL_TEXT = re.compile(r"尚需|不确定|后续.*方案|届时.*公告|提请.*授权|具体.*另行公告")


def classify(requirements, triage, already_closed, cash=()):
    by_id = {row["document_id"]: row for row in triage}
    final_by_symbol = {}
    for accepted in cash:
        event = accepted["event"]
        if (
            event["source_url"].startswith("https://static.cninfo.com.cn/finalpage/")
            and event["source_provider"].startswith("OFFICIAL_ISSUER_CNINFO_")
            and re.search(r"实施公告|实施的公告", event["source_document"])
        ):
            final_by_symbol.setdefault(event["security_id"]["value"].split(":")[-1], []).append(
                accepted
            )
    rows = []
    for requirement in requirements:
        document_id = requirement["document_id"]
        title = requirement["title"]
        no_distribution = bool(NO_DISTRIBUTION_TITLE.search(title))
        deferred = bool(DEFERRED_TITLE.search(title))
        if document_id in already_closed or not (
            PROPOSAL_TITLE.search(title)
            or MIDTERM_TITLE.search(title)
            or no_distribution
            or deferred
        ):
            continue
        row = by_id[document_id]
        if (
            row["candidate_class"] not in {"NEITHER", "CASH_ONLY"}
            or ((no_distribution or deferred) and row["candidate_class"] != "NEITHER")
            or row["record_dates"]
            or row["ex_dates"]
            or row["preferred_instrument_marker"]
        ):
            continue
        linked = None
        if row["candidate_class"] == "CASH_ONLY":
            published = date.fromisoformat(requirement["published_on"])
            matches = [
                accepted
                for accepted in final_by_symbol.get(requirement["issuer"], [])
                if Decimal(accepted["event"]["cash_per_share"])
                == Decimal(row["cash_candidate_per_share"])
                and published
                < date.fromisoformat(accepted["event"]["announcement_date"])
                <= date.fromisoformat(accepted["event"]["ex_date"])
                and 0 < (date.fromisoformat(accepted["event"]["ex_date"]) - published).days <= 180
            ]
            if len(matches) != 1:
                continue
            linked = matches[0]
        result = {
            "document_id": document_id,
            "affected_events": requirement["affected_events"],
            "issuer": requirement["issuer"],
            "title": requirement["title"],
            "url": requirement["url"],
            "source_sha256": row["source_sha256"],
            "text_cache_sha256": row["text_cache_sha256"],
            "classification": (
                "NONFINAL_NO_DISTRIBUTION_NOTICE"
                if no_distribution
                else "NONFINAL_DEFERRED_IMPLEMENTATION_NOTICE"
                if deferred
                else "NONFINAL_CASH_PROPOSAL_MATCHED_LATER_OFFICIAL_IMPLEMENTATION"
                if linked
                else "NONFINAL_PROPOSAL_NO_EXECUTABLE_CASH_OR_BONUS_TERMS"
            ),
        }
        if linked:
            result["accepted_event_checksum"] = linked["event_checksum"]
            result["accepted_event_ex_date"] = linked["event"]["ex_date"]
            result["accepted_primary_source_url"] = linked["event"]["source_url"]
            result["cash_per_share"] = row["cash_candidate_per_share"]
        rows.append(result)
    return sorted(rows, key=lambda item: item["document_id"])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--closure", type=Path, required=True)
    parser.add_argument("--triage", type=Path, required=True)
    parser.add_argument("--prior", type=Path, required=True)
    parser.add_argument("--prior-proposals", type=Path)
    parser.add_argument("--source-manifest", type=Path, required=True)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--cash-ledger", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    closure, triage, prior, sources, cash = (
        verified(path)
        for path in (args.closure, args.triage, args.prior, args.source_manifest, args.cash_ledger)
    )
    earlier = verified(args.prior_proposals) if args.prior_proposals else {"closed": []}
    if triage["closure_sha256"] != sha256_file(args.closure):
        raise ValueError("TRIAGE_CLOSURE_CHANGED")
    excluded = {row["document_id"] for row in prior["closed"]}
    rows = classify(
        closure["remaining_cash_documents"], triage["documents"], excluded, cash["events"]
    )
    if rows != classify(
        list(reversed(closure["remaining_cash_documents"])),
        list(reversed(triage["documents"])),
        excluded,
        list(reversed(cash["events"])),
    ):
        raise ValueError("INPUT_ORDER_CHANGED")
    by_url = {row["url"]: row for row in sources["documents"]}
    for row in rows:
        source = by_url[row["url"]]
        pdf = args.source_root / source["source_path"]
        cache = args.source_root / "batch-v1/text" / f"{row['source_sha256']}.json"
        if (
            source["retrieval_status"] != "PASS"
            or source["issuer"] != row["issuer"]
            or source["title"] != row["title"]
            or source["source_sha256"] != row["source_sha256"]
            or sha256_file(pdf) != row["source_sha256"]
            or sha256_file(cache) != row["text_cache_sha256"]
        ):
            raise ValueError("PROPOSAL_SOURCE_CHANGED")
        extracted = json.loads(cache.read_bytes())
        text = "\n".join(extracted["pages"])
        parsed = diagnose(extracted["pages"], row["issuer"])
        compact = re.sub(r"\s+", "", text)
        required_marker = (
            "不实施"
            if row["classification"] == "NONFINAL_NO_DISTRIBUTION_NOTICE"
            else "推迟"
            if row["classification"] == "NONFINAL_DEFERRED_IMPLEMENTATION_NOTICE"
            else None
        )
        if (
            extracted["source_sha256"] != row["source_sha256"]
            or parsed["candidate_class"] not in {"NEITHER", "CASH_ONLY"}
            or parsed["record_dates"]
            or parsed["ex_dates"]
            or (
                row["classification"]
                == "NONFINAL_CASH_PROPOSAL_MATCHED_LATER_OFFICIAL_IMPLEMENTATION"
                and Decimal(parsed["cash_candidate_per_share"]) != Decimal(row["cash_per_share"])
            )
            or (
                required_marker not in compact
                if required_marker
                else not CONDITIONAL_TEXT.search(compact)
            )
        ):
            raise ValueError("PROPOSAL_NOT_NONFINAL")
    old_ids = {row["document_id"] for row in earlier["closed"]}
    if not old_ids.issubset(excluded) or any(row["document_id"] in old_ids for row in rows):
        raise ValueError("PRIOR_PROPOSAL_LINEAGE_CHANGED")
    rows = sorted([*earlier["closed"], *rows], key=lambda row: row["document_id"])
    inputs = {
        "closure": args.closure,
        "triage": args.triage,
        "prior": args.prior,
        "source_manifest": args.source_manifest,
        "cash_ledger": args.cash_ledger,
    }
    if args.prior_proposals:
        inputs["prior_proposals"] = args.prior_proposals
    report = {
        "report_version": "P1_OFFICIAL_NONFINAL_PROPOSAL_SCOPE_V4",
        "parser_sha256": sha256_file(Path(__file__)),
        "input_sha256s": {key: sha256_file(path) for key, path in inputs.items()},
        "closed_documents": len(rows),
        "closed_facts": sum(len(row["affected_events"]) for row in rows),
        "closed": rows,
        "input_order_reproducibility": "PASS",
        "no_new_economic_event_created": True,
    }
    report["manifest_sha256"] = canonical_sha256(report)
    write_immutable(args.output, canonical_json_bytes(report) + b"\n")
    print(json.dumps({key: value for key, value in report.items() if key != "closed"}))


if __name__ == "__main__":
    main()
