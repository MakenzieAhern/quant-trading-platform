from decimal import Decimal

from scripts.audit_adjustment_residual_mechanics import parity


def test_factor_parity_uses_only_source_precision_tolerance():
    assert parity(Decimal("1.3045457"), Decimal("1.304545721558199"))["status"].endswith(
        "PASS"
    )
    assert parity(Decimal("1.30454"), Decimal("1.304545721558199"))["status"] == "CONFLICT"
