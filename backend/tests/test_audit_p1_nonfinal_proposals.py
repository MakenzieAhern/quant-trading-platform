"""Proposal-only notices must never substitute for final cash facts."""

from scripts.audit_p1_nonfinal_proposals import classify


def test_only_undated_nonfinal_proposal_is_out_of_scope():
    requirement = {
        "document_id": "a",
        "affected_events": ["CNINFO:1"],
        "issuer": "000001",
        "title": "关于收到董事长提议实施中期分红的公告",
        "url": "official-url",
    }
    triage = {
        "document_id": "a",
        "candidate_class": "NEITHER",
        "record_dates": [],
        "ex_dates": [],
        "preferred_instrument_marker": False,
        "source_sha256": "sha",
        "text_cache_sha256": "cache",
    }
    assert len(classify([requirement], [triage], set())) == 1
    assert classify([requirement], [dict(triage, record_dates=["2025-01-01"])], set()) == []
    assert classify([requirement], [dict(triage, candidate_class="CASH_ONLY")], set()) == []
    assert classify([requirement], [triage], {"a"}) == []
