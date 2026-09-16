from decimal import Decimal

from scripts.reconcile_cash_gap_candidates import (
    affected_cash_events,
    approved_distribution_periods,
    authoritative_evidence,
    distribution_periods,
    exchange_with_historical_symbols,
    extraction_cache,
    is_final_implementation_document,
    is_final_implementation_title,
    is_shareholder_approval_title,
    retrospective_completion,
    unique_candidate_event,
    unique_event_match,
    unique_official_event,
)


def test_retrospective_completion_requires_matching_fiscal_and_completion_years():
    assert retrospective_completion(
        "2012年度利润分配方案每10股派1元。2012年度利润分配方案已于2013年04月18日实施完毕。",
        "2012年年度权益分派实施公告",
        "2013-04-18",
    )
    assert not retrospective_completion(
        "2011年度利润分配方案已于2012年05月22日实施完毕。",
        "2012年年度权益分派实施公告",
        "2013-04-18",
    )


def test_alternate_extraction_cache_is_preferred(tmp_path):
    legacy = tmp_path / "batch-v1/text/abc.json"
    alternate = tmp_path / "batch-v1/text-pymupdf/abc.json"
    legacy.parent.mkdir(parents=True)
    legacy.touch()
    assert extraction_cache(tmp_path, "abc") == legacy
    alternate.parent.mkdir(parents=True)
    alternate.touch()
    assert extraction_cache(tmp_path, "abc") == alternate


def test_final_title_accepts_only_explicit_distribution_execution_wording():
    for title in (
        "2024年年度权益分派实施公告",
        "2020年度分红派息公告",
        "2011年度权益分配实施公告",
        "2015年度分红及送股实施公告",
        "2010年度末期股息派发实施公告",
        "泛微网络2022年年度权益实施分派公告",
        "董事会2015年度分红派息公告",
        "2011年度权益分派方案公告",
        "2015年度利润分配及资本公积金转增股本公告",
        "2010年度利润分配及资本公积转增股本公告",
        "A股派发特别股息实施公告",
        "关于现金股利实施的公告",
        "派发2014年度末期股息公告",
        "关于派发2015年度末期股息的公告",
        "2010年度利润分配公告",
        "宁波鲍斯能源装备股份有限公司2021年半年度权益分派",
    ):
        assert is_final_implementation_title(title)
    assert not is_final_implementation_title("2024年度利润分配方案公告")
    assert not is_final_implementation_title("关于2024年度利润分配预案的公告")
    assert not is_final_implementation_title("董事会战略委员会实施细则(2022年4月)")
    assert not is_final_implementation_title("关于实施利润分配方案后调整回购价格上限的公告")
    assert is_final_implementation_document(
        "董事会公告", "股权登记日 除息日 分红派息具体实施日期 分红派息实施办法"
    )
    assert is_shareholder_approval_title("2010年度股东大会决议公告")


def test_approval_and_board_terms_require_the_same_distribution_period():
    approval = "审议通过了《关于2010年半年度利润分配方案》。审议通过2012年度利润分配议案。"
    proposal = "董事会提议2010年半年度利润分配方案为每10股派2元。2012年度利润分配。"
    wrong_year = "董事会提议2011年度利润分配方案为每10股派2元。"
    assert approved_distribution_periods(approval) == {"2010年半年度", "2012年度"}
    assert approved_distribution_periods(approval) <= distribution_periods(proposal)
    assert not approved_distribution_periods(approval) & distribution_periods(wrong_year)


def test_corrected_notice_supersedes_original_notice():
    original = {"source": {"title": "2023年年度权益分派实施公告"}}
    corrected = {"source": {"title": "2023年年度权益分派实施公告(更正版)"}}
    assert authoritative_evidence([original, corrected]) == [corrected]


def test_unique_event_match_requires_one_exact_official_event():
    first = "CASH:600000:2020-01-02:2020-01-03"
    second = "CASH:600000:2020-06-02:2020-06-03"
    exchange = {
        ("600000", "2020-01-02", "2020-01-03"): {Decimal("0.1")},
        ("600000", "2020-06-02", "2020-06-03"): {Decimal("0.2")},
    }
    assert unique_event_match(Decimal("0.1"), [first, second], exchange) == (
        "600000",
        "2020-01-02",
        "2020-01-03",
    )
    assert unique_event_match(Decimal("0.3"), [first], exchange) is None
    assert unique_official_event(Decimal("0.2"), [first, second], exchange) == (
        "600000",
        "2020-06-02",
        "2020-06-03",
    )
    exchange[("600000", "2020-06-02", "2020-06-03")] = {Decimal("0.1")}
    assert unique_event_match(Decimal("0.1"), [first, second], exchange) is None
    assert unique_candidate_event([first], exchange) == (
        "600000",
        "2020-01-02",
        "2020-01-03",
    )
    assert unique_candidate_event([first, second], exchange) is None


def test_exchange_with_historical_symbols_maps_backfilled_current_code():
    exchange = {("601360", "2017-05-10", "2017-05-11"): {Decimal("0.13")}}
    master = [
        {
            "security_id": "CN-A:SSE:601360",
            "symbol": "601313",
            "effective_from": "2012-01-16",
            "effective_to": "2018-02-22",
        }
    ]
    enriched, aliases = exchange_with_historical_symbols(exchange, master)
    assert enriched[("601313", "2017-05-10", "2017-05-11")] == {Decimal("0.13")}
    assert aliases == [
        {
            "security_id": "CN-A:SSE:601360",
            "historical_symbol": "601313",
            "official_source_symbol": "601360",
            "record_date": "2017-05-10",
            "ex_date": "2017-05-11",
        }
    ]


def test_affected_cash_events_falls_back_to_bounded_exchange_candidates():
    document = {
        "issuer": "600000",
        "published_on": "2020-01-01",
        "affected_events": ["CNINFO:1"],
    }
    by_symbol = {
        "600000": [
            ("600000", "2020-02-29", "2020-03-02"),
            ("600000", "2020-04-01", "2020-04-02"),
        ]
    }
    assert affected_cash_events(document, by_symbol) == ["CASH:600000:2020-02-29:2020-03-02"]
