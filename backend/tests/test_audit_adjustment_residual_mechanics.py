from decimal import Decimal

import pytest

from scripts.audit_adjustment_residual_mechanics import first_observed_boundary, parity


def test_factor_parity_uses_only_source_precision_tolerance():
    assert parity(Decimal("1.3045457"), Decimal("1.304545721558199"))["status"].endswith("PASS")
    assert parity(Decimal("1.30454"), Decimal("1.304545721558199"))["status"] == "CONFLICT"


def test_first_observed_boundary_requires_the_exact_official_suspension():
    event = "FACTOR:CN-A:SZSE:000156:2012-10-19"
    interval = {
        "security_id": "CN-A:SZSE:000156",
        "classification": "OFFICIAL_PRE2010_LISTING_SUSPENSION",
        "suspended_from": "2006-04-13",
        "first_trading_day": "2012-10-19",
    }
    assert first_observed_boundary(event, [interval]) == interval
    with pytest.raises(ValueError, match="FIRST_OBSERVED_BOUNDARY_UNPROVEN"):
        first_observed_boundary(event, [{**interval, "first_trading_day": "2012-10-18"}])
