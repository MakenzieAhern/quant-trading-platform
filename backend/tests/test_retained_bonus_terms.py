from decimal import Decimal, localcontext

import pytest

from scripts.retained_bonus_terms import retained_ratio


def test_exact_retained_components_and_fail_closed_identity():
    header = "证券代码:600000\n"
    with localcontext() as context:
        context.prec = 6
        assert retained_ratio([header + "每10股送红股2股,每10股转增8股"], "600000") == 1
        assert retained_ratio([header + "每10股转增1.234567股"], "600000") == Decimal("0.1234567")
    for body in ("每10股转增10股,每10股转增5股", "重整每10股转增10股", "无分配方案"):
        with pytest.raises(ValueError):
            retained_ratio([header + body], "600000")
    with pytest.raises(ValueError, match="ISSUER_HEADER"):
        retained_ratio([header + "每10股转增10股"], "600004")
