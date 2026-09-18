import pytest

from scripts.close_szse_000693_row_gaps import close_report


def test_000693_closure_is_bounded_and_preserves_other_gaps():
    base = {
        "report_version": "SZSE_OFFICIAL_ROW_GAPS_V1",
        "manifest_sha256": "old",
        "missing_rows": 3,
        "classification_counts": {"NO_MATCHING_HALT_SOURCE": 3},
        "unresolved_rows": [
            {
                "security_id": "CN-A:SZSE:000693",
                "date": "2010-01-04",
                "reason": "NO_MATCHING_HALT_SOURCE",
            },
            {
                "security_id": "CN-A:SZSE:000693",
                "date": "2014-01-09",
                "reason": "NO_MATCHING_HALT_SOURCE",
            },
            {
                "security_id": "CN-A:SZSE:000498",
                "date": "2010-01-04",
                "reason": "NO_MATCHING_HALT_SOURCE",
            },
        ],
    }
    result = close_report(base, [], expected_rows=2)
    assert result["classification_counts"]["OFFICIAL_PRE2010_LISTING_SUSPENSION"] == 2
    assert result["unresolved_rows"] == base["unresolved_rows"][2:]
    assert result["unresolved_symbols"] == {"000498": 1}
    base["unresolved_rows"][1]["date"] = "2014-01-10"
    with pytest.raises(ValueError, match="BOUNDARY"):
        close_report(base, [], expected_rows=2)
