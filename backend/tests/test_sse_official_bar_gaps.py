from scripts.audit_sse_official_bar_gaps import classify


def test_gap_classification_boundaries():
    intervals = [("2013-02-01", "2013-02-05")]
    assert classify("600705", "2012-08-29", intervals) == "OFFICIAL_LISTING_SUSPENSION"
    assert classify("600705", "2012-08-30", intervals) == "UNRESOLVED"
    assert classify("600705", "2013-02-04", intervals) == "SSE_OPEN_BLOCKED_SOURCE_INTERVAL"
    assert classify("600053", "2012-08-29", intervals) == "UNRESOLVED"
    assert classify("600053", "2010-09-21", intervals) == "OFFICIAL_ISSUER_HALT"
    assert classify("600053", "2011-04-18", intervals) == "OFFICIAL_ISSUER_HALT"
    assert classify("600240", "2015-07-03", intervals) == "OFFICIAL_ISSUER_HALT"
    assert classify("601360", "2018-02-27", intervals) == "OFFICIAL_ISSUER_HALT"
    assert classify("601360", "2018-02-28", intervals) == "UNRESOLVED"
    assert (
        classify("600705", "2025-05-27", intervals, "2025-05-27")
        == "MASTER_DELISTING_BOUNDARY_NO_BAR"
    )
