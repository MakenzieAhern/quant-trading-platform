import json

import pytest

from scripts.szse_st_recovery import audit, normalize, risk_state, status_on


def test_dated_changes_ignore_current_name_and_preserve_delisting_period():
    rows = [
        ("2023-01-03", "000001", "TODAY", "普通名", "ST旧名"),
        ("2023-02-01", "000001", "TODAY", "ST旧名", "*ST旧名"),
        ("2023-03-01", "000001", "TODAY", "*ST旧名", "旧名退"),
    ]
    events = normalize(rows, {"000001"})
    assert events == normalize(rows[::-1], {"000001"}) == normalize(rows + rows, {"000001"})
    assert normalize([("2023-01-03", "200001", "B股", "旧名", "新名")], {"000001"}) == []
    assert events[-1]["status"] == "DELISTING_PERIOD"
    anchor = dict(status="NORMAL", effective_from="2022-12-31")
    assert status_on(anchor, events, "2022-12-30") == "UNKNOWN"
    assert status_on(anchor, events, "2023-01-02") == "NORMAL"
    assert status_on(anchor, events, "2023-01-03") == "ST"
    assert status_on(anchor, events, "2023-02-01") == "STAR_ST"
    assert status_on(anchor, events[::-1], "2023-03-01") == "DELISTING_PERIOD"
    assert status_on(anchor, events[1:], "2023-02-01") == "UNKNOWN"
    assert status_on(dict(anchor, effective_from="2023-01-03"), events, "2023-01-03") == "UNKNOWN"
    removal = normalize([("2023-04-01", "000001", "IGNORED", "*ST旧名", "普通名")], {"000001"})
    assert status_on(anchor, events[:2] + removal, "2023-04-01") == "NORMAL"
    assert risk_state("*ST 旧名") == "STAR_ST"
    assert risk_state("PT旧名") == "UNKNOWN"


def test_invalid_dates_conflicts_and_missing_rows_fail_closed():
    row = ("2023-01-03", "000001", "TODAY", "普通名", "ST旧名")
    for invalid in [
        row[:4],
        ("2023-02-30", *row[1:]),
        ("20230103", *row[1:]),
        (row[0], "1", *row[2:]),
        (*row[:4], ""),
    ]:
        with pytest.raises(ValueError):
            normalize([invalid], {"000001"})
    with pytest.raises(ValueError, match="CONFLICTING"):
        normalize([row, (*row[:4], "*ST旧名")], {"000001"})


def test_changed_source_is_rejected_before_parsing(tmp_path):
    source = tmp_path / "source.xlsx"
    source.write_bytes(b"changed source")
    source.with_suffix(".xlsx.meta.json").write_text(json.dumps({"sha256": "0" * 64}))
    with pytest.raises(ValueError, match="SOURCE_CHECKSUM_MISMATCH"):
        audit(source, tmp_path, tmp_path / "calendar.json", tmp_path / "output")
