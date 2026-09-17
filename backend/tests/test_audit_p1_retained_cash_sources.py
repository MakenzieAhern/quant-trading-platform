from decimal import Decimal

from scripts.audit_p1_orphan_cash_facts import select
from scripts.audit_p1_retained_cash_sources import (
    eligible,
    exchange_amount_matches,
    exchange_resolves_year_conflict,
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
