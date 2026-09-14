from scripts.probe_full_sse_chain import diagnose


def test_missing_transition_and_conflicting_dates_cannot_be_silently_normal():
    exit_event = dict(
        effective_from="2012-01-05", old_status="ST", status="NORMAL", cninfo_document_id="1"
    )
    result = diagnose([exit_event, exit_event], "NORMAL", "2009-12-31")
    assert len(result["gaps"]) == 1 and len(result["trace"]) == 1
    assert result["gaps"][0]["required_old_state"] == "ST"
    entry = dict(
        effective_from="2011-01-05", old_status="NORMAL", status="ST", cninfo_document_id="2"
    )
    assert not diagnose([exit_event, entry], "NORMAL", "2009-12-31")["gaps"]
    conflict = dict(exit_event, status="STAR_ST", cninfo_document_id="3")
    result = diagnose([exit_event, conflict], "ST", "2009-12-31")
    assert len(result["conflicts"]) == 1 and not result["trace"]
    assert result == diagnose([conflict, exit_event], "ST", "2009-12-31")
