from scripts.build_full_cash_gap_queue import gap_requirements


def test_gap_requirements_uses_point_in_time_symbol():
    gaps = [
        {
            "security_id": "CN-A:SZSE:001872",
            "record_date": "2018-01-02",
            "ex_date": "2018-01-03",
        }
    ]
    master = [
        {
            "security_id": "CN-A:SZSE:001872",
            "symbol": "000022",
            "instrument_type": "COMMON_A_SHARE",
            "effective_from": "1993-05-05",
            "effective_to": "2018-12-25",
        }
    ]
    assert gap_requirements(gaps, master)[0]["affected_events"] == [
        "CASH:000022:2018-01-02:2018-01-03"
    ]
