from scripts.close_p1_residual_restructuring_facts import classify


def test_restructuring_closure_keeps_positive_holder_event_distinct_from_no_holder():
    positive = {
        "document_id": "positive",
        "affected_events": ["event-positive"],
        "issuer": "000001",
        "title": "关于重整计划资本公积金转增股本事项实施的公告",
        "published_on": "2024-01-01",
        "url": "https://example.test/positive.pdf",
        "source_sha256": "a" * 64,
        "security_id": "CN-A:SZSE:000001",
        "retrieved_at_utc": "2024-01-01T00:00:00Z",
        "record_dates": ["2024-01-02"],
        "ex_dates": ["2024-01-03"],
        "pages": ["向其他全部股东分配,按照每10股转增2股获得转增股票。"],
        "text": "转增股本上市日为2024年1月3日",
    }
    zero = {
        **positive,
        "document_id": "zero",
        "affected_events": ["event-zero"],
        "issuer": "000002",
        "security_id": "CN-A:SZSE:000002",
        "source_sha256": "b" * 64,
        "pages": ["前述转增股票不向原股东进行分配。"],
        "text": "前述转增股票不向原股东进行分配。",
    }
    closed, events = classify({"000002": [zero], "000001": [positive]}, [])
    assert [(row["issuer"], row["holder_ratio"]) for row in closed] == [
        ("000001", "0.2"),
        ("000002", "0"),
    ]
    assert events[0]["event"]["listing_date"] == "2024-01-03"
