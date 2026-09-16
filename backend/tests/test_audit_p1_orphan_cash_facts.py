from scripts.audit_p1_orphan_cash_facts import final_issuer_title, select


def test_url_less_requirement_uses_exact_official_issuer_notice():
    requirement = {
        "priority": "P1",
        "source_group": "CNINFO",
        "document_id": "orphan",
        "known_urls": [],
        "required_document_types": ["FINAL_IMPLEMENTATION_NOTICE_WITH_GROSS_ORDINARY_A_SHARE_CASH"],
        "affected_events": ["CASH:000001:2023-11-29:2023-11-30"],
    }
    url = "https://static.cninfo.com.cn/finalpage/2023-11-24/test.PDF"
    event = {
        "event": {
            "security_id": {"value": "CN-A:SZSE:000001"},
            "record_date": "2023-11-29",
            "ex_date": "2023-11-30",
            "cash_per_share": "0.4",
            "source_provider": "OFFICIAL_ISSUER_CNINFO_EXCHANGE_RECONCILED",
            "source_url": url,
            "source_document": "权益分派实施公告",
            "source_document_sha256": "sha",
            "announcement_date": "2023-11-24",
        },
        "event_checksum": "event-sha",
    }
    master = [
        {
            "symbol": "000001",
            "security_id": "CN-A:SZSE:000001",
            "effective_from": "1991-01-01",
            "effective_to": None,
            "instrument_type": "COMMON_A_SHARE",
            "listing_date": "1991-01-01",
            "delisting_date": None,
        }
    ]
    source = {
        "url": url,
        "retrieval_status": "PASS",
        "issuer": "000001",
        "title": "权益分派实施公告",
        "published_on": "2023-11-24",
        "source_sha256": "sha",
        "source_path": "notice.pdf",
    }
    rows = select([requirement], [], [], [event], master, [source])
    assert len(rows) == 1
    assert rows[0]["classification"] == "AUTHORITATIVE_OFFICIAL_SOURCE_SUBSTITUTION"
    source["title"] = "提议分红公告"
    assert select([requirement], [], [], [event], master, [source]) == []


def test_legacy_final_title_does_not_admit_proposal():
    assert final_issuer_title("2010年度分红派息公告")
    assert not final_issuer_title("董事会关于提议2010年度分红公告")
