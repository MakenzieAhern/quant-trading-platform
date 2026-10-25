from decimal import localcontext

import pytest

from scripts.audit_p1_cash_corrections import unchanged_except_cash_aggregate


def paragraph(aggregate="576,000,000", *, shares="72,000,000", gross="8", net="7.2"):
    return (
        f"本次利润分配以总股本{shares}股为基数,"
        f"向全体股东每10股派发现金红利{gross}元(含税,"
        f"扣税后个人实际每10股派现金红利{net}元),共计派发股利{aggregate}元。"
    )


def notice(before=None, after=None):
    return (
        "合成更正公告。原文:"
        + (paragraph() if before is None else before)
        + "现更正为:"
        + (paragraph("57,600,000") if after is None else after)
        + "本公司对上述更正给投资者带来的不便深表歉意。"
    )


def test_cash_aggregate_only_correction_returns_complete_normalized_paragraphs():
    text = notice().replace(",", "\uff0c").replace(":", "\uff1a")
    text = text.replace("10股", "\uff11\uff10 股").replace("元", " 元\n")
    midpoint = len(text) // 2
    assert unchanged_except_cash_aggregate([text[:midpoint], text[midpoint:]]) == {
        "original_aggregate": "576000000",
        "corrected_aggregate": "57600000",
        "base_shares": 72000000,
        "cash_per_share": "0.8",
        "original_paragraph": paragraph(),
        "corrected_paragraph": paragraph("57,600,000"),
    }


def test_cash_aggregate_math_is_exact_and_independent_of_decimal_context():
    before = paragraph("1", shares="123456789", gross="0.123456789123456789")
    after = paragraph(
        "1524157.8765432099750190521", shares="123456789", gross="0.123456789123456789"
    )
    with localcontext() as context:
        context.prec = 3
        result = unchanged_except_cash_aggregate([notice(before, after)])
        assert context.prec == 3
    assert result is not None
    assert result["cash_per_share"] == "0.0123456789123456789"
    assert result["corrected_aggregate"] == "1524157.8765432099750190521"


@pytest.mark.parametrize(
    "old,new",
    [
        ("每10股派发现金红利8元", "每10股派发现金红利9元"),
        ("实际每10股派现金红利7.2元", "实际每10股派现金红利7.3元"),
        ("72,000,000股", "73,000,000股"),
        ("含税", "不含税"),
        ("向全体股东", "向部分股东"),
        ("股为基数", "股为基数,另送10股"),
        ("元。", "元。登记日改为2011年5月6日。"),
    ],
)
def test_rejects_other_changes_anywhere_in_corrected_paragraph(old, new):
    after = paragraph("57,600,000").replace(old, new)
    assert unchanged_except_cash_aggregate([notice(after=after)]) is None


@pytest.mark.parametrize(
    "old,new",
    [
        ("原文:", ""),
        ("现更正为:", ""),
        ("本公司对上述更正", ""),
        ("原文:", "原文:原文:"),
        ("现更正为:", "现更正为:现更正为:"),
        ("本公司对上述更正", "本公司对上述更正本公司对上述更正"),
        ("原文:", "更正前:"),
        ("现更正为:", "更正后:"),
    ],
)
def test_rejects_missing_duplicate_or_unsupported_section_markers(old, new):
    assert unchanged_except_cash_aggregate([notice().replace(old, new)]) is None


def test_rejects_reversed_sections_and_empty_input():
    assert unchanged_except_cash_aggregate([]) is None
    text = "现更正为:" + paragraph("57,600,000") + "原文:" + paragraph() + "本公司对上述更正。"
    assert unchanged_except_cash_aggregate([text]) is None


@pytest.mark.parametrize("side", ["before", "after"])
@pytest.mark.parametrize("suffix", ["共计派发股利1元。", "共计派发股利未知元。"])
def test_rejects_duplicate_or_unparsed_second_aggregate(side, suffix):
    value = paragraph() if side == "before" else paragraph("57,600,000")
    assert unchanged_except_cash_aggregate([notice(**{side: value + suffix})]) is None


@pytest.mark.parametrize(
    "aggregate",
    [
        "576,000,000",
        "576000000.00",
        "57,600,001",
        "57,600,000.0000000001",
        "57,60,000",
        "-57,600,000",
        "NaN",
        "",
        "0",
    ],
)
def test_rejects_equal_malformed_or_mathematically_inconsistent_totals(aggregate):
    assert unchanged_except_cash_aggregate([notice(after=paragraph(aggregate))]) is None


@pytest.mark.parametrize(
    "old,new",
    [
        ("共计派发股利", "派发现金"),
        ("总股本72,000,000股为基数", "总股本未知股为基数"),
        ("总股本72,000,000股为基数", "总股本72,00,000股为基数"),
        ("总股本72,000,000股为基数", "总股本72,000,000.0股为基数"),
        ("总股本72,000,000股为基数", "总股本0股为基数"),
        ("总股本72,000,000股为基数", "总股本72,000,000股为基数,总股本72,000,000股为基数"),
        ("每10股派发现金红利8元", "每10股派发现金红利0元"),
        ("每10股派发现金红利8元", "每10股派发现金红利-8元"),
        ("每10股派发现金红利8元", "每10股派发现金红利8.0.0元"),
        ("每10股派发现金红利8元", "每10股派现金红利8元"),
        ("每10股派发现金红利8元(含税", "每10股派发现金红利8元(税后"),
        ("元。", "元。每10股派发现金红利8元(含税)。"),
    ],
)
def test_rejects_missing_malformed_or_ambiguous_terms_even_when_unchanged(old, new):
    assert unchanged_except_cash_aggregate([notice().replace(old, new)]) is None


def test_rejects_nonpositive_original_total():
    assert unchanged_except_cash_aggregate([notice(before=paragraph("0"))]) is None


def test_rejects_numerically_unchanged_correct_total_and_duplicate_totals_in_both_sections():
    before = paragraph("57600000.00")
    after = paragraph("57,600,000")
    assert unchanged_except_cash_aggregate([notice(before, after)]) is None
    duplicate = "共计派发股利1元。"
    assert (
        unchanged_except_cash_aggregate([notice(paragraph() + duplicate, after + duplicate)])
        is None
    )


def test_accepts_decimal_totals_and_comma_free_share_count():
    before = paragraph("3.60", shares="12", gross="0.3")
    after = paragraph("0.36", shares="12", gross="0.3")
    result = unchanged_except_cash_aggregate([notice(before, after)])
    assert result is not None
    assert result["original_aggregate"] == "3.60"
    assert result["corrected_aggregate"] == "0.36"
    assert result["base_shares"] == 12
    assert result["cash_per_share"] == "0.03"
