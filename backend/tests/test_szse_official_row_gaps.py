from scripts.audit_szse_official_row_gaps import classify


def test_unknown_resumption_never_closes_a_gap():
    events = [("2010-01-04", None), ("2011-04-01", "2011-04-19")]
    assert classify("2011-04-06", None, events) == "DATED_SOURCE_HALT_INTERVAL"
    assert classify("2011-04-19", None, events) == "UNKNOWN_RESUMPTION_NOT_CLOSED"
    assert classify("2011-04-19", "2011-04-19", events) == "MASTER_DELISTING_BOUNDARY_NO_ROW"
    assert classify("2009-12-31", None, events) == "NO_MATCHING_HALT_SOURCE"


def test_slash_dated_resumption_does_not_leak_forward():
    events = [("2011/04/12 09:30", "2011/04/13 09:30")]
    assert classify("2011-04-12", None, events) == "DATED_SOURCE_HALT_INTERVAL"
    assert classify("2011-04-13", None, events) == "NO_MATCHING_HALT_SOURCE"
    assert classify("2011-07-25", None, events) == "NO_MATCHING_HALT_SOURCE"
