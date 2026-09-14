import pytest

from scripts.parse_sse_factbook_names import name_pages, name_row


def test_official_dated_name_columns_preserve_order_and_dates():
    row = name_row("600076 2010-6-9 ST 华光 *ST 华光")
    assert (row["old_status"], row["new_status"], row["effective_date"]) == (
        "STAR_ST",
        "ST",
        "2010-06-09",
    )
    assert name_row("22 600760 2018/1/12 中航沈飞 中航黑豹")["effective_date"] == "2018-01-12"
    assert name_row("600696.SH 2018-06-19 ST岩石 ST匹凸")["old_status"] == "ST"
    with pytest.raises(ValueError):
        name_row("600076 ST华光 *ST华光")
    with pytest.raises(ValueError):
        name_row("600076 2010-2-30 ST华光 *ST华光")


def test_headerless_continuation_stops_at_next_named_section():
    first = "更名日期 新股票简称 原股票简称\n600076 2010-6-9 ST华光 *ST华光"
    continuation = "上市公司\n114 2015 市场资料\n600728 2014-1-2 佳都科技 佳都新太"
    unrelated = "2014年上市公司名称更改一览\n600728 2014-1-2 完整公司名 另一公司名"
    assert [number for number, _ in name_pages([first, continuation, unrelated])] == [1, 2]
