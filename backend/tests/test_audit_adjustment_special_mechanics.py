from decimal import Decimal

from scripts.audit_adjustment_special_mechanics import reference_parity


def test_reference_parity_accepts_exact_and_same_display_tick_only() -> None:
    exact = reference_parity(
        Decimal("4.83"),
        Decimal("1.084949890799154325807673255"),
        399_347_513,
        (str(211_737_774 * Decimal("4.83")), str(187_609_739 * Decimal("3.22"))),
        399_347_513,
    )
    assert exact["status"] == "OFFICIAL_FORMULA_REFERENCE_PARITY_PASS"

    rounded = reference_parity(
        Decimal("2.86"),
        Decimal("2.3252"),
        622_372_316,
        (str(Decimal("0.58") * 1_555_930_790),),
        1_555_930_790,
    )
    assert rounded["status"] == "OFFICIAL_FORMULA_DISPLAY_TICK_PARITY_PASS"

    conflict = reference_parity(
        Decimal("2.86"),
        Decimal("2"),
        622_372_316,
        (str(Decimal("0.58") * 1_555_930_790),),
        1_555_930_790,
    )
    assert conflict["status"] == "OFFICIAL_FORMULA_REFERENCE_PARITY_CONFLICT"
