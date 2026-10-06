from decimal import Decimal, localcontext

import pytest

from app.domain.markets.corporate_actions import cash_bonus_reference_price
from scripts.retained_bonus_reference_terms import repurchase_reference_basis


def _page(formula):
    return (
        "证券代码:300522 证券简称:示例 公告编号:2021-001\n"
        "公司回购专用证券账户股份不参与分红。按公司总股本折算每股现金红利。"
        "股权登记日为:2021年5月27日,除权除息日为:2021年5月28日。"
        "本次权益分派实施后的除权除息价格" + formula
    )


def _parse(pages, **kwargs):
    return repurchase_reference_basis(
        pages,
        kwargs.get("symbol", "300522"),
        kwargs.get("title", "2020年年度权益分派实施公告"),
        "2021-05-27",
        kwargs.get("ex_date", "2021-05-28"),
    )


def test_reference_basis_is_not_holder_cash_or_ratio_and_preserves_precision():
    for formula in (
        "=(除权除息日的前一日收盘价-0.1983936)÷1.4959841。",
        "=(股权登记日收盘价格-0.1983936元/股)÷(1+0.4959841)。",
    ):
        for precision in (3, 50):
            with localcontext() as context:
                context.prec = precision
                result = _parse([_page(formula)])
                assert result["cash_per_total_old_share"] == "0.1983936"
                assert result["share_ratio_per_total_old_share"] == "0.4959841"
                assert result["changes_holder_entitlements"] is False
                assert cash_bonus_reference_price(
                    Decimal("29.29"),
                    cash_per_old_share=Decimal(result["cash_per_total_old_share"]),
                    aggregate_share_ratio=Decimal(result["share_ratio_per_total_old_share"]),
                    minimum_tick=Decimal("0.01"),
                ) == Decimal("19.45")


def test_reference_basis_fails_closed_at_source_boundaries():
    formula = "=(除权除息日的前一日收盘价-0.1983936)÷1.4959841。"
    page = _page(formula)
    declaration = "本次权益分派实施后的除权除息价格"
    for pages, kwargs in (
        ([page], {"symbol": "002568"}),
        ([page], {"title": "2020年年度权益分派预案"}),
        ([page], {"ex_date": "2021-05-29"}),
        ([page.replace("不参与", "参与")], {}),
        ([page.replace("折算", "调整")], {}),
        ([page + "差异化分红送转:是"], {}),
        ([page + "本次让渡股份"], {}),
        ([page.replace("本次权益分派实施后的除权除息价格", "以下仅为测算示例,拟采用参考价格")], {}),
        (
            [
                page.replace(
                    "本次权益分派实施后的除权除息价格", "示例:本次权益分派实施后的除权除息价格"
                )
            ],
            {},
        ),
        ([page.replace("本次权益分派实施后的除权除息价格", "其他参数计算")], {}),
        ([page.replace(declaration, "已作废的" + declaration)], {}),
        ([page.replace(declaration, "不再采用" + declaration)], {}),
        ([page.replace(declaration, declaration + "=已作废")], {}),
        ([page + formula.replace("0.1983936", "0.2")], {}),
        ([page.replace(formula, "=(除权除息日前收盘价-每股现金)÷(1+股份变动比例)。")], {}),
        ([page.replace(formula, formula.split("1.495")[0] + "1.495"), "9841。"], {}),
        ([page.replace("1.4959841", "0.4959841")], {}),
    ):
        with pytest.raises(ValueError):
            _parse(pages, **kwargs)


def test_reference_basis_only_strips_identical_running_header_at_page_start():
    formula = "=(股权登记日收盘价格-0.1983936元/股)÷(1+0.4959841)。"
    page = _page(formula)
    header = page.split("\n", 1)[0]
    start, declaration = page.split("本次权益分派实施后的除权除息价格", 1)
    pages = [start, header + "\n本次权益分派实施后的除权除息价格" + declaration]
    assert _parse(pages)["share_ratio_per_total_old_share"] == "0.4959841"
    pages[1] = pages[1].replace("300522", "002568")
    with pytest.raises(ValueError, match="IMPLEMENTED_DECLARATION"):
        _parse(pages)


@pytest.mark.parametrize(
    ("basis", "declaration", "cash", "ratio"),
    [
        (
            "二、权益分派方案以公司现有总股本剔除已回购股份2,098,000.00股后的"
            "174,222,000.00股为基数。按公司总股本折算每股现金分红金额。",
            "在保证本次权益分派方案不变的前提下,本次权益分派实施后的除权除息参考价"
            "=(除权除息日前一交易日收盘价-按公司总股本折算每股现金分红金额)"
            "/(1+股份变动比例)=(股权登记日收盘价-0.5928607元/股)/(1+0.3952404)。",
            "0.5928607",
            "0.3952404",
        ),
        (
            "公司回购专用证券账户股份不参与分红。按公司总股本折算每股现金红利。",
            "3、本次权益分派实施后的除权除息价格"
            "=(本次权益分派股权登记日收盘价-按公司总股本折算的每股现金分红金额)"
            "/(1+按公司总股本折算的每股转增股数)"
            "=(本次权益分派股权登记日收盘价-0.3987349元)/(1+0.3987349)。",
            "0.3987349",
            "0.3987349",
        ),
    ],
    ids=["explicit_excluded_capital", "current_distribution_price"],
)
def test_reference_basis_explicit_exclusion_and_current_distribution_formula(
    basis, declaration, cash, ratio
):
    # Synthetic notice using official grammar, not an issuer-specific allowlist.
    page = (
        _page("")
        .replace(
            "公司回购专用证券账户股份不参与分红。按公司总股本折算每股现金红利。",
            "。" + basis,
        )
        .removesuffix("本次权益分派实施后的除权除息价格")
        + declaration
    )
    for precision in (3, 50):
        with localcontext() as context:
            context.prec = precision
            result = _parse([page])
            assert result["cash_per_total_old_share"] == cash
            assert result["share_ratio_per_total_old_share"] == ratio
            assert result["changes_holder_entitlements"] is False
    invalid_pages = [
        page.replace(basis, basis.replace("不参与", "参与").replace("剔除已回购", "未剔除已回购")),
        page.replace(declaration, "示例:" + declaration),
        page.replace(declaration, "已作废的" + declaration),
        page.replace(declaration, "拟采用" + declaration),
        page.replace("实施后的", "实施前的"),
        page + declaration.replace(cash, "0.7"),
    ]
    if "剔除" in basis:
        invalid_pages.extend(
            [
                page.replace(basis, "示例:" + basis),
                page.replace("以公司现有", "拟以公司现有"),
                page.replace("股份2,098,000.00股", "股份"),
                page.replace("174,222,000.00股为基数", "为基数"),
            ]
        )
    for invalid in invalid_pages:
        with pytest.raises(ValueError):
            _parse([invalid])
    with pytest.raises(ValueError):
        _parse([page.split("=(", 1)[0], "=(" + page.split("=(", 1)[1]])
