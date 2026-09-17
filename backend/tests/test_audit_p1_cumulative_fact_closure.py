import pytest

from scripts.audit_p1_cumulative_fact_closure import recount
from scripts.audit_p1_merger_000418_closure import EVENT, close


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
            "dual",
            "designated",
            "merger_new",
            "merger_600832",
            "merger_600631",
        )
    }
    reports["base"] = baseline
    reports["preferred"]["excluded"] = [baseline["remaining_cash_documents"][0]]
    reports["sse_st"]["closed"] = [{"document_id": "st", "affected_events": ["b", "c"]}]
    assert recount(reports)["p1_true_missing_source_facts"] == 0
    assert recount(reports)["p1_resolved_by_official_substitution"] == 1
    reports["base"]["p1_unestablished_unique_documents"] = 3
    reports["base"]["p1_true_missing_source_facts"] = 4
    reports["merger_600832"]["closed"] = [
        {"document_id": "parent-source", "affected_events": ["MERGER_NEW:600832:600637"]}
    ]
    assert recount(reports)["p1_true_missing_source_facts"] == 0
    assert recount(reports)["p1_resolved_by_official_substitution"] == 2
    reports["matched"]["closed"] = [baseline["remaining_cash_documents"][0]]
    with pytest.raises(ValueError, match="DUPLICATE_P1_CLOSURE"):
        recount(reports)


def test_000418_source_closure_requires_audited_chain():
    import json
    from pathlib import Path

    from scripts.reconcile_merger_implementation_batch import event_from_review

    fixture = json.loads(
        (Path(__file__).parent / "fixtures/merger_000418_recovery_v1.json").read_bytes()
    )
    requirements = {
        "documents": [
            {"document_id": "parent-source", "affected_events": [EVENT], "priority": "P1"}
        ]
    }
    audit = {
        "event_checksum": event_from_review(fixture["case"]).event_checksum,
        "review_sha256": "fixture-sha",
        "scope": fixture["case"]["scope"],
        "source_bytes_verified": True,
        "source_terms_verified": True,
        "input_order_reproducibility": "PASS",
        "full_census_certified": False,
        "full_dataset_created": False,
        "manifest_sha256": "audit-sha",
    }
    result = close(requirements, audit, fixture, "fixture-sha")
    assert result["closed"][0]["affected_events"] == [EVENT]
    assert not result["inventory_admitted"]
    with pytest.raises(ValueError, match="P1_MERGER_SOURCE_AUDIT_NOT_ACCEPTED"):
        close(requirements, {**audit, "source_terms_verified": False}, fixture, "fixture-sha")


def test_600832_source_closure_requires_exact_event_and_recounts():
    import json
    from pathlib import Path

    from scripts.reconcile_merger_implementation_batch import event_from_review

    fixture = json.loads(
        (Path(__file__).parent / "fixtures/merger_600832_recovery_v1.json").read_bytes()
    )
    event_id = "MERGER_NEW:600832:600637"
    requirements = {
        "documents": [
            {"document_id": "parent-source", "affected_events": [event_id], "priority": "P1"}
        ]
    }
    audit = {
        "event_checksum": event_from_review(fixture["case"]).event_checksum,
        "review_sha256": "fixture-sha",
        "scope": fixture["case"]["scope"],
        "source_bytes_verified": True,
        "source_terms_verified": True,
        "input_order_reproducibility": "PASS",
        "full_census_certified": False,
        "full_dataset_created": False,
        "manifest_sha256": "audit-sha",
    }
    assert close(requirements, audit, fixture, "fixture-sha", event_id)["closed"][0][
        "affected_events"
    ] == [event_id]
    with pytest.raises(ValueError, match="P1_MERGER_EVENT_ID_MISMATCH"):
        close(requirements, audit, fixture, "fixture-sha", EVENT)


def test_600631_source_closure_requires_exact_event():
    import json
    from pathlib import Path

    from scripts.reconcile_merger_implementation_batch import event_from_review

    fixture = json.loads(
        (Path(__file__).parent / "fixtures/merger_600631_recovery_v1.json").read_bytes()
    )
    event_id = "MERGER_NEW:600631:600827"
    requirements = {
        "documents": [
            {"document_id": "parent-source", "affected_events": [event_id], "priority": "P1"}
        ]
    }
    audit = {
        "event_checksum": event_from_review(fixture["case"]).event_checksum,
        "review_sha256": "fixture-sha",
        "scope": fixture["case"]["scope"],
        "source_bytes_verified": True,
        "source_terms_verified": True,
        "input_order_reproducibility": "PASS",
        "full_census_certified": False,
        "full_dataset_created": False,
        "manifest_sha256": "audit-sha",
    }
    assert close(requirements, audit, fixture, "fixture-sha", event_id)["closed"][0][
        "affected_events"
    ] == [event_id]
    with pytest.raises(ValueError, match="P1_MERGER_SOURCE_AUDIT_NOT_ACCEPTED"):
        close(
            requirements,
            {**audit, "source_terms_verified": False},
            fixture,
            "fixture-sha",
            event_id,
        )
