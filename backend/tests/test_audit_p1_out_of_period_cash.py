from scripts.audit_p1_out_of_period_cash import classify


def test_only_post_2025_effective_dates_close():
    findings = [
        {
            "document_id": key,
            "finding": "OUTSIDE_FULL_DATASET_PERIOD",
            "record_date": record,
            "ex_date": "2026-01-08",
            "cash_candidate_per_share": "0.4",
            "security_id": "CN-A:SZSE:000001",
            "url": key,
            "source_sha256": key,
        }
        for key, record in (("closed", "2026-01-07"), ("open", "2025-12-31"))
    ]
    triage = [
        {
            "document_id": item["document_id"],
            "candidate_class": "CASH_ONLY",
            "preferred_instrument_marker": False,
            "record_dates": [item["record_date"]],
            "ex_dates": [item["ex_date"]],
            "cash_candidate_per_share": "0.4",
        }
        for item in findings
    ]
    requirements = [
        {
            "document_id": item["document_id"],
            "title": "权益分派实施公告",
            "affected_events": [item["document_id"]],
        }
        for item in findings
    ]
    closed, open_items = classify(findings, triage, requirements)
    assert [row["document_id"] for row in closed] == ["closed", "open"]
    assert {row["document_id"]: row["record_date_in_scope"] for row in closed} == {
        "closed": False,
        "open": True,
    }
    assert not open_items
