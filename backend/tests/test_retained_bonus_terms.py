from decimal import Decimal, localcontext

import pytest

from scripts.retained_bonus_terms import retained_ratio


def test_exact_retained_components_and_fail_closed_identity():
    header = "证券代码:600000\n"
    with localcontext() as context:
        context.prec = 6
        assert retained_ratio([header + "每10股送红股2股,每10股转增8股"], "600000") == 1
        assert retained_ratio([header + "每10股转增1.234567股"], "600000") == Decimal("0.1234567")
        for terms in (
            "每股送股0.2股,每股转增0.8股",
            "每10股送股数2每10股转增股数8",
            "每10股派送股票2股,每10股转增比例8股",
            "每股分配比例:现金0.1元,转增0.8股;每10股送股数2",
            "差异化分红送转:否;每10股转增10股",
            "每10股派送红股4股,每10股资本公积金转增6股",
            "每10股送4股,转增6股",
            "向全体股东实施10股送5股,每10股转增5股",
            "每10股派现金红利0.50元,送2股,转增8股",
        ):
            assert retained_ratio([header + terms], "600000") == 1
        assert (
            retained_ratio(
                ["股票股票股票股票代码代码代码代码:: ::600000 600000\n每10股转增10股"],
                "600000",
            )
            == 1
        )
        assert retained_ratio(["证券号码:600000\n每10股转增10股"], "600000") == 1
    for body in (
        "每10股转增10股,每10股转增5股",
        "重整每10股转增10股",
        "差异化分红送转:是;每10股转增10股",
        "无分配方案",
    ):
        with pytest.raises(ValueError):
            retained_ratio([header + body], "600000")
    with pytest.raises(ValueError, match="ISSUER_HEADER"):
        retained_ratio([header + "每10股转增10股"], "600004")
