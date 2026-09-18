import pytest

from scripts.close_szse_five_later_listing_row_gaps import close_report


def test_later_listing_closure_is_bounded_and_conserves_other_categories():
    base = {
        "report_version": "SZSE_OFFICIAL_ROW_GAPS_V5",
        "manifest_sha256": "old",
        "missing_rows": 2,
        "classification_counts": {
            "UNKNOWN_RESUMPTION_NOT_CLOSED": 1,
            "DATED_SOURCE_HALT_INTERVAL": 1,
        },
        "unresolved_rows": [
            {
                "security_id": "CN-A:SZSE:002506",
                "date": "2014-09-05",
                "reason": "UNKNOWN_RESUMPTION_NOT_CLOSED",
            }
        ],
        "additional_official_2010plus_intervals": [{"security_id": "CN-A:SZSE:000820"}],
    }
    closures = {
        "002506": {
            "suspended_from": "2014-05-28",
            "first_trading_day": "2015-08-12",
            "expected_rows": 1,
            "evidence": [],
        }
    }
    report = close_report(base, closures)
    assert report["classification_counts"]["OFFICIAL_2010PLUS_LISTING_SUSPENSION"] == 1
    assert report["classification_counts"]["DATED_SOURCE_HALT_INTERVAL"] == 1
    assert len(report["additional_official_2010plus_intervals"]) == 2
    assert report["unresolved_rows"] == []
    base["unresolved_rows"][0]["date"] = "2015-08-12"
    with pytest.raises(ValueError, match="SOURCE_INTERVAL"):
        close_report(base, closures)
