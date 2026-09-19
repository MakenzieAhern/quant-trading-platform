from decimal import Decimal

from scripts.close_p1_residual_bonus_facts import exchange_matches, implementation_ratio


def test_residual_bonus_prefers_implemented_holder_ratio_and_allows_exchange_rounding():
    pages = [
        "股东大会方案为每10股转增4股。"
        "本公司权益分派方案为:以扣除回购股后的股本为基数,"
        "向全体股东每10股转增4.015392股。"
    ]
    ratio = implementation_ratio(pages)
    assert ratio == Decimal("0.4015392")
    assert exchange_matches(ratio, [{"ratio": "0.402"}]) == "ROUNDED_EXCHANGE_CORROBORATION"
