from scripts.audit_szse_raw_gap_factor_impact import build_report


def test_missing_row_impact_excludes_pre_warmup_sessions():
    sessions = [f"2020-01-0{day}" for day in range(1, 7)]
    gap = {
        "unresolved_rows": [
            {"date": "2020-01-02", "security_id": "CN-A:SZSE:300001"},
            {"date": "2020-01-02", "security_id": "CN-A:SZSE:300002"},
        ]
    }
    candidate = {
        "target_date": "2020-01-02",
        "results": [{}, {}],
        "promoted": False,
        "completed": True,
        "status": "CANDIDATE_ONLY",
    }
    calendar = {"sessions": sessions, "trading_sessions": len(sessions)}
    master = {
        "records": [
            {
                "security_id": "CN-A:SZSE:300001",
                "listing_date": "2020-01-01",
                "delisting_date": "",
            },
            {
                "security_id": "CN-A:SZSE:300002",
                "listing_date": "2020-01-02",
                "delisting_date": "",
            },
        ]
    }

    report = build_report(
        gap, candidate, calendar, master, lookback_sessions=3, rebalance_sessions=1
    )

    assert report["affected_window"] == ["2020-01-02", "2020-01-04"]
    assert report["lifecycle_security_days"] == 6
    assert report["observed_only_bridge_security_days"] == 1
    assert report["observed_only_bridge_rebalance_evaluations"] == 1
    assert report["status"] == "MATERIAL_FACTOR_TREATMENT_DECISION_REQUIRED"
