import hashlib
import json

from scripts.reconcile_szse_resumptions import (
    bind_resumptions,
    continued_halt_restoration_dates,
    exact_restoration_dates,
    exact_resume_dates,
    execution_open_blocked,
    non_equity_resumption_title,
    official_document_text,
    unresolved_facts,
)


def test_non_equity_resumption_titles_require_an_equity_subject():
    assert non_equity_resumption_title("关于“14雏鹰债”复牌的公告")
    assert non_equity_resumption_title("关于中装转2复牌及恢复转股的提示性公告")
    assert not non_equity_resumption_title("关于筹划控制权变更事项进展暨复牌及恢复转股的公告")
    assert not non_equity_resumption_title("关于公司股票及可转换公司债券复牌的公告")


def test_exact_resumption_dates_reject_plans_and_stop_dates():
    assert exact_resume_dates("公司股票将于2010年2月10日开市时复牌。", "2010-02-10") == [
        "2010-02-10"
    ]
    assert exact_resume_dates(
        "公司股票于2013年1月28日开市起停牌,并将于2013年1月29日开市起复牌。",
        "2013-01-29",
    ) == ["2013-01-29"]
    assert exact_resume_dates("公司股票预计于2011年8月4日公告并复牌。", "2011-08-03") == []
    assert exact_resume_dates("公司股票不迟于2015年11月20日前复牌。", "2015-11-18") == []
    assert exact_resume_dates("公司证券最晚将于2013年11月10日恢复交易。", "2013-10-31") == []
    assert exact_resume_dates("公司股票将于2016年12月13日前复牌。", "2016-12-10") == []
    assert exact_resume_dates("决定延期至不超过2013年3月18日复牌。", "2013-03-14") == []
    assert exact_resume_dates("决定延期至2013年4月18日复牌。", "2013-04-08") == []
    assert (
        exact_resume_dates(
            "决定延期至2013年5月4日披露相关公告并于2013年5月6日复牌。",
            "2013-05-03",
        )
        == []
    )
    assert exact_resume_dates(
        "经公司申请,公司股票将于2015年11月18日开市起复牌。", "2015-11-18"
    ) == ["2015-11-18"]
    assert exact_resume_dates(
        "经向深圳证券交易所申请,公司股票自2016年8月15日开市起复牌。",
        "2016-08-13",
    ) == ["2016-08-15"]
    assert (
        exact_resume_dates(
            "经公司申请,本公司股票自2012年5月8日起停牌,"
            "待刊登相关公告后,计划于2012年5月11日申请复牌。",
            "2012-05-08",
        )
        == []
    )
    assert exact_resume_dates(
        "特别提示:公司股票自2013年7月10日开市起恢复交易。"
        "经向深圳证券交易所申请,公司股票自2013年7月11日开市起复牌。",
        "2013-07-11",
    ) == ["2013-07-10", "2013-07-11"]
    assert (
        exact_resume_dates(
            "公司股票定于2014年4月25日开市起复牌,但是因重大事项自2014年4月25日开市起停牌。",
            "2014-04-25",
        )
        == []
    )
    assert exact_resume_dates("公司股票自本公告公布当日起复牌。", "2011-10-28") == ["2011-10-28"]
    assert exact_resume_dates(
        "公司于2018年5月31日接到《关于筹划重大事项复牌的通知》。"
        "公司股票将于2018年6月1日上午开市起复牌。",
        "2018-06-01",
    ) == ["2018-06-01"]
    assert exact_resume_dates(
        "股票复牌安排公司于2015年9月30日披露《关于股票复牌公告》。"
        "公司股票将于2015年10月8日上午开市起复牌。",
        "2015-09-30",
    ) == ["2015-10-08"]
    assert exact_resume_dates(
        "公司于2016年10月28日披露《关于延期复牌的公告》。"
        "公司股票将于2016年10月31日上午开市起复牌。",
        "2016-10-29",
    ) == ["2016-10-31"]


def test_exact_resumption_dates_cover_observed_official_forms():
    assert exact_resume_dates(
        "公司股票进入退市整理期交易的起始日为2019年8月27日。", "2019-08-20"
    ) == ["2019-08-27"]
    assert exact_resume_dates(
        "公司股票于2012年4月23日停牌,公告日即2012年4月24日开市起即复牌。",
        "2012-04-24",
    ) == ["2012-04-24"]
    assert exact_resume_dates("复牌时间定为2012年12月28日上午9点30分。", "2012-12-28") == [
        "2012-12-28"
    ]
    assert exact_resume_dates(
        "因事项预计金额较小,本公司股票将于2014年5月13日复牌。", "2014-05-13"
    ) == ["2014-05-13"]
    assert exact_resume_dates("公司股票拟于2014年3月10日(周一)开市起复牌。", "2014-03-08") == []
    assert exact_resume_dates(
        "公司股票于2011年2月25日开市起停牌,于2011年2月28日开市起恢复正常交易。",
        "2011-02-25",
    ) == ["2011-02-28"]
    assert exact_resume_dates(
        "本公司股票于2011年2月25日停牌1天,于2月26日披露年报,于2月28日复牌。",
        "2011-02-25",
    ) == ["2011-02-28"]
    assert (
        exact_resume_dates(
            "公司将于2011年8月17日开会,并于8月18日公告,同时申请股票复牌。",
            "2011-08-17",
        )
        == []
    )
    assert (
        exact_resume_dates(
            "若8月27日未召开董事会,公司将申请股票自8月28日起复牌。",
            "2018-08-23",
        )
        == []
    )
    assert exact_resume_dates(
        "本公司股票2011年2月14日上午停牌,下午13:00复牌。",
        "2011-02-14",
    ) == ["2011-02-14"]
    assert exact_resume_dates("公司股票于2012年1月5日停牌一小时后复牌。", "2012-01-05") == [
        "2012-01-05"
    ]
    assert exact_resume_dates("公司股票复牌时间为:2011年4月20日。", "2011-04-13") == ["2011-04-20"]
    assert execution_open_blocked("公司股票将于2014年5月23日13:00起复牌。", "2014-05-23")
    assert execution_open_blocked("公司股票将于2011年9月15日开市起复牌。", "2011-09-15") is False
    assert execution_open_blocked("公司股票将于2011年9月15日恢复交易。", "2011-09-15") is None
    correction = "公司于2015年1月21日披露《复牌公告》,1月20日下午接到通知。"
    assert execution_open_blocked(correction, "2015-01-21") is None
    assert exact_resume_dates("本公司股票自2011年4月11日复牌。", "2012-04-11") == []
    assert exact_resume_dates("公司B股股票将于2011年5月4日复牌。", "2011-05-04") == []
    assert (
        exact_resume_dates(
            "本公司境内上市外资股B股因事项停牌,股票将于2011年5月4日复牌。", "2011-05-04"
        )
        == []
    )


def test_exact_restoration_dates_require_an_effective_trading_boundary():
    assert exact_restoration_dates("公司股票将于2018年8月24日起恢复上市。") == ["2018-08-24"]
    assert exact_restoration_dates("2012年10月19日,公司股票在深交所恢复上市交易。") == [
        "2012-10-19"
    ]
    assert exact_restoration_dates("公司于2021年4月8日向深交所申请恢复上市。") == []
    assert exact_restoration_dates("公司股票已于2020年5月13日起暂停上市。") == []
    continued = "公司股票自2015年8月18日起恢复上市,因重大事项自同日开市起继续停牌。"
    assert exact_restoration_dates(continued) == []
    assert continued_halt_restoration_dates(continued) == ["2015-08-18"]


def test_official_cninfo_javascript_attachment(tmp_path):
    body = json.dumps(
        [{"Title": "股票复牌", "Zw": "公司股票将于2014年6月23日开市起复牌。"}],
        ensure_ascii=False,
    )
    source = tmp_path / "official.js"
    source.write_bytes(f"var affiches={body};".encode("gb18030"))
    document = {
        "source_path": "official.js",
        "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "retrieval_status": "NON_PDF_ATTACHMENT",
        "url": "https://static.cninfo.com.cn/finalpage/official.js",
    }
    assert exact_resume_dates(official_document_text(tmp_path, document), "2014-06-23") == [
        "2014-06-23"
    ]


def test_resumption_binding_stops_before_the_next_suspension():
    events = [
        {"symbol": "000001", "suspended_at": "2010/01/04 09:30"},
        {"symbol": "000001", "suspended_at": "2010/01/08 09:30"},
    ]
    unresolved = [
        {
            "security_id": "CN-A:SZSE:000001",
            "symbol": "000001",
            "suspended_at": "2010/01/04 09:30",
        }
    ]
    evidence = [
        {
            "symbol": "000001",
            "resumed_at": "2010-01-09",
            "url": "u",
            "source_sha256": "a",
        }
    ]
    accepted, remaining = bind_resumptions(unresolved, events, evidence)
    assert accepted == [] and remaining == unresolved
    assert unresolved_facts({"remaining_unresolved": unresolved}) == unresolved


def test_resumption_binding_is_stable_for_duplicate_source_identity():
    events = [{"symbol": "000001", "suspended_at": "2010/01/04 09:30"}]
    unresolved = [
        {
            "security_id": "CN-A:SZSE:000001",
            "symbol": "000001",
            "suspended_at": "2010/01/04 09:30",
        }
    ]
    evidence = [
        {
            "symbol": "000001",
            "resumed_at": "2010-01-05",
            "url": "u",
            "source_sha256": "a",
            "title": title,
        }
        for title in ("b", "a")
    ]
    assert bind_resumptions(unresolved, events, evidence) == bind_resumptions(
        unresolved, events, list(reversed(evidence))
    )


def test_resumption_binding_blocks_open_when_same_date_evidence_has_two_intraday_episodes():
    events = [{"symbol": "000001", "suspended_at": "2010/01/04 09:30"}]
    unresolved = [
        {
            "security_id": "CN-A:SZSE:000001",
            "symbol": "000001",
            "suspended_at": "2010/01/04 09:30",
        }
    ]
    evidence = [
        {"symbol": "000001", "resumed_at": "2010-01-05", "execution_open_blocked": False},
        {"symbol": "000001", "resumed_at": "2010-01-05", "execution_open_blocked": True},
    ]
    accepted, _ = bind_resumptions(unresolved, events, evidence)
    assert accepted[0]["execution_open_blocked"] is True
    assert accepted[0]["execution_open_status_conflict"] is True
