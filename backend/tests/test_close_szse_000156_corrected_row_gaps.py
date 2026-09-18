import pytest

from scripts.close_szse_000156_corrected_row_gaps import close_report


def test_only_bounded_000156_rows_close_without_raw_promotion():
    base = {
        "report_version": "SZSE_OFFICIAL_ROW_GAPS_CORRECTED_V2",
        "raw_authority_promoted": False,
        "manifest_sha256": "base",
        "missing_rows": 3,
        "classification_counts": {"NO_MATCHING_HALT_SOURCE": 3},
        "official_intervals": [],
        "unresolved_rows": [
            {
                "security_id": "CN-A:SZSE:000156",
                "date": "2010-01-04",
                "reason": "NO_MATCHING_HALT_SOURCE",
            },
            {
                "security_id": "CN-A:SZSE:000156",
                "date": "2012-10-18",
                "reason": "NO_MATCHING_HALT_SOURCE",
            },
            {
                "security_id": "CN-A:SZSE:000732",
                "date": "2010-01-04",
                "reason": "NO_MATCHING_HALT_SOURCE",
            },
        ],
    }
    evidence = {"url": "https://disc.static.szse.cn/test.pdf", "sha256": "source"}
    report = close_report(base, evidence, expected_rows=2)
    assert report["classification_counts"] == {
        "NO_MATCHING_HALT_SOURCE": 1,
        "OFFICIAL_PRE2010_LISTING_SUSPENSION": 2,
    }
    assert report["unresolved_symbols"] == {"000732": 1}
    assert report["raw_authority_promoted"] is False
    assert report["official_intervals"][0]["evidence_temporality"].startswith("RETROSPECTIVE")
    assert (
        close_report(base, evidence, expected_rows=2)["manifest_sha256"]
        == report["manifest_sha256"]
    )
    base["unresolved_rows"][1]["date"] = "2012-10-19"
    with pytest.raises(ValueError, match="SOURCE_INTERVAL_OR_COUNT_CHANGED"):
        close_report(base, evidence, expected_rows=2)
