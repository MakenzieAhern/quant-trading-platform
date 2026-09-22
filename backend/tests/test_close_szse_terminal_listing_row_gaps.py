import pytest

from scripts.close_szse_terminal_listing_row_gaps import close_report


def test_terminal_listing_closure_is_bounded_and_conserves_other_categories():
    base = {
        "report_version": "SZSE_OFFICIAL_ROW_GAPS_V6",
        "manifest_sha256": "old",
        "missing_rows": 2,
        "classification_counts": {
            "UNKNOWN_RESUMPTION_NOT_CLOSED": 1,
            "DATED_SOURCE_HALT_INTERVAL": 1,
        },
        "unresolved_rows": [
            {
                "security_id": "CN-A:SZSE:000594",
                "date": "2014-09-05",
                "reason": "UNKNOWN_RESUMPTION_NOT_CLOSED",
            }
        ],
    }
    closure = {
        "000594": {
            "suspended_from": "2014-07-17",
            "terminal_decision_on": "2015-05-21",
            "expected_rows": 1,
            "previous_reason": "UNKNOWN_RESUMPTION_NOT_CLOSED",
            "evidence": [],
        }
    }
    report = close_report(base, closure)
    assert report["classification_counts"]["OFFICIAL_TERMINAL_LISTING_SUSPENSION"] == 1
    assert report["classification_counts"]["DATED_SOURCE_HALT_INTERVAL"] == 1
    assert report["unresolved_rows"] == []
    base["unresolved_rows"][0]["date"] = "2015-05-21"
    with pytest.raises(ValueError, match="SOURCE_INTERVAL"):
        close_report(base, closure)
