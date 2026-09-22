from scripts.build_cash_gap_queue import candidate_queue


def test_cash_gap_queue_is_candidate_only_and_order_independent():
    requirement = {
        "priority": "P1",
        "source_group": "CNINFO",
        "required_document_types": ["FINAL_IMPLEMENTATION_NOTICE_WITH_GROSS_ORDINARY_A_SHARE_CASH"],
        "known_urls": [],
        "affected_events": ["CASH:000001:2022-07-21:2022-07-22"],
    }
    candidates = [
        {
            "issuer": "000001",
            "published_on": "2022-07-15",
            "title": "权益分派实施公告",
            "url": "https://static.cninfo.com.cn/finalpage/example.PDF",
        },
        {
            "issuer": "000001",
            "published_on": "2021-07-15",
            "title": "旧公告",
            "url": "https://static.cninfo.com.cn/finalpage/old.PDF",
        },
    ]
    result = candidate_queue([requirement], candidates)
    assert result == candidate_queue([requirement], list(reversed(candidates)))
    assert result[0][0]["affected_events"] == requirement["affected_events"]
    assert result[0][0]["queue_type"] == "OFFICIAL_CASH_GAP_CANDIDATE_PDF"
    assert result[1] == requirement["affected_events"]
    assert result[2] == []


def test_cash_gap_queue_uses_historical_source_symbol():
    requirement = {
        "priority": "P1",
        "source_group": "CNINFO",
        "required_document_types": ["FINAL_IMPLEMENTATION_NOTICE_WITH_GROSS_ORDINARY_A_SHARE_CASH"],
        "known_urls": [],
        "affected_events": ["CASH:000022:2012-07-19:2012-07-20"],
    }
    candidate = {
        "issuer": "001872",
        "source_symbol": "000022",
        "published_on": "2012-07-12",
        "title": "2011年度分红派息实施公告",
        "url": "https://static.cninfo.com.cn/finalpage/example.PDF",
    }

    queue, covered, uncovered = candidate_queue([requirement], [candidate])

    assert queue[0]["issuer"] == "000022"
    assert covered == requirement["affected_events"]
    assert uncovered == []
