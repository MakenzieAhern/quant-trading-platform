import pytest

from scripts.audit_szse_official_daily_scope import validate_traded_row


def test_official_stock_row_distinguishes_no_turnover_from_invalid_ohlc():
    row = ["2023-04-10", "000001", "平安银行", "12", "12", "12.1", "11.9", "12", "0", "0", "0"]
    assert validate_traded_row(tuple(row)) is False
    row[9:11] = ["100.00", "1200.00"]
    assert validate_traded_row(tuple(row)) is True
    row[5] = "11.8"
    with pytest.raises(ValueError, match="INVALID_OHLC"):
        validate_traded_row(tuple(row))
