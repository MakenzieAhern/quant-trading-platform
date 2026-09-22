import pytest

from scripts.close_szse_three_listing_row_gaps import close_report


def test_three_listing_closure_preserves_other_rows_and_rejects_boundary_leakage():
    base = {
        "report_version": "SZSE_OFFICIAL_ROW_GAPS_V3",
        "manifest_sha256": "old",
        "missing_rows": 3,
        "classification_counts": {"NO_MATCHING_HALT_SOURCE": 2, "DATED_SOURCE_HALT_INTERVAL": 1},
        "unresolved_rows": [
            {
                "security_id": "CN-A:SZSE:000038",
                "date": "2013-02-07",
                "reason": "NO_MATCHING_HALT_SOURCE",
            },
            {
                "security_id": "CN-A:SZSE:000719",
                "date": "2011-12-01",
                "reason": "NO_MATCHING_HALT_SOURCE",
            },
        ],
        "additional_official_pre2010_intervals": [{"security_id": "CN-A:SZSE:000693"}],
    }
    closures = {
        "000038": {
            "suspended_from": "2007-05-22",
            "first_trading_day": "2013-02-08",
            "expected_rows": 1,
            "evidence": [],
        }
    }
    report = close_report(base, closures)
    assert report["classification_counts"]["OFFICIAL_PRE2010_LISTING_SUSPENSION"] == 1
    assert report["unresolved_rows"] == base["unresolved_rows"][1:]
    assert len(report["additional_official_pre2010_intervals"]) == 2
    base["unresolved_rows"][0]["date"] = "2013-02-08"
    with pytest.raises(ValueError, match="SOURCE_INTERVAL"):
        close_report(base, closures)
