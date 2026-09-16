from scripts.audit_p1_orphan_exchange_dates import compatible_partial_date


def test_exchange_dates_only_fill_missing_issuer_dates():
    row = {"record_date": "2023-11-29", "ex_date": "2023-11-30"}
    assert compatible_partial_date(row, [], [])
    assert compatible_partial_date(row, ["2023-11-29"], [])
    assert not compatible_partial_date(row, ["2023-11-28"], [])
    assert not compatible_partial_date(row, ["2023-11-29"], ["2023-11-30"])
