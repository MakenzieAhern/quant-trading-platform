from scripts.audit_p1_bonus_source_facts import corroborate


def test_bonus_corroboration_requires_exact_dated_official_ratio_and_identity():
    triage = [
        {
            "document_id": "a",
            "url": "official",
            "source_sha256": "pdf",
            "text_cache_sha256": "text",
            "bonus_candidate_per_share": "0.30",
            "record_dates": ["2023-07-14"],
            "ex_dates": ["2023-07-17"],
            "preferred_instrument_marker": False,
            "candidate_class": "BONUS_ONLY",
        }
    ]
    requirements = [
        {
            "document_id": "a",
            "issuer": "603033",
            "published_on": "2023-07-10",
            "affected_events": ["CNINFO:a"],
        }
    ]
    oracle = [
        {
            "symbol": "603033",
            "record_date": "2023-07-14",
            "ex_date": "2023-07-17",
            "ratio_consistency": "SINGLE_DISPLAYED_RATIO",
            "evidence_sha256": "exchange",
            "evidence": [{"ratio": "0.3"}],
        }
    ]
    master = [
        {
            "symbol": "603033",
            "instrument_type": "COMMON_A_SHARE",
            "security_id": "CN-A:SSE:603033",
            "effective_from": "2015-01-01",
            "effective_to": None,
            "listing_date": "2015-01-01",
            "delisting_date": None,
        }
    ]
    assert (
        corroborate(triage, requirements, oracle, master)[0]["exchange_evidence_sha256"]
        == "exchange"
    )
    assert (
        corroborate(triage, requirements, [{**oracle[0], "evidence": [{"ratio": "0.4"}]}], master)
        == []
    )
    assert (
        corroborate(triage, requirements, oracle, [{**master[0], "instrument_type": "B_SHARE"}])
        == []
    )
    assert (
        corroborate(triage, [{**requirements[0], "published_on": "2023-07-17"}], oracle, master)
        == []
    )
    assert corroborate(triage, requirements, oracle, master) == corroborate(
        triage[::-1], requirements[::-1], oracle[::-1], master[::-1]
    )
