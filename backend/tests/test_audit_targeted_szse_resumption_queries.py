from scripts.audit_targeted_szse_resumption_queries import contiguous


def test_query_closure_requires_no_gap_or_overlap():
    expected = {"start": "2014-03-21", "end": "2014-04-03"}
    first = {"start": "2014-03-21", "end": "2014-03-27"}
    second = {"start": "2014-03-28", "end": "2014-04-03"}
    assert contiguous(expected, [second, first])
    assert not contiguous(expected, [first])
    assert not contiguous(expected, [first, {**second, "start": "2014-03-27"}])
