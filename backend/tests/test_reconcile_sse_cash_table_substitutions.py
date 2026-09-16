from decimal import Decimal

from scripts.reconcile_sse_cash_table_substitutions import (
    distribution_class,
    notice_amount_conflicts,
)


def test_distribution_class_requires_an_unambiguous_explicit_marker():
    assert distribution_class(["差异化分红送转\uff1a否"]) == "NON_DIFFERENTIATED"
    assert distribution_class(["差异化分红送转:是"]) == "DIFFERENTIATED"
    assert distribution_class(["差异化分红送转:是\uff1b差异化分红送转:否"]) == "CONFLICT"
    assert distribution_class(["每股现金红利 0.1 元"]) == "UNMARKED"


def test_precise_issuer_cash_amount_cannot_be_replaced_by_rounded_exchange_table():
    assert notice_amount_conflicts([({}, Decimal("0.3261"))], "0.326")
    assert not notice_amount_conflicts([({}, Decimal("0.326"))], "0.326")
