import pytest

from scripts.close_szse_six_listing_row_gaps import close_report


def test_mixed_listing_eras_and_reasons_do_not_relabel_peers():
    base = {
        "report_version": "SZSE_OFFICIAL_ROW_GAPS_V4",
        "manifest_sha256": "old",
        "missing_rows": 3,
        "classification_counts": {
            "NO_MATCHING_HALT_SOURCE": 1,
            "UNKNOWN_RESUMPTION_NOT_CLOSED": 1,
            "DATED_SOURCE_HALT_INTERVAL": 1,
        },
        "unresolved_rows": [
            {
                "security_id": "CN-A:SZSE:000620",
                "date": "2011-07-07",
                "reason": "NO_MATCHING_HALT_SOURCE",
            },
            {
                "security_id": "CN-A:SZSE:000820",
                "date": "2013-04-25",
                "reason": "UNKNOWN_RESUMPTION_NOT_CLOSED",
            },
        ],
        "additional_official_pre2010_intervals": [{"security_id": "CN-A:SZSE:000693"}],
    }
    closures = {
        "000620": {
            "suspended_from": "2006-04-03",
            "first_trading_day": "2011-07-08",
            "expected_rows": 1,
            "previous_reason": "NO_MATCHING_HALT_SOURCE",
            "category": "OFFICIAL_PRE2010_LISTING_SUSPENSION",
            "evidence": [],
        },
        "000820": {
            "suspended_from": "2011-04-28",
            "first_trading_day": "2013-04-26",
            "expected_rows": 1,
            "previous_reason": "UNKNOWN_RESUMPTION_NOT_CLOSED",
            "category": "OFFICIAL_2010PLUS_LISTING_SUSPENSION",
            "evidence": [],
        },
    }
    report = close_report(base, closures)
    assert report["classification_counts"]["OFFICIAL_PRE2010_LISTING_SUSPENSION"] == 1
    assert report["classification_counts"]["OFFICIAL_2010PLUS_LISTING_SUSPENSION"] == 1
    assert report["classification_counts"]["DATED_SOURCE_HALT_INTERVAL"] == 1
    assert report["unresolved_rows"] == []
    assert len(report["additional_official_pre2010_intervals"]) == 2
    base["unresolved_rows"][1]["date"] = "2013-04-26"
    with pytest.raises(ValueError, match="SOURCE_INTERVAL"):
        close_report(base, closures)
