import json
from decimal import Decimal

import pytest

from scripts.audit_p1_orphan_cash_facts import select
from scripts.audit_p1_retained_cash_sources import (
    ab_currency_dps_conflict,
    cash_terms_with_alternates,
    correction_600801_terms,
    date_correction_terms,
    eligible,
    exact_date_correction_source,
    exact_final_companion,
    exchange_amount_matches,
    exchange_resolves_year_conflict,
    issuer_body_finality,
    issuer_internal_date_corroboration,
    retained_final_title,
    supplement_300207_terms,
)


def test_retained_cash_candidates_require_exact_event_and_official_issuer_source():
    requirements = [
        {
            "document_id": "cash-1",
            "priority": "P1",
            "required_document_types": [
                "FINAL_IMPLEMENTATION_NOTICE_WITH_GROSS_ORDINARY_A_SHARE_CASH"
            ],
            "known_urls": [],
            "affected_events": ["CASH:600001:2022-06-01:2022-06-02"],
        }
    ]
    cash = [
        {
            "event": {
                "security_id": {"value": "SSE:600001"},
                "record_date": "2022-06-01",
                "ex_date": "2022-06-02",
                "source_provider": "OFFICIAL_ISSUER_CNINFO_EXCHANGE_DATED",
            }
        }
    ]
    assert eligible(requirements, set(), cash) == (requirements, cash)
    assert eligible(requirements, {"cash-1"}, cash) == ([], [])
    assert eligible(requirements, set(), cash + cash) == ([], [])
    cash[0]["event"]["source_provider"] = "UNVERIFIED_VENDOR"
    assert eligible(requirements, set(), cash) == ([], [])
    cash[0]["event"]["source_provider"] = "OFFICIAL_ISSUER_CNINFO_DIFFERENTIATED_PUBLIC_A"
    assert eligible(requirements, set(), cash) == ([], [])
    cash[0]["policy_id"] = "DIFFERENTIATED_CASH_ORDINARY_PUBLIC_A_V1"
    assert eligible(requirements, set(), cash) == (requirements, cash)
    cash[0]["event"]["source_provider"] = "OFFICIAL_SSE_TABLE_CNINFO_NOTICE_COMPOSITE"
    assert eligible(requirements, set(), cash) == (requirements, cash)
    assert exchange_amount_matches(Decimal("0.100022"), {Decimal("0.1000")})
    assert not exchange_amount_matches(Decimal("0.1006"), {Decimal("0.1000")})


def test_year_conflict_needs_impossible_issuer_year_and_exact_exchange_month_day():
    row = {"record_date": "2015-06-25", "ex_date": "2015-06-26"}
    assert exchange_resolves_year_conflict(row, ["2015-06-25"], ["2014-06-26"], "2015-06-18")
    assert not exchange_resolves_year_conflict(row, ["2015-06-25"], ["2014-06-27"], "2015-06-18")
    assert not exchange_resolves_year_conflict(row, ["2015-06-25"], ["2014-06-26"], "2014-06-01")
    assert not exchange_resolves_year_conflict(
        row, ["2015-06-25", "2014-06-25"], ["2014-06-26"], "2015-06-18"
    )


def test_retained_final_title_accepts_final_variants_not_proposals_or_tips():
    assert retained_final_title("2021年年度权益分派及资本公积转增股本方案实施公告")
    assert retained_final_title("关于派发2017年度末期股息的公告")
    assert not retained_final_title("2011年度权益分派方案公告")
    assert not retained_final_title("董事会2015年度分红派息公告")
    assert not retained_final_title("A股分红派息实施暨停牌提示性公告")
    assert issuer_body_finality("2014年度利润分配公告", ["三、利润分配实施办法"]) == "实施办法"
    assert issuer_body_finality("2011年中期利润分配公告", ["四、分配方法"]) == "分配方法"
    assert issuer_body_finality("分红派息提示性公告", ["利润分配实施办法"]) is None


def test_final_companion_requires_same_event_and_post_announcement_issuer_notice():
    event = {
        "security_id": {"value": "CN-A:SSE:601818"},
        "record_date": "2019-06-25",
        "ex_date": "2019-06-26",
        "announcement_date": "2019-06-13",
    }
    doc = {
        "issuer": "601818",
        "affected_events": ["CASH:601818:2019-06-25:2019-06-26"],
        "published_on": "2019-06-19",
        "title": "2018年度A股普通股分红派息实施公告",
        "url": "https://static.cninfo.com.cn/finalpage/2019-06-19/1206365161.PDF",
    }
    assert exact_final_companion(doc, event)
    assert not exact_final_companion({**doc, "published_on": "2019-06-12"}, event)
    assert not exact_final_companion({**doc, "affected_events": []}, event)
    assert not exact_final_companion({**doc, "title": "分红派息提示性公告"}, event)
    assert not exact_final_companion({**doc, "title": "第一期优先股股息发放实施公告"}, event)


def test_official_date_correction_requires_original_error_and_explicit_replacement():
    doc = {
        "url": "https://static.cninfo.com.cn/finalpage/2015-05-19/1201031428.PDF",
        "source_sha256": "0125c03f41c9f57e60a69b8204ecc17ddf5acf1dd99a00effddc1ce19acca9bd",
        "issuer": "600378",
        "title": "2014年度利润分配实施更正公告",
        "published_on": "2015-05-19",
        "affected_events": ["CASH:600378:2015-05-21:2015-05-22"],
    }
    original = ["股权登记日:2014年5月21日;除息及现金红利发放日:2014年5月22日"]
    correction = [
        "2015年5月15日披露2014年度利润分配实施公告。由于工作疏忽,"
        "更正为“1、股权登记日:2015年5月21日;"
        "2、除息及现金红利发放日:2015年5月22日。”其他内容保持不变。"
    ]
    assert exact_date_correction_source(doc)
    assert not exact_date_correction_source({**doc, "affected_events": []})
    assert date_correction_terms(original, correction)
    assert not date_correction_terms(
        original, [correction[0].replace("2015年5月22日", "2015年5月23日")]
    )


def test_300207_supplement_requires_exact_original_and_replacement_dates():
    doc = {
        "url": "https://static.cninfo.com.cn/finalpage/2017-04-14/1203299879.PDF",
        "source_sha256": "432ececce5cd96195b954f32d524a0f7828fd751942cd018efdfd3d9993f72a1",
        "issuer": "300207",
        "title": "关于2016年年度权益分派实施的补充公告",
        "published_on": "2017-04-14",
        "affected_events": ["CASH:300207:2017-04-20:2017-04-21"],
    }
    original = ["股权登记日为:2017年4月18日,除权除息日为:2017年4月19日"]
    supplement = [
        "证券代码:300207 关于2016年年度权益分派实施的补充公告。"
        "2017年4月11日。原披露内容:股权登记日为:2017年4月18日,"
        "除权除息日为:2017年4月19日。补充披露后:"
        "股权登记日为:2017年4月20日,除权除息日为:2017年4月21日。"
        "其他内容不变。"
    ]
    assert exact_date_correction_source(doc)
    assert supplement_300207_terms(original, supplement)
    assert not supplement_300207_terms(
        original, [supplement[0].replace("2017年4月21日", "2017年4月22日")]
    )
    assert not exact_date_correction_source({**doc, "source_sha256": "wrong"})


def test_600801_correction_requires_exact_original_and_replacement_ex_date():
    doc = {
        "url": "https://static.cninfo.com.cn/finalpage/2014-06-12/64127751.PDF",
        "source_sha256": "487d25df48ab08e892e90699af09b42f89fe38d5c3aac0f38b3c7af4e1e603b4",
        "issuer": "600801",
        "title": "更正公告",
        "published_on": "2014-06-12",
        "affected_events": ["CASH:600801:2014-06-16:2014-06-17"],
    }
    original = ["证券代码:600801、900933 除权(除息)日:2014年6月18日"]
    correction = [
        "证券代码:600801、900933 华新水泥股份有限公司于2014年6月11日披露。"
        "除权(除息)日为2014年6月18日有误,应更正为"
        "除权(除息)日为2014年6月17日。"
    ]
    assert exact_date_correction_source(doc)
    assert correction_600801_terms(original, correction)
    assert not correction_600801_terms(
        original, [correction[0].replace("2014年6月17日", "2014年6月19日")]
    )


def test_internal_date_conflict_needs_exact_issuer_and_exchange_corroboration():
    row = {
        "substitute_source_sha256": (
            "623e3a4a2bf718b0e5e74818c1e89e00cc845f41982f60744ec86bcbaf24bfb9"
        ),
        "security_id": "CN-A:SZSE:000826",
        "issuer": "000826",
        "record_date": "2012-05-08",
        "ex_date": "2012-05-09",
        "cash_per_share": "0.1",
    }
    pages = [
        "股权登记日:2015年5月8日;除权除息日:2012年5月9日。"
        "截止2012年5月8日在册。现金红利将于2012年5月9日发放。"
    ]
    exchange = {
        "symbol": "000826",
        "record_date": "2012-05-08",
        "ex_date": "2012-05-09",
        "raw_cells": ["", "", "", "", "", "0.100"],
        "source_url": "https://docs.static.szse.cn/official",
        "source_sha256": "75aa41299d54169c3010c73d4d43c5e45fc2b74e1613a0c7d46c63af1d808398",
    }
    args = row, pages, ["2015-05-08"], ["2012-05-09"]
    assert issuer_internal_date_corroboration(*args, {"rows": [exchange]})
    assert not issuer_internal_date_corroboration(
        *args, {"rows": [{**exchange, "source_sha256": "wrong"}]}
    )
    assert not issuer_internal_date_corroboration(
        row,
        [pages[0].replace("截止2012年5月8日", "截止2013年5月8日")],
        ["2015-05-08"],
        ["2012-05-09"],
        {"rows": [exchange]},
    )


def test_garbled_pdf_text_uses_source_bound_alternate_extraction(tmp_path):
    sha = "official-pdf-sha"
    cache = tmp_path / "batch-v1/text-pymupdf" / f"{sha}.json"
    cache.parent.mkdir(parents=True)
    cache.write_text(
        json.dumps(
            {
                "source_sha256": sha,
                "parser_version": "PYMUPDF_NFKC_PAGE_EXTRACTION_V1:1.28.2",
                "event_acceptance": "NOT_PERFORMED",
                "pages": [
                    "股票代码:300127。向全体股东每10股派4.5元人民币现金(含税)。"
                    "股权登记日为:2013年4月11日;除权除息日为:2013年4月12日。"
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    doc = {"source_sha256": sha, "title": "2012年年度权益分派实施公告"}
    amount, records, ex_dates, _, receipts = cash_terms_with_alternates(
        {"pages": ["garbled"]},
        doc,
        "300127",
        {Decimal("0.45")},
        False,
        tmp_path,
        tmp_path,
    )
    assert (amount, records, ex_dates) == (Decimal("0.45"), ["2013-04-11"], ["2013-04-12"])
    assert receipts[0]["parser_version"].startswith("PYMUPDF_NFKC_PAGE_EXTRACTION_V1")
    cache.write_text(
        cache.read_text(encoding="utf-8").replace(sha, "wrong-source"), encoding="utf-8"
    )
    with pytest.raises(RuntimeError, match="ALTERNATE_OFFICIAL_TEXT_CHANGED"):
        cash_terms_with_alternates(
            {"pages": ["garbled"]},
            doc,
            "300127",
            {Decimal("0.45")},
            False,
            tmp_path,
            tmp_path,
        )


def test_official_historical_code_alias_needs_point_in_time_master_receipt():
    requirement = {
        "priority": "P1",
        "source_group": "CNINFO",
        "document_id": "historical-cash",
        "known_urls": [],
        "required_document_types": ["FINAL_IMPLEMENTATION_NOTICE_WITH_GROSS_ORDINARY_A_SHARE_CASH"],
        "affected_events": ["CASH:601360:2012-04-23:2012-04-24"],
    }
    url = "https://static.cninfo.com.cn/finalpage/2012-04-18/notice.PDF"
    event = {
        "event": {
            "security_id": {"value": "CN-A:SSE:601360"},
            "record_date": "2012-04-23",
            "ex_date": "2012-04-24",
            "cash_per_share": "0.15",
            "source_provider": "OFFICIAL_ISSUER_CNINFO_EXCHANGE_RECONCILED",
            "source_url": url,
            "source_document": "分红派息实施公告",
            "source_document_sha256": "issuer-sha",
            "announcement_date": "2012-04-18",
        },
        "event_checksum": "event-sha",
    }
    master = [
        {
            "symbol": "601313",
            "security_id": "CN-A:SSE:601360",
            "effective_from": "2012-01-16",
            "effective_to": "2018-02-22",
            "instrument_type": "COMMON_A_SHARE",
            "code_transition_source_url": "https://static.cninfo.com.cn/finalpage/change.PDF",
            "code_transition_source_sha256": "transition-sha",
        }
    ]
    source = {
        "url": url,
        "retrieval_status": "PASS",
        "issuer": "601313",
        "title": "分红派息实施公告",
        "published_on": "2012-04-18",
        "source_sha256": "issuer-sha",
        "source_path": "notice.pdf",
    }
    assert not select([requirement], [], [], [event], master, [source])
    rows = select([requirement], [], [], [event], master, [source], historical_alias=True)
    assert rows[0]["issuer"] == "601313"
    assert rows[0]["security_id"] == "CN-A:SSE:601360"
    assert rows[0]["official_code_transition_sha256"] == "transition-sha"
    assert not select(
        [requirement],
        [],
        [],
        [event],
        [{**master[0], "code_transition_source_sha256": None}],
        [source],
        historical_alias=True,
    )


@pytest.mark.parametrize(
    "security_id,issuer,record,ex,source_sha,cash,rate_text,dps,before,after,exchange_sha",
    [
        (
            "CN-A:SZSE:001872",
            "000022",
            "2012-07-19",
            "2012-07-20",
            "5ee3949582e2c5c967b4a3059c2b8c7a8077d50b0067608af584542b5deabee6",
            "0.4",
            "1港币=0.8149元人民币",
            "0.491",
            "9.880",
            "9.480",
            "0f13e92f0907611a3cdc26bbb29c096301ad4f43924915d6fefd5211ceb5976d",
        ),
        (
            "CN-A:SZSE:000028",
            "000028",
            "2012-06-18",
            "2012-06-19",
            "d13d3e8442b8dd5aa1b19779da584db530daaacb6f0107f04cc0ceb02028f7f3",
            "0.13",
            "1港元=人民币0.8078元",
            "0.161",
            "27.110",
            "26.980",
            "80ef456982db2dd05542ffc7cd1024f0481d096c85952c5e34e6fe81321e9c02",
        ),
        (
            "CN-A:SZSE:000530",
            "000530",
            "2012-05-22",
            "2012-05-23",
            "e613a32b97c2bbf36fa025ad39616b291b118362da208caeee927ccd978d0cd1",
            "0.15",
            "1港币=0.8106人民币",
            "0.185",
            "7.590",
            "7.440",
            "75aa41299d54169c3010c73d4d43c5e45fc2b74e1613a0c7d46c63af1d808398",
        ),
        (
            "CN-A:SZSE:000570",
            "000570",
            "2012-06-12",
            "2012-06-13",
            "bb9898638f6cfe2e6dda1c8a08565c542ab0ffcaee295339094a7e63947ecba7",
            "0.02",
            "1港币=0.8145人民币",
            "0.025",
            "6.760",
            "6.740",
            "80ef456982db2dd05542ffc7cd1024f0481d096c85952c5e34e6fe81321e9c02",
        ),
        (
            "CN-A:SZSE:000581",
            "000581",
            "2012-07-17",
            "2012-07-18",
            "b8ef0150ce1b052171a7f7de7553ab6ddae8224ddac077e235223025b04b7e2c",
            "0.3",
            "1港币=0.8145人民币",
            "0.368",
            "26.350",
            "26.050",
            "0f13e92f0907611a3cdc26bbb29c096301ad4f43924915d6fefd5211ceb5976d",
        ),
    ],
)
def test_ab_currency_conflict_requires_issuer_and_exchange_price_crosscheck(
    security_id, issuer, record, ex, source_sha, cash, rate_text, dps, before, after, exchange_sha
):
    row = {
        "security_id": security_id,
        "issuer": issuer,
        "record_date": record,
        "ex_date": ex,
        "substitute_source_sha256": source_sha,
    }
    pages = [
        f"股票代码\uff1a{issuer} 向全体股东每10股派现金人民币。"
        f"A股股权登记日为{record}\uff0cB股股息折算汇率 {rate_text}。"
    ]
    exchange = {
        "rows": [
            {
                "symbol": issuer,
                "record_date": record,
                "ex_date": ex,
                "source_url": "https://investor.szse.cn/official.html",
                "source_sha256": exchange_sha,
                "raw_cells": [
                    issuer,
                    "深赤湾A",
                    "0",
                    "0.000",
                    "185,947,320",
                    dps,
                    "",
                    "",
                    "",
                    "",
                    ex.replace("-", "/"),
                    record.replace("-", "/"),
                    after,
                    before,
                ],
            }
        ]
    }
    result = ab_currency_dps_conflict(row, Decimal(cash), pages, exchange)
    assert result["exchange_reported_dps"] == dps
    assert Decimal(result["exchange_ex_price_delta"]) == Decimal(cash)
    assert ab_currency_dps_conflict(row, Decimal(cash) + Decimal("0.01"), pages, exchange) is None
    changed = {**exchange["rows"][0], "raw_cells": [*exchange["rows"][0]["raw_cells"]]}
    changed["raw_cells"][12] = str(Decimal(after) - Decimal("0.01"))
    assert ab_currency_dps_conflict(row, Decimal(cash), pages, {"rows": [changed]}) is None
    assert (
        ab_currency_dps_conflict(
            row, Decimal(cash), pages, {"rows": [{**exchange["rows"][0], "source_sha256": "other"}]}
        )
        is None
    )


def test_historical_requirement_symbol_links_only_with_official_transition():
    requirement = {
        "priority": "P1",
        "source_group": "CNINFO",
        "document_id": "historical-code-cash",
        "known_urls": [],
        "required_document_types": ["FINAL_IMPLEMENTATION_NOTICE_WITH_GROSS_ORDINARY_A_SHARE_CASH"],
        "affected_events": ["CASH:000022:2012-07-19:2012-07-20"],
    }
    event = {
        "event": {
            "security_id": {"value": "CN-A:SZSE:001872"},
            "record_date": "2012-07-19",
            "ex_date": "2012-07-20",
            "cash_per_share": "0.4",
            "source_provider": "OFFICIAL_ISSUER_CNINFO_EXCHANGE_DATED",
            "source_url": "https://static.cninfo.com.cn/finalpage/notice.PDF",
            "source_document": "2011年度分红派息实施公告",
            "source_document_sha256": "pdf-sha",
            "announcement_date": "2012-07-12",
        },
        "event_checksum": "event-sha",
    }
    master = [
        {
            "symbol": "000022",
            "security_id": "CN-A:SZSE:001872",
            "effective_from": "1993-05-05",
            "effective_to": "2018-12-25",
            "instrument_type": "COMMON_A_SHARE",
            "code_transition_source_url": "https://static.cninfo.com.cn/finalpage/change.PDF",
            "code_transition_source_sha256": "transition-sha",
        }
    ]
    source = {
        "url": event["event"]["source_url"],
        "retrieval_status": "PASS",
        "issuer": "000022",
        "title": event["event"]["source_document"],
        "published_on": "2012-07-12",
        "source_sha256": "pdf-sha",
        "source_path": "notice.pdf",
    }
    assert eligible([requirement], set(), [event]) == ([], [])
    assert eligible([requirement], set(), [event], master) == ([requirement], [event])
    selected = select([requirement], [], [], [event], master, [source], historical_alias=True)
    assert selected[0]["security_id"] == "CN-A:SZSE:001872"
    assert selected[0]["requirement_historical_symbol"] == "000022"
    assert selected[0]["official_code_transition_sha256"] == "transition-sha"
    assert not select(
        [requirement],
        [],
        [],
        [event],
        [{**master[0], "code_transition_source_sha256": None}],
        [source],
        historical_alias=True,
    )
