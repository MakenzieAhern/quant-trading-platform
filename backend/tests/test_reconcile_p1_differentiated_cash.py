from decimal import Decimal

from scripts.reconcile_distribution_cash import differentiated_cash
from scripts.reconcile_p1_differentiated_cash import decision


def test_differentiated_cash_never_overrides_conflicting_accepted_event():
    assert decision([], "2024-08-23", Decimal("0.00555")) == "NEW_OFFICIAL_ISSUER_EVENT"
    peer = {"event": {"record_date": "2024-08-23", "cash_per_share": "0.00555"}}
    assert decision([peer], "2024-08-23", Decimal("0.00555")) == "EXACT_ACCEPTED_EVENT"
    assert decision([peer], "2024-08-23", Decimal("0.00551")) == "ACCEPTED_EVENT_CONFLICT"
    assert decision([peer], "2024-08-24", Decimal("0.00555")) == "ACCEPTED_EVENT_CONFLICT"


def test_actual_holder_cash_is_not_diluted_ex_price_reference():
    pages = [
        "证券代码:600157\n每股分配比例 A股每股现金红利0.00555元(含税)\n"
        "相关日期\n差异化分红送转:是\n"
        "每股现金红利=(参与分配股份数*0.00555)÷总股本=0.00551元/股。"
    ]
    assert differentiated_cash(pages, "600157", "2023年年度权益分派实施公告") == Decimal("0.00555")
