"""Retrospective coverage tables must never silently lose an issuer row."""

import pytest

from scripts.audit_csdcc_bonus_yearbook import coverage_gaps, parse_bonus_section

HEADER = (
    "4.11B 深市上市公司送股一览表\n"
    "每10股送股或转赠股数(股) 股权登记日 除权日 红股上市日 红股分配总数\n"
)
ROW = "300048 合康变频 10.00 2011-03-25 2011-03-28 2011-03-28 12,306.40"
END = "4.12A 沪市上市公司配股一览表"


def test_full_section_preserves_all_rows_and_date_semantics():
    other = "300062 中能电气 10.00 2011-05-13 2011-05-16 2011-05-16 7,700.00"
    rows = parse_bonus_section([HEADER + ROW, other + "\n" + END], 2011)
    assert [row["symbol"] for row in rows] == ["300048", "300062"]
    assert rows[0]["bonus_shares_per_ten"] == "10.00"
    assert rows[0]["record_date"] == "2011-03-25"
    assert rows[0]["ex_date"] == rows[0]["declared_listing_date"] == "2011-03-28"
    assert rows[0]["pdf_page"] == 1
    oracle = [{"symbol": "300062", "ex_date": "2011-05-16"}]
    assert coverage_gaps(rows, oracle) == coverage_gaps(
        list(reversed(rows)), list(reversed(oracle))
    )
    assert [row["symbol"] for row in coverage_gaps(rows, oracle)] == ["300048"]


def test_actual_column_interleaved_header_remains_on_one_pdf_page():
    header = HEADER.replace(
        "每10股送股或转赠股数(股)", "每10股送股或转\n股票简称 红股上市日\n赠股数(股)Bonus"
    )
    assert parse_bonus_section([header + ROW, END], 2011)[0]["symbol"] == "300048"


def test_code_name_conflict_is_retained_for_identity_reconciliation():
    source = "000771 杭汽轮B 3.00 2011-06-21 2011-06-22 2011-06-22 9,227.40"
    rows = parse_bonus_section([HEADER + source, END], 2011)
    assert coverage_gaps(rows, []) == rows
    assert rows[0]["source_line"] == source
    assert rows[0]["symbol"] == "000771"
    assert rows[0]["source_observed_name"] == "杭汽轮B"


@pytest.mark.parametrize(
    ("old", "malformed"),
    [("10.00", "10,,00"), ("10.00", "1,"), ("12,306.40", "12,30.40"), ("12,306.40", "1,,000.00")],
)
def test_invalid_comma_groups_are_not_normalized_into_source_values(old, malformed):
    with pytest.raises(ValueError, match="YEARBOOK_UNPARSED_ROW"):
        parse_bonus_section([HEADER + ROW.replace(old, malformed), END], 2011)


@pytest.mark.parametrize(
    ("pages", "reason"),
    [
        ([ROW, END], "YEARBOOK_SECTION_HEADER_UNRESOLVED"),
        ([HEADER + ROW], "YEARBOOK_SECTION_END_UNRESOLVED"),
        ([HEADER + ROW + "\n" + ROW, END], "YEARBOOK_DUPLICATE_EVENT"),
        ([HEADER + ROW.replace("12,306.40", "unknown"), END], "YEARBOOK_UNPARSED_ROW"),
        ([HEADER + ROW.replace("2011-03-25", "2010-03-25"), END], "YEARBOOK_ROW_YEAR_MISMATCH"),
        ([HEADER + ROW.replace("2011-03-25", "2011-03-29"), END], "YEARBOOK_ROW_DATE_ORDER"),
        ([HEADER + ROW[:35], ROW[35:] + "\n" + END], "YEARBOOK_UNPARSED_ROW"),
        (
            [
                HEADER
                + ROW.replace("300048 合康", "300048合康")
                + "\n300062 中能电气 10.00 2011-05-13 2011-05-16 2011-05-16 7,700.00",
                END,
            ],
            "YEARBOOK_UNPARSED_ROW",
        ),
        (
            [HEADER.replace("红股上市日", "登记日期") + ROW, END],
            "YEARBOOK_SECTION_HEADER_UNRESOLVED",
        ),
    ],
)
def test_fail_closed(pages, reason):
    with pytest.raises(ValueError, match=reason):
        parse_bonus_section(pages, 2011)
