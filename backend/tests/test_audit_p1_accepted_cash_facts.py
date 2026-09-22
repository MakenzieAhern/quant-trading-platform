from scripts.audit_p1_accepted_cash_facts import reconcile


def test_same_official_cash_document_survives_symbol_change_without_cross_issuer_match():
    queue = [
        {
            "document_id": "one",
            "affected_events": ["CNINFO:one"],
            "issuer": "302132",
            "published_on": "2025-06-10",
            "queue_type": "OFFICIAL_ISSUER_DISTRIBUTION_IMPLEMENTATION_PDF",
            "url": "https://static.cninfo.com.cn/one.PDF",
        }
    ]
    master = [
        {
            "symbol": "302132",
            "security_id": "CN-A:SZSE:300114",
            "effective_from": "2025-02-17",
            "effective_to": None,
            "instrument_type": "COMMON_A_SHARE",
        }
    ]
    event = {
        "event": {
            "source_url": queue[0]["url"],
            "security_id": {"value": "CN-A:SZSE:300114"},
            "announcement_date": "2025-06-10",
            "action_type": "CASH_DIVIDEND",
            "source_provider": "OFFICIAL_ISSUER_CNINFO_EXCHANGE_RECONCILED",
            "cash_per_share": "0.14",
            "record_date": "2025-06-16",
            "ex_date": "2025-06-17",
            "source_document_sha256": "a" * 64,
        },
        "event_checksum": "b" * 64,
    }
    accepted, remaining = reconcile(queue, [event], master)
    assert len(accepted) == 1 and remaining == []
    assert accepted[0]["security_id"] == "CN-A:SZSE:300114"
    event["event"]["security_id"] = {"value": "CN-A:SZSE:other"}
    assert reconcile(queue, [event], master) == ([], queue)
