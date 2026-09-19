import hashlib
import json

from scripts.reconcile_szse_resumptions import (
    bind_resumptions,
    exact_restoration_dates,
    exact_resume_dates,
    official_document_text,
    unresolved_facts,
)


def test_exact_resumption_dates_reject_plans_and_stop_dates():
    assert exact_resume_dates("公司股票将于2010年2月10日开市时复牌。", "2010-02-10") == [
        "2010-02-10"
    ]
    assert exact_resume_dates(
        "公司股票于2013年1月28日开市起停牌,并将于2013年1月29日开市起复牌。",
        "2013-01-29",
    ) == ["2013-01-29"]
    assert exact_resume_dates("公司股票预计于2011年8月4日公告并复牌。", "2011-08-03") == []
    assert exact_resume_dates("公司股票自本公告公布当日起复牌。", "2011-10-28") == ["2011-10-28"]


def test_exact_resumption_dates_cover_observed_official_forms():
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
