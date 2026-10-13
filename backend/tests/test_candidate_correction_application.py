"""Source-text corrections never replace negative evidence or grant admission."""

import json
from copy import deepcopy

import pytest

from app.domain.markets.corporate_actions import CorporateAction
from scripts import audit_full_dataset as auditor
from scripts.materialize_full_dataset import action_row
from tests.test_candidate_source_gaps import known_gap
from tests.test_distribution_reference_basis import reference_fixture


def proof_for(rows):
    events = [CorporateAction.model_validate_json(row["event_json"]) for row in rows]
    cash = next(event for event in events if event.action_type == "CASH_DIVIDEND")
    bonus = next((event for event in events if event.action_type == "BONUS_SHARE"), None)
    return {
        "security_id": str(cash.security_id),
        "record_date": cash.record_date.isoformat(),
        "ex_date": cash.ex_date.isoformat(),
        "source_sha256": cash.source_document_sha256,
        "source_url": cash.source_url,
        "cash_per_share": str(cash.cash_per_share),
        "bonus_share_ratio": str(bonus.share_ratio) if bonus else "0",
        "correction_evidence": {"scope": "SYNTHETIC_UNIT_TEST_NOT_OFFICIAL_AUTHORITY"},
    }


def replace_event(row, **changes):
    payload = json.loads(row["event_json"])
    payload.update(changes)
    event = CorporateAction.model_validate(payload)
    row.update(
        action_row(
            event.model_dump(mode="json"),
            event.event_checksum,
            event_kind=row["event_kind"],
            application_date=event.effective_date.isoformat() if event.effective_date else None,
            security_id=str(event.security_id),
            acceptance={},
        )
    )


@pytest.fixture
def correction_case(tmp_path):
    _, cash, bonus, _ = reference_fixture(tmp_path)
    rows = [
        action_row(
            event.model_dump(mode="json"),
            event.event_checksum,
            event_kind="CORPORATE_ACTION",
            application_date=event.effective_date.isoformat(),
            security_id=str(event.security_id),
            acceptance={},
        )
        for event in (cash, bonus)
    ]
    return rows, known_gap(rows), proof_for(rows)


def apply_without_mutation(result, rows, proofs):
    original = deepcopy((result, rows, proofs))
    report = auditor.apply_cash_corrections(result, rows, proofs)
    assert (result, rows, proofs) == original
    assert report is not result
    assert report["findings"] == result["findings"]
    assert report["original_status"] == result["status"]
    assert report["financial_admission"] is False
    for resolution in report["source_text_resolutions"]:
        assert resolution["financial_admission"] is False
        assert resolution["matched_event_checksums"] == sorted(
            resolution["matched_event_checksums"]
        )
    return report


def assert_unresolved(rows, gaps, proof):
    result = auditor.source_economic_integrity(rows, gaps)
    report = apply_without_mutation(result, rows, [proof])
    assert report["status"] == "FAIL"
    assert report["resolved_source_text_gap_count"] == 0
    assert report["unresolved_source_gap_count"] == report["unresolved_matched_gap_count"] == 1
    assert report["source_text_resolutions"][0]["status"] == "CANDIDATE_EVENT_TERMS_UNRESOLVED"


def test_complete_candidate_legs_resolve_only_source_text(correction_case):
    rows, gaps, proof = correction_case
    result = auditor.source_economic_integrity(rows, gaps)
    report = apply_without_mutation(result, rows, [proof])
    assert report["original_status"] == "FAIL"
    assert report["status"] == "NOT_EVIDENCED"
    assert report["resolved_source_text_gap_count"] == 1
    assert report["unresolved_source_gap_count"] == report["unresolved_matched_gap_count"] == 0
    assert report["source_text_resolutions"] == [
        {
            "evidence": proof,
            "status": "CASH_AGGREGATE_TEXT_RESOLVED",
            "matched_event_checksums": sorted(row["event_checksum"] for row in rows),
            "financial_admission": False,
        }
    ]
    report["findings"][0]["gap"]["evidence"] = "changed returned report only"
    report["source_text_resolutions"][0]["evidence"]["correction_evidence"]["scope"] = "changed"
    assert result["findings"][0]["gap"] == gaps["records"][0]
    assert proof["correction_evidence"]["scope"] == "SYNTHETIC_UNIT_TEST_NOT_OFFICIAL_AUTHORITY"


@pytest.mark.parametrize("share_ratio", [None, "0", "0.000"])
def test_zero_bonus_proof_accepts_one_cash_leg_with_no_share_entitlement(
    correction_case, share_ratio
):
    rows, gaps, proof = correction_case
    rows = rows[:1]
    replace_event(rows[0], share_ratio=share_ratio)
    proof["bonus_share_ratio"] = "0"
    result = auditor.source_economic_integrity(rows, gaps)
    report = apply_without_mutation(result, rows, [proof])
    assert report["status"] == "NOT_EVIDENCED"
    assert report["resolved_source_text_gap_count"] == 1
    assert report["source_text_resolutions"][0]["matched_event_checksums"] == [
        rows[0]["event_checksum"]
    ]


@pytest.mark.parametrize("leg", [0, 1], ids=["cash", "bonus"])
@pytest.mark.parametrize(
    "field,value",
    [
        ("security_id", "CN-A:SSE:600099"),
        ("source_document_sha256", "f" * 64),
        ("source_url", "https://example.com/wrong.pdf"),
        ("application_date", "2011-02-02"),
        ("event_kind", "RIGHTS_ISSUE"),
    ],
)
def test_outer_identity_and_event_kind_must_match(correction_case, leg, field, value):
    rows, gaps, proof = correction_case
    rows[leg][field] = value
    assert_unresolved(rows, gaps, proof)


@pytest.mark.parametrize("leg", [0, 1], ids=["cash", "bonus"])
@pytest.mark.parametrize(
    "field", ["security_id", "source_document_sha256", "source_url", "application_date"]
)
def test_missing_outer_authority_cannot_resolve(correction_case, leg, field):
    rows, gaps, proof = correction_case
    rows[leg].pop(field)
    assert_unresolved(rows, gaps, proof)


@pytest.mark.parametrize("leg", [0, 1], ids=["cash", "bonus"])
@pytest.mark.parametrize(
    "field,value",
    [
        ("security_id", {"value": "CN-A:SSE:600099"}),
        ("source_document_sha256", "f" * 64),
        ("source_url", "https://example.com/wrong.pdf"),
        ("record_date", "2011-01-30"),
        ("record_date", None),
        ("ex_date", "2011-02-02"),
        ("effective_date", "2011-02-02"),
        ("effective_date", None),
    ],
)
def test_consistent_inner_and_outer_drift_still_cannot_match_proof(
    correction_case, leg, field, value
):
    rows, gaps, proof = correction_case
    replace_event(rows[leg], **{field: value})
    assert_unresolved(rows, gaps, proof)


@pytest.mark.parametrize(
    "leg,field,value",
    [
        (0, "cash_per_share", "0.21"),
        (0, "cash_per_share", "0"),
        (0, "share_ratio", "0.5"),
        (0, "action_type", "BONUS_SHARE"),
        (0, "action_type", "STOCK_DIVIDEND"),
        (1, "cash_per_share", "0.01"),
        (1, "share_ratio", "0.6"),
        (1, "share_ratio", "0"),
        (1, "share_ratio", None),
        (1, "action_type", "CASH_DIVIDEND"),
        (1, "action_type", "STOCK_DIVIDEND"),
    ],
)
def test_economic_drift_or_wrong_ordinary_action_type_cannot_resolve(
    correction_case, leg, field, value
):
    rows, gaps, proof = correction_case
    replace_event(rows[leg], **{field: value})
    assert_unresolved(rows, gaps, proof)


@pytest.mark.parametrize("leg", [0, 1], ids=["cash", "bonus"])
@pytest.mark.parametrize("change", ["missing", "duplicate"])
def test_exactly_one_of_each_required_leg_is_required(correction_case, leg, change):
    rows, gaps, proof = correction_case
    if change == "missing":
        rows.pop(leg)
    else:
        rows.append(deepcopy(rows[leg]))
    assert_unresolved(rows, gaps, proof)


@pytest.mark.parametrize(
    "field,value",
    [("cash_per_share", "0.21"), ("bonus_share_ratio", "0.6"), ("bonus_share_ratio", "0")],
)
def test_candidate_economics_must_match_proof_values(correction_case, field, value):
    rows, gaps, proof = correction_case
    proof[field] = value
    assert_unresolved(rows, gaps, proof)


def test_current_payload_cannot_reuse_a_stale_event_checksum(correction_case):
    rows, gaps, proof = correction_case
    result = auditor.source_economic_integrity(rows, gaps)
    payload = json.loads(rows[0]["event_json"])
    payload["cash_per_share"] = "0.21"
    rows[0]["event_json"] = CorporateAction.model_validate(payload).model_dump_json()
    report = apply_without_mutation(result, rows, [proof])
    assert report["status"] == "FAIL"
    assert report["resolved_source_text_gap_count"] == 0
    assert report["source_text_resolutions"][0]["status"] == "CANDIDATE_EVENT_TERMS_UNRESOLVED"


@pytest.mark.parametrize(
    "field,value",
    [
        ("security_id", "CN-A:SSE:600099"),
        ("record_date", "2011-01-30"),
        ("ex_date", "2011-02-02"),
        ("source_sha256", "f" * 64),
        ("source_url", "https://example.com/unmatched.pdf"),
    ],
)
def test_proof_must_match_an_existing_finding_identity(correction_case, field, value):
    rows, gaps, proof = correction_case
    result = auditor.source_economic_integrity(rows, gaps)
    proof[field] = value
    before = deepcopy((result, rows, proof))
    with pytest.raises(ValueError, match=r"^CASH_CORRECTION_GAP_IDENTITY_CHANGED$"):
        auditor.apply_cash_corrections(result, rows, [proof])
    assert (result, rows, proof) == before


def test_duplicate_proof_is_rejected_even_if_its_extra_evidence_differs(correction_case):
    rows, gaps, proof = correction_case
    result = auditor.source_economic_integrity(rows, gaps)
    second = {**deepcopy(proof), "additional_evidence": "not a second gap"}
    with pytest.raises(ValueError, match=r"^CASH_CORRECTION_GAP_IDENTITY_CHANGED$"):
        auditor.apply_cash_corrections(result, rows, [proof, second])


def test_known_but_unmatched_gap_is_retained_without_resolution(correction_case):
    _, gaps, proof = correction_case
    result = auditor.source_economic_integrity([], gaps)
    report = apply_without_mutation(result, [], [proof])
    assert report["status"] == report["original_status"] == "NOT_EVIDENCED"
    assert report["resolved_source_text_gap_count"] == report["unresolved_matched_gap_count"] == 0
    assert report["unresolved_source_gap_count"] == 1
    assert report["source_text_resolutions"][0]["status"] == "UNMATCHED_NOT_RESOLVED"
    assert report["source_text_resolutions"][0]["matched_event_checksums"] == []


def two_gap_case(correction_case):
    rows, gaps, proof = deepcopy(correction_case)
    other_rows = deepcopy(rows)
    for row in other_rows:
        replace_event(
            row,
            security_id={"value": "CN-A:SSE:600099"},
            source_document_sha256="c" * 64,
            source_url="https://static.cninfo.com.cn/finalpage/2011-01-28/second-fixture.PDF",
        )
    gaps["records"].extend(known_gap(other_rows)["records"])
    return rows + other_rows, gaps, [proof, proof_for(other_rows)]


def test_empty_proofs_preserve_legacy_report_without_any_new_fields(correction_case):
    rows, gaps, _ = correction_case
    result = auditor.source_economic_integrity(rows, gaps)
    before = deepcopy((result, rows))
    report = auditor.apply_cash_corrections(result, rows, [])
    assert report == result == before[0]
    assert rows == before[1]
    assert "original_status" not in report
    assert "source_text_resolutions" not in report


@pytest.mark.parametrize("proof_count", [1, 2])
def test_only_resolved_gap_is_counted_and_all_known_resolved_is_still_not_admitted(
    correction_case, proof_count
):
    rows, gaps, proofs = two_gap_case(correction_case)
    proofs = proofs[:proof_count]
    result = auditor.source_economic_integrity(rows, gaps)
    report = apply_without_mutation(result, rows, proofs)
    assert report["status"] == ("NOT_EVIDENCED" if proof_count == 2 else "FAIL")
    assert report["resolved_source_text_gap_count"] == proof_count
    assert (
        report["unresolved_source_gap_count"]
        == report["unresolved_matched_gap_count"]
        == 2 - proof_count
    )
    reversed_result = auditor.source_economic_integrity(
        list(reversed(rows)), {**gaps, "records": list(reversed(gaps["records"]))}
    )
    assert report == apply_without_mutation(
        reversed_result, list(reversed(rows)), list(reversed(proofs))
    )


def test_unmatched_remaining_gap_does_not_become_economic_pass(correction_case):
    rows, gaps, proofs = two_gap_case(correction_case)
    rows = rows[:2]
    result = auditor.source_economic_integrity(rows, gaps)
    report = apply_without_mutation(result, rows, proofs)
    assert report["status"] == "NOT_EVIDENCED"
    assert report["resolved_source_text_gap_count"] == report["unresolved_source_gap_count"] == 1
    assert report["unresolved_matched_gap_count"] == 0
    assert {item["status"] for item in report["source_text_resolutions"]} == {
        "CASH_AGGREGATE_TEXT_RESOLVED",
        "UNMATCHED_NOT_RESOLVED",
    }


def test_date_only_normalization_changes_hashes_without_erasing_negative_source_record(
    correction_case,
):
    rows, gaps, proof = correction_case
    gap_before = deepcopy(gaps)
    for row in rows:
        replace_event(row, effective_date="2011-02-02")
    original_checksums = sorted(row["event_checksum"] for row in rows)
    proof["original_event_checksums"] = original_checksums
    original_result = auditor.source_economic_integrity(rows, gaps)
    assert_unresolved(rows, gaps, proof)
    for row in rows:
        replace_event(row, effective_date=proof["ex_date"])
    assert sorted(row["event_checksum"] for row in rows) != original_checksums
    result = auditor.source_economic_integrity(rows, gaps)
    report = apply_without_mutation(result, rows, [proof])
    assert report["status"] == "NOT_EVIDENCED"
    assert report["resolved_source_text_gap_count"] == 1
    assert report["source_text_resolutions"][0]["matched_event_checksums"] == sorted(
        row["event_checksum"] for row in rows
    )
    assert (
        report["findings"][0]["gap"]
        == original_result["findings"][0]["gap"]
        == gap_before["records"][0]
    )
    assert gaps == gap_before
