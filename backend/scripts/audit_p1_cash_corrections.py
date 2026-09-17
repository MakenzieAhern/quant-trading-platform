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
LIABILITY_RECORD_DATE = re.compile(r"至股权登记日:(\d{4})年(\d{1,2})月(\d{1,2})日")
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


def corrected_payment_and_record_date(pages):
    text = normalized("\n".join(pages))
    parts = re.split(r"更正前:?|更正后:?", text)
    if len(parts) != 3 or "除上述事项外,原公告其他内容不变" not in parts[2]:
        return None
    before, after = parts[1], parts[2].split("除上述事项外")[0]
    old_payment, new_payment = PAYMENT_DATE.findall(before), PAYMENT_DATE.findall(after)
    old_record, new_record = (
        LIABILITY_RECORD_DATE.findall(before),
        LIABILITY_RECORD_DATE.findall(after),
    )
    if any(len(dates) != 1 for dates in (old_payment, new_payment, old_record, new_record)):
        return None

    def scrub(value):
        return LIABILITY_RECORD_DATE.sub(
            "至股权登记日:<RECORD>", PAYMENT_DATE.sub("现金红利将于<PAYMENT>", value)
        )

    if scrub(before) != scrub(after):
        return None
    dates = {
        "original_payment_date": old_payment[0],
        "corrected_payment_date": new_payment[0],
        "original_record_date": old_record[0],
        "corrected_record_date": new_record[0],
    }
    result = {
        key: f"{int(value[0]):04d}-{int(value[1]):02d}-{int(value[2]):02d}"
        for key, value in dates.items()
    }
    if (
        result["original_payment_date"] == result["corrected_payment_date"]
        or result["original_record_date"] == result["corrected_record_date"]
        or result["corrected_record_date"] != result["original_payment_date"]
        or result["corrected_payment_date"] != result["original_record_date"]
    ):
        return None
    return result


def corrected_reference_price_only(pages):
    text = normalized("\n".join(pages))
    sections = re.split(r"更正前:|更正后:", text)
    if (
        len(sections) != 3
        or "现就公告中" not in sections[0]
        or "除权(息)参考价格" not in sections[0]
        or "内容进行更正" not in sections[0]
        or "除上述更正内容外" not in sections[2]
        or "其他内容不变" not in sections[2]
    ):
        return None
    before, after = sections[1], sections[2].split("除上述更正内容外")[0]
    pattern = r"实际分派的每股现金红利\)÷总股本=[\d,]+\u00d7(\d+(?:\.\d+)?)÷[\d,]+"
    old, new = re.findall(pattern, before), re.findall(pattern, after)
    if len(old) != 1 or old != new or before == after:
        return None
    if "虚拟分派的现金红利" not in after or "前收盘价格" not in after:
        return None
    return {"gross_cash_per_share_unchanged": old[0]}


def corrected_repurchase_share_count_only(pages):
    text = normalized("\n".join(pages))
    if "一、关于" not in text or "二、关于" not in text:
        return None
    dividend_section = text.split("一、关于", 1)[1].split("二、关于", 1)[0]
    sections = re.split(r"更正前:|更正后:", dividend_section)
    if len(sections) != 3 or "除上述更正外" not in sections[2]:
        return None
    before, after = sections[1], sections[2].split("除上述更正外")[0]
    # A page ordinal can sit immediately before the second paragraph in PDF text.
    before = re.sub(r"(?<=。)\d+(?=由于)", "", before)
    patterns = {
        "repurchased": r"公司回购股份余额为([\d,]+)股",
        "participating": r"实际参与分配的股份为([\d,]+)股",
        "payout": r"共计派发现金红利([\d,]+(?:\.\d+)?)元",
    }
    values = {}
    for name, pattern in patterns.items():
        old, new = re.findall(pattern, before), re.findall(pattern, after)
        if len(old) != 1 or len(new) != 1 or old == new:
            return None
        values[name] = old[0], new[0]
        before = before.replace(old[0], f"<{name}>")
        after = after.replace(new[0], f"<{name}>")
    if before != after:
        return None
    old_repurchased, new_repurchased = (int(x.replace(",", "")) for x in values["repurchased"])
    old_participating, new_participating = (
        int(x.replace(",", "")) for x in values["participating"]
    )
    old_payout, new_payout = (Decimal(x.replace(",", "")) for x in values["payout"])
    ratio = new_payout / new_participating
    if (
        new_repurchased - old_repurchased != old_participating - new_participating
        or old_payout / old_participating != ratio
        or ratio <= 0
    ):
        return None
    return {
        "corrected_repurchased_shares": new_repurchased,
        "corrected_participating_shares": new_participating,
        "corrected_total_cash": str(new_payout),
        "gross_cash_per_share_unchanged": str(ratio),
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


def corrected_entitlement_year(pages):
    text = normalized("\n".join(pages))
    sections = re.split(r"补充更正前:|补充更正后:", text)
    if len(sections) != 3 or "除上述补充更正内容外" not in sections[2]:
        return None
    before = sections[1][sections[1].find("三、股权登记日") :]
    after = sections[2].split("除上述补充更正内容外")[0]
    after = after[after.find("三、股权登记日") :]
    if not before.startswith("三、股权登记日") or not after.startswith("三、股权登记日"):
        return None
    old, new = (
        re.findall(r"股权登记日为:(\d{4})年(\d{1,2})月(\d{1,2})日", before),
        re.findall(r"股权登记日为:(\d{4})年(\d{1,2})月(\d{1,2})日", after),
    )
    ex_old, ex_new = (
        re.findall(r"除权除息日为:(\d{4})年(\d{1,2})月(\d{1,2})日", before),
        re.findall(r"除权除息日为:(\d{4})年(\d{1,2})月(\d{1,2})日", after),
    )
    if (
        len(old) != 1
        or len(new) != 1
        or len(ex_old) != 1
        or len(ex_new) != 1
        or old[0][0] != ex_old[0][0]
        or new[0][0] != ex_new[0][0]
        or int(new[0][0]) != int(old[0][0]) + 1
        or before.replace(old[0][0] + "年", new[0][0] + "年") != after
    ):
        return None
    return {
        "original_record_date": f"{old[0][0]}-{int(old[0][1]):02d}-{int(old[0][2]):02d}",
        "corrected_record_date": f"{new[0][0]}-{int(new[0][1]):02d}-{int(new[0][2]):02d}",
        "original_ex_date": f"{ex_old[0][0]}-{int(ex_old[0][1]):02d}-{int(ex_old[0][2]):02d}",
        "corrected_ex_date": f"{ex_new[0][0]}-{int(ex_new[0][1]):02d}-{int(ex_new[0][2]):02d}",
    }


def corrected_cash_amount(pages):
    text = normalized("\n".join(pages))
    sections = re.split(r"原披露内容:|现更正为:", text)
    if len(sections) != 3 or "除上述更正外" not in sections[2]:
        return None
    before, after = sections[1], sections[2].split("除上述更正外")[0]
    pattern = r"每10股派发现金红利(\d+(?:\.\d+)?)元\(含税\)"
    old, new = re.findall(pattern, before), re.findall(pattern, after)
    if len(old) != 1 or len(new) != 1 or old == new or before.replace(old[0], new[0]) != after:
        return None
    return {
        "original_cash_per_share": str(Decimal(old[0]) / 10),
        "corrected_cash_per_share": str(Decimal(new[0]) / 10),
    }


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
        entitlement_year = (
            "补充更正公告" in requirement["title"] and row["candidate_class"] == "NEITHER"
        )
        cash_amount = "更正公告" in requirement["title"] and row["candidate_class"] == "NEITHER"
        if (
            not (share_count or payment or bonus_removal or entitlement_year or cash_amount)
            or (not bonus_removal and row["bonus_candidate_per_share"] is not None)
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
            corrected_entitlement_year(extracted["pages"])
            if entitlement_year
            else unchanged_except_share_count(extracted["pages"])
            if share_count
            else bonus_removed_without_cash_change(extracted["pages"])
            if bonus_removal
            else corrected_cash_amount(extracted["pages"])
            or unchanged_except_payment_date(extracted["pages"])
            or corrected_payment_and_record_date(extracted["pages"])
            or corrected_reference_price_only(extracted["pages"])
            or corrected_repurchase_share_count_only(extracted["pages"])
        )
        if change:
            cash_amount = "corrected_cash_per_share" in change
            payment = "corrected_payment_date" in change
        reference_only = bool(change and "gross_cash_per_share_unchanged" in change)
        repurchase = bool(change and "corrected_repurchased_shares" in change)
        if (
            not change
            or (
                bonus_removal
                and Decimal(change["removed_bonus_ratio"])
                != Decimal(row["bonus_candidate_per_share"])
            )
            or (
                entitlement_year
                and (
                    set(row["record_dates"])
                    != {change["original_record_date"], change["corrected_record_date"]}
                    or set(row["ex_dates"])
                    != {change["original_ex_date"], change["corrected_ex_date"]}
                )
            )
            or (
                (row["record_dates"] or row["ex_dates"])
                and not entitlement_year
                and (
                    "corrected_record_date" not in change
                    or set(row["record_dates"])
                    != {change["original_record_date"], change["corrected_record_date"]}
                    or row["ex_dates"]
                )
            )
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
                and (
                    normalized(original["title"]).removesuffix("公告")
                    in normalized(requirement["title"])
                    or (
                        cash_amount
                        and re.sub(
                            r"(?=\d{4}年)",
                            "关于",
                            normalized(original["title"]).removesuffix("公告"),
                            count=1,
                        )
                        in normalized(requirement["title"])
                    )
                    or (
                        repurchase
                        and "权益分派实施公告" in normalized(original["title"])
                        and "权益分派实施公告" in normalized(requirement["title"])
                        and f"{int(original['published_on'][:4])}年"
                        f"{int(original['published_on'][5:7])}月"
                        f"{int(original['published_on'][8:])}日"
                        in normalized("\n".join(extracted["pages"]))
                    )
                )
                and original["published_on"] <= requirement["published_on"] < event["record_date"]
                and event["record_date"] < event["ex_date"] <= "2025-12-31"
                and (
                    payment
                    or entitlement_year
                    or cash_amount
                    or reference_only
                    or Decimal(event["cash_per_share"]) == Decimal(row["cash_candidate_per_share"])
                )
                and (not payment or change["corrected_payment_date"] >= event["ex_date"])
                and (
                    not payment
                    or "corrected_record_date" not in change
                    or event["record_date"] == change["corrected_record_date"]
                )
                and (
                    not entitlement_year
                    or (
                        event["record_date"] == change["corrected_record_date"]
                        and event["ex_date"] == change["corrected_ex_date"]
                    )
                )
                and (
                    not cash_amount
                    or Decimal(event["cash_per_share"])
                    == Decimal(change["corrected_cash_per_share"])
                )
                and (
                    not reference_only
                    or Decimal(event["cash_per_share"])
                    == Decimal(change["gross_cash_per_share_unchanged"])
                )
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
                    "OFFICIAL_ENTITLEMENT_YEAR_CORRECTION"
                    if entitlement_year
                    else "OFFICIAL_GROSS_CASH_CORRECTION"
                    if cash_amount
                    else "OFFICIAL_PAYMENT_AND_RECORD_METADATA_CORRECTION_CASH_UNCHANGED"
                    if payment and "corrected_record_date" in change
                    else "OFFICIAL_REFERENCE_PRICE_CORRECTION_CASH_UNCHANGED"
                    if reference_only and not repurchase
                    else "OFFICIAL_REPURCHASE_COUNT_CORRECTION_CASH_UNCHANGED"
                    if repurchase
                    else "OFFICIAL_SHARE_COUNT_SUPPLEMENT_CASH_UNCHANGED"
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
    parser.add_argument("--prior-corrections", type=Path)
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
    earlier = verified(args.prior_corrections) if args.prior_corrections else {"closed": []}
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
    prior_ids = {row["document_id"] for row in earlier["closed"]}
    if not prior_ids.issubset(already_closed) or any(
        row["document_id"] in prior_ids for row in closed
    ):
        raise ValueError("PRIOR_CORRECTION_LINEAGE_CHANGED")
    closed = sorted([*earlier["closed"], *closed], key=lambda row: row["document_id"])
    input_paths = {
        "triage": args.triage,
        "closure": args.closure,
        "cash_ledger": args.cash_ledger,
        "source_manifest": args.source_manifest,
        "cumulative": args.cumulative,
    }
    if args.prior_corrections:
        input_paths["prior_corrections"] = args.prior_corrections
    report = {
        "report_version": "P1_CORRECTION_CASH_FACT_CLOSURE_V9",
        "parser_sha256": sha256_file(Path(__file__)),
        "input_sha256s": {name: sha256_file(path) for name, path in input_paths.items()},
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
