"""Only explicit linked date corrections can yield a derived parsing context."""

import pytest

from scripts.distribution_timing_correction import timing_corrected_context
from scripts.link_distribution_notices import current_notice_dates
from scripts.retained_bonus_terms import same_day_listing

TITLE = "2010年度利润分配及资本公积金转增股本实施公告"
ORIGINAL = {
    "issuer": "600000",
    "title": TITLE,
    "published_on": "2011-03-22",
    "source_sha256": "a" * 64,
    "url": "https://static.cninfo.com.cn/finalpage/2011-03-22/123.PDF",
}
CORRECTION = {
    "issuer": "600000",
    "title": "更正公告",
    "published_on": "2011-03-23",
    "source_sha256": "b" * 64,
    "url": "https://static.cninfo.com.cn/finalpage/2011-03-23/124.PDF",
}
BODY = (
    "证券代码:600000 证券简称:测试 编号:2011-020\n"
    "二、分配方案 公司2010年度利润分派方案为:向全体股东每10股派2.5元,每10股转增10股。"
    "三、分红派息日期 股权登记日:2010年03月25日。除权除息日:2010年03月28日。"
    "现金红利发放日:2010年03月28日。新增股份上市日:2010年03月28日。"
    "四、权益分派对象 本次分派对象为:截止2010年3月25日收市后登记在册的全体股东。"
)
METHOD = (
    "五、权益分派方法 1、本次所转增股于2011年3月28日直接记入股东证券账户。"
    "2、股息将于2010年3月28日直接划入账户。"
)
AMENDMENT = (
    "证券代码:600000 证券简称:测试 编号:2011-021\n"
    "公司于2011年3月22日在指定的网站公告了公司《" + TITLE + "》,更正内容如下:"
    "1、原公告第一页“三、分红派息日期”需进行更正,详细如下表:更正前 更正后\n"
    "股权登记日:2010年03月25日 股权登记日:2011年03月25日\n"
    "除权除息日:2010年03月28日 除权除息日:2011年03月28日\n"
    "现金红利发放日:2010年03月28日 现金红利发放日:2011年03月28日\n"
    "新增股份上市日:2010年03月28日 新增股份上市日:2011年03月28日\n"
    "2、原公告第一页“四、权益分派对象”中“本次分派对象为:截止2010年3月25日收市后”,"
    "现更正为:“本次分派对象为:截止2011年3月25日收市后”。"
    "3、原公告第二页“五、权益分派方法”中“2、股息将于2010年3月28日直接划入账户”,"
    "现更正为“2、股息将于2011年3月28日直接划入账户”。"
)


def test_explicit_chain_preserves_financial_terms_and_original_pages():
    original = [BODY, METHOD]
    assert current_notice_dates(original, ORIGINAL["published_on"]) == ([], [])
    result = timing_corrected_context(original, [AMENDMENT], ORIGINAL, CORRECTION)
    assert result["record_date"] == "2011-03-25"
    assert result["ex_date"] == "2011-03-28"
    assert current_notice_dates(result["derived_pages"], result["available_on"]) == (
        ["2011-03-25"],
        ["2011-03-28"],
    )
    assert original == [BODY, METHOD] and "2010年度" in result["derived_pages"][0]
    assert "每10股派2.5元,每10股转增10股" in result["derived_pages"][0]
    assert len(result["changes"]) == 6 and result["event_admitted"] is False


@pytest.mark.parametrize(
    "extra",
    ["4、转增比例修正为0.5。", "4、现金红利金额改为0.3元。", "股东范围改为法人股东。"],
)
@pytest.mark.parametrize("position", ["before_items", "after_items"])
def test_unconsumed_correction_items_are_not_date_only(extra, position):
    amendment = (
        AMENDMENT.replace("更正内容如下:", extra + "更正内容如下:")
        if position == "before_items"
        else AMENDMENT + extra
    )
    with pytest.raises(ValueError, match="TIMING_CORRECTION_UNCONSUMED_CONTENT"):
        timing_corrected_context([BODY, METHOD], [amendment], ORIGINAL, CORRECTION)


@pytest.mark.parametrize(
    ("old", "new"),
    [
        ("证券代码:600000", "证券代码:600001"),
        (TITLE, "其他年度利润分配实施公告"),
        ("于2011年3月22日", "于2011年3月21日"),
        ("更正前 更正后", "更正后 更正前"),
        ("新增股份上市日:2011年03月28日", "除权除息日:2011年03月28日"),
        ("截止2011年3月25日收市后", "截止2011年3月25日收市后向控股股东分派"),
        ("股息将于2011年3月28日", "股息将于2011年3月29日"),
    ],
)
def test_conflicts_and_non_date_changes_fail_closed(old, new):
    with pytest.raises(ValueError):
        timing_corrected_context(
            [BODY, METHOD], [AMENDMENT.replace(old, new)], ORIGINAL, CORRECTION
        )


def test_mismatched_source_binding_future_publication_duplicate_and_split_rows_rejected():
    for correction in (
        {**CORRECTION, "issuer": "600001"},
        {**CORRECTION, "source_sha256": ORIGINAL["source_sha256"]},
        {**CORRECTION, "url": CORRECTION["url"].replace("static.cninfo.com.cn", "example.com")},
        {
            **CORRECTION,
            "published_on": "2011-03-29",
            "url": CORRECTION["url"].replace("2011-03-23", "2011-03-29"),
        },
    ):
        with pytest.raises(ValueError):
            timing_corrected_context([BODY, METHOD], [AMENDMENT], ORIGINAL, correction)
    for pages in ([BODY + BODY, METHOD], [BODY, METHOD.replace("2、股息", "3、股息")]):
        with pytest.raises(ValueError):
            timing_corrected_context(pages, [AMENDMENT], ORIGINAL, CORRECTION)
    cut = AMENDMENT.index("股权登记日:2011") + len("股权登记日:2011年03月")
    with pytest.raises(ValueError):
        timing_corrected_context(
            [BODY, METHOD], [AMENDMENT[:cut], AMENDMENT[cut:]], ORIGINAL, CORRECTION
        )
    with pytest.raises(ValueError):
        timing_corrected_context(
            [BODY, METHOD], [AMENDMENT + "本次分配延期,现金每10股改为3元。"], ORIGINAL, CORRECTION
        )


def test_explicit_later_listing_is_not_replaced_with_same_day_tradability():
    amendment = AMENDMENT.replace("新增股份上市日:2011年03月28日", "新增股份上市日:2011年03月29日")
    result = timing_corrected_context([BODY, METHOD], [amendment], ORIGINAL, CORRECTION)
    assert result["declared_listing_date"] == "2011-03-29"
    assert result["ex_date"] == "2011-03-28" and result["event_admitted"] is False


def test_corrected_generic_listing_does_not_satisfy_unrestricted_listing_guard():
    result = timing_corrected_context([BODY, METHOD], [AMENDMENT], ORIGINAL, CORRECTION)
    with pytest.raises(ValueError, match="BONUS_SAME_DAY_DATES_UNRESOLVED") as failure:
        same_day_listing(result["derived_pages"], "600000", TITLE, "2011-03-25", "2011-03-28")
    assert failure.value.__notes__ == ["UNRESTRICTED_LISTING"]


def test_exact_repeated_title_header_does_not_hide_an_explicit_credit_statement():
    result = timing_corrected_context([BODY, METHOD], [AMENDMENT], ORIGINAL, CORRECTION)
    pages = result["derived_pages"]
    pages[1] += "本次转增的无限售条件流通股份的起始交易日为2011年3月28日。"
    assert same_day_listing(pages, "600000", TITLE, "2011-03-25", "2011-03-28") == "2011-03-28"
    repeated = [TITLE + "\n" + page for page in pages]
    assert same_day_listing(repeated, "600000", TITLE, "2011-03-25", "2011-03-28") == "2011-03-28"
    for malformed in (
        [repeated[0], "其他公告\n" + pages[1]],
        [repeated[0], repeated[1].replace("2011年3月28日直接", "2011年3月29日直接")],
        [repeated[0], repeated[1].replace("无限售条件", "有限售条件")],
    ):
        with pytest.raises(ValueError):
            same_day_listing(malformed, "600000", TITLE, "2011-03-25", "2011-03-28")
