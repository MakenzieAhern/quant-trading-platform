"""Replace rounded SSE cash rows only with exact pre-record issuer terms."""

import argparse
import json
import re
from collections import defaultdict
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

from app.data.catalog.checksums import canonical_json_bytes, canonical_sha256, sha256_file
from app.data.catalog.freeze import write_immutable
from app.domain.markets.corporate_actions import CorporateAction, require_supported_corporate_action
from scripts.audit_p1_cash_census_counterexamples import PRIMARY, SECONDARY
from scripts.audit_p1_public_fact_requirements import verified
from scripts.link_distribution_notices import notice_dates
from scripts.reconcile_distribution_cash import issuer_code_matches, normalized_document
from scripts.retained_bonus_terms import retained_ratio

SUMMARY = re.compile(r"重要内容提示:.*?每股分配比例A股每股现金红利(\d+(?:\.\d+)?)元.*?相关日期")


def final_amount(pages, symbol):
    normalized = normalized_document(pages)
    if not issuer_code_matches(normalized, symbol):
        raise ValueError("ISSUER_IDENTITY_MISMATCH")
    text = re.sub(r"\s+", "", normalized)
    if "差异化分红送转:否" not in text:
        raise ValueError("DIFFERENTIATED_OR_MISSING_CASH_CLASS")
    matches = SUMMARY.findall(text)
    if len(matches) != 1:
        raise ValueError("NO_UNIQUE_FINAL_A_SHARE_SUMMARY")
    amount = Decimal(matches[0])
    if amount <= 0 or not re.search(
        r"本次利润分配以方案实施前[^。]{0,180}?每股派发现金红利"
        + re.escape(matches[0])
        + r"元\(含税\)",
        text,
    ):
        raise ValueError("FINAL_IMPLEMENTATION_BODY_DISAGREES")
    try:
        retained_ratio(pages, symbol)
    except ValueError as exc:
        if str(exc) != "NO_EXPLICIT_BONUS_RATIO":
            raise
    else:
        raise ValueError("BONUS_LEG_REQUIRES_SEPARATE_ACCOUNTING")
    return amount


def reconcile(requirements, triage, prior_ids, cash, master, sources, root):
    by_id = {row["document_id"]: row for row in triage}
    by_url = {row["url"]: row for row in sources}
    by_event = defaultdict(list)
    for row in cash:
        event = row["event"]
        by_event[(event["security_id"]["value"], event["ex_date"])].append(row)
    closed, events = [], []
    for requirement in requirements:
        title, document_id = requirement["title"], requirement["document_id"]
        if document_id in prior_ids or not PRIMARY.search(title) or SECONDARY.search(title):
            continue
        row = by_id[document_id]
        if (
            row["candidate_class"] != "NEITHER"
            or row["bonus_parser_error"] != "NO_EXPLICIT_BONUS_RATIO"
            or len(row["record_dates"]) != 1
            or len(row["ex_dates"]) != 1
        ):
            continue
        source = by_url[row["url"]]
        pdf = root / source["source_path"]
        cache = root / "batch-v1/text" / f"{row['source_sha256']}.json"
        if (
            source["retrieval_status"] != "PASS"
            or source["issuer"] != requirement["issuer"]
            or source["title"] != title
            or source["published_on"] != requirement["published_on"]
            or source["source_sha256"] != row["source_sha256"]
            or sha256_file(pdf) != row["source_sha256"]
            or sha256_file(cache) != row["text_cache_sha256"]
        ):
            raise ValueError("PRECISE_CASH_SOURCE_CHANGED")
        extracted = json.loads(cache.read_bytes())
        if extracted["source_sha256"] != row["source_sha256"]:
            raise ValueError("PRECISE_CASH_TEXT_CHANGED")
        try:
            amount = final_amount(extracted["pages"], requirement["issuer"])
        except ValueError as exc:
            if str(exc) in {
                "NO_UNIQUE_FINAL_A_SHARE_SUMMARY",
                "DIFFERENTIATED_OR_MISSING_CASH_CLASS",
            }:
                continue
            raise
        record, ex = row["record_dates"][0], row["ex_dates"][0]
        if (
            notice_dates(extracted["pages"]) != ([record], [ex])
            or not requirement["published_on"] <= record < ex
        ):
            raise ValueError("PRECISE_CASH_DATES_CHANGED")
        members = {
            item["security_id"]
            for item in master
            if item["symbol"] == requirement["issuer"]
            and item["instrument_type"] == "COMMON_A_SHARE"
            and item["effective_from"] <= record <= ex <= (item["effective_to"] or "2025-12-31")
        }
        if len(members) != 1:
            raise ValueError("PRECISE_CASH_IDENTITY_UNRESOLVED")
        sid = next(iter(members))
        peers = by_event[(sid, ex)]
        if len(peers) != 1 or peers[0]["event"]["record_date"] != record:
            raise ValueError("PRECISE_CASH_ACCEPTED_EVENT_UNRESOLVED")
        old = Decimal(peers[0]["event"]["cash_per_share"])
        if amount == old:
            continue
        if (
            amount.quantize(Decimal(1).scaleb(old.as_tuple().exponent), rounding=ROUND_HALF_UP)
            != old
        ):
            raise ValueError("PRECISE_CASH_NOT_EXCHANGE_ROUNDING")
        terms = {
            "security_id": sid,
            "record_date": record,
            "ex_date": ex,
            "cash_per_share": str(amount),
            "source_sha256": row["source_sha256"],
        }
        action = CorporateAction.model_validate(
            {
                "security_id": {"value": sid},
                "action_type": "CASH_DIVIDEND",
                "announcement_date": requirement["published_on"],
                "effective_date": ex,
                "record_date": record,
                "ex_date": ex,
                "cash_per_share": str(amount),
                "source_document": title,
                "source_url": row["url"],
                "source_document_sha256": row["source_sha256"],
                "retrieved_at": source["retrieved_at_utc"],
                "source_provider": "OFFICIAL_ISSUER_CNINFO_PRIMARY_IMPLEMENTATION",
                "source_version": "P1_PRECISE_SSE_CASH_SUMMARY_V1",
                "source_record_hash": canonical_sha256(terms),
                "completeness": "COMPLETE",
            }
        )
        require_supported_corporate_action(action)
        events.append(
            {
                "event": action.model_dump(mode="json"),
                "event_checksum": action.event_checksum,
                "supersedes_event_checksum": peers[0]["event_checksum"],
            }
        )
        closed.append(
            {
                "document_id": document_id,
                "affected_events": requirement["affected_events"],
                "security_id": sid,
                "url": row["url"],
                "source_sha256": row["source_sha256"],
                "text_cache_sha256": row["text_cache_sha256"],
                "record_date": record,
                "ex_date": ex,
                "old_cash_per_share": str(old),
                "cash_per_share": str(amount),
                "classification": "PRECISE_OFFICIAL_ISSUER_REPLACES_ROUNDED_SSE_ROW",
            }
        )
    return sorted(closed, key=lambda row: row["document_id"]), sorted(
        events, key=lambda row: row["event_checksum"]
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in (
        "closure",
        "triage",
        "prior",
        "cash-ledger",
        "master",
        "source-manifest",
        "source-root",
        "output",
    ):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    closure, triage, prior, cash, sources = (
        verified(path)
        for path in (args.closure, args.triage, args.prior, args.cash_ledger, args.source_manifest)
    )
    master = json.loads(args.master.read_bytes())
    if triage["closure_sha256"] != sha256_file(args.closure):
        raise ValueError("PRECISE_CASH_TRIAGE_CHANGED")
    ids = {row["document_id"] for row in prior["closed"]}
    inputs = (
        closure["remaining_cash_documents"],
        triage["documents"],
        cash["events"],
        master,
        sources["documents"],
    )
    closed, events = reconcile(inputs[0], inputs[1], ids, *inputs[2:], args.source_root)
    if (closed, events) != reconcile(
        *(list(reversed(rows)) for rows in inputs[:2]),
        ids,
        *(list(reversed(rows)) for rows in inputs[2:]),
        args.source_root,
    ):
        raise ValueError("INPUT_ORDER_CHANGED")
    if len(
        {(row["event"]["security_id"]["value"], row["event"]["ex_date"]) for row in events}
    ) != len(events):
        raise ValueError("DUPLICATE_PRECISE_CASH_EVENT")
    report = {
        "report_version": "P1_PRECISE_SSE_CASH_SUMMARY_V1",
        "parser_sha256": sha256_file(Path(__file__)),
        "input_sha256s": {
            name: sha256_file(path)
            for name, path in (
                ("closure", args.closure),
                ("triage", args.triage),
                ("prior", args.prior),
                ("cash_ledger", args.cash_ledger),
                ("master", args.master),
                ("source_manifest", args.source_manifest),
            )
        },
        "closed_documents": len(closed),
        "closed_facts": sum(len(row["affected_events"]) for row in closed),
        "closed": closed,
        "events": events,
        "input_order_reproducibility": "PASS",
        "full_cash_census_status": "PARTIAL",
    }
    report["manifest_sha256"] = canonical_sha256(report)
    write_immutable(args.output, canonical_json_bytes(report) + b"\n")
    print(json.dumps({key: value for key, value in report.items() if not isinstance(value, list)}))


if __name__ == "__main__":
    main()
