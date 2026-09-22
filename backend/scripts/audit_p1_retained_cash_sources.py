"""Close stale P1 cash requests using retained final issuer PDFs and exchange dates."""

import argparse
import json
import re
import unicodedata
from collections import Counter
from datetime import date, timedelta
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

from app.data.catalog.checksums import canonical_json_bytes, canonical_sha256, sha256_file
from app.data.catalog.freeze import write_immutable
from scripts.audit_full_cash_ledger import official_targets
from scripts.audit_p1_cash_census_counterexamples import SECONDARY
from scripts.audit_p1_orphan_cash_facts import REQUIREMENT, final_issuer_title, select
from scripts.audit_p1_orphan_exchange_dates import classify_dates
from scripts.audit_p1_public_fact_requirements import verified
from scripts.link_distribution_notices import notice_dates
from scripts.reconcile_distribution_cash import differentiated_cash, gross_cash

PROVIDERS = {
    "OFFICIAL_ISSUER_CNINFO_EXCHANGE_DATED",
    "OFFICIAL_ISSUER_CNINFO_EXCHANGE_RECONCILED",
    "OFFICIAL_ISSUER_CNINFO_PRIMARY_IMPLEMENTATION",
    "OFFICIAL_ISSUER_CNINFO_DIFFERENTIATED_PUBLIC_A",
    "OFFICIAL_SSE_TABLE_CNINFO_NOTICE_COMPOSITE",
}
FINAL_VARIANT = re.compile(r"(?:实施(?:的)?公告|实施方案|实施报告|派发.*(?:股息|股利).*公告)$")
NONFINAL_VARIANT = re.compile(r"董事会|股东大会|预案|决议|停牌|提示")
AB_CURRENCY_CASES = {
    # issuer PDF SHA: stable ID, historical code, record, ex, A cash, B FX, SZSE DPS, SZSE SHA
    "5ee3949582e2c5c967b4a3059c2b8c7a8077d50b0067608af584542b5deabee6": (
        "CN-A:SZSE:001872",
        "000022",
        "2012-07-19",
        "2012-07-20",
        "0.4",
        "0.8149",
        "0.491",
        "0f13e92f0907611a3cdc26bbb29c096301ad4f43924915d6fefd5211ceb5976d",
    ),
    "d13d3e8442b8dd5aa1b19779da584db530daaacb6f0107f04cc0ceb02028f7f3": (
        "CN-A:SZSE:000028",
        "000028",
        "2012-06-18",
        "2012-06-19",
        "0.13",
        "0.8078",
        "0.161",
        "80ef456982db2dd05542ffc7cd1024f0481d096c85952c5e34e6fe81321e9c02",
    ),
    "e613a32b97c2bbf36fa025ad39616b291b118362da208caeee927ccd978d0cd1": (
        "CN-A:SZSE:000530",
        "000530",
        "2012-05-22",
        "2012-05-23",
        "0.15",
        "0.8106",
        "0.185",
        "75aa41299d54169c3010c73d4d43c5e45fc2b74e1613a0c7d46c63af1d808398",
    ),
    "bb9898638f6cfe2e6dda1c8a08565c542ab0ffcaee295339094a7e63947ecba7": (
        "CN-A:SZSE:000570",
        "000570",
        "2012-06-12",
        "2012-06-13",
        "0.02",
        "0.8145",
        "0.025",
        "80ef456982db2dd05542ffc7cd1024f0481d096c85952c5e34e6fe81321e9c02",
    ),
    "b8ef0150ce1b052171a7f7de7553ab6ddae8224ddac077e235223025b04b7e2c": (
        "CN-A:SZSE:000581",
        "000581",
        "2012-07-17",
        "2012-07-18",
        "0.3",
        "0.8145",
        "0.368",
        "0f13e92f0907611a3cdc26bbb29c096301ad4f43924915d6fefd5211ceb5976d",
    ),
}
DATE_CORRECTION_600378 = (
    "https://static.cninfo.com.cn/finalpage/2015-05-19/1201031428.PDF",
    "0125c03f41c9f57e60a69b8204ecc17ddf5acf1dd99a00effddc1ce19acca9bd",
)
DATE_CORRECTION_300207 = (
    "https://static.cninfo.com.cn/finalpage/2017-04-14/1203299879.PDF",
    "432ececce5cd96195b954f32d524a0f7828fd751942cd018efdfd3d9993f72a1",
)
DATE_CORRECTION_600801 = (
    "https://static.cninfo.com.cn/finalpage/2014-06-12/64127751.PDF",
    "487d25df48ab08e892e90699af09b42f89fe38d5c3aac0f38b3c7af4e1e603b4",
)
INTERNAL_DATE_CASES = {
    # Exact issuer PDF SHA: stable ID, code, record, ex, SZSE monthly SHA, conflicting
    # date text, and independent issuer-body timing corroboration.
    "623e3a4a2bf718b0e5e74818c1e89e00cc845f41982f60744ec86bcbaf24bfb9": (
        "CN-A:SZSE:000826",
        "000826",
        "2012-05-08",
        "2012-05-09",
        "75aa41299d54169c3010c73d4d43c5e45fc2b74e1613a0c7d46c63af1d808398",
        ("股权登记日:2015年5月8日",),
        ("截止2012年5月8日", "除权除息日:2012年5月9日", "现金红利将于2012年5月9日"),
    ),
    "37b8e09a9377d779779843b14ddca358d42299c4b22ca04f33dc9a160d6c346e": (
        "CN-A:SZSE:300384",
        "300384",
        "2019-06-27",
        "2019-06-28",
        "2435499de09a130e445073b20f668e01ff3fb4c326b2d75e63f0bb5941dda774",
        ("股权除息日为:2018年6月28日",),
        (
            "股权登记日为:2019年6月27日",
            "申请日:2019年6月20日至登记日:2019年6月27日",
            "现金红利将于2019年6月28日",
        ),
    ),
    "379daf0876a8278fad267343d4f7fbd149291ec3e98949492680b9cc5bb58d8f": (
        "CN-A:SZSE:300852",
        "300852",
        "2022-04-22",
        "2022-04-25",
        "656a47e2365f817e80a1fe7be52aa9f566cac75bccd4e5cf27f983e11b66c15f",
        ("股权登记日:2021年4月22日", "除权除息日:2021年4月25日"),
        (
            "截止2022年4月22日",
            "现金红利将于2022年4月25日",
            "申请日2022年4月15日至股权登记日2022年4月22日",
        ),
    ),
}


def retained_final_title(title):
    return final_issuer_title(title) or bool(
        FINAL_VARIANT.search(title)
        and not SECONDARY.search(title)
        and not NONFINAL_VARIANT.search(title)
    )


def issuer_body_finality(title, pages):
    if SECONDARY.search(title) and not re.search(r"利润分配实施.*调整.*公告$", title):
        return None
    text = re.sub(r"\s+", "", "".join(pages))
    return next(
        (
            token
            for token in ("实施办法", "分派方法", "具体实施", "实施方案", "分配实施", "分配方法")
            if token in text
        ),
        None,
    )


def eligible(requirements, excluded, cash, master=()):
    by_key = {}
    by_historical = {}
    for accepted in cash:
        event = accepted["event"]
        key = (
            event["security_id"]["value"].split(":")[-1],
            event["record_date"],
            event["ex_date"],
        )
        by_key.setdefault(key, []).append(accepted)
    for row in master:
        if row["instrument_type"] == "COMMON_A_SHARE":
            by_historical.setdefault(row["symbol"], []).append(row)
    rows, events = [], []
    for row in sorted(requirements, key=lambda item: item["document_id"]):
        if (
            row["priority"] != "P1"
            or row["document_id"] in excluded
            or row["required_document_types"] != [REQUIREMENT]
            or row["known_urls"]
            or len(row["affected_events"]) != 1
        ):
            continue
        parts = row["affected_events"][0].split(":")
        if len(parts) != 4 or parts[0] != "CASH":
            continue
        symbol, record, ex = parts[1:]
        matches = by_key.get((symbol, record, ex), [])
        if not matches:
            identities = {
                row["security_id"]
                for row in by_historical.get(symbol, [])
                if row["effective_from"] <= record <= (row["effective_to"] or "2025-12-31")
                and (
                    row["security_id"].rsplit(":", 1)[-1] == symbol
                    or (
                        row.get("code_transition_source_url")
                        and row.get("code_transition_source_sha256")
                    )
                )
            }
            if len(identities) == 1:
                sid = next(iter(identities))
                matches = by_key.get((sid.rsplit(":", 1)[-1], record, ex), [])
        if (
            len(matches) == 1
            and matches[0]["event"]["source_provider"] in PROVIDERS
            and (
                matches[0]["event"]["source_provider"]
                != "OFFICIAL_ISSUER_CNINFO_DIFFERENTIATED_PUBLIC_A"
                or matches[0].get("policy_id") == "DIFFERENTIATED_CASH_ORDINARY_PUBLIC_A_V1"
            )
        ):
            rows.append(row)
            events.append(matches[0])
    return rows, events


def exact_final_companion(doc, event):
    symbol = event["security_id"]["value"].split(":")[-1]
    return (
        doc.get("issuer") == symbol
        and doc.get("affected_events")
        == [f"CASH:{symbol}:{event['record_date']}:{event['ex_date']}"]
        and event["announcement_date"] <= doc.get("published_on", "") <= event["record_date"]
        and doc.get("url", "").startswith("https://static.cninfo.com.cn/finalpage/")
        and not re.search(r"优先股|B股|H股|可转债", doc.get("title", ""))
        and retained_final_title(doc.get("title", ""))
    )


def exact_date_correction_source(doc):
    old = (
        (doc.get("url"), doc.get("source_sha256")) == DATE_CORRECTION_600378
        and doc.get("issuer") == "600378"
        and doc.get("title") == "2014年度利润分配实施更正公告"
        and doc.get("published_on") == "2015-05-19"
        and doc.get("affected_events") == ["CASH:600378:2015-05-21:2015-05-22"]
    )
    new = (
        (doc.get("url"), doc.get("source_sha256")) == DATE_CORRECTION_300207
        and doc.get("issuer") == "300207"
        and doc.get("title") == "关于2016年年度权益分派实施的补充公告"
        and doc.get("published_on") == "2017-04-14"
        and doc.get("affected_events") == ["CASH:300207:2017-04-20:2017-04-21"]
    )
    sse = (
        (doc.get("url"), doc.get("source_sha256")) == DATE_CORRECTION_600801
        and doc.get("issuer") == "600801"
        and doc.get("title") == "更正公告"
        and doc.get("published_on") == "2014-06-12"
        and doc.get("affected_events") == ["CASH:600801:2014-06-16:2014-06-17"]
    )
    return old or new or sse


def retained_sources(staging, events):
    direct = {}
    composite = {}
    companions = {}
    for row in events:
        event = row["event"]
        symbol = event["security_id"]["value"].split(":")[-1]
        direct[(event["source_url"], event["source_document_sha256"])] = (
            event["source_document"],
            event["announcement_date"],
        )
        companions[f"CASH:{symbol}:{event['record_date']}:{event['ex_date']}"] = event
        if event["source_provider"] == "OFFICIAL_SSE_TABLE_CNINFO_NOTICE_COMPOSITE":
            record = event["record_date"]
            composite.setdefault(symbol, []).append(
                ((date.fromisoformat(record) - timedelta(days=60)).isoformat(), record)
            )
    found = {}
    for manifest in sorted(staging.rglob("source-manifest.json")):
        data = json.loads(manifest.read_bytes())
        if not isinstance(data, dict):
            continue
        for doc in data.get("documents", []):
            key = doc.get("url"), doc.get("source_sha256")
            published = doc.get("published_on", "")
            direct_match = key in direct and (doc.get("title"), published) == direct[key]
            composite_match = (
                doc.get("url", "").startswith("https://static.cninfo.com.cn/finalpage/")
                and retained_final_title(doc.get("title", ""))
                and any(
                    start <= published <= record
                    for start, record in composite.get(doc.get("issuer"), [])
                )
            )
            affected = doc.get("affected_events", [])
            companion = companions.get(affected[0]) if len(affected) == 1 else None
            companion_match = companion is not None and exact_final_companion(doc, companion)
            if (
                not direct_match
                and not composite_match
                and not companion_match
                and not exact_date_correction_source(doc)
            ) or doc.get("retrieval_status") != "PASS":
                continue
            if key in found:
                earlier = found[key][1]
                if any(
                    doc[field] != earlier[field] for field in ("issuer", "title", "published_on")
                ):
                    raise ValueError(f"CONFLICTING_OFFICIAL_RECEIPTS:{key[0]}")
                continue
            verified(manifest)
            found[key] = (manifest, doc)
    source_docs = []
    by_url = {}
    for (url, sha), (manifest, doc) in sorted(found.items()):
        if url in by_url and by_url[url] != sha:
            raise ValueError(f"CONFLICTING_OFFICIAL_SOURCE_BYTES:{url}")
        by_url[url] = sha
        finality = None
        if not retained_final_title(doc["title"]):
            cache = manifest.parents[1] / "batch-v1/text" / f"{sha}.json"
            if cache.is_file():
                extracted = json.loads(cache.read_bytes())
                if extracted["source_sha256"] == sha:
                    finality = issuer_body_finality(doc["title"], extracted["pages"])
        source_docs.append(
            {
                **doc,
                "source_path": str((manifest.parents[1] / doc["source_path"]).resolve()),
                **({"issuer_body_finality_marker": finality} if finality else {}),
            }
        )
    return found, source_docs


def exchange_amount_matches(amount, targets):
    return any(
        amount == target
        or amount.quantize(Decimal(1).scaleb(target.as_tuple().exponent), rounding=ROUND_HALF_UP)
        == target
        for target in targets
    )


def ab_currency_dps_conflict(row, amount, pages, szse):
    case = AB_CURRENCY_CASES.get(row["substitute_source_sha256"])
    if case is None:
        return None
    security_id, issuer, record, ex, cash, rate, dps, exchange_sha = case
    if (row["security_id"], row["issuer"], row["record_date"], row["ex_date"]) != (
        security_id,
        issuer,
        record,
        ex,
    ) or amount != Decimal(cash):
        return None
    text = re.sub(r"\s+", "", unicodedata.normalize("NFKC", "".join(pages)))
    rates = re.findall(r"1港(?:币|元)=(?:人民币)?(0\.\d+)(?:元)?(?:人民币)?", text)
    if (
        issuer not in text
        or "A股股权登记日" not in text
        or "B股" not in text
        or "每10股" not in text
        or rates != [rate]
    ):
        return None
    rows = [
        item
        for item in szse["rows"]
        if item["symbol"] == issuer
        and item["record_date"] == row["record_date"]
        and item["ex_date"] == row["ex_date"]
    ]
    if len(rows) != 1:
        return None
    exchange = rows[0]
    cells = exchange["raw_cells"]
    if len(cells) != 14 or exchange["source_sha256"] != exchange_sha:
        return None
    reported_dps = Decimal(cells[5])
    if (
        reported_dps != Decimal(dps)
        or Decimal(cells[13]) - Decimal(cells[12]) != amount
        or (amount / Decimal(rate)).quantize(Decimal("0.001"), rounding=ROUND_HALF_UP)
        != reported_dps
    ):
        return None
    return {
        "policy": "A_SHARE_FINAL_ISSUER_TERMS_OVER_EXCHANGE_AB_CURRENCY_DPS_CONFLICT",
        "exchange_source_url": exchange["source_url"],
        "exchange_source_sha256": exchange["source_sha256"],
        "exchange_reported_dps": str(reported_dps),
        "exchange_ex_price_delta": str(Decimal(cells[13]) - Decimal(cells[12])),
        "issuer_gross_a_cash_per_share": str(amount),
        "official_b_hkd_conversion_rate": rate,
    }


def date_correction_terms(original_pages, corrected_pages):
    original = re.sub(r"\s+", "", unicodedata.normalize("NFKC", "".join(original_pages)))
    corrected = re.sub(r"\s+", "", unicodedata.normalize("NFKC", "".join(corrected_pages)))
    return all(
        marker in original
        for marker in ("股权登记日:2014年5月21日", "除息及现金红利发放日:2014年5月22日")
    ) and all(
        marker in corrected
        for marker in (
            "2015年5月15日",
            "2014年度利润分配实施公告",
            "由于工作疏忽",
            "更正为“1、股权登记日:2015年5月21日;2、除息及现金红利发放日:2015年5月22日。",
            "其他内容保持不变",
        )
    )


def supplement_300207_terms(original_pages, corrected_pages):
    original = re.sub(r"\s+", "", unicodedata.normalize("NFKC", "".join(original_pages)))
    corrected = re.sub(r"\s+", "", unicodedata.normalize("NFKC", "".join(corrected_pages)))
    return all(
        marker in original
        for marker in ("股权登记日为:2017年4月18日", "除权除息日为:2017年4月19日")
    ) and all(
        marker in corrected
        for marker in (
            "证券代码:300207",
            "关于2016年年度权益分派实施的补充公告",
            "2017年4月11日",
            "原披露内容",
            "股权登记日为:2017年4月18日",
            "除权除息日为:2017年4月19日",
            "补充披露后",
            "股权登记日为:2017年4月20日",
            "除权除息日为:2017年4月21日",
            "其他内容不变",
        )
    )


def correction_600801_terms(original_pages, corrected_pages):
    original = re.sub(r"\s+", "", unicodedata.normalize("NFKC", "".join(original_pages)))
    corrected = re.sub(r"\s+", "", unicodedata.normalize("NFKC", "".join(corrected_pages)))
    return all(
        marker in original for marker in ("证券代码:600801、900933", "除权(除息)日:2014年6月18日")
    ) and all(
        marker in corrected
        for marker in (
            "证券代码:600801、900933",
            "华新水泥股份有限公司",
            "2014年6月11日",
            "除权(除息)日为2014年6月18日",
            "应更正为",
            "除权(除息)日为2014年6月17日",
        )
    )


def official_date_correction(row, original_pages, found, staging):
    key = (
        row["security_id"],
        row["issuer"],
        row["record_date"],
        row["ex_date"],
        row["substitute_source_sha256"],
    )
    cases = {
        (
            "CN-A:SSE:600378",
            "600378",
            "2015-05-21",
            "2015-05-22",
            "9fe4928323880236582959001105c5b188379b98e490e7b52f9262b56ae4eaf6",
        ): (DATE_CORRECTION_600378, date_correction_terms),
        (
            "CN-A:SZSE:300207",
            "300207",
            "2017-04-20",
            "2017-04-21",
            "976bc6226f9d124c721994b482a1eb28bd5e1022aba1798b845815735afd2818",
        ): (DATE_CORRECTION_300207, supplement_300207_terms),
        (
            "CN-A:SSE:600801",
            "600801",
            "2014-06-16",
            "2014-06-17",
            "bd0d7e1100fa27fc04b9083608cc8d9552bb4d78121246f43051428f30d0d2f6",
        ): (DATE_CORRECTION_600801, correction_600801_terms),
    }
    if key not in cases:
        return None
    correction_key, terms_match = cases[key]
    if correction_key not in found:
        return None
    manifest, doc = found[correction_key]
    if not exact_date_correction_source(doc):
        return None
    root = manifest.parents[1]
    pdf = (root / doc["source_path"]).resolve()
    cache = root / "batch-v1/text" / f"{doc['source_sha256']}.json"
    if (
        not pdf.is_relative_to(staging.resolve())
        or sha256_file(pdf) != doc["source_sha256"]
        or not cache.is_file()
    ):
        raise ValueError("OFFICIAL_DATE_CORRECTION_SOURCE_CHANGED")
    extracted = json.loads(cache.read_bytes())
    if extracted["source_sha256"] != doc["source_sha256"] or not terms_match(
        original_pages, extracted["pages"]
    ):
        return None
    return {
        "source_url": doc["url"],
        "source_sha256": doc["source_sha256"],
        "source_manifest_sha256": sha256_file(manifest),
        "source_text_sha256": sha256_file(cache),
        "corrected_record_date": row["record_date"],
        "corrected_ex_date": row["ex_date"],
    }


def issuer_internal_date_corroboration(row, pages, records, ex_dates, szse):
    case = INTERNAL_DATE_CASES.get(row["substitute_source_sha256"])
    if case is None:
        return None
    security_id, issuer, record, ex, exchange_sha, conflict, corroboration = case
    if (row["security_id"], row["issuer"], row["record_date"], row["ex_date"]) != (
        security_id,
        issuer,
        record,
        ex,
    ):
        return None
    text = re.sub(r"\s+", "", unicodedata.normalize("NFKC", "".join(pages)))
    if not all(marker in text for marker in (*conflict, *corroboration)):
        return None
    matches = [
        item
        for item in szse["rows"]
        if item["symbol"] == issuer
        and item["record_date"] == record
        and item["ex_date"] == ex
        and item["source_sha256"] == exchange_sha
        and Decimal(item["raw_cells"][5]) == Decimal(row["cash_per_share"])
    ]
    if len(matches) != 1:
        return None
    return {
        "policy": "EXACT_ISSUER_INTERNAL_TIMING_PLUS_OFFICIAL_SZSE_DATE_AND_AMOUNT",
        "issuer_conflicting_record_dates": records,
        "issuer_conflicting_ex_dates": ex_dates,
        "issuer_body_corroboration": list(corroboration),
        "exchange_source_url": matches[0]["source_url"],
        "exchange_source_sha256": exchange_sha,
    }


def cash_terms_with_alternates(extracted, doc, issuer, targets, differentiated, root, staging):
    pages = extracted["pages"]
    try:
        amount = (
            differentiated_cash(pages, issuer, doc["title"])
            if differentiated
            else gross_cash(pages, issuer, targets, trusted_issuer=True)
        )
        records, ex_dates = notice_dates(pages)
        return amount, records, ex_dates, pages, None
    except ValueError as exc:
        if differentiated or str(exc) not in {
            "NO_EXPLICIT_GROSS_CASH",
            "NO_UNIQUE_EXPLICIT_GROSS_CASH",
        }:
            raise
    sha = doc["source_sha256"]
    alternatives = (
        ("PYMUPDF_NFKC_PAGE_EXTRACTION_V1", root / "batch-v1/text-pymupdf" / f"{sha}.json"),
        (
            "P1_CASH_PUBLIC_SUBSTITUTION_OCR_V1",
            staging / "p1-public-cash-substitution-v1/ocr" / f"{sha}.json",
        ),
    )
    parsed = []
    for version, path in alternatives:
        if not path.is_file():
            continue
        data = json.loads(path.read_bytes())
        if (
            data.get("source_sha256") != sha
            or data.get("event_acceptance") != "NOT_PERFORMED"
            or not data.get("parser_version", "").startswith(version)
        ):
            raise RuntimeError(f"ALTERNATE_OFFICIAL_TEXT_CHANGED:{sha}")
        try:
            amount = gross_cash(data["pages"], issuer, targets, trusted_issuer=True)
            records, ex_dates = notice_dates(data["pages"])
        except ValueError:
            continue
        parsed.append(
            (
                amount,
                records,
                ex_dates,
                data["pages"],
                {
                    "parser_version": data["parser_version"],
                    "source_text_sha256": sha256_file(path),
                },
            )
        )
    if not parsed:
        raise ValueError("NO_UNIQUE_EXPLICIT_GROSS_CASH")
    if (
        len(
            {
                (amount, tuple(records), tuple(ex_dates))
                for amount, records, ex_dates, _, _ in parsed
            }
        )
        != 1
    ):
        raise ValueError("ALTERNATE_EXTRACTION_CONFLICT")
    amount, records, ex_dates, pages, _ = parsed[0]
    return amount, records, ex_dates, pages, [item[4] for item in parsed]


def exchange_resolves_year_conflict(row, records, ex_dates, published_on):
    if (len(records), len(ex_dates)) != (1, 1):
        return False
    expected = row["record_date"], row["ex_date"]
    parsed = records[0], ex_dates[0]
    return (
        published_on <= expected[0] < expected[1]
        and any(actual != target for actual, target in zip(parsed, expected, strict=True))
        and all(
            actual[5:] == target[5:] and (actual == target or actual < published_on)
            for actual, target in zip(parsed, expected, strict=True)
        )
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in (
        "requirements",
        "reassessment",
        "base",
        "prior",
        "cash-ledger",
        "master",
        "instruments",
        "sse-audit",
        "szse-audit",
        "staging",
        "output",
    ):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    requirements, reassessment, base, prior, cash, instruments, sse, szse = (
        verified(path)
        for path in (
            args.requirements,
            args.reassessment,
            args.base,
            args.prior,
            args.cash_ledger,
            args.instruments,
            args.sse_audit,
            args.szse_audit,
        )
    )
    master = json.loads(args.master.read_bytes())
    excluded = (
        {row["document_id"] for row in reassessment["out_of_scope_cninfo_documents"]}
        | {row["document_id"] for row in base["accepted_cash_matches"]}
        | {row["document_id"] for row in prior["closed"]}
    )
    requests, events = eligible(requirements["documents"], excluded, cash["events"], master)
    if (requests, events) != eligible(
        list(reversed(requirements["documents"])),
        excluded,
        list(reversed(cash["events"])),
        list(reversed(master)),
    ):
        raise ValueError("INPUT_ORDER_CHANGED")
    found, source_docs = retained_sources(args.staging, events)
    finality_by_source = {
        (doc["url"], doc["source_sha256"]): doc.get("issuer_body_finality_marker")
        for doc in source_docs
    }
    body_confirmed_titles = {
        doc["title"] for doc in source_docs if doc.get("issuer_body_finality_marker")
    }

    def final_title(title):
        return retained_final_title(title) or title in body_confirmed_titles

    selected = select(
        requests,
        [],
        [],
        events,
        master,
        source_docs,
        final_title=final_title,
        historical_alias=True,
    )
    if selected != select(
        list(reversed(requests)),
        [],
        [],
        list(reversed(events)),
        list(reversed(master)),
        list(reversed(source_docs)),
        final_title=final_title,
        historical_alias=True,
    ):
        raise ValueError("SOURCE_INPUT_ORDER_CHANGED")
    instrument_types = {
        row["classification"]["security_id"]["value"]: row["classification"]["instrument_type"]
        for row in instruments["classifications"]
    }
    targets, _ = official_targets(master, instrument_types, sse, szse)
    by_checksum = {item["event_checksum"]: item for item in events}
    if len(by_checksum) != len(events):
        raise ValueError("DUPLICATE_ACCEPTED_CASH_CHECKSUM")
    closed = []
    selected_ids = {row["document_id"] for row in selected}
    rejected = [
        {"document_id": row["document_id"], "reason": "SOURCE_TITLE_OR_MASTER_UNMATCHED"}
        for row in requests
        if row["document_id"] not in selected_ids
    ]
    for row in selected:
        key = row["security_id"], row["record_date"], row["ex_date"]
        accepted = by_checksum[row["accepted_event_checksum"]]
        differentiated = (
            accepted["event"]["source_provider"] == "OFFICIAL_ISSUER_CNINFO_DIFFERENTIATED_PUBLIC_A"
        )
        reason = None
        if key not in targets:
            reason = "NO_EXACT_OFFICIAL_EXCHANGE_TARGET"
        else:
            source_key = row["substitute_source_url"], row["substitute_source_sha256"]
            manifest, doc = found[source_key]
            body_finality = finality_by_source[source_key]
            source_root = manifest.parents[1]
            pdf = (source_root / doc["source_path"]).resolve()
            cache = source_root / "batch-v1/text" / f"{doc['source_sha256']}.json"
            if (
                not pdf.is_relative_to(args.staging.resolve())
                or sha256_file(pdf) != doc["source_sha256"]
                or not cache.is_file()
            ):
                raise ValueError(f"RETAINED_OFFICIAL_SOURCE_CHANGED:{row['document_id']}")
            extracted = json.loads(cache.read_bytes())
            if extracted["source_sha256"] != doc["source_sha256"]:
                raise ValueError(f"RETAINED_OFFICIAL_TEXT_CHANGED:{row['document_id']}")
            try:
                amount, records, ex_dates, term_pages, alternate_text = cash_terms_with_alternates(
                    extracted,
                    doc,
                    row["issuer"],
                    targets[key],
                    differentiated,
                    source_root,
                    args.staging,
                )
            except ValueError as exc:
                reason = str(exc)
            else:
                classification = classify_dates(
                    row, records, ex_dates, differentiated=differentiated
                )
                conflict_resolution = (
                    ab_currency_dps_conflict(row, amount, term_pages, szse)
                    if not exchange_amount_matches(amount, targets[key])
                    else None
                )
                date_correction = (
                    official_date_correction(row, extracted["pages"], found, args.staging)
                    if classification is None
                    else None
                )
                internal_dates = (
                    issuer_internal_date_corroboration(row, term_pages, records, ex_dates, szse)
                    if classification is None
                    else None
                )
                if classification is None and exchange_resolves_year_conflict(
                    row, records, ex_dates, doc["published_on"]
                ):
                    classification = (
                        "DIFFERENTIATED_PUBLIC_A_OFFICIAL_EXCHANGE_RESOLVED_SOURCE_YEAR_CONFLICT"
                        if differentiated
                        else "OFFICIAL_EXCHANGE_RESOLVED_SOURCE_YEAR_CONFLICT"
                    )
                if classification is None and date_correction:
                    classification = "OFFICIAL_ISSUER_DATE_CORRECTION_EXACT"
                if classification is None and internal_dates:
                    classification = "OFFICIAL_ISSUER_INTERNAL_AND_EXCHANGE_DATE_CORROBORATION"
                if not retained_final_title(doc["title"]) and not body_finality:
                    reason = "NO_FINAL_IMPLEMENTATION_BODY"
                elif amount != Decimal(row["cash_per_share"]):
                    reason = "ISSUER_CASH_AMOUNT_CONFLICT"
                elif not exchange_amount_matches(amount, targets[key]) and not conflict_resolution:
                    reason = "ISSUER_EXCHANGE_AMOUNT_CONFLICT"
                elif classification is None:
                    reason = "ISSUER_DATE_CONFLICT"
                else:
                    closed.append(
                        {
                            **{k: v for k, v in row.items() if k != "substitute_source_path"},
                            "classification": classification,
                            **(
                                {"holder_policy": "DIFFERENTIATED_CASH_ORDINARY_PUBLIC_A_V1"}
                                if differentiated
                                else {}
                            ),
                            **(
                                {"issuer_body_finality_marker": body_finality}
                                if not retained_final_title(doc["title"])
                                else {}
                            ),
                            "issuer_notice_record_dates": records,
                            "issuer_notice_ex_dates": ex_dates,
                            "official_exchange_amounts": sorted(
                                str(value) for value in targets[key]
                            ),
                            **(
                                {"official_exchange_amount_conflict": conflict_resolution}
                                if conflict_resolution
                                else {}
                            ),
                            **(
                                {"official_date_correction": date_correction}
                                if date_correction
                                else {}
                            ),
                            **(
                                {"issuer_internal_date_corroboration": internal_dates}
                                if internal_dates
                                else {}
                            ),
                            **(
                                {"alternate_text_extractions": alternate_text}
                                if alternate_text
                                else {}
                            ),
                            "source_manifest_sha256": sha256_file(manifest),
                            "source_text_sha256": sha256_file(cache),
                        }
                    )
        if reason:
            rejected.append({"document_id": row["document_id"], "reason": reason})
    if len(closed) + len(rejected) != len(requests):
        raise ValueError("RETAINED_P1_CANDIDATES_NOT_PARTITIONED")
    report = {
        "report_version": "P1_RETAINED_OFFICIAL_FULL_CASH_SOURCE_CLOSURE_V22",
        "candidate_documents": len(requests),
        "selected_documents": len(selected),
        "closed_documents": len(closed),
        "closed_facts": sum(len(row["affected_events"]) for row in closed),
        "historical_code_alias_closures": sum(
            "requirement_stable_symbol" in row or "requirement_historical_symbol" in row
            for row in closed
        ),
        "explicit_exchange_amount_conflicts_resolved": sum(
            "official_exchange_amount_conflict" in row for row in closed
        ),
        "classification_counts": dict(
            sorted(Counter(row["classification"] for row in closed).items())
        ),
        "rejected_counts": dict(sorted(Counter(row["reason"] for row in rejected).items())),
        "rejected": rejected,
        "closed": closed,
        "input_sha256s": {
            name: sha256_file(getattr(args, name))
            for name in (
                "requirements",
                "reassessment",
                "base",
                "prior",
                "cash_ledger",
                "master",
                "instruments",
                "sse_audit",
                "szse_audit",
            )
        },
        "source_manifest_sha256s": {
            str(path): sha256_file(path) for path in sorted({item[0] for item in found.values()})
        },
        "parser_sha256": sha256_file(Path(__file__)),
        "selector_sha256": sha256_file(Path(__file__).with_name("audit_p1_orphan_cash_facts.py")),
        "cash_parser_sha256": sha256_file(
            Path(__file__).with_name("reconcile_distribution_cash.py")
        ),
        "date_parser_sha256": sha256_file(Path(__file__).with_name("link_distribution_notices.py")),
        "input_order_reproducibility": "PASS",
        "closed_source_checksum_verified": True,
        "new_economic_events_created": 0,
    }
    report["manifest_sha256"] = canonical_sha256(report)
    write_immutable(args.output, canonical_json_bytes(report) + b"\n")
    print(
        json.dumps(
            {key: value for key, value in report.items() if key not in {"closed", "rejected"}}
        )
    )


if __name__ == "__main__":
    main()
