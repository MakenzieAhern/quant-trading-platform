from scripts.index_szse_resumption_scan_gaps import select_candidates


def test_scan_candidates_are_bounded_deduplicated_and_order_independent():
    intervals = {
        "000001": [
            {
                "start": "2011-01-04",
                "end": "2011-02-01",
                "fact": {"security_id": "CN-A:SZSE:000001", "suspended_at": "2011/01/04 09:30"},
            }
        ]
    }
    valid = {
        "issuer": "000001",
        "published_on": "2011-01-04",
        "text_characters": 0,
        "source_sha256": "a" * 64,
        "source_manifest": "a",
    }
    rows = [
        valid,
        {**valid, "source_manifest": "b"},
        {**valid, "published_on": "2011-01-03"},
        {**valid, "published_on": "2011-02-01"},
        {**valid, "issuer": "000002"},
        {**valid, "text_characters": 60},
    ]
    selected = select_candidates(rows, intervals)
    assert len(selected) == 1
    assert selected[0]["source_manifest"] == "a"
    assert selected[0]["affected_suspensions"] == [["CN-A:SZSE:000001", "2011/01/04 09:30"]]
    assert selected == select_candidates(list(reversed(rows)), intervals)
