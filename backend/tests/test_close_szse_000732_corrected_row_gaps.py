import pytest

from scripts.close_szse_000732_corrected_row_gaps import close_report, notice_block


def test_issuer_notice_and_bounded_source_absence_only():
    page = (
        "证券代码:000732证券简称:*ST三农公告编号:2010-29号"
        "福建三农集团股份有限公司关于公司股票恢复上市的公告"
        "公司选定的信息披露报纸:《证券时报》《中国证券报》"
        "深证上[2010]310号"
        "本所决定你公司股票自2010年9月30日起恢复上市"
        "因2004、2005、2006年连续三年亏损,公司股票自2007年5月11日起被深交所暂停上市"
        "福建三农集团股份有限公司董事会2010年9月20日"
        "证券代码:000732证券简称:*ST三农公告编号:2010-30号"
    )
    assert "2010年9月30日" in notice_block(page)
    with pytest.raises(ValueError, match="OFFICIAL_INTERVAL_NOT_PROVEN"):
        notice_block(page.replace("2007年5月11日", "2007年5月12日"))

    base = {
        "report_version": "SZSE_OFFICIAL_ROW_GAPS_CORRECTED_V3",
        "raw_authority_promoted": False,
        "manifest_sha256": "base",
        "missing_rows": 3,
        "classification_counts": {"NO_MATCHING_HALT_SOURCE": 3},
        "official_intervals": [],
        "unresolved_rows": [
            {
                "security_id": "CN-A:SZSE:000732",
                "date": "2010-01-04",
                "reason": "NO_MATCHING_HALT_SOURCE",
            },
            {
                "security_id": "CN-A:SZSE:000732",
                "date": "2010-09-29",
                "reason": "NO_MATCHING_HALT_SOURCE",
            },
            {
                "security_id": "CN-A:SZSE:002075",
                "date": "2010-05-07",
                "reason": "NO_MATCHING_HALT_SOURCE",
            },
        ],
    }
    evidence = {"pdfs": [{"url": "original"}], "cninfo_official_notice_index": {}}
    report = close_report(base, evidence, "notice", expected_rows=2)
    assert report["classification_counts"] == {
        "NO_MATCHING_HALT_SOURCE": 1,
        "OFFICIAL_PRE2010_LISTING_SUSPENSION": 2,
    }
    assert report["unresolved_symbols"] == {"002075": 1}
    assert report["raw_authority_promoted"] is False
    assert report["official_intervals"][0]["evidence"] == evidence["pdfs"]
    assert (
        close_report(base, evidence, "notice", expected_rows=2)["manifest_sha256"]
        == report["manifest_sha256"]
    )
    base["unresolved_rows"][1]["date"] = "2010-09-30"
    with pytest.raises(ValueError, match="SOURCE_INTERVAL_OR_COUNT_CHANGED"):
        close_report(base, {}, "notice", expected_rows=2)
