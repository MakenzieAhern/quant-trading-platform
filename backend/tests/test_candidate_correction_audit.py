"""Audit wiring and publication isolation; PDF verification has separate loader tests."""

import json
from pathlib import Path

import pyarrow.parquet as pq
import pytest

from app.data.catalog.checksums import sha256_file
from scripts import audit_full_dataset as auditor
from tests.test_candidate_source_gaps import audit_with_gap, known_gap
from tests.test_successor_dataset_audit import audit_inputs


def correction_audit(tmp_path, monkeypatch):
    repository, spec_path, spec = audit_inputs(tmp_path)
    rows = pq.read_table(Path(spec["final_root"]) / "corporate-actions.parquet").to_pylist()
    inventory = known_gap(rows)
    gap_path = tmp_path / "gaps.json"
    gap_path.write_text(json.dumps(inventory))
    source = tmp_path / "synthetic-loader-input.json"
    source.write_text('{"test_fixture_only":true}')
    pins = {source.resolve(): sha256_file(source)}
    proof = {
        **{
            key: inventory["records"][0][key]
            for key in ("security_id", "record_date", "ex_date", "source_sha256", "source_url")
        },
        "cash_per_share": "0.2",
        "bonus_share_ratio": "0.5",
        "published_at": "2011-01-28T07:53:00+00:00",
        "scope": "SYNTHETIC_LOADER_STUB_NOT_REAL_SOURCE_EVIDENCE",
    }
    monkeypatch.setattr(auditor, "load_cash_corrections", lambda *args: ([proof], pins))

    def run(output):
        return audit_with_gap(repository, spec_path, spec, output, gap_path, sha256_file(gap_path))

    return run, source, inventory


def test_candidate_audit_consumes_verified_correction_without_approving_financial_gates(
    tmp_path, monkeypatch
):
    run, source, inventory = correction_audit(tmp_path, monkeypatch)
    report = run(tmp_path / "audit.json")
    check = report["source_economic_integrity"]
    assert check["resolved_source_text_gap_count"] == 1
    assert check["unresolved_source_gap_count"] == 0
    assert check["original_status"] == "FAIL"
    assert check["status"] == "NOT_EVIDENCED"
    assert check["findings"][0]["gap"] == inventory["records"][0]
    assert check["findings"][0]["status"] == "MATCHED_NEGATIVE_EVIDENCE"
    assert len(check["findings"][0]["events"]) == 2
    assert check["correction_input_sha256"] == {str(source.resolve()): sha256_file(source)}
    code_names = {Path(path).name for path in report["audit_code_sha256"]}
    assert {
        "candidate_cash_corrections.py",
        "audit_p1_cash_corrections.py",
        "retained_bonus_terms.py",
    } <= code_names
    assert report["gates"]["SOURCE_ECONOMIC_INTEGRITY"] == "NOT_EVIDENCED"
    for gate in ("LOOK_AHEAD", "CORPORATE_ACTION_COMPLETENESS", "CASH_RECONCILIATION"):
        assert report["gates"][gate] == "NOT_EVIDENCED"
    assert not report["dataset_audited"]
    assert not report["full_financial_admission"]
    assert not report["strategy_run"]
    assert report == run(tmp_path / "audit.json")


@pytest.mark.parametrize("alias", ["direct", "symlink", "hardlink"])
def test_correction_inputs_are_protected_from_audit_output(tmp_path, monkeypatch, alias):
    run, source, _ = correction_audit(tmp_path, monkeypatch)
    before = source.read_bytes()
    output = source if alias == "direct" else tmp_path / "output.json"
    if alias == "symlink":
        output.symlink_to(source)
    elif alias == "hardlink":
        output.hardlink_to(source)
    with pytest.raises(ValueError, match="AUDIT_OUTPUT_NOT_ISOLATED"):
        run(output)
    assert source.read_bytes() == before


def test_correction_dependency_is_rechecked_before_report_publication(tmp_path, monkeypatch):
    run, source, _ = correction_audit(tmp_path, monkeypatch)
    original = auditor.apply_cash_corrections

    def replace_after_consumption(*args):
        result = original(*args)
        source.write_text("changed after verified consumption")
        return result

    monkeypatch.setattr(auditor, "apply_cash_corrections", replace_after_consumption)
    output = tmp_path / "audit.json"
    with pytest.raises(ValueError, match="CASH_CORRECTION_INPUT_CHANGED_DURING_AUDIT"):
        run(output)
    assert not output.exists()


def test_correction_parser_code_is_pinned_before_loading_evidence(tmp_path, monkeypatch):
    run, _, _ = correction_audit(tmp_path, monkeypatch)
    load = auditor.load_cash_corrections
    real_sha = auditor.sha256_file
    loaded = False

    def mark_loaded(*args):
        nonlocal loaded
        loaded = True
        return load(*args)

    def observed_sha(path):
        if loaded and path.name == "candidate_cash_corrections.py":
            return "0" * 64
        return real_sha(path)

    monkeypatch.setattr(auditor, "load_cash_corrections", mark_loaded)
    monkeypatch.setattr(auditor, "sha256_file", observed_sha)
    output = tmp_path / "audit.json"
    with pytest.raises(ValueError, match="CANDIDATE_AUDIT_INPUT_CHANGED"):
        run(output)
    assert not output.exists()
