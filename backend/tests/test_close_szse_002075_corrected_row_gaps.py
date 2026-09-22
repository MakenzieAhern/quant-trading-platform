import pytest

from scripts.close_szse_002075_corrected_row_gaps import close_report, notice_block


def test_original_exchange_notices_and_bounded_source_absence_only():
    title = "关于同意江苏沙钢股份有限公司股票恢复上市的公告"
    page = title + "股票自2011年4月8日起恢复上市深圳证券交易所" + "关于支付2009年辽宁省政府债券"
    assert "2011年4月8日" in notice_block(
        page, title, "关于支付2009年辽宁省政府债券", ("2011年4月8日",)
    )
    with pytest.raises(ValueError, match="INTERVAL_NOT_PROVEN"):
        notice_block(page, title, "关于支付2009年辽宁省政府债券", ("2011年4月7日",))

    base = {
        "report_version": "SZSE_OFFICIAL_ROW_GAPS_CORRECTED_V4",
        "raw_authority_promoted": False,
        "manifest_sha256": "base",
        "missing_rows": 3,
        "classification_counts": {"UNKNOWN_RESUMPTION_NOT_CLOSED": 2, "NO_MATCHING_HALT_SOURCE": 1},
        "official_intervals": [],
        "unresolved_rows": [
            {
                "security_id": "CN-A:SZSE:002075",
                "date": "2010-05-07",
                "reason": "UNKNOWN_RESUMPTION_NOT_CLOSED",
            },
            {
                "security_id": "CN-A:SZSE:002075",
                "date": "2011-04-07",
                "reason": "UNKNOWN_RESUMPTION_NOT_CLOSED",
            },
            {
                "security_id": "CN-A:SZSE:300001",
                "date": "2011-07-25",
                "reason": "NO_MATCHING_HALT_SOURCE",
            },
        ],
    }
    report = close_report(base, [{"url": "original"}], ["start", "end"], expected_rows=2)
    assert report["classification_counts"] == {
        "NO_MATCHING_HALT_SOURCE": 1,
        "OFFICIAL_2010PLUS_LISTING_SUSPENSION": 2,
        "UNKNOWN_RESUMPTION_NOT_CLOSED": 0,
    }
    assert report["unresolved_symbols"] == {"300001": 1}
    assert report["raw_authority_promoted"] is False
    assert (
        close_report(base, [{"url": "original"}], ["start", "end"], expected_rows=2)[
            "manifest_sha256"
        ]
        == report["manifest_sha256"]
    )
    base["unresolved_rows"][1]["date"] = "2011-04-08"
    with pytest.raises(ValueError, match="SOURCE_INTERVAL_OR_COUNT_CHANGED"):
        close_report(base, [], [], expected_rows=2)
