from scripts.reconcile_retained_issuer_precision import precision_gap


def test_precision_gap_requires_same_official_issuer_source_and_rounded_amount():
    source = {
        "url": "https://static.cninfo.com.cn/finalpage/2018-05-21/1.PDF",
        "source_sha256": "a" * 64,
    }
    row = {
        "status": "UNRESOLVED_CASH_TERMS",
        "unresolved_documents": [],
        "evidence": [{"cash_per_share": "0.1100224", "source": source}],
        "exchange_amounts": ["0.110"],
        "record_date": "2018-05-25",
    }
    prior = {
        "event": {
            "cash_per_share": "0.11",
            "record_date": "2018-05-25",
            "source_url": source["url"],
            "source_document_sha256": source["source_sha256"],
            "source_provider": "OFFICIAL_ISSUER_CNINFO_EXCHANGE_DATED",
        }
    }
    assert precision_gap(row, prior)
    assert not precision_gap(
        {**row, "evidence": [{"cash_per_share": "0.112", "source": source}]}, prior
    )
    assert not precision_gap(row, {"event": {**prior["event"], "source_document_sha256": "b" * 64}})
    composite = {
        "event": {
            **prior["event"],
            "security_id": {"value": "CN-A:SSE:601226"},
            "source_url": "https://query.sse.com.cn/commonQuery.do",
            "source_provider": "OFFICIAL_SSE_TABLE_CNINFO_NOTICE_COMPOSITE",
        }
    }
    assert precision_gap(row, composite)
    assert not precision_gap(
        row,
        {"event": {**composite["event"], "security_id": {"value": "CN-A:SZSE:001226"}}},
    )
