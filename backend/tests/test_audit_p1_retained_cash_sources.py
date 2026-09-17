from decimal import Decimal

from scripts.audit_p1_orphan_cash_facts import select
from scripts.audit_p1_retained_cash_sources import (
    ab_currency_dps_conflict,
    eligible,
    exchange_amount_matches,
    exchange_resolves_year_conflict,
    issuer_body_finality,
    retained_final_title,
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


def test_ab_currency_conflict_requires_issuer_and_exchange_price_crosscheck():
    row = {
        "security_id": "CN-A:SZSE:001872",
        "issuer": "000022",
        "record_date": "2012-07-19",
        "ex_date": "2012-07-20",
        "substitute_source_sha256": (
            "5ee3949582e2c5c967b4a3059c2b8c7a8077d50b0067608af584542b5deabee6"
        ),
    }
    pages = [
        "股票代码\uff1a000022、200022 向全体股东每10股派4.00元人民币现金。"
        "A股股权登记日为2012年7月19日\uff0cB股股息折算汇率 1港币\uff1d0.8149元人民币。"
    ]
    exchange = {
        "rows": [
            {
                "symbol": "000022",
                "record_date": "2012-07-19",
                "ex_date": "2012-07-20",
                "source_url": "https://investor.szse.cn/official.html",
                "source_sha256": "exchange-sha",
                "raw_cells": [
                    "000022",
                    "深赤湾A",
                    "0",
                    "0.000",
                    "185,947,320",
                    "0.491",
                    "",
                    "",
                    "",
                    "",
                    "2012/07/20",
                    "2012/07/19",
                    "9.480",
                    "9.880",
                ],
            }
        ]
    }
    result = ab_currency_dps_conflict(row, Decimal("0.4"), pages, exchange)
    assert result["exchange_reported_dps"] == "0.491"
    assert result["exchange_ex_price_delta"] == "0.400"
    assert ab_currency_dps_conflict(row, Decimal("0.49"), pages, exchange) is None
    changed = {**exchange["rows"][0], "raw_cells": [*exchange["rows"][0]["raw_cells"]]}
    changed["raw_cells"][12] = "9.470"
    assert ab_currency_dps_conflict(row, Decimal("0.4"), pages, {"rows": [changed]}) is None


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
