"""All accounting kinds bind their serialized record to the event authority."""

from datetime import timedelta

import pytest

from app.data.full_dataset import FullDataset, pa, pq
from tests.test_consolidation_accounting import event as consolidation
from tests.test_demerger_accounting import event as demerger
from tests.test_demerger_accounting import retained_parent_event
from tests.test_distribution_reference_basis import reference_fixture, write_actions
from tests.test_merger_accounting import event as merger
from tests.test_partial_share_surrender import approved_convention as surrender
from tests.test_pass_through_accounting import event as pass_through
from tests.test_rights_issue_policy import rights

FACTORIES = {
    "RIGHTS_ISSUE": rights,
    "MERGER": merger,
    "DEMERGER": demerger,
    "PARTIAL_SURRENDER": surrender,
    "BONUS_PASS_THROUGH": pass_through,
    "SHARE_CONSOLIDATION": consolidation,
}
KINDS = ("CORPORATE_ACTION", *FACTORIES)


def record_fixture(tmp_path, kind):
    event = reference_fixture(tmp_path)[1] if kind == "CORPORATE_ACTION" else FACTORIES[kind]()
    day = getattr(event, "application_date", event.effective_date)
    assert day is not None
    row = dict(
        application_date=day.isoformat(),
        event_kind=kind,
        event_json=event.model_dump_json(),
        event_checksum=event.event_checksum,
    )
    loader = object.__new__(FullDataset)
    loader.root = tmp_path
    return loader, event, day, row


@pytest.mark.parametrize("kind", KINDS)
def test_accounting_record_retains_event_and_point_in_time_boundary(tmp_path, kind):
    loader, event, day, row = record_fixture(tmp_path, kind)
    pq.write_table(pa.Table.from_pylist([row]), tmp_path / "corporate-actions.parquet")
    assert loader._actions(day.isoformat())[day.isoformat()][kind] == [event]
    assert not loader._actions((day - timedelta(days=1)).isoformat())


@pytest.mark.parametrize("kind", KINDS)
@pytest.mark.parametrize("corruption", ("early", "hidden_late", "checksum", "missing_checksum"))
def test_accounting_record_corruption_fails_before_period_filter(tmp_path, kind, corruption):
    loader, _, day, row = record_fixture(tmp_path, kind)
    if corruption in ("early", "hidden_late"):
        row["application_date"] = (
            day + timedelta(days=1 if corruption == "hidden_late" else -1)
        ).isoformat()
    elif corruption == "checksum":
        row["event_checksum"] = "0" * 64
    else:
        del row["event_checksum"]
    pq.write_table(pa.Table.from_pylist([row]), tmp_path / "corporate-actions.parquet")
    with pytest.raises(ValueError, match="CORPORATE_ACTION_RECORD_MISMATCH"):
        loader._actions(day.isoformat())


def test_demerger_uses_approved_research_boundary_not_legal_date(tmp_path):
    event = retained_parent_event()
    assert event.application_date != event.effective_date
    loader = object.__new__(FullDataset)
    loader.root = tmp_path
    row = dict(
        application_date=event.application_date.isoformat(),
        event_kind="DEMERGER",
        event_json=event.model_dump_json(),
        event_checksum=event.event_checksum,
    )
    path = tmp_path / "corporate-actions.parquet"
    pq.write_table(pa.Table.from_pylist([row]), path)
    assert not loader._actions(event.effective_date.isoformat())
    assert loader._actions(event.application_date.isoformat())[row["application_date"]][
        "DEMERGER"
    ] == [event]
    row["application_date"] = event.effective_date.isoformat()
    pq.write_table(pa.Table.from_pylist([row]), path)
    with pytest.raises(ValueError, match="CORPORATE_ACTION_RECORD_MISMATCH"):
        loader._actions(event.application_date.isoformat())


def test_reference_record_cannot_hide_a_due_event_after_cutoff(tmp_path):
    loader, cash, bonus, payload = reference_fixture(tmp_path)
    write_actions(loader, cash, bonus, payload)
    path = tmp_path / "corporate-actions.parquet"
    rows = pq.read_table(path).to_pylist()
    for row in rows:
        if row["event_kind"] == "ORDINARY_REFERENCE":
            row["application_date"] = "2011-02-02"
    pq.write_table(pa.Table.from_pylist(rows), path)
    with pytest.raises(ValueError, match="ORDINARY_REFERENCE_RECORD_MISMATCH"):
        loader._actions("2011-02-01")
