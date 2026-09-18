import pytest

from scripts.close_szse_pre2010_row_gaps import close_report


def test_bounded_closure_reconciles_mixed_reasons_without_touching_peers():
    base = {
        "report_version": "SZSE_OFFICIAL_ROW_GAPS_V2",
        "manifest_sha256": "old",
        "missing_rows": 3,
        "classification_counts": {
            "NO_MATCHING_HALT_SOURCE": 2,
            "UNKNOWN_RESUMPTION_NOT_CLOSED": 1,
        },
        "unresolved_rows": [
            {
                "security_id": "CN-A:SZSE:000688",
                "date": "2010-01-04",
                "reason": "NO_MATCHING_HALT_SOURCE",
            },
            {
                "security_id": "CN-A:SZSE:000688",
                "date": "2013-04-25",
                "reason": "UNKNOWN_RESUMPTION_NOT_CLOSED",
            },
            {
                "security_id": "CN-A:SZSE:000403",
                "date": "2010-01-04",
                "reason": "NO_MATCHING_HALT_SOURCE",
            },
        ],
    }
    closure = {
        "000688": {
            "suspended_from": "2007-05-23",
            "first_trading_day": "2013-04-26",
            "reasons": {"NO_MATCHING_HALT_SOURCE": 1, "UNKNOWN_RESUMPTION_NOT_CLOSED": 1},
            "url": "official",
            "sha256": "hash",
            "retrieved_at_utc": "2026-09-19T00:00:00+00:00",
        }
    }
    report = close_report(base, closure)
    assert report["classification_counts"]["OFFICIAL_PRE2010_LISTING_SUSPENSION"] == 2
    assert report["unresolved_rows"] == base["unresolved_rows"][2:]
    base["unresolved_rows"][1]["date"] = "2013-04-26"
    with pytest.raises(ValueError, match="SOURCE_INTERVAL"):
        close_report(base, closure)
