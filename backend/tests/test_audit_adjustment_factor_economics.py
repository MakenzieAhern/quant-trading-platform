from decimal import Decimal

from scripts.audit_adjustment_factor_economics import economics


def test_exact_terms_factor_economics() -> None:
    pre_close = Decimal("19.24")
    cash = Decimal("0.17")
    bonus = Decimal("0.6")
    expected = pre_close * (Decimal(1) + bonus) / (pre_close - cash)
    assert economics(pre_close, cash, bonus, expected)["status"] == (
        "GROSS_TERMS_FACTOR_PARITY_PASS"
    )
    assert economics(pre_close, cash, bonus, Decimal("1"))["status"] == (
        "GROSS_TERMS_FACTOR_PARITY_CONFLICT"
    )
