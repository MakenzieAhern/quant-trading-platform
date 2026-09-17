from scripts.audit_p1_derivative_notices import classify


def test_derivative_requires_unique_existing_exact_issuer_cash():
    requirement = {
        "document_id": "a",
        "affected_events": ["CNINFO:a"],
        "issuer": "000001",
        "title": "关于停止转股的提示性公告",
        "published_on": "2024-06-01",
    }
    triage = {
        "document_id": "a",
        "candidate_class": "CASH_ONLY",
        "cash_candidate_per_share": "0.1",
        "record_dates": [],
        "ex_dates": [],
        "preferred_instrument_marker": False,
        "url": "derivative",
        "source_sha256": "sha",
        "text_cache_sha256": "cache",
    }
    accepted = {
        "event_checksum": "event",
        "event": {
            "security_id": {"value": "CN-A:SZSE:000001"},
            "ex_date": "2024-06-05",
            "cash_per_share": "0.100",
            "source_provider": "OFFICIAL_ISSUER_CNINFO_PRIMARY",
            "source_url": "https://static.cninfo.com.cn/finalpage/primary.PDF",
        },
    }
    assert len(classify([requirement], [triage], set(), [accepted])) == 1
    assert (
        len(
            classify(
                [dict(requirement, title="关于实施分红后调整回购股份价格上限的公告")],
                [triage],
                set(),
                [accepted],
            )
        )
        == 1
    )
    assert classify([requirement], [triage], set(), [accepted, accepted]) == []
    assert (
        classify(
            [requirement],
            [triage],
            set(),
            [dict(accepted, event=dict(accepted["event"], cash_per_share="0.2"))],
        )
        == []
    )
