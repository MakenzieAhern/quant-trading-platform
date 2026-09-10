"""Offline completeness safety checks: evidence replay is not coverage certification."""

import copy

import pytest

from scripts.sse_st_coverage import (
    assert_completeness,
    header_state,
    intervals_for,
    non_primary,
    replay,
    status_on,
)

SECURITY = {
    "security_id": "CN-A:SSE:600001",
    "listing_date": "2022-01-01",
    "delisting_date": "2023-01-05",
}
POINT = {
    "status": "ST",
    "known_on": "2022-12-30",
    "effective_from": "2022-12-30",
}


def test_dated_observation_no_backfill_and_future_input_order():
    assert replay([POINT], "2022-12-29") == "EXCLUDED"
    assert replay([POINT], "2023-01-01") == "ST"
    future = {**POINT, "status": "NORMAL", "known_on": "2023-01-04"}
    assert replay([future, POINT], "2023-01-01") == "ST"
    assert replay([future, POINT], "2023-01-04") == "EXCLUDED"
    assert replay([POINT, future], "2023-01-04") == "EXCLUDED"
    assert replay([], "2023-01-01") == "EXCLUDED"


def test_interval_resolution_requires_certification_and_catches_gaps_overlaps():
    points = [POINT, {**POINT, "status": "NORMAL", "effective_from": "2023-01-04"}]
    rows = intervals_for(SECURITY, points)
    assert rows == intervals_for(SECURITY, list(reversed(points)))
    assert [(r["effective_from"], r["effective_to"]) for r in rows] == [
        ("2023-01-01", "2023-01-03"),
        ("2023-01-04", "2023-01-05"),
    ]
    identity = SECURITY["security_id"]
    assert status_on(rows, identity, "2023-01-03") == "EXCLUDED"
    assert status_on(rows, "missing", "2023-01-03") == "EXCLUDED"
    certified = [{**rows[0], "coverage_certified": True, "status": "ST"}]
    assert status_on(certified, identity, "2023-01-03") == "ST"
    assert status_on(certified * 2, identity, "2023-01-03") == "EXCLUDED"
    certified[0]["status"] = "UNKNOWN"
    assert status_on(certified, identity, "2023-01-03") == "EXCLUDED"
    sessions = ["2023-01-03", "2023-01-04", "2023-01-05", "2023-01-06"]
    metrics = assert_completeness([SECURITY], rows, sessions)
    assert metrics["eligible_security_days"] == metrics["excluded_security_days"] == 3
    assert metrics["excluded_security_day_percentage"] == 100
    for invalid in (rows[:1], rows * 2):
        with pytest.raises(ValueError, match="TIMELINE_GAP_OR_OVERLAP"):
            assert_completeness([SECURITY], invalid, sessions)
    ipo = {**SECURITY, "listing_date": "2023-01-04"}
    assert intervals_for(ipo, points)[0]["effective_from"] == "2023-01-04"
    assert intervals_for({**ipo, "listing_date": "2025-01-01"}, points) == []
    with pytest.raises(ValueError, match="INVALID_PILOT_CALENDAR"):
        assert_completeness([SECURITY], rows, list(reversed(sessions)))


def test_headers_and_nonprimary_purpose_do_not_invent_transitions():
    pages = ["证券代码\uff1a600001 证券简称\uff1aST测试"]
    assert header_state(pages, "600001", "ST测试") == "ST"
    with pytest.raises(ValueError, match="HEADER_SECURITY_MISMATCH"):
        header_state(pages, "600002", "ST测试")
    with pytest.raises(ValueError, match="HEADER_NAME_MISMATCH"):
        header_state(pages, "600001", "测试")
    record = {"sse": {"TITLE": "申请撤销风险警示", "SECURITY_NAME": "ST测试"}}
    assert non_primary(record, pages)[0] == "APPLICATION_ONLY"
    for title, body, expected in (
        ("相关事项进展公告", "", "PROGRESS_NOTICE"),
        ("可能实施风险警示", "", "NON_STATE_RISK_NOTICE"),
        ("继续实施其他风险警示", "继续实施其他风险警示", "STATUS_CONFIRMATION"),
        ("叠加实施其他风险警示", "", "NO_EFFECTIVE_CHANGE"),
        ("被实施退市风险警示", "2020年5月6日及2022年5月6日", "CONFLICTING_EVIDENCE"),
    ):
        item = copy.deepcopy(record)
        item["sse"]["TITLE"] = title
        assert non_primary(item, [*pages, body])[0] == expected
