import json
from decimal import Decimal

import pytest

from scripts.sina_adjustment_audit import factor_at, feature_close, parse_factors


def test_safe_factor_parser_and_temporal_rebasing():
    rows = [{"d": "2023-06-01", "f": "2"}, {"d": "1900-01-01", "f": "1"}]
    raw = (
        "var sz000001hfq=" + json.dumps({"total": 2, "data": rows}) + "\n/* source comment */"
    ).encode()
    curve = parse_factors(raw, "sz000001", "hfq")
    assert factor_at(curve, "2023-05-31") == 1
    assert feature_close(Decimal(10), "2023-05-31", "2023-06-01", curve) == 5
    extended = [*curve, ("2025-01-01", Decimal(1000))]
    assert feature_close(Decimal(10), "2023-05-31", "2023-06-01", extended) == 5
    assert (
        feature_close(Decimal(10), "2023-05-31", "2023-06-01", [(d, v * 13) for d, v in curve]) == 5
    )
    with pytest.raises(ValueError, match="INVALID_RESEARCH"):
        feature_close(Decimal(10), "2025-01-01", "2023-01-01", curve)
    with pytest.raises(ValueError, match="UNKNOWN_FACTOR"):
        factor_at(curve[1:], "2023-01-01")
    with pytest.raises(ValueError):
        parse_factors(raw.replace(b'"1"', b'"NaN"'), "sz000001", "hfq")
    with pytest.raises(ValueError):
        parse_factors(raw, "sh600000", "hfq")
    with pytest.raises(ValueError):
        parse_factors(b"var sz000001hfq=__import__('os').system('false')", "sz000001", "hfq")
