from decimal import Decimal

import pytest

from scripts.audit_p1_precise_sse_cash import final_amount


def test_final_sse_cash_summary_requires_matching_implementation_body():
    page = (
        "证券代码:600459 证券简称:贵研铂业\n"
        "重要内容提示: 每股分配比例 A股每股现金红利0.16502元 相关日期\n"
        "差异化分红送转:否\n"
        "本次利润分配以方案实施前总股本为基数,每股派发现金红利0.16502元(含税)。"
        "旧预案每10股派1.65元。"
    )
    assert final_amount([page], "600459") == Decimal("0.16502")
    with pytest.raises(ValueError, match="FINAL_IMPLEMENTATION_BODY_DISAGREES"):
        final_amount([page.replace("派发现金红利0.16502", "派发现金红利0.165")], "600459")
