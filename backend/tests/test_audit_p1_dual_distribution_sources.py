import pytest

from scripts.audit_p1_dual_distribution_sources import DUAL_TYPES, dual_candidates


def test_dual_source_request_requires_both_distinct_facts_and_is_order_stable():
    row = {
        "priority": "P1",
        "required_document_types": DUAL_TYPES,
        "affected_events": [
            "BONUS:600000:2016-05-06:2016-05-09",
            "CASH:600000:2016-05-06:2016-05-09",
        ],
        "known_urls": [],
        "document_id": "dual",
    }
    key = ("600000", "2016-05-06", "2016-05-09")
    cash, bonus = {key: {"leg": "cash"}}, {key: {"leg": "bonus"}}
    assert dual_candidates([row], set(), cash, bonus) == [(row, key, cash[key], bonus[key])]
    assert dual_candidates([row], set(), cash, {})[0][-1] is None
    with pytest.raises(ValueError, match="ALREADY_CLOSED"):
        dual_candidates([row], {"dual"}, cash, bonus)
    with pytest.raises(ValueError, match="FACT_COUNT_CHANGED"):
        dual_candidates(
            [{**row, "affected_events": [row["affected_events"][0]]}], set(), cash, bonus
        )
