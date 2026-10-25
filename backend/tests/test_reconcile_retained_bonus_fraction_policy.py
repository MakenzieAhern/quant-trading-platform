from decimal import Decimal

import pytest

from scripts.reconcile_retained_bonus_fraction_policy import (
    combined_retained_ratio,
    restructuring_holder_ratio,
)


def test_restructuring_holder_ratio_distinguishes_no_entitlement_and_retained_component():
    assert restructuring_holder_ratio(["本次转增形成的股份不向原股东分配。"]) == 0
    assert restructuring_holder_ratio(["前述转增股票不向原出资人进行分配。"]) == 0
    assert restructuring_holder_ratio(
        ["按照每 10 股转增 7 股的比例对股权登记日登记在册的全体股东实施。"]
    ) == Decimal("0.7")
    assert restructuring_holder_ratio(
        [
            "每10股转增约12.35股,其中10转约4.94143股部分将在股权登记日"
            "向除控股股东以外的其他全部股东予以无偿分配,剩余股份不向原股东分配。"
        ]
    ) == Decimal("0.494143")
    with pytest.raises(ValueError, match="ORDINARY_HOLDER_RATIO_UNRESOLVED"):
        restructuring_holder_ratio(["转增股份的具体分配另行公告。"])


def test_combined_ratio_ignores_conflicting_per_share_summary_typo():
    pages = [
        "证券代码:600667\n"
        "每10股转增股数:7.4股;每股转增股数:0.74股\n"
        "每10股送股股数:2.6股;每股转增股数:0.26股"
    ]
    assert combined_retained_ratio(pages, "600667") == 1


@pytest.mark.parametrize(
    "pages",
    [
        ["每10股转增7股的比例对全体股东实施。其余转增股份不向原股东分配。"],
        ["其余转增股份不向原股东分配。每10股转增7股的比例对全体股东实施。"],
    ],
)
def test_positive_direct_holder_component_is_not_overridden_by_other_no_award(pages):
    assert restructuring_holder_ratio(pages) == Decimal("0.7")


def test_combined_ratio_collapses_total_and_tax_components():
    pages = ["证券代码:600763\n每股转增1股;其中每股转增0.34股,另每股转增0.66股"]
    assert combined_retained_ratio(pages, "600763") == 1
