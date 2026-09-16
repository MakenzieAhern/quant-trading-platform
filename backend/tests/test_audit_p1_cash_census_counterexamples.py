from scripts.audit_p1_cash_census_counterexamples import crosscheck


def test_primary_official_cash_notice_exposes_missing_and_conflicting_events():
    triage = [
        {
            "document_id": name,
            "url": f"https://example.com/{name}.pdf",
            "source_sha256": "a" * 64,
            "preferred_instrument_marker": False,
            "cash_candidate_per_share": amount,
            "record_dates": ["2024-07-09"],
            "ex_dates": [date],
        }
        for name, amount, date in (
            ("missing", "0.4", "2024-07-10"),
            ("conflict", "0.5", "2024-07-11"),
        )
    ]
    requirements = [
        {
            "document_id": name,
            "issuer": "000001",
            "published_on": "2024-07-03",
            "title": "2023年年度权益分派实施公告",
        }
        for name in ("missing", "conflict")
    ]
    master = [
        {
            "symbol": "000001",
            "security_id": "CN-A:SZSE:000001",
            "effective_from": "2010-01-01",
            "effective_to": None,
            "instrument_type": "COMMON_A_SHARE",
        }
    ]
    cash = [
        {
            "event": {
                "security_id": {"value": "CN-A:SZSE:000001"},
                "record_date": "2024-07-09",
                "ex_date": "2024-07-11",
                "cash_per_share": "0.45",
                "source_url": "https://example.com/accepted.pdf",
            }
        }
    ]
    assert [row["finding"] for row in crosscheck(triage, requirements, cash, master)] == [
        "ACCEPTED_EX_DATE_TERM_CONFLICT",
        "NO_ACCEPTED_EX_DATE_EVENT",
    ]
