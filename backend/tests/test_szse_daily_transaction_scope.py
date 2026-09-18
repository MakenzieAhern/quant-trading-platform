from decimal import Decimal

from scripts.audit_szse_daily_transaction_scope import classify


def test_scope_classification_does_not_promote_close_price_pattern():
    row = {"symbol": "000001", "volume_gap": "999900", "amount_gap": "12029952.38"}
    assert classify(row, (Decimal(1000000), Decimal(12030000)), Decimal("12.00")) == (
        "OFFICIAL_BLOCK_RECONCILED_WITHIN_DISPLAY_PRECISION"
    )
    row = {"symbol": "300001", "volume_gap": "1800", "amount_gap": "33700"}
    assert classify(row, (Decimal(0), Decimal(0)), Decimal("17.76")) == (
        "CHINEXT_CLOSE_PRICE_PATTERN_UNPROVEN"
    )
    row["symbol"] = "000002"
    assert classify(row, (Decimal(0), Decimal(0)), Decimal("17.76")) == ("UNEXPLAINED_SCOPE_GAP")
