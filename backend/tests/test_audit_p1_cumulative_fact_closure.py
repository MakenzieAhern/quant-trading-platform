import pytest

from scripts.audit_p1_cumulative_fact_closure import recount
from scripts.audit_p1_merger_000418_closure import EVENT, close


def test_false_hebei_parent_identity_requires_both_official_sources():
    from scripts.audit_p1_false_hebei_merger_parents import classify

    requirements = [
        {
            "document_id": code,
            "affected_events": [f"MERGER_NEW:{code}:000709"],
            "priority": "P1",
            "why_required": ["Complete cached HEBEI_STEEL lead"],
        }
        for code in ("000761", "000898")
    ]
    master = [
        {
            "security_id": f"CN-A:SZSE:{code}",
            "symbol": code,
            "source_observed_name": name,
            "effective_from": "1997-01-01",
            "effective_to": None,
            "instrument_type": "COMMON_A_SHARE",
        }
        for code, name in (("000761", "本钢板材"), ("000898", "鞍钢股份"))
    ]
    issuer = "股票代码:000709;换股吸收合并邯郸钢铁和承德钒钛"
    sse = "邯郸钢铁(600001)和承德钒钛(600357)因吸收合并退市"
    assert len(classify(requirements, master, issuer, sse)) == 2
    with pytest.raises(ValueError, match="SSE_PARENT_IDENTITIES_CHANGED"):
        classify(requirements, master, issuer, sse.replace("600357", "000898"))


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
            "merger_600607",
            "merger_600842",
            "false_hebei_parents",
            "restructuring_no_entitlement",
            "residual_restructuring",
            "bonus",
            "residual_bonus",
            "residual_merger",
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


@pytest.mark.parametrize(
    "parent,successor", [("600832", "600637"), ("600607", "600849"), ("600842", "600849")]
)
def test_recovered_merger_source_closure_requires_exact_event(parent, successor):
    import json
    from pathlib import Path

    from scripts.reconcile_merger_implementation_batch import event_from_review

    fixture = json.loads(
        (Path(__file__).parent / f"fixtures/merger_{parent}_recovery_v1.json").read_bytes()
    )
    event_id = f"MERGER_NEW:{parent}:{successor}"
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
