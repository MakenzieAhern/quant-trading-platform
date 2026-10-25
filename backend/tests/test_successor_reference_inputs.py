"""Price-only inputs must survive the real builder without becoming entitlements."""

import json
from pathlib import Path

import pyarrow.parquet as pq
import pytest

from app.data.catalog.checksums import sha256_file
from app.data.full_dataset import parse_action_records
from app.domain.markets.corporate_actions import OrdinaryDistributionReference
from scripts.full_dataset_build_inputs import CandidateBuildInputs
from tests.test_distribution_reference_basis import reference_fixture
from tests.test_full_dataset_build_inputs import build, candidate_inputs
from tests.test_full_dataset_sources import _manifest


def update_spec(repository, path, spec):
    for row in spec["source_contracts"]:
        if row["name"] in {"CASH_ACTIONS", "BONUS_ACTIONS"}:
            source = Path(row["source_path"])
            row.update(
                source_file_sha256=sha256_file(source),
                source_manifest_sha256=json.loads(source.read_bytes())["manifest_sha256"],
            )
    preflight_row = next(
        row for row in spec["source_contracts"] if row["name"] == "SOURCE_PREFLIGHT"
    )
    preflight_path = Path(preflight_row["source_path"])
    preflight = json.loads(preflight_path.read_bytes())
    preflight.pop("manifest_sha256")
    preflight["input_selection_sha256"] = CandidateBuildInputs.model_validate(
        spec
    ).input_selection_sha256(repository)
    preflight = _manifest(preflight_path, preflight)
    preflight_row.update(
        source_manifest_sha256=preflight["manifest_sha256"],
        source_file_sha256=sha256_file(preflight_path),
    )
    spec["reference_pins"].update(
        full_source_preflight_manifest_sha256=preflight["manifest_sha256"],
        full_source_preflight_file_sha256=sha256_file(preflight_path),
    )
    path.write_text(json.dumps(spec))


def reference_inputs(tmp_path):
    repository, path, spec = candidate_inputs(tmp_path)
    fixture_root = tmp_path / "price-fixture"
    fixture_root.mkdir()
    _, cash, bonus, payload = reference_fixture(fixture_root)
    for name, event in (("CASH_ACTIONS", cash), ("BONUS_ACTIONS", bonus)):
        row = next(row for row in spec["source_contracts"] if row["name"] == name)
        _manifest(
            Path(row["source_path"]),
            {
                "events": [
                    {
                        "event": event.model_dump(mode="json"),
                        "event_checksum": event.event_checksum,
                        "status": "SYNTHETIC_TEST_ONLY",
                    }
                ]
            },
        )
    reference = OrdinaryDistributionReference.model_validate(payload)
    report_path = tmp_path / "reference-report.json"
    _manifest(
        report_path,
        {
            "private_candidate_reference_rows": [
                {
                    "event_kind": "ORDINARY_REFERENCE",
                    "event_json": reference.model_dump_json(),
                    "event_checksum": reference.event_checksum,
                    "application_date": reference.ex_date.isoformat(),
                }
            ],
            "financial_admission": False,
        },
    )
    spec["auxiliary_inputs"]["ordinary_references"] = {
        "path": str(report_path),
        "sha256": sha256_file(report_path),
    }
    update_spec(repository, path, spec)
    return repository, path, spec, cash, bonus, reference


def test_successor_preserves_price_reference_and_holder_entitlements(tmp_path):
    repository, path, spec, cash, bonus, reference = reference_inputs(tmp_path)
    report = build(repository, path)
    assert build(repository, path) == report
    rows = pq.read_table(Path(spec["final_root"]) / "corporate-actions.parquet").to_pylist()
    scoped = [
        row for row in rows if row["event_kind"] in {"CORPORATE_ACTION", "ORDINARY_REFERENCE"}
    ]
    parsed = parse_action_records(scoped, "2025-12-31")["2011-02-01"]
    assert {event.event_checksum for event in parsed["CORPORATE_ACTION"]} == {
        cash.event_checksum,
        bonus.event_checksum,
    }
    assert parsed["ORDINARY_REFERENCE"] == [reference]
    assert report["ordinary_reference_rows"] == 1
    assert report["accounting_action_rows"] == 26
    assert report["corporate_action_rows"] == 27 and not report["full_financial_admission"]


@pytest.mark.parametrize(
    "change", ["checksum", "date", "cash_pair", "source", "duplicate", "kind", "manifest"]
)
def test_successor_rejects_invalid_price_reference_before_publication(tmp_path, change):
    repository, path, spec, _, _, _ = reference_inputs(tmp_path)
    pin = spec["auxiliary_inputs"]["ordinary_references"]
    report_path = Path(pin["path"])
    report = json.loads(report_path.read_bytes())
    report.pop("manifest_sha256")
    row = report["private_candidate_reference_rows"][0]
    if change == "checksum":
        row["event_checksum"] = "0" * 64
    elif change == "date":
        row["application_date"] = "2011-02-02"
    elif change in {"cash_pair", "source"}:
        event = json.loads(row["event_json"])
        event["cash_event_checksum" if change == "cash_pair" else "source_document_sha256"] = (
            "0" * 64
        )
        changed = OrdinaryDistributionReference.model_validate(event)
        row.update(event_json=changed.model_dump_json(), event_checksum=changed.event_checksum)
    elif change == "duplicate":
        report["private_candidate_reference_rows"].append(dict(row))
    elif change == "kind":
        row["event_kind"] = "CORPORATE_ACTION"
    changed_report = _manifest(report_path, report)
    if change == "manifest":
        changed_report["manifest_sha256"] = "0" * 64
        report_path.write_text(json.dumps(changed_report))
    pin["sha256"] = sha256_file(report_path)
    update_spec(repository, path, spec)
    with pytest.raises(ValueError, match="ORDINARY_REFERENCE"):
        build(repository, path)
    assert not Path(spec["final_root"]).exists()


def test_reference_selection_cannot_be_removed_under_unchanged_preflight(tmp_path):
    repository, path, spec, _, _, _ = reference_inputs(tmp_path)
    del spec["auxiliary_inputs"]["ordinary_references"]
    path.write_text(json.dumps(spec))
    with pytest.raises(ValueError, match="CANDIDATE_PREFLIGHT_INPUT_SELECTION_MISMATCH"):
        build(repository, path)
    assert not Path(spec["work_root"]).exists()
