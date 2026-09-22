from decimal import Decimal

from scripts.audit_p1_differentiated_bonus import terms


def test_differentiated_bonus_preserves_zero_cash_and_red_stock_distinction():
    conversion = [
        "每股转增0.45股。股权登记日2023/11/16 除权日2023/11/17。"
        "不派发现金红利。流通股份变动比例0.44997。"
    ]
    assert terms(conversion) == (
        {Decimal("0.45")},
        {"2023-11-16", "2023-11-17"},
        True,
        "CAPITAL_RESERVE_CONVERSION",
    )
    red_stock = ["每股派送红股0.2股。2023/7/14 2023/7/17。现金红利为0。"]
    assert terms(red_stock)[-1] == "RED_STOCK_DIVIDEND"
    assert terms(["每股转增0.3股。2023/7/6 2023/7/7。公司本年度不分配利润。"])[2]
    assert terms(["每股转增0.4股。2023/7/17 2023/7/18。每10股派发现金红利人民币0元。"])[2]
    assert terms(["每股转增0.4股。2025/1/3 2025/1/6。不派发现金红利。"])[:2] == (
        {Decimal("0.4")},
        {"2025-01-03", "2025-01-06"},
    )
