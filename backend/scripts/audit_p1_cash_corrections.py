"""Close official distribution corrections that leave accepted cash terms unchanged."""

import argparse
import json
import re
import unicodedata
from decimal import Decimal
from pathlib import Path

from app.data.catalog.checksums import canonical_json_bytes, canonical_sha256, sha256_file
from app.data.catalog.freeze import write_immutable
from scripts.audit_p1_public_fact_requirements import verified
from scripts.triage_p1_remaining_distribution_docs import diagnose

SHARE_COUNT = re.compile(r"\d{1,3}(?:,\d{3})+股")
PAYMENT_DATE = re.compile(r"现金红利将于(\d{4})年(\d{1,2})月(\d{1,2})日")
REMOVED_BONUS = re.compile(r",同时,以资本公积金向全体股东每10股转增(\d+(?:\.\d+)?)股")
PAGE_GUARANTEE = (
    "本公司及董事会全体成员保证信息披露的内容真实、准确、完整,没有虚假记载、误导性陈述或重大遗漏。"
)


def normalized(text):
    return re.sub(r"\s+", "", unicodedata.normalize("NFKC", text))


def unchanged_except_share_count(pages):
    text = normalized("\n".join(pages))
    sections = re.split(r"原披露内容:|补充后内容:", text)
    if len(sections) != 3 or "除上述补充的内容外,原公告其他内容不变" not in sections[2]:
        return None
    before, after = sections[1], re.split(r"除上述补充的内容外", sections[2])[0]
    old, new = SHARE_COUNT.findall(before), SHARE_COUNT.findall(after)
    if not old or len(old) != len(new) or old == new:
        return None
    if SHARE_COUNT.sub("<SHARES>", before) != SHARE_COUNT.sub("<SHARES>", after):
        return None
    return {"original_share_counts": old, "supplemented_share_counts": new}


def unchanged_except_payment_date(pages):
    text = normalized("\n".join(pages))
    sections = re.split(r"更正前:|更正后:", text)
    if len(sections) != 3 or "除上述更正内容外,原公告其他内容不变" not in sections[2]:
        return None
    before, after = sections[1], sections[2].split("除上述更正内容外")[0]
    old, new = PAYMENT_DATE.findall(before), PAYMENT_DATE.findall(after)
    if len(old) != 1 or len(new) != 1 or old == new:
        return None
    if PAYMENT_DATE.sub("现金红利将于<PAYMENT_DATE>", before) != PAYMENT_DATE.sub(
        "现金红利将于<PAYMENT_DATE>", after
    ):
        return None
    return {
        "original_payment_date": f"{int(old[0][0]):04d}-{int(old[0][1]):02d}-{int(old[0][2]):02d}",
        "corrected_payment_date": f"{int(new[0][0]):04d}-{int(new[0][1]):02d}-{int(new[0][2]):02d}",
    }


def bonus_removed_without_cash_change(pages):
    text = normalized("\n".join(pages))
    sections = re.split(r"更正前:|更正后:", text)
    if len(sections) != 3 or "除上述更正内容外,原公告其他内容不变" not in sections[2]:
        return None
    before = sections[1].replace(PAGE_GUARANTEE, "")
    after = sections[2].split("除上述更正内容外")[0].replace(PAGE_GUARANTEE, "")
    found = REMOVED_BONUS.findall(before)
    if len(found) != 1 or REMOVED_BONUS.search(after):
        return None
    if REMOVED_BONUS.sub("", before) != after:
        return None
    return {"removed_bonus_ratio": str(Decimal(found[0]) / Decimal(10))}


def close_supplements(triage, requirements, cash, sources, root, already_closed):
    by_id = {row["document_id"]: row for row in requirements}
    by_url = {row["url"]: row for row in sources}
    closed = []
    for row in triage:
        if row["document_id"] in already_closed:
            continue
        requirement = by_id[row["document_id"]]
        share_count = "补充公告" in requirement["title"] and row["candidate_class"] == "CASH_ONLY"
        payment = "更正公告" in requirement["title"] and row["candidate_class"] == "NEITHER"
        bonus_removal = "更正公告" in requirement["title"] and row["candidate_class"] == "BOTH"
        if (
            not (share_count or payment or bonus_removal)
            or (not bonus_removal and row["bonus_candidate_per_share"] is not None)
            or row["record_dates"]
            or row["ex_dates"]
            or row["preferred_instrument_marker"]
        ):
            continue
        source = by_url[row["url"]]
        pdf = root / source["source_path"]
        cache = root / "batch-v1/text" / f"{source['source_sha256']}.json"
        if (
            source["retrieval_status"] != "PASS"
            or source["issuer"] != requirement["issuer"]
            or source["title"] != requirement["title"]
            or source["published_on"] != requirement["published_on"]
            or source["source_sha256"] != row["source_sha256"]
            or sha256_file(pdf) != row["source_sha256"]
            or sha256_file(cache) != row["text_cache_sha256"]
        ):
            raise ValueError("P1_SUPPLEMENT_SOURCE_CHANGED")
        extracted = json.loads(cache.read_bytes())
        if extracted["source_sha256"] != row["source_sha256"]:
            raise ValueError("P1_SUPPLEMENT_EXTRACTION_CHANGED")
        parsed = diagnose(extracted["pages"], requirement["issuer"])
        if any(parsed[key] != row[key] for key in parsed):
            raise ValueError("P1_SUPPLEMENT_TERMS_CHANGED")
        change = (
            unchanged_except_share_count(extracted["pages"])
            if share_count
            else unchanged_except_payment_date(extracted["pages"])
            if payment
            else bonus_removed_without_cash_change(extracted["pages"])
        )
        if not change or (
            bonus_removal
            and Decimal(change["removed_bonus_ratio"]) != Decimal(row["bonus_candidate_per_share"])
        ):
            continue
        accepted = []
        for item in cash:
            event = item["event"]
            original = by_url.get(event["source_url"])
            if (
                event["security_id"]["value"].endswith(":" + requirement["issuer"])
                and original is not None
                and original["retrieval_status"] == "PASS"
                and original["issuer"] == requirement["issuer"]
                and event["source_document_sha256"] == original["source_sha256"]
                and event["source_provider"].startswith("OFFICIAL_ISSUER_CNINFO_")
                and event["announcement_date"] == original["published_on"]
                and normalized(original["title"]).removesuffix("公告")
                in normalized(requirement["title"])
                and original["published_on"] <= requirement["published_on"] < event["record_date"]
                and event["record_date"] < event["ex_date"] <= "2025-12-31"
                and (
                    payment
                    or Decimal(event["cash_per_share"]) == Decimal(row["cash_candidate_per_share"])
                )
                and (not payment or change["corrected_payment_date"] >= event["ex_date"])
            ):
                accepted.append((item, original))
        if len(accepted) != 1:
            continue
        item, original = accepted[0]
        if sha256_file(root / original["source_path"]) != original["source_sha256"]:
            raise ValueError("P1_SUPPLEMENT_ORIGINAL_SOURCE_CHANGED")
        event = item["event"]
        closed.append(
            {
                "document_id": row["document_id"],
                "affected_events": requirement["affected_events"],
                "classification": (
                    "OFFICIAL_SHARE_COUNT_SUPPLEMENT_CASH_UNCHANGED"
                    if share_count
                    else "OFFICIAL_PAYMENT_DATE_CORRECTION_CASH_UNCHANGED"
                    if payment
                    else "OFFICIAL_BONUS_REMOVAL_CASH_UNCHANGED"
                ),
                "url": row["url"],
                "source_sha256": row["source_sha256"],
                "text_cache_sha256": row["text_cache_sha256"],
                "original_url": original["url"],
                "original_sha256": original["source_sha256"],
                "accepted_event_checksum": item["event_checksum"],
                "security_id": event["security_id"]["value"],
                "record_date": event["record_date"],
                "ex_date": event["ex_date"],
                "cash_per_share": str(Decimal(event["cash_per_share"])),
                **change,
            }
        )
    return sorted(closed, key=lambda item: item["document_id"])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--triage", type=Path, required=True)
    parser.add_argument("--closure", type=Path, required=True)
    parser.add_argument("--cash-ledger", type=Path, required=True)
    parser.add_argument("--source-manifest", type=Path, required=True)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--cumulative", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    triage, closure, cash, sources, cumulative = (
        verified(path)
        for path in (
            args.triage,
            args.closure,
            args.cash_ledger,
            args.source_manifest,
            args.cumulative,
        )
    )
    inputs = (
        triage["documents"],
        closure["remaining_cash_documents"],
        cash["events"],
        sources["documents"],
    )
    already_closed = {row["document_id"] for row in cumulative["closed"]}
    closed = close_supplements(*inputs, args.source_root, already_closed)
    if closed != close_supplements(
        *(list(reversed(rows)) for rows in inputs), args.source_root, already_closed
    ):
        raise ValueError("INPUT_ORDER_CHANGED")
    report = {
        "report_version": "P1_CORRECTION_CASH_FACT_CLOSURE_V5",
        "parser_sha256": sha256_file(Path(__file__)),
        "input_sha256s": {
            name: sha256_file(path)
            for name, path in (
                ("triage", args.triage),
                ("closure", args.closure),
                ("cash_ledger", args.cash_ledger),
                ("source_manifest", args.source_manifest),
                ("cumulative", args.cumulative),
            )
        },
        "closed_documents": len(closed),
        "closed_facts": sum(len(row["affected_events"]) for row in closed),
        "closed": closed,
        "input_order_reproducibility": "PASS",
        "no_new_economic_event_created": True,
    }
    report["manifest_sha256"] = canonical_sha256(report)
    write_immutable(args.output, canonical_json_bytes(report) + b"\n")
    print(json.dumps({key: value for key, value in report.items() if key != "closed"}))


if __name__ == "__main__":
    main()
