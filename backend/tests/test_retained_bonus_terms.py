from decimal import Decimal, localcontext

import pytest

from scripts.retained_bonus_terms import retained_ratio


def test_exact_retained_components_and_fail_closed_identity():
    header = "证券代码:600000\n"
    assert retained_ratio(
        [
            header
            + "一、权益分派方案\n每10股派现金1元、送红股3股(含税),"
            + "并以资本公积金每10股转增2股。\n二、股权登记日"
        ],
        "600000",
    ) == Decimal("0.5")
    with pytest.raises(ValueError, match="NO_EXPLICIT_BONUS_RATIO"):
        retained_ratio(
            [
                header
                + "一、权益分派方案\n每10股派现金1元(含税)。\n"
                + "五、调整相关参数\n历史方案每10股送红股1.8股。"
            ],
            "600000",
        )
    assert retained_ratio(
        [
            header
            + "二、利润分配及转增股本方案\n每10股转增15股。\n"
            + "三、利润分配方案具体实施日期\n除权除息日"
        ],
        "600000",
    ) == Decimal("1.5")
    assert retained_ratio(
        [header + "一、2013年资本公积金转增股本方案\n每10股转增2股。\n二、实施日期"],
        "600000",
    ) == Decimal("0.2")
    with pytest.raises(ValueError, match="NO_EXPLICIT_BONUS_RATIO"):
        retained_ratio(
            [header + "一、权益分派方案\n每10股派现金1元。\n二、吸收合并税务说明"],
            "600000",
        )
    assert (
        retained_ratio(
            [header + "一、权益分派方案\n每10股派现金1元,不送红股,不以公积金转增股本。"],
            "600000",
        )
        == 0
    )
    assert retained_ratio(
        [
            header
            + "原方案每10股转增10股。公司按最新股本计算的2013年度权益分派方案为:"
            + "以公司现有总股本为基数,向全体股东每10股转增9.138541股。"
        ],
        "600000",
    ) == Decimal("0.9138541")
    with localcontext() as context:
        context.prec = 6
        assert retained_ratio([header + "每10股送红股2股,每10股转增8股"], "600000") == 1
        assert retained_ratio([header + "每10股转增1.234567股"], "600000") == Decimal("0.1234567")
        assert retained_ratio([header + "每10股转增10股。末页每10股转增10", "2股。"], "600000") == 1
        assert retained_ratio([header + "每股送红股1股、每", "股转增1股"], "600000") == 2
        assert (
            retained_ratio(
                [
                    header + "每股送红股0.5股;每股转增1.5股。二、方案每股送红股0.5股;"
                    "每股转增1.5股。(四)扣税说明:每股转增1.3股免税,"
                    "每股转增0.2股需扣税。三、实施日期:股权登记日"
                ],
                "600000",
            )
            == 2
        )
        with pytest.raises(ValueError, match="FRACTIONAL_COMPONENT_ALLOCATION_UNRESOLVED"):
            retained_ratio(
                [header + "每股送红股0.5股;每股转增1.5股"],
                "600000",
                require_integral_components=True,
            )
        assert (
            retained_ratio(
                [header + "每股送红股1股;每股转增1股"],
                "600000",
                require_integral_components=True,
            )
            == 2
        )
        assert (
            retained_ratio(
                [
                    header + "重要内容提示重要内容提示每每每每10101010股送红股10101010股"
                    "一、通过分配方案二、分配方案每10股送红股10股"
                ],
                "600000",
            )
            == 1
        )
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
            "每10股派发股票股利1股;每10股转增9股",
            "每10股转增股10股",
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
        assert (
            retained_ratio(
                [header + "资本公积金转赠股本方案。向全体股东每10股转增10股。五、转赠股本实施办法"],
                "600000",
            )
            == 1
        )
        assert (
            retained_ratio(
                [
                    header + "每10股送股数10。向全体股东每10股转增10股。"
                    "实施后总股本为963600000股,增加481800000股。"
                ],
                "600000",
            )
            == 1
        )
        assert (
            retained_ratio(
                [
                    header + "向全体股东每10股送11.06852股。"
                    "调整后每10股送10股、每10股转增10股。"
                    "实施后总股本为1,012,513,400股,增加506,256,700股。"
                ],
                "600000",
            )
            == 1
        )
    for body in (
        "每10股转增10股,每10股转增5股",
        "重整每10股转增10股",
        "差异化分红送转:是;每10股转增10股",
        "无分配方案",
        "重要内容提示重要内容提示每每每每重整一、分配方案每10股转增10股",
        "每10股转增10股。每10股转增5股。实施后总股本为200股,增加100股",
        "每10股转增10股。实施后总股本为300股,增加200股",
        "股权转赠每10股转增10股",
        "每10股转增10股。(四)扣税说明:重整股份另行处理。三、实施日期",
    ):
        with pytest.raises(ValueError):
            retained_ratio([header + body], "600000")
    with pytest.raises(ValueError, match="ISSUER_HEADER"):
        retained_ratio([header + "每10股转增10股"], "600004")
