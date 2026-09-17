"""Scope non-primary bond, option and buyback notices to accepted issuer cash."""

import argparse
import json
import re
from collections import defaultdict
from datetime import date
from decimal import Decimal
from pathlib import Path

from app.data.catalog.checksums import canonical_json_bytes, canonical_sha256, sha256_file
from app.data.catalog.freeze import write_immutable
from scripts.audit_p1_public_fact_requirements import verified
from scripts.triage_p1_remaining_distribution_docs import diagnose

DERIVATIVE = re.compile(
    r"停止转股|转股连续停牌|转股价格|股票期权.*行权价格|回购(?:股份)?价格上限|"
    r"员工持股计划.*购买价格调整|调整.*员工持股计划.*购买价格|调整.*向特定对象发行.*价格"
)
COMPLETED_DATE = re.compile(r"(20\d{2})\s*年\s*(\d{1,2})\s*月\s*(\d{1,2})\s*日\s*实施完毕")


def completed_dates(pages):
    dates = set()
    for parts in COMPLETED_DATE.findall(re.sub(r"\s+", "", "\n".join(pages))):
        try:
            dates.add(date(*map(int, parts)).isoformat())
        except ValueError:
            continue
    return dates


def classify(requirements, triage, prior_ids, cash, completed_dates=None):
    completed_dates = completed_dates or {}
    by_id = {row["document_id"]: row for row in triage}
    by_symbol = defaultdict(list)
    for row in cash:
        event = row["event"]
        by_symbol[event["security_id"]["value"].split(":")[-1]].append(row)
    closed = []
    for requirement in requirements:
        document_id = requirement["document_id"]
        if document_id in prior_ids or not DERIVATIVE.search(requirement["title"]):
            continue
        row = by_id[document_id]
        if (
            row["candidate_class"] != "CASH_ONLY"
            or row["cash_candidate_per_share"] is None
            or row["preferred_instrument_marker"]
        ):
            continue
        historical_year = re.search(r"(?:根据|因)(\d{4})年", requirement["title"])
        candidates = [
            accepted
            for accepted in by_symbol[requirement["issuer"]]
            if (
                -10
                <= (
                    date.fromisoformat(accepted["event"]["ex_date"])
                    - date.fromisoformat(requirement["published_on"])
                ).days
                <= 75
                or (
                    historical_year
                    and 0
                    <= (
                        date.fromisoformat(requirement["published_on"])
                        - date.fromisoformat(accepted["event"]["ex_date"])
                    ).days
                    <= 400
                    and historical_year[1] in accepted["event"]["source_document"]
                    and (
                        "半年度" not in requirement["title"]
                        or "半年度" in accepted["event"]["source_document"]
                    )
                )
                or (
                    accepted["event"]["ex_date"] in completed_dates.get(document_id, set())
                    and 0
                    <= (
                        date.fromisoformat(requirement["published_on"])
                        - date.fromisoformat(accepted["event"]["ex_date"])
                    ).days
                    <= 400
                )
            )
            and (
                not row["record_dates"]
                or row["record_dates"] == [accepted["event"].get("record_date")]
            )
            and (not row["ex_dates"] or row["ex_dates"] == [accepted["event"]["ex_date"]])
            and Decimal(accepted["event"]["cash_per_share"])
            == Decimal(row["cash_candidate_per_share"])
            and accepted["event"]["source_url"].startswith(
                "https://static.cninfo.com.cn/finalpage/"
            )
            and accepted["event"]["source_provider"].startswith("OFFICIAL_ISSUER_CNINFO_")
            and accepted["event"]["source_url"] != row["url"]
        ]
        if len(candidates) != 1:
            continue
        accepted = candidates[0]
        closed.append(
            {
                "document_id": document_id,
                "affected_events": requirement["affected_events"],
                "issuer": requirement["issuer"],
                "title": requirement["title"],
                "published_on": requirement["published_on"],
                "url": row["url"],
                "source_sha256": row["source_sha256"],
                "text_cache_sha256": row["text_cache_sha256"],
                "cash_per_share": row["cash_candidate_per_share"],
                "accepted_event_checksum": accepted["event_checksum"],
                "accepted_event_ex_date": accepted["event"]["ex_date"],
                "accepted_primary_source_url": accepted["event"]["source_url"],
                "classification": "NON_PRIMARY_DERIVATIVE_EXACT_ACCEPTED_ISSUER_EVENT",
            }
        )
    return sorted(closed, key=lambda row: row["document_id"])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in (
        "closure",
        "triage",
        "prior",
        "cash-ledger",
        "source-manifest",
        "source-root",
        "output",
    ):
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--queue", type=Path)
    args = parser.parse_args()
    closure, triage, prior, cash, sources = (
        verified(path)
        for path in (args.closure, args.triage, args.prior, args.cash_ledger, args.source_manifest)
    )
    requirements = (
        json.loads(args.queue.read_bytes()) if args.queue else closure["remaining_cash_documents"]
    )
    baseline = {row["document_id"]: row for row in closure["remaining_cash_documents"]}
    if (
        len(baseline) != len(closure["remaining_cash_documents"])
        or len({row["document_id"] for row in requirements}) != len(requirements)
        or len(triage["documents"]) != len(requirements)
        or {row["document_id"] for row in triage["documents"]}
        != {row["document_id"] for row in requirements}
        or any(baseline.get(row["document_id"]) != row for row in requirements)
        or triage["source_requirements_sha256" if args.queue else "closure_sha256"]
        != sha256_file(args.queue or args.closure)
        or triage["source_manifest_sha256"] != sha256_file(args.source_manifest)
    ):
        raise ValueError("DERIVATIVE_TRIAGE_CHANGED")
    ids = {row["document_id"] for row in prior["closed"]}
    by_url = {row["url"]: row for row in sources["documents"]}
    by_id = {row["document_id"]: row for row in triage["documents"]}
    historical = {}
    for requirement in requirements:
        if not DERIVATIVE.search(requirement["title"]):
            continue
        row, source = by_id[requirement["document_id"]], by_url[requirement["url"]]
        pdf = args.source_root / source["source_path"]
        cache = args.source_root / "batch-v1/text" / f"{row['source_sha256']}.json"
        if (
            source["retrieval_status"] != "PASS"
            or source["issuer"] != requirement["issuer"]
            or source["source_sha256"] != row["source_sha256"]
            or sha256_file(pdf) != row["source_sha256"]
            or sha256_file(cache) != row["text_cache_sha256"]
        ):
            raise ValueError("DERIVATIVE_OFFICIAL_SOURCE_CHANGED")
        extracted = json.loads(cache.read_bytes())
        if extracted["source_sha256"] != row["source_sha256"]:
            raise ValueError("DERIVATIVE_OFFICIAL_EXTRACTION_CHANGED")
        historical[requirement["document_id"]] = completed_dates(extracted["pages"])
    inputs = (requirements, triage["documents"], cash["events"])
    closed = classify(*inputs[:2], ids, inputs[2], historical)
    if closed != classify(
        *(list(reversed(rows)) for rows in inputs[:2]), ids, list(reversed(inputs[2])), historical
    ):
        raise ValueError("INPUT_ORDER_CHANGED")
    for row in closed:
        source = by_url[row["url"]]
        pdf = args.source_root / source["source_path"]
        cache = args.source_root / "batch-v1/text" / f"{row['source_sha256']}.json"
        if (
            source["retrieval_status"] != "PASS"
            or source["issuer"] != row["issuer"]
            or source["title"] != row["title"]
            or source["published_on"] != row["published_on"]
            or source["source_sha256"] != row["source_sha256"]
            or sha256_file(pdf) != row["source_sha256"]
            or sha256_file(cache) != row["text_cache_sha256"]
        ):
            raise ValueError("DERIVATIVE_OFFICIAL_SOURCE_CHANGED")
        extracted = json.loads(cache.read_bytes())
        parsed = diagnose(extracted["pages"], row["issuer"])
        if (
            extracted["source_sha256"] != row["source_sha256"]
            or parsed["candidate_class"] != "CASH_ONLY"
            or parsed["record_dates"] != by_id[row["document_id"]]["record_dates"]
            or parsed["ex_dates"] != by_id[row["document_id"]]["ex_dates"]
            or Decimal(parsed["cash_candidate_per_share"]) != Decimal(row["cash_per_share"])
        ):
            raise ValueError("DERIVATIVE_NOTICE_TERMS_CHANGED")
    combined = sorted([*prior["closed"], *closed], key=lambda row: row["document_id"])
    if len(combined) != len({row["document_id"] for row in combined}):
        raise ValueError("DERIVATIVE_PRIOR_CONFLICT")
    report = {
        "report_version": "P1_NON_PRIMARY_DERIVATIVE_CASH_SCOPE_V4",
        "parser_sha256": sha256_file(Path(__file__)),
        "input_sha256s": {
            name: sha256_file(path)
            for name, path in (
                ("closure", args.closure),
                ("triage", args.triage),
                ("prior", args.prior),
                ("cash_ledger", args.cash_ledger),
                ("source_manifest", args.source_manifest),
                *([("queue", args.queue)] if args.queue else []),
            )
        },
        "closed_documents": len(combined),
        "closed_facts": sum(len(row["affected_events"]) for row in combined),
        "closed": combined,
        "input_order_reproducibility": "PASS",
        "no_new_economic_event_created": True,
    }
    report["manifest_sha256"] = canonical_sha256(report)
    write_immutable(args.output, canonical_json_bytes(report) + b"\n")
    print(json.dumps({key: value for key, value in report.items() if key != "closed"}))


if __name__ == "__main__":
    main()
