from scripts.classify_adjustment_term_residuals import classify


def test_residual_classification_is_source_bound_and_fail_closed() -> None:
    event = "FACTOR:CN-A:SZSE:000001:2024-01-02"
    terms = {
        "factor_results": [{"factor_change": event, "status": "NO_EXACT_OFFICIAL_TERMS_CANDIDATE"}],
        "documents": [{"source_sha256": "a" * 64, "status": "NOT_FINAL_IMPLEMENTATION_DOCUMENT"}],
    }
    sources = [
        {
            "affected_factor_changes": [event],
            "source_sha256": "a" * 64,
            "title": "关于重整计划资本公积金转增股本事项实施的公告",
            "url": "https://static.cninfo.com.cn/finalpage/one.PDF",
        }
    ]
    report = classify(terms, sources)
    assert report["counts"] == {"RESTRUCTURING_OR_DIRECTED_CAPITAL_MECHANICS": 1}
    assert not report["adjustment_authority_promoted"]
