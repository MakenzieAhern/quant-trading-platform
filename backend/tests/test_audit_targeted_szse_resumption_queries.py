from scripts.audit_targeted_szse_resumption_queries import contiguous, expected_query_windows


def test_query_closure_requires_no_gap_or_overlap():
    expected = {"start": "2014-03-21", "end": "2014-04-03"}
    first = {"start": "2014-03-21", "end": "2014-03-27"}
    second = {"start": "2014-03-28", "end": "2014-04-03"}
    assert contiguous(expected, [second, first])
    assert not contiguous(expected, [first])
    assert not contiguous(expected, [first, {**second, "start": "2014-03-27"}])


def test_offset_query_scope_excludes_intervals_closed_before_offset():
    unresolved = [
        {"security_id": "a", "symbol": "000001", "suspended_at": "2014/03/01 09:30"},
        {"security_id": "b", "symbol": "000002", "suspended_at": "2014/03/01 09:30"},
    ]
    suspensions = [
        {"symbol": "000001", "suspended_at": "2014/03/01 09:30"},
        {"symbol": "000001", "suspended_at": "2014/03/10 09:30"},
        {"symbol": "000002", "suspended_at": "2014/03/01 09:30"},
    ]
    windows = expected_query_windows(unresolved, suspensions, 30, 14)
    assert list(windows) == [("b", "2014/03/01 09:30")]
    assert (
        windows[("b", "2014/03/01 09:30")]["start"],
        windows[("b", "2014/03/01 09:30")]["end"],
    ) == (
        "2014-03-15",
        "2014-04-13",
    )
