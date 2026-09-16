from scripts.audit_p1_orphan_exchange_dates import classify_dates


def test_exchange_dates_only_fill_missing_issuer_dates():
    row = {"record_date": "2023-11-29", "ex_date": "2023-11-30"}
    assert classify_dates(row, [], []) == "OFFICIAL_ISSUER_AMOUNT_PLUS_OFFICIAL_EXCHANGE_DATES"
    assert classify_dates(row, ["2023-11-29"], [])
    assert classify_dates(row, ["2023-11-29", "2023-12-01"], ["2023-11-30"]) == (
        "OFFICIAL_EXCHANGE_DISAMBIGUATED_ISSUER_DATE_SET"
    )
    assert classify_dates(row, ["2023-11-28"], []) is None
    assert classify_dates(row, ["2023-11-29"], ["2023-11-30"]) is None
