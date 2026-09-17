import pytest

from scripts.audit_p1_cumulative_fact_closure import recount


def test_cumulative_p1_closure_rejects_duplicate_and_recounts_facts():
    baseline = {
        "remaining_cash_documents": [
            {"document_id": "cash", "url": "https://official/cash", "affected_events": ["a"]}
        ],
        "p1_unestablished_unique_documents": 2,
        "p1_true_missing_source_facts": 3,
        "p1_raw_requirements": 4,
    }
    blank = {"excluded": [], "closed": [], "events": [], "classifications": []}
    reports = {
        name: dict(blank)
        for name in (
            "preferred",
            "matched",
            "out_of_period",
            "primary",
            "orphan_issuer",
            "orphan_exchange",
            "sse_st",
            "differentiated",
            "correction",
            "proposal",
            "precise",
            "derivative",
            "retained_cash",
        )
    }
    reports["base"] = baseline
    reports["preferred"]["excluded"] = [baseline["remaining_cash_documents"][0]]
    reports["sse_st"]["closed"] = [{"document_id": "st", "affected_events": ["b", "c"]}]
    assert recount(reports)["p1_true_missing_source_facts"] == 0
    assert recount(reports)["p1_resolved_by_official_substitution"] == 1
    reports["matched"]["closed"] = [baseline["remaining_cash_documents"][0]]
    with pytest.raises(ValueError, match="DUPLICATE_P1_CLOSURE"):
        recount(reports)
