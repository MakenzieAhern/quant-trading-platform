import pytest

from scripts.close_p1_residual_merger_facts import CASES, close


def test_residual_merger_closure_requires_every_exact_p1_fact():
    requirements = {
        "documents": [
            {"document_id": event_id, "affected_events": [event_id], "priority": "P1"}
            for event_id in CASES
        ]
    }
    evidence = {
        event_id: [{"sha256": row[1]} for row in case["documents"]]
        for event_id, case in CASES.items()
    }
    result = close(requirements, evidence)
    assert result["closed_facts"] == 4
    assert {row["affected_events"][0] for row in result["closed"]} == set(CASES)
    cross_market = {
        row["affected_events"][0]: row["facts"]
        for row in result["closed"]
        if row["affected_events"][0] in ("MERGER:000522:600332", "MERGER:002013:600372")
    }
    assert set(cross_market) == {"MERGER:000522:600332", "MERGER:002013:600372"}
    assert all(
        facts["accounting_policy"] == "NON_TRADABLE_PENDING_ACCOUNTING_V1"
        and facts["boundary_policy"] == "FIRST_POST_EVENT_TRADING_BOUNDARY_V1"
        and facts["account_scope"] == "EXISTING_ORDINARY_A_SHARE_CASH_ACCOUNT_MODEL"
        for facts in cross_market.values()
    )
    with pytest.raises(ValueError, match="P1_MERGER_EVIDENCE_INCOMPLETE"):
        close(requirements, {**evidence, "MERGER:000578:000792": []})
