"""Negative source evidence must cover base events too, never grant admission."""

import json
from copy import deepcopy
from pathlib import Path

import pyarrow.parquet as pq
import pytest

from app.data.catalog.checksums import sha256_file
from scripts import audit_full_dataset as auditor
from tests.test_successor_dataset_audit import audit_inputs, run_audit


def known_gap(rows):
    event = json.loads(next(r for r in rows if r["event_kind"] == "CORPORATE_ACTION")["event_json"])
    return {
        "scope": "KNOWN_EVENT_SOURCE_CONTRADICTIONS_NOT_WHOLE_SECURITY_EXCLUSIONS",
        "financial_admission": False,
        "records": [
            {
                "security_id": event["security_id"]["value"],
                "record_date": event["record_date"],
                "ex_date": event["ex_date"],
                "source_sha256": event["source_document_sha256"],
                "source_url": event["source_url"],
                "status": "BLOCKED_SOURCE_AGGREGATE_CONTRADICTION",
                "evidence": "Synthetic conflicting issuer totals; not real source evidence.",
                "blocks_new_economic_candidate": True,
                "reference_price_match_resolves_issue": False,
            }
        ],
    }


def audit_with_gap(repository, path, spec, output, gaps, digest):
    return auditor.audit(
        Path(spec["final_root"]),
        repository,
        output,
        build_spec=path,
        build_spec_sha256=sha256_file(path),
        known_source_gaps=gaps,
        known_source_gaps_sha256=digest,
    )


def test_whole_candidate_source_contradiction_cannot_hide_behind_reference_pass(tmp_path):
    repository, path, spec = audit_inputs(tmp_path)
    rows = pq.read_table(Path(spec["final_root"]) / "corporate-actions.parquet").to_pylist()
    gaps = tmp_path / "known-gaps.json"
    payload = known_gap(rows)
    gaps.write_text(json.dumps(payload))
    before = {str(p): sha256_file(p) for p in tmp_path.rglob("*") if p.is_file()}
    report = audit_with_gap(
        repository, path, spec, tmp_path / "audit.json", gaps, sha256_file(gaps)
    )
    assert report == audit_with_gap(
        repository, path, spec, tmp_path / "audit.json", gaps, sha256_file(gaps)
    )
    assert report["gates"]["REFERENCE_PRICE_CONTINUITY"] == "PASS"
    assert report["gates"]["SOURCE_EVENT_SET_MATCH"] == "PASS"
    assert report["gates"]["SOURCE_ECONOMIC_INTEGRITY"] == "FAIL"
    check = report["source_economic_integrity"]
    assert check["known_source_gaps_sha256"] == sha256_file(gaps)
    assert check["ordinary_event_rows_checked"] == 2
    assert check["matched_event_count"] == 2
    assert check["findings"][0]["gap"] == payload["records"][0]
    assert {e["classification"] for e in check["findings"][0]["events"]} == {
        "KNOWN_SOURCE_CONTRADICTION"
    }
    assert not report["dataset_audited"] and report["audit_status"] == "FAIL_CLOSED"
    assert report["gates"]["CASH_RECONCILIATION"] == "NOT_EVIDENCED"
    assert all(sha256_file(Path(p)) == digest for p, digest in before.items())


def test_missing_negative_inventory_cannot_mean_economic_pass(tmp_path):
    repository, path, spec = audit_inputs(tmp_path)
    report = run_audit(repository, path, spec, tmp_path / "audit.json")
    assert report["gates"]["SOURCE_ECONOMIC_INTEGRITY"] == "NOT_EVIDENCED"
    assert "SOURCE_ECONOMIC_INTEGRITY" in report["unevidenced_gates"]


@pytest.mark.parametrize(
    "changed", ["record_date", "ex_date", "security_id", "source_document_sha256"]
)
def test_related_identity_changes_remain_unresolved_not_silently_dropped(tmp_path, changed):
    _, _, spec = audit_inputs(tmp_path)
    rows = pq.read_table(Path(spec["final_root"]) / "corporate-actions.parquet").to_pylist()
    gaps = known_gap(rows)
    changed_rows = deepcopy(rows)
    from app.domain.markets.corporate_actions import CorporateAction

    for row in changed_rows:
        if row["event_kind"] != "CORPORATE_ACTION":
            continue
        payload = json.loads(row["event_json"])
        payload[changed] = {
            "record_date": None,
            "ex_date": "2011-02-02",
            "security_id": {"value": "CN-A:SZSE:000002"},
            "source_document_sha256": "0" * 64,
        }[changed]
        event = CorporateAction.model_validate(payload)
        row.update(
            event_json=event.model_dump_json(),
            event_checksum=event.event_checksum,
            security_id=str(event.security_id),
            application_date=event.ex_date.isoformat(),
        )
    report = auditor.source_economic_integrity(changed_rows, gaps)
    assert report["matched_event_count"] == 2
    assert {e["classification"] for e in report["findings"][0]["events"]} == {
        "EVENT_SOURCE_IDENTITY_UNRESOLVED"
    }


def test_unmatched_gap_is_retained_and_order_does_not_change_result(tmp_path):
    _, _, spec = audit_inputs(tmp_path)
    rows = pq.read_table(Path(spec["final_root"]) / "corporate-actions.parquet").to_pylist()
    gaps = known_gap(rows)
    gap = gaps["records"][0]
    gap.update(
        security_id="CN-A:SZSE:000099",
        record_date="2012-01-01",
        ex_date="2012-01-02",
        source_sha256="f" * 64,
        source_url="https://example.com/unrelated.pdf",
    )
    report = auditor.source_economic_integrity(rows, gaps)
    assert report == auditor.source_economic_integrity(list(reversed(rows)), gaps)
    assert report["status"] == "NOT_EVIDENCED" and report["unmatched_gap_count"] == 1
    assert report["findings"] == [{"gap": gap, "events": [], "status": "UNMATCHED_NOT_RESOLVED"}]


@pytest.mark.parametrize("bad", [None, [], {}, "records", "duplicate", "flags", "date", "sha"])
def test_invalid_gap_inventory_is_rejected_without_report(tmp_path, bad):
    repository, path, spec = audit_inputs(tmp_path)
    rows = pq.read_table(Path(spec["final_root"]) / "corporate-actions.parquet").to_pylist()
    payload = known_gap(rows)
    if bad in ("records", "duplicate", "flags", "date", "sha"):
        if bad == "records":
            payload["records"] = []
        elif bad == "duplicate":
            payload["records"] *= 2
        elif bad == "flags":
            payload["records"][0]["blocks_new_economic_candidate"] = "true"
        elif bad == "date":
            payload["records"][0]["ex_date"] = "2026-02-30"
        else:
            payload["records"][0]["source_sha256"] = "not-a-digest"
    else:
        payload = bad
    gaps = tmp_path / "gaps.json"
    gaps.write_text(json.dumps(payload))
    output = tmp_path / "audit.json"
    with pytest.raises(ValueError, match="KNOWN_SOURCE_GAP"):
        audit_with_gap(repository, path, spec, output, gaps, sha256_file(gaps))
    assert not output.exists()


@pytest.mark.parametrize("target", ["direct", "symlink", "hardlink"])
def test_audit_output_cannot_replace_gap_input(tmp_path, target):
    repository, path, spec = audit_inputs(tmp_path)
    rows = pq.read_table(Path(spec["final_root"]) / "corporate-actions.parquet").to_pylist()
    gaps = tmp_path / "gaps.json"
    gaps.write_text(json.dumps(known_gap(rows)))
    digest = sha256_file(gaps)
    output = gaps if target == "direct" else tmp_path / "alias.json"
    if target == "symlink":
        output.symlink_to(gaps)
    elif target == "hardlink":
        output.hardlink_to(gaps)
    with pytest.raises(ValueError, match="AUDIT_OUTPUT_NOT_ISOLATED"):
        audit_with_gap(repository, path, spec, output, gaps, digest)
    assert sha256_file(gaps) == digest


def test_gap_pin_and_publication_recheck_fail_closed(tmp_path, monkeypatch):
    repository, path, spec = audit_inputs(tmp_path)
    rows = pq.read_table(Path(spec["final_root"]) / "corporate-actions.parquet").to_pylist()
    gaps = tmp_path / "gaps.json"
    gaps.write_text(json.dumps(known_gap(rows)))
    digest = sha256_file(gaps)
    output = tmp_path / "audit.json"
    with pytest.raises(ValueError, match="PARTITION_CONSUMED_BYTES_CHANGED"):
        audit_with_gap(repository, path, spec, output, gaps, "0" * 64)
    original = auditor.source_economic_integrity

    def mutate(actions, payload):
        result = original(actions, payload)
        if actions:
            gaps.write_bytes(gaps.read_bytes() + b" ")
        return result

    monkeypatch.setattr(auditor, "source_economic_integrity", mutate)
    with pytest.raises(ValueError, match="KNOWN_SOURCE_GAPS_CHANGED_DURING_AUDIT"):
        audit_with_gap(repository, path, spec, output, gaps, digest)
    assert not output.exists()


@pytest.mark.parametrize(
    "kwargs",
    [
        {"known_source_gaps": Path("missing")},
        {"known_source_gaps_sha256": "0" * 64},
        {"known_source_gaps": Path("missing"), "known_source_gaps_sha256": "0" * 64},
    ],
)
def test_gap_arguments_require_candidate_and_matching_pair_before_legacy_io(tmp_path, kwargs):
    with pytest.raises(ValueError, match="KNOWN_SOURCE_GAPS_REQUIRE_CANDIDATE"):
        auditor.audit(tmp_path / "missing", tmp_path, tmp_path / "audit.json", **kwargs)
    assert not (tmp_path / "audit.json").exists()


def test_transient_gap_alias_cannot_change_reported_consumed_path(tmp_path, monkeypatch):
    repository, path, spec = audit_inputs(tmp_path)
    rows = pq.read_table(Path(spec["final_root"]) / "corporate-actions.parquet").to_pylist()
    original = tmp_path / "original-gap.json"
    original.write_text(json.dumps(known_gap(rows)))
    unrelated = tmp_path / "unrelated.json"
    unrelated.write_text("{}")
    alias = tmp_path / "alias.json"
    alias.symlink_to(original)
    check = auditor.source_economic_integrity
    publication = auditor.candidate_publication
    calls = 0

    def switch_alias(actions, payload):
        result = check(actions, payload)
        if actions:
            alias.unlink()
            alias.symlink_to(unrelated)
        return result

    def restore_alias(*args, **kwargs):
        nonlocal calls
        calls += 1
        if calls == 2:
            alias.unlink()
            alias.symlink_to(original)
        return publication(*args, **kwargs)

    monkeypatch.setattr(auditor, "source_economic_integrity", switch_alias)
    monkeypatch.setattr(auditor, "candidate_publication", restore_alias)
    report = audit_with_gap(
        repository, path, spec, tmp_path / "audit.json", alias, sha256_file(original)
    )
    pin = report["source_economic_integrity"]
    assert pin["known_source_gaps_path"] == str(original)
    assert sha256_file(Path(pin["known_source_gaps_path"])) == pin["known_source_gaps_sha256"]


@pytest.mark.parametrize("genuine_rights", [False, True])
def test_scan_uses_typed_economics_not_outer_kind_label(tmp_path, genuine_rights):
    from app.domain.markets.corporate_actions import CorporateAction

    _, _, spec = audit_inputs(tmp_path)
    rows = pq.read_table(Path(spec["final_root"]) / "corporate-actions.parquet").to_pylist()
    gaps = known_gap(rows)
    for row in rows:
        if row["event_kind"] != "CORPORATE_ACTION":
            continue
        row["event_kind"] = "RIGHTS_ISSUE"
        if genuine_rights:
            payload = json.loads(row["event_json"])
            payload["action_type"] = "RIGHTS_RELATED_EVENT"
            event = CorporateAction.model_validate(payload)
            row.update(event_json=event.model_dump_json(), event_checksum=event.event_checksum)
    report = auditor.source_economic_integrity(rows, gaps)
    assert report["ordinary_event_rows_checked"] == (0 if genuine_rights else 2)
    assert report["matched_event_count"] == (0 if genuine_rights else 2)
    assert report["status"] == ("NOT_EVIDENCED" if genuine_rights else "FAIL")
