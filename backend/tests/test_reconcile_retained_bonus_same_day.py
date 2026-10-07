"""Same-day evidence is explicit, opt-in and never repairs a frozen dataset."""

import json
import sys
from pathlib import Path

import pytest

from app.data.catalog.checksums import canonical_sha256, sha256_file
from scripts import reconcile_retained_bonus
from scripts.retained_bonus_terms import same_day_listing

TITLE = "2010年度权益分派实施公告"
RECORD = "2011-03-25"
EX = "2011-03-28"
NOTICE = (
    "证券代码:600000\n2010年度权益分派实施公告。"
    "一、权益分派方案\n向全体股东每10股转增10股。"
    "二、股权登记日与除权除息日\n股权登记日为2011年3月25日,"
    "除权除息日为2011年3月28日。"
    "三、分派对象\n本次权益分派对象为:2011年3月25日下午交易所收市后,"
    "在登记结算公司登记在册的本公司全体股东。"
    "四、转增股本方法\n本次转增股于2011年03月28日直接记入股东证券账户。"
    "五、本次转增的无限售条件流通股的起始交易日为2011年3月28日。"
)


@pytest.mark.parametrize("separate_page", [False, True])
def test_conditional_option_adjustment_is_not_an_implemented_share_consolidation(separate_page):
    option_clause = (
        "八、股权激励计划相关事项2、股票期权激励计划调整事项"
        "本公司《限制性股票与股票期权激励计划》规定:"
        "若在行权前公司有资本公积金转增股份、派送股票红利、股票拆细、配股或缩股等事项,"
        "应对股票期权数量和行权价格进行相应的调整。"
    )

    def pages(clause=option_clause, notice=NOTICE):
        return [notice, clause] if separate_page else [notice + clause]

    assert same_day_listing(pages(), "600000", TITLE, RECORD, EX) == EX
    for old, new in (
        ("规定:", "说明:"),
        ("若在行权前", "本次权益分派实施后"),
        ("若在行权前", "在行权前"),
        ("应对股票期权数量", "应对普通股数量"),
        ("进行相应的调整。", "进行相应的调整"),
        ("缩股等事项", "缩股已实施等事项"),
        ("缩股等事项", "缩股和重整等事项"),
    ):
        with pytest.raises(ValueError, match="NONSTANDARD_OR_TENTATIVE"):
            same_day_listing(pages(option_clause.replace(old, new)), "600000", TITLE, RECORD, EX)
    for suffix in ("本次缩股已实施。", "本次重整已实施。", "上市日期另行公告。"):
        with pytest.raises(ValueError, match="NONSTANDARD_OR_TENTATIVE"):
            same_day_listing(pages(option_clause + suffix), "600000", TITLE, RECORD, EX)
    first, second = option_clause.split("行权价格")
    with pytest.raises(ValueError, match="NONSTANDARD_OR_TENTATIVE"):
        same_day_listing([NOTICE + first, "行权价格" + second], "600000", TITLE, RECORD, EX)
    for old, new in (
        ("2011年03月28日直接记入", "2011年03月29日直接记入"),
        ("本公司全体股东", "本公司控股股东"),
        ("无限售条件", "有限售条件"),
    ):
        with pytest.raises(ValueError):
            same_day_listing(pages(notice=NOTICE.replace(old, new)), "600000", TITLE, RECORD, EX)


@pytest.mark.parametrize("credit", ["本次所送(转增)股", "本次所送股份"])
def test_implemented_will_credit_wording_still_requires_exact_dates_and_all_holders(credit):
    notice = NOTICE.replace("本次转增股于", credit + "将于")
    assert same_day_listing([notice], "600000", TITLE, RECORD, EX) == EX
    for old, new in (
        (credit + "将于", "预计" + credit + "将于"),
        (credit + "将于", "拟将" + credit + "将于"),
        ("2011年03月28日直接记入", "2011年03月29日直接记入"),
        ("2011年03月28日直接记入", "直接记入"),
        ("本公司全体股东", "本公司控股股东"),
        ("无限售条件", "有限售条件"),
        ("起始交易日为2011年3月28日", "起始交易日为2011年3月29日"),
    ):
        with pytest.raises(ValueError):
            same_day_listing([notice.replace(old, new)], "600000", TITLE, RECORD, EX)
    with pytest.raises(ValueError):
        same_day_listing(
            [notice + notice.replace("2011年03月28日直接记入", "2011年03月29日直接记入")],
            "600000",
            TITLE,
            RECORD,
            EX,
        )
    first, second = notice.split("2011年03月28日直接记入")
    with pytest.raises(ValueError):
        same_day_listing(
            [first + "2011年03月", "28日直接记入" + second], "600000", TITLE, RECORD, EX
        )


@pytest.mark.parametrize(
    ("credit", "listing"),
    (
        ("本次所转增股份", "本次所转增"),
        ("本次所(转增)股", "本次所(转增)"),
        ("本次所送(转增)股", "本次所送(转增)"),
    ),
)
def test_same_day_retained_notice_wording_keeps_all_dates_and_holder_scope(credit, listing):
    notice = (
        NOTICE.replace("本次权益分派对象", "本次分派对象")
        .replace("本次转增股", credit)
        .replace("本次转增的无限售", listing + "的无限售")
        .replace("证券账户", "证券帐户")
    )
    assert same_day_listing([notice], "600000", TITLE, RECORD, EX) == EX
    for old, new in (
        ("2011年03月28日直接记入", "2011年03月29日直接记入"),
        ("本公司全体股东", "本公司控股股东"),
        ("无限售条件", "有限售条件"),
        ("起始交易日为2011年3月28日", "起始交易日为2011年3月29日"),
        ("起始交易日为2011年3月28日", "起始交易日待定"),
    ):
        with pytest.raises(ValueError):
            same_day_listing([notice.replace(old, new)], "600000", TITLE, RECORD, EX)
    # A conflicting alternative wording is still an official-date conflict.
    with pytest.raises(ValueError):
        same_day_listing(
            [NOTICE + notice.replace("2011年03月28日直接记入", "2011年03月29日直接记入")],
            "600000",
            TITLE,
            RECORD,
            EX,
        )


@pytest.mark.parametrize(
    ("holder_prefix", "credit", "holder", "entry"),
    (
        ("截止", "本次转增股", "本次权益分派对象", "记"),
        ("", "本次转增的股份", "本次权益分派对象", "记"),
        ("截止", "本次转增的股份", "本次权益分派对象", "记"),
        ("", "本次所送红股", "本次分派对象", "计"),
        ("", "本次所(转增)股", "本次分红派息及资本公积金转增股本对象", "记"),
        ("", "本次资本公积金转增股份", "本次分派对象", "记"),
        ("截至", "本次转增股", "本次分派对象", "记"),
        ("截止", "本次所(转增)的股份", "本次分派对象", "记"),
        ("截至", "本次所(转增)的股份", "本次分派对象", "记"),
    ),
)
def test_explicit_cutoff_and_credit_wording_never_infers_missing_dates(
    holder_prefix, credit, holder, entry
):
    entry_text = "直接" + entry + "入"
    notice = (
        NOTICE.replace("对象为:", "对象为:" + holder_prefix)
        .replace("本次权益分派对象", holder)
        .replace("本次转增股于", credit + "于")
        .replace("直接记入", entry_text)
    )
    assert same_day_listing([notice], "600000", TITLE, RECORD, EX) == EX
    for old, new in (
        ("2011年3月25日下午", "2011年3月24日下午"),
        ("2011年3月25日下午", "2011年2月30日下午"),
        ("2011年3月25日下午", "股权登记日下午"),
        ("2011年03月28日" + entry_text, "2011年03月29日" + entry_text),
        ("2011年03月28日" + entry_text, entry_text),
        ("2011年03月28日" + entry_text, "2011年03月28" + entry_text),
        (credit + "于", "预计" + credit + "于"),
        (credit + "于", "计划" + credit + "于"),
        (credit + "于", "拟将" + credit + "于"),
        (credit + "于", "讨论" + credit + "于"),
        ("全体股东", "控股股东"),
        ("无限售条件", "有限售条件"),
        ("2011年3月28日。", "上市日期另行公告。"),
    ):
        with pytest.raises(ValueError):
            same_day_listing([notice.replace(old, new)], "600000", TITLE, RECORD, EX)
    with pytest.raises(ValueError):
        same_day_listing(
            [NOTICE + notice.replace("2011年3月25日下午", "2011年3月24日下午")],
            "600000",
            TITLE,
            RECORD,
            EX,
        )
    with pytest.raises(ValueError):
        same_day_listing(
            [notice.replace("2011年03月28日" + entry_text, "2011年03月29日" + entry_text) + NOTICE],
            "600000",
            TITLE,
            RECORD,
            EX,
        )
    # The actual 002006 source has explicit credit but no unrestricted listing clause.
    with pytest.raises(ValueError):
        same_day_listing([notice.split("五、本次")[0]], "600000", TITLE, RECORD, EX)
    first, second = notice.split("2011年03月28日" + entry_text)
    with pytest.raises(ValueError):
        same_day_listing(
            [first + "2011年03月", "28日" + entry_text + second], "600000", TITLE, RECORD, EX
        )


@pytest.mark.parametrize("layout", ["holder-object", "unnumbered-metadata", "numbered-metadata"])
def test_declared_holder_object_and_current_distribution_metadata_remain_bounded(layout):
    if layout == "holder-object":
        notice = NOTICE.replace("三、分派对象", "三、利润分配、转增股本的对象").replace(
            "本次权益分派对象为:", "本次权益分派的对象为:截止"
        )
    else:
        numbering = ("1、", "2、") if layout == "numbered-metadata" else ("", "")
        notice = NOTICE.replace(
            "二、股权登记日与除权除息日\n股权登记日为2011年3月25日,除权除息日为2011年3月28日。",
            "二、股权登记日与除权除息日"
            + numbering[0]
            + "本次权益分派股权登记日为:2011年3月25日"
            + numbering[1]
            + "除权除息日为:2011年3月28日",
        ).replace("三、分派对象", "三、权益分派对象")
    assert same_day_listing([notice], "600000", TITLE, RECORD, EX) == EX
    for old, new in (
        ("2011年3月25日下午", "2011年3月24日下午"),
        ("2011年3月25日下午", "股权登记日下午"),
        ("全体股东", "控股股东"),
        ("2011年03月28日直接记入", "2011年03月29日直接记入"),
        ("2011年03月28日直接记入", "直接记入"),
        ("无限售条件", "有限售条件"),
        ("起始交易日为2011年3月28日", "起始交易日为2011年3月29日"),
        ("本次权益分派", "讨论本次权益分派"),
        ("本次权益分派", "拟将本次权益分派"),
        ("三、", "讨论三、"),
        ("二、", "讨论二、"),
        ("二、", "二、其他事项"),
    ):
        if layout == "holder-object" and old == "二、":
            continue  # The existing punctuated holder clause does not rely on metadata.
        with pytest.raises(ValueError):
            same_day_listing([notice.replace(old, new)], "600000", TITLE, RECORD, EX)
    for dated in ("2011年3月25日下午", "2011年03月28日直接记入", "2011年3月28日。"):
        first, second = notice.rsplit(dated, 1)
        with pytest.raises(ValueError):
            same_day_listing([first + dated[:6], dated[6:] + second], "600000", TITLE, RECORD, EX)
    with pytest.raises(ValueError):
        same_day_listing(
            [notice + notice.replace("2011年3月25日下午", "2011年3月24日下午")],
            "600000",
            TITLE,
            RECORD,
            EX,
        )


@pytest.mark.parametrize("weekday,listing", [(True, False), (False, True), (True, True)])
def test_explicit_weekday_and_capital_listing_preserve_all_date_guards(weekday, listing):
    notice = NOTICE
    if weekday:
        notice = notice.replace("25日", "25日(星期五)").replace("28日", "28日(星期一)")
    if listing:
        notice = notice.replace("本次转增的无限售", "本次新增资本公积金转增股本的无限售")
    assert same_day_listing([notice], "600000", TITLE, RECORD, EX) == EX
    for old, new in (
        ("2011年03月28日", "2011年03月29日"),
        ("2011年03月28日", "2011年02月30日"),
        ("2011年03月28日", "3月28日"),
        ("本公司全体股东", "本公司控股股东"),
        ("无限售条件", "有限售条件"),
        ("起始交易日为2011年3月28日", "起始交易日为2011年3月29日"),
        ("起始交易日为2011年3月28日", "起始交易日待定"),
    ):
        with pytest.raises(ValueError):
            same_day_listing([notice.replace(old, new)], "600000", TITLE, RECORD, EX)
    if weekday:
        for old, new in (
            ("星期一", "星期二"),
            ("星期五", "星期四"),
            ("(星期一)", "(预计入账)"),
            ("2011年03月28日(星期一)", "(星期一)"),
        ):
            with pytest.raises(ValueError):
                same_day_listing([notice.replace(old, new)], "600000", TITLE, RECORD, EX)
    first, second = notice.split("2011年03月28日")
    with pytest.raises(ValueError):
        same_day_listing([first + "2011年03月", "28日" + second], "600000", TITLE, RECORD, EX)
    with pytest.raises(ValueError):
        same_day_listing([notice.split("五、本次")[0]], "600000", TITLE, RECORD, EX)
    with pytest.raises(ValueError):
        same_day_listing(
            [notice + notice.replace("2011年03月28日", "2011年03月29日")],
            "600000",
            TITLE,
            RECORD,
            EX,
        )


@pytest.mark.parametrize(
    "heading",
    [
        "四、转增股本方法",
        "四、权益分派方法",
        "四、权益分派方法1、",
        "四、权益分派方法:1、",
        "四、权益分派方法1.",
        "四、权益分配方法1、",
        "四、权益分派办法1、",
        "四、利润分配和转增股本方法",
        "五、利润分配和资本公积金转增股本方法",
        "四、利润分配和资本公积金转增股本方法1、",
        "四、分配、转增股份方法1、",
        "四、分红派息及资本公积金转增股本方法1、",
        "2、",
        "",
    ],
)
def test_credit_declaration_requires_boundary_and_reviewed_method_heading(heading):
    notice = NOTICE.replace("四、转增股本方法\n", heading)
    assert same_day_listing([notice], "600000", TITLE, RECORD, EX) == EX
    for prefix in ("拟将", "讨论", "拟将1、", "讨论四、权益分派方法"):
        with pytest.raises(ValueError, match="DATES_UNRESOLVED"):
            same_day_listing(
                [notice.replace("本次转增股于", prefix + "本次转增股于")],
                "600000",
                TITLE,
                RECORD,
                EX,
            )


@pytest.mark.parametrize(
    "heading,credit,counter",
    [
        ("四、分配、转增股本方法1、", "本次所转增股", ""),
        ("四、转增股本方法", "本次所送(转)股", ""),
        ("四、分配、转增股本方法1、", "本次所送(转)股", ""),
        ("四、权益分派方法1.", "本次所(转增)股", "2/3"),
        ("四、分配、转增股本方法1、", "本次转增的股份", "-2-"),
    ],
)
def test_credit_method_parenthetic_transfer_and_page_counter_keep_complete_terms(
    heading, credit, counter
):
    notice = NOTICE.replace("四、转增股本方法\n", heading).replace("本次转增股于", credit + "于")

    def pages(text):
        if counter:
            first, second = text.split(heading, 1)
            return [first, counter + heading + second]
        return [text]

    assert same_day_listing(pages(notice), "600000", TITLE, RECORD, EX) == EX
    for old, new in (
        ("2011年03月28日直接记入", "2010年03月28日直接记入"),
        ("2011年03月28日直接记入", "2011年03月29日直接记入"),
        ("2011年03月28日直接记入", "2011年03月28直接记入"),
        ("2011年03月28日直接记入", "3月28日直接记入"),
        ("2011年03月28日直接记入", "直接记入"),
        ("全体股东", "控股股东"),
        ("无限售条件", "有限售条件"),
        ("起始交易日为2011年3月28日", "起始交易日为2011年3月29日"),
        (credit + "于", "讨论" + credit + "于"),
        (credit + "于", "拟将" + credit + "于"),
        (credit + "于", "预计" + credit + "于"),
        (credit, "本次现金红利"),
    ):
        with pytest.raises(ValueError):
            same_day_listing(pages(notice.replace(old, new)), "600000", TITLE, RECORD, EX)
    for prefix in ("讨论", "拟将", "预计"):
        with pytest.raises(ValueError):
            same_day_listing(
                [page.replace(heading, prefix + heading) for page in pages(notice)],
                "600000",
                TITLE,
                RECORD,
                EX,
            )
    for dated in ("2011年3月25日下午", "2011年03月28日直接记入", "2011年3月28日。"):
        first, second = notice.rsplit(dated, 1)
        with pytest.raises(ValueError):
            same_day_listing(
                [first + dated[:6], counter + dated[6:] + second], "600000", TITLE, RECORD, EX
            )
    with pytest.raises(ValueError):
        same_day_listing(
            [
                *pages(notice),
                *pages(notice.replace("2011年03月28日直接记入", "2011年03月29日直接记入")),
            ],
            "600000",
            TITLE,
            RECORD,
            EX,
        )
    # A separately complete cash date cannot repair the actual incomplete share date.
    with pytest.raises(ValueError):
        same_day_listing(
            [
                *pages(notice.replace("2011年03月28日直接记入", "2011年03月28直接记入")),
                "本次现金红利于2011年03月28日直接记入股东资金账户。",
            ],
            "600000",
            TITLE,
            RECORD,
            EX,
        )


@pytest.mark.parametrize(
    "holder,credit,listing",
    [
        ("本次权益分配对象为:", "本次转增股", "本次转增的无限售条件流通股的起始交易日为"),
        ("四、分红派息对象截止", "资本公积金转增的股份", "新增无限售条件流通股份上市日:"),
        ("四、利润分配和转增对象截止", "本次资本公积金转增股份", "新增无限售条件流通股份上市日:"),
    ],
)
def test_legacy_headings_keep_explicit_holder_credit_and_unrestricted_listing(
    holder, credit, listing
):
    notice = (
        NOTICE.replace("本次权益分派对象为:", holder)
        .replace("本次转增股于", credit + "于")
        .replace("本次转增的无限售条件流通股的起始交易日为", listing)
    )
    assert same_day_listing([notice], "600000", TITLE, RECORD, EX) == EX
    for old, new in (
        ("2011年3月25日下午", "2011年3月24日下午"),
        ("2011年3月25日下午", "股权登记日下午"),
        ("2011年03月28日直接记入", "2011年03月29日直接记入"),
        ("2011年03月28日直接记入", "直接记入"),
        ("全体股东", "控股股东"),
        ("无限售条件", "有限售条件"),
        (listing + "2011年3月28日", listing + "2011年3月29日"),
        (listing + "2011年3月28日", listing + "上市另行公告"),
        (listing + "2011年3月28日", "预计" + listing + "2011年3月28日"),
        (credit + "于", "预计" + credit + "于"),
        (listing + "2011年3月28日", "计划" + listing + "2011年3月28日"),
        (credit + "于", "计划" + credit + "于"),
    ):
        with pytest.raises(ValueError):
            same_day_listing([notice.replace(old, new)], "600000", TITLE, RECORD, EX)
    for dated in ("2011年3月25日下午", "2011年03月28日直接记入", "2011年3月28日。"):
        first, second = notice.rsplit(dated, 1)
        with pytest.raises(ValueError):
            same_day_listing([first + dated[:6], dated[6:] + second], "600000", TITLE, RECORD, EX)
    with pytest.raises(ValueError):
        same_day_listing(
            [notice + notice.replace("2011年03月28日", "2011年03月29日")],
            "600000",
            TITLE,
            RECORD,
            EX,
        )


@pytest.mark.parametrize("layout", ["equity-dates", "capital-credit", "both"])
def test_equity_date_chain_and_capital_credit_still_require_separate_complete_dates(layout):
    notice = NOTICE
    if layout != "capital-credit":
        notice = notice.replace(
            "二、股权登记日与除权除息日\n股权登记日为2011年3月25日,除权除息日为2011年3月28日。",
            "二、权益分派日期1、股权登记日:2011年3月25日2、除权除息日:2011年3月28日",
        )
    if layout != "equity-dates":
        notice = notice.replace("本次转增股于", "本次资本公积所转增的股份于")
    assert same_day_listing([notice], "600000", TITLE, RECORD, EX) == EX
    for old, new in (
        ("二、权益分派日期", "讨论二、权益分派日期"),
        ("二、权益分派日期", "二、其他事项"),
        ("2、除权除息日:", "讨论2、除权除息日:"),
        ("本次资本公积所转增", "计划本次资本公积所转增"),
        ("本次资本公积所转增", "讨论本次资本公积所转增"),
        ("本次资本公积所转增", "本次现金红利所转增"),
        ("2011年3月25日下午", "2011年3月24日下午"),
        ("2011年03月28日直接记入", "2011年03月29日直接记入"),
        ("2011年03月28日直接记入", "2011年03月28直接记入"),
        ("本公司全体股东", "本公司控股股东"),
        ("无限售条件", "可流通"),
        ("起始交易日为2011年3月28日", "起始交易日为2011年3月29日"),
        ("股东证券账户", "股东资金账户"),
    ):
        if old in notice:
            with pytest.raises(ValueError):
                same_day_listing([notice.replace(old, new)], "600000", TITLE, RECORD, EX)
    for dated in ("2011年3月25日下午", "2011年03月28日直接记入", "2011年3月28日。"):
        first, second = notice.rsplit(dated, 1)
        with pytest.raises(ValueError):
            same_day_listing([first + dated[:6], dated[6:] + second], "600000", TITLE, RECORD, EX)
    with pytest.raises(ValueError):
        same_day_listing(
            [notice + notice.replace("2011年03月28日直接记入", "2011年03月29日直接记入")],
            "600000",
            TITLE,
            RECORD,
            EX,
        )


@pytest.mark.parametrize("split_prose", [False, True])
def test_capital_transfer_holder_object_keeps_complete_dates_and_all_holder_scope(split_prose):
    notice = NOTICE.replace("三、分派对象", "三、转增股本对象").replace(
        "本次权益分派对象为:", "本次转增股本对象为:"
    )

    def pages(text):
        if split_prose:
            first, second = text.split("在登记结算公司", 1)
            return [first + "在登记", "结算公司" + second]
        return [text]

    assert same_day_listing(pages(notice), "600000", TITLE, RECORD, EX) == EX
    for old, new in (
        ("三、转增股本对象", "讨论三、转增股本对象"),
        ("三、转增股本对象", "三、其他事项"),
        ("本次转增股本对象为:", "拟将本次转增股本对象为:"),
        ("本次转增股本对象为:", "讨论本次转增股本对象为:"),
        ("本次转增股本对象为:", "预计本次转增股本对象为:"),
        ("2011年3月25日下午", "2011年3月24日下午"),
        ("2011年3月25日下午", "2011年3月25下午"),
        ("2011年3月25日下午", "股权登记日下午"),
        ("全体股东", "控股股东"),
        ("2011年03月28日直接记入", "2011年03月29日直接记入"),
        ("2011年03月28日直接记入", "2011年03月28直接记入"),
        ("无限售条件", "可流通"),
        ("起始交易日为2011年3月28日", "起始交易日为2011年3月29日"),
    ):
        with pytest.raises(ValueError):
            same_day_listing(pages(notice.replace(old, new)), "600000", TITLE, RECORD, EX)
    with pytest.raises(ValueError, match="FINAL_ISSUER"):
        same_day_listing(pages(notice), "600001", TITLE, RECORD, EX)
    with pytest.raises(ValueError):
        same_day_listing(pages(notice), "600000", "转增股本预案", RECORD, EX)
    with pytest.raises(ValueError):
        same_day_listing(
            [*pages(notice), *pages(notice.replace("2011年3月25日下午", "2011年3月24日下午"))],
            "600000",
            TITLE,
            RECORD,
            EX,
        )
    first, second = notice.split("2011年3月25日下午")
    with pytest.raises(ValueError):
        same_day_listing([first + "2011年3月", "25日下午" + second], "600000", TITLE, RECORD, EX)


@pytest.mark.parametrize("heading", ["三、权益分派对象", "三、分派对象"])
def test_dated_holder_heading_requires_complete_date_and_all_holders(heading):
    notice = NOTICE.replace("三、分派对象\n本次权益分派对象为:", heading + "\n")
    assert same_day_listing([notice], "600000", TITLE, RECORD, EX) == EX
    for old, new in (
        (heading, "拟" + heading),
        (heading, "讨论" + heading),
        (heading, "计划" + heading),
        (heading, "三、权益分派方案"),
        (heading, ""),
        ("2011年3月25日下午", "2011年3月24日下午"),
        ("2011年3月25日下午", "2011年2月30日下午"),
        ("2011年3月25日下午", "2011年3月25下午"),
        ("2011年3月25日下午", "股权登记日下午"),
        ("本公司全体股东", "本公司控股股东"),
        ("2011年03月28日直接记入", "2011年03月29日直接记入"),
        ("无限售条件", "有限售条件"),
    ):
        with pytest.raises(ValueError):
            same_day_listing([notice.replace(old, new)], "600000", TITLE, RECORD, EX)
    first, second = notice.split("2011年3月25日下午")
    with pytest.raises(ValueError):
        same_day_listing([first + "2011年3月", "25日下午" + second], "600000", TITLE, RECORD, EX)
    with pytest.raises(ValueError):
        same_day_listing(
            [notice + notice.replace("2011年3月25日下午", "2011年3月24日下午")],
            "600000",
            TITLE,
            RECORD,
            EX,
        )


@pytest.mark.parametrize(
    "listing",
    [
        "本次所送(转增)股的无限售条件流通股的起始交易时间为",
        "本次所送(转)的无限售条件流通股的起始交易日为",
        "本次(转增)股的无限售条件流通股的起始交易时间为",
        "新增股份起始交易日本次所转增无限售条件流通股的起始交易日为",
        "转增流通股上市日本次所转增的无限售条件流通股的起始交易日为",
        "本次所转增的无限售条件流通股上市日为:",
        "本次所转增的无限售流通股的起始交易日为",
    ],
)
def test_parenthetic_listing_aliases_require_complete_non_tentative_dates(listing):
    notice = NOTICE.replace("本次转增的无限售条件流通股的起始交易日为", listing)
    assert same_day_listing([notice], "600000", TITLE, RECORD, EX) == EX
    for old, new in (
        (listing + "2011年3月28日", listing + "2011年3月29日"),
        (listing + "2011年3月28日", listing + "2011年2月30日"),
        (listing + "2011年3月28日", listing + "3月28日"),
        (listing + "2011年3月28日", listing + "2011年3月28"),
        (listing, "预计" + listing),
        (listing, "计划" + listing),
        (listing, "拟上市" + listing),
        (listing, listing.replace("本次", "计划本次")),
        (listing, listing.replace("本次", "讨论本次")),
        ("无限售", "有限售"),
        ("无限售", "可流通"),
        ("本公司全体股东", "本公司控股股东"),
        ("2011年3月25日下午", "2011年3月24日下午"),
        ("2011年03月28日直接记入", "2011年03月29日直接记入"),
        # Incomplete credit cannot borrow the complete listing/cash date (002299).
        ("2011年03月28日直接记入", "2011年03月28直接记入"),
    ):
        with pytest.raises(ValueError):
            same_day_listing([notice.replace(old, new)], "600000", TITLE, RECORD, EX)
    first, second = notice.rsplit("2011年3月28日", 1)
    with pytest.raises(ValueError):
        same_day_listing([first + "2011年3月", "28日" + second], "600000", TITLE, RECORD, EX)
    with pytest.raises(ValueError):
        same_day_listing(
            [notice + notice.replace(listing + "2011年3月28日", listing + "2011年3月29日")],
            "600000",
            TITLE,
            RECORD,
            EX,
        )


@pytest.mark.parametrize(
    "holder,listing,adjacent",
    [
        (True, False, False),
        (False, True, False),
        (True, True, False),
        (True, True, True),
        (True, True, "short"),
    ],
)
def test_numbered_long_holder_and_listing_trade_day_keep_explicit_declarations(
    holder, listing, adjacent
):
    notice = NOTICE
    if holder:
        notice = notice.replace(
            "三、分派对象\n本次权益分派对象为:",
            "三、分红派息及资本公积金转增股本对象\n截止",
        )
    if listing:
        notice = notice.replace(
            "五、本次转增的无限售条件流通股的起始交易日为",
            "3、新增无限售条件流通股份上市交易日:",
        )
    if adjacent:
        # Reviewed 002479/002093 layouts have no full stop between dated fields.
        metadata_heading = (
            "二、分红派息日期"
            if adjacent == "short"
            else "二、股权登记日、除权除息日、新增无限售条件流通股份上市日和红利发放日"
        )
        notice = (
            notice.replace("。三、分红派息", "。4、红利发放日:2011年3月28日三、分红派息")
            .replace("3、新增无限售条件流通股份上市交易日:2011年3月28日。", "")
            .replace(
                "二、股权登记日与除权除息日\n股权登记日为2011年3月25日,除权除息日为2011年3月28日。",
                metadata_heading + "1、股权登记日为:2011年3月25日"
                "2、除权除息日为:2011年3月28日"
                "3、新增无限售条件流通股份上市交易日:2011年3月28日。",
            )
        )
    assert same_day_listing([notice], "600000", TITLE, RECORD, EX) == EX
    if adjacent:
        for label in ("4、红利发放日", "2、除权除息日", metadata_heading):
            for prefix in ("拟将", "讨论"):
                with pytest.raises(ValueError):
                    same_day_listing(
                        [notice.replace(label, prefix + label)], "600000", TITLE, RECORD, EX
                    )
    for old, new in (
        ("2011年3月25日下午", "2011年3月24日下午"),
        ("2011年3月25日下午", "股权登记日下午"),
        ("2011年03月28日直接记入", "2011年03月28直接记入"),
        ("2011年03月28日直接记入", "2011年03月29日直接记入"),
        ("2011年3月28日。", "2011年3月29日。"),
        ("2011年3月28日。", "2011年2月30日。"),
        ("2011年3月28日。", "上市日期待定。"),
        ("全体股东", "控股股东"),
        ("无限售条件", "有限售条件"),
    ):
        with pytest.raises(ValueError):
            same_day_listing([notice.replace(old, new)], "600000", TITLE, RECORD, EX)
    declarations = []
    if holder:
        declarations.append("三、分红派息及资本公积金转增股本对象")
    if listing:
        declarations.append("3、新增无限售条件流通股份上市交易日:")
    for declaration in declarations:
        for prefix in ("预计", "计划", "拟将", "讨论"):
            with pytest.raises(ValueError):
                same_day_listing(
                    [notice.replace(declaration, prefix + declaration)],
                    "600000",
                    TITLE,
                    RECORD,
                    EX,
                )
    for dated in ("2011年3月25日下午", "2011年03月28日直接记入", "2011年3月28日。"):
        first, second = notice.rsplit(dated, 1)
        with pytest.raises(ValueError):
            same_day_listing([first + dated[:6], dated[6:] + second], "600000", TITLE, RECORD, EX)
    with pytest.raises(ValueError):
        same_day_listing(
            [notice + notice.replace("2011年3月25日下午", "2011年3月24日下午")],
            "600000",
            TITLE,
            RECORD,
            EX,
        )


@pytest.mark.parametrize("holder,account", [(True, False), (False, True), (True, True)])
def test_numbered_equity_holder_and_share_account_require_complete_explicit_terms(holder, account):
    notice = NOTICE
    if holder:
        notice = notice.replace("三、分派对象\n本次权益分派对象为:", "三、权益分派对象\n截止")
    if account:
        notice = notice.replace("股东证券账户", "股东账户")
    assert same_day_listing([notice], "600000", TITLE, RECORD, EX) == EX
    for old, new in (
        ("2011年3月25日下午", "2011年3月24日下午"),
        ("2011年3月25日下午", "股权登记日下午"),
        ("2011年03月28日直接记入", "2011年03月29日直接记入"),
        ("2011年03月28日直接记入", "2011年03月28直接记入"),
        ("2011年03月28日直接记入", "直接记入"),
        ("本次转增股于", "本次现金红利于"),
        ("全体股东", "控股股东"),
        ("无限售条件", "有限售条件"),
        ("起始交易日为2011年3月28日", "起始交易日为2011年3月29日"),
    ):
        with pytest.raises(ValueError):
            same_day_listing([notice.replace(old, new)], "600000", TITLE, RECORD, EX)
    account_label = "股东账户" if account else "股东证券账户"
    with pytest.raises(ValueError):
        same_day_listing(
            [notice.replace(account_label, "股东资金账户")], "600000", TITLE, RECORD, EX
        )
    for declaration in (["三、权益分派对象"] if holder else []) + ["本次转增股于"]:
        for prefix in ("预计", "计划", "拟将", "讨论"):
            with pytest.raises(ValueError):
                same_day_listing(
                    [notice.replace(declaration, prefix + declaration)], "600000", TITLE, RECORD, EX
                )
    for dated in ("2011年3月25日下午", "2011年03月28日直接记入", "2011年3月28日。"):
        first, second = notice.rsplit(dated, 1)
        with pytest.raises(ValueError):
            same_day_listing([first + dated[:6], dated[6:] + second], "600000", TITLE, RECORD, EX)
    with pytest.raises(ValueError):
        same_day_listing(
            [notice + notice.replace("2011年03月28日", "2011年03月29日")],
            "600000",
            TITLE,
            RECORD,
            EX,
        )


@pytest.mark.parametrize(
    "split_after,counter",
    [("收市后,", ""), ("在中国", "-2-"), ("登记", ""), ("登记在", "")],
)
def test_holder_prose_page_continuation_never_completes_a_date_or_changes_scope(
    split_after, counter
):
    notice = NOTICE.replace("在登记结算公司", "在中国证券登记结算公司")
    first, second = notice.rsplit(split_after, 1)
    pages = [first + split_after, counter + second]
    assert same_day_listing(pages, "600000", TITLE, RECORD, EX) == EX
    for old, new in (
        ("2011年3月25日下午", "2011年3月24日下午"),
        ("2011年3月25日下午", "股权登记日下午"),
        ("全体股东", "控股股东"),
        ("无限售条件", "有限售条件"),
        ("2011年03月28日直接记入", "2011年03月29日直接记入"),
        ("本次权益分派对象为:", "拟将本次权益分派对象为:"),
        ("本次权益分派对象为:", "讨论本次权益分派对象为:"),
        ("登记", "四、其他分派对象登记"),
        ("登记", "2011年3月24日登记"),
    ):
        with pytest.raises(ValueError):
            same_day_listing([p.replace(old, new) for p in pages], "600000", TITLE, RECORD, EX)
    with pytest.raises(ValueError):
        same_day_listing([pages[0] + "。", pages[1]], "600000", TITLE, RECORD, EX)
    for section in ("4、其他分派对象", "4.其他分派对象"):
        with pytest.raises(ValueError):
            same_day_listing([pages[0], section + pages[1]], "600000", TITLE, RECORD, EX)
    for dated in ("2011年3月25日下午", "2011年03月28日直接记入", "2011年3月28日。"):
        first, second = notice.rsplit(dated, 1)
        with pytest.raises(ValueError):
            same_day_listing(
                [first + dated[:6], "2" + dated[6:] + second], "600000", TITLE, RECORD, EX
            )
    # A second valid-looking holder clause with a different complete date conflicts.
    with pytest.raises(ValueError):
        same_day_listing(
            [*pages, notice.replace("2011年3月25日下午", "2011年3月24日下午")],
            "600000",
            TITLE,
            RECORD,
            EX,
        )


@pytest.mark.parametrize(
    "metadata,heading",
    [
        (
            "二、股权登记日与除权除息日1、股权登记日:2011年3月25日2、除权除息日:2011年3月28日",
            "三、分派对象",
        ),
        (
            "二、分红派息日期1、股权登记日为:2011年3月25日2、除权除息日为:2011年3月28日",
            "三、分红派息对象",
        ),
        (
            "二、股权登记日、除息日、红利发放日1、股权登记日为:2011年3月25日"
            "2、除息日为:2011年3月28日3、红利发放日为:2011年3月28日",
            "三、权益分派对象",
        ),
        (
            "二、股权登记日与除权(除息)日本次权益分派股权登记日为:2011年3月25日"
            "除权(除息)日为:2011年3月28日",
            "三、权益分派对象",
        ),
        (
            "二、股权登记日与除权除息日股权登记日为2011年3月25日,除权除息日为2011年3月28日。",
            "三、利润分配和资本公积金转增股本对象",
        ),
    ],
)
def test_holder_metadata_chain_is_contiguous_and_not_a_proposed_internal_anchor(metadata, heading):
    notice = NOTICE.replace(
        "二、股权登记日与除权除息日\n股权登记日为2011年3月25日,"
        "除权除息日为2011年3月28日。三、分派对象",
        metadata + heading,
    )
    assert same_day_listing([notice], "600000", TITLE, RECORD, EX) == EX
    for label in ("二、", heading, "本次权益分派对象为:"):
        for prefix in ("拟将", "讨论"):
            with pytest.raises(ValueError):
                same_day_listing(
                    [notice.replace(label, prefix + label)], "600000", TITLE, RECORD, EX
                )
    for old, new in (
        ("2011年3月25日下午", "2011年3月24日下午"),
        ("全体股东", "控股股东"),
        ("无限售条件", "有限售条件"),
        ("2011年03月28日直接记入", "2011年03月28直接记入"),
    ):
        with pytest.raises(ValueError):
            same_day_listing([notice.replace(old, new)], "600000", TITLE, RECORD, EX)
    for dated in ("2011年3月25日下午", "2011年03月28日直接记入", "2011年3月28日。"):
        first, second = notice.rsplit(dated, 1)
        with pytest.raises(ValueError):
            same_day_listing(
                [first + dated[:6], "2" + dated[6:] + second], "600000", TITLE, RECORD, EX
            )


@pytest.mark.parametrize("layout", ["repeated-header", "heading-page-counter"])
def test_holder_page_start_preserves_header_identity_and_complete_date(layout):
    header = "测试股份有限公司2010年度权益分派实施公告"
    if layout == "repeated-header":
        first, second = NOTICE.split("三、分派对象", 1)
        pages = [header + "1" + first, header + "2三、分派对象" + second]
    else:
        first, second = NOTICE.split("本次权益分派对象为:", 1)
        pages = [first, "2/3本次权益分派对象为:" + second]
    assert same_day_listing(pages, "600000", TITLE, RECORD, EX) == EX
    for prefix in ("拟将", "讨论"):
        with pytest.raises(ValueError):
            same_day_listing(
                [pages[0], pages[1].replace("本次权益分派对象为:", prefix + "本次权益分派对象为:")],
                "600000",
                TITLE,
                RECORD,
                EX,
            )
    for old, new in (
        ("2011年3月25日下午", "2011年3月24日下午"),
        ("2011年3月25日下午", "股权登记日下午"),
        ("全体股东", "控股股东"),
        ("无限售条件", "有限售条件"),
    ):
        with pytest.raises(ValueError):
            same_day_listing([p.replace(old, new) for p in pages], "600000", TITLE, RECORD, EX)
    if layout == "repeated-header":
        with pytest.raises(ValueError):
            same_day_listing(
                [pages[0], pages[1].replace("测试股份", "其他股份")], "600000", TITLE, RECORD, EX
            )
    first, second = NOTICE.split("2011年3月25日下午", 1)
    with pytest.raises(ValueError):
        same_day_listing([first + "2011年3月", "2/328日下午" + second], "600000", TITLE, RECORD, EX)


def test_same_day_requires_same_final_issuer_holder_credit_and_listing():
    assert same_day_listing([NOTICE], "600000", TITLE, RECORD, EX) == EX
    with pytest.raises(ValueError, match="FINAL_ISSUER"):
        same_day_listing([NOTICE], "600001", TITLE, RECORD, EX)
    for title in (
        "董事会决议公告",
        "年度利润分配预案",
        "权益分派实施提示性公告",
        "2010年度权益分派实施公告(预案)",
        "2010年度权益分派实施公告(提议)",
        "2010年度权益分派实施公告(进展)",
        "2010年度权益分派实施公告(实施后)",
        "董事会关于2010年度权益分派实施公告",
    ):
        with pytest.raises(ValueError, match="FINAL_ISSUER"):
            same_day_listing([NOTICE], "600000", title, RECORD, EX)
    for old, new in (
        ("2011年03月28日直接记入", "直接记入"),
        ("2011年03月28日直接记入", "3月28日直接记入"),
        ("2011年03月28日直接记入", "2011年03月29日直接记入"),
        ("2011年03月28日直接记入", "2011年02月30日直接记入"),
        ("无限售条件", "有限售条件"),
        ("起始交易日为2011年3月28日", "起始交易日未确定"),
        ("起始交易日为2011年3月28日", "起始交易日为2011年3月29日"),
        ("本公司全体股东", "本公司控股股东"),
    ):
        expected = "NONSTANDARD_OR_TENTATIVE" if "未确定" in new else "DATES_UNRESOLVED"
        with pytest.raises(ValueError, match=expected):
            same_day_listing([NOTICE.replace(old, new)], "600000", TITLE, RECORD, EX)
    for suffix in (
        "本次转增股于2011年03月29日直接记入股东证券账户。",
        "本次转增的无限售条件流通股的起始交易日为2011年2月30日。",
        "本次转增的无限售条件流通股的起始交易日为2011年3月29日。",
        "股权登记日为2011年2月30日。",
        "除权除息日为2011年2月30日。",
        "差异化分红送转:是",
        "拟于除权日入账。",
        "上市日期另行公告。",
        "本条款适用于B股。",
        "本次转增的无限售条件流通股的起始交易日未确定。",
        "取消本次转增股份入账。",
        "新增股份上市日期另行通知。",
    ):
        with pytest.raises(ValueError):
            same_day_listing([NOTICE + suffix], "600000", TITLE, RECORD, EX)
    with pytest.raises(ValueError, match="RECORD_EX_CONFLICT"):
        same_day_listing([NOTICE], "600000", TITLE, "2011-03-24", EX)
    # A cross-page date cannot be assembled from unverified margin/page text.
    first, second = NOTICE.split("2011年03月28日直接记入")
    with pytest.raises(ValueError, match="DATES_UNRESOLVED"):
        same_day_listing(
            [first + "2011年03月", "28日直接记入" + second], "600000", TITLE, RECORD, EX
        )


@pytest.mark.parametrize(
    "credit,account,listing",
    [
        ("本次所转增股", "股东的证券帐户", "本次所转增"),
        ("本次送转股份将", "股东证券账户", "本次所送(转)"),
        ("公司本次所转增股", "股东证券账户", "公司本次所转增"),
    ],
)
def test_reviewed_credit_aliases_preserve_complete_dates_holder_and_account(
    credit, account, listing
):
    notice = (
        NOTICE.replace("本次转增股于", credit + "于")
        .replace("股东证券账户", account)
        .replace("本次转增的无限售", listing + "的无限售")
    )
    assert same_day_listing([notice], "600000", TITLE, RECORD, EX) == EX
    for old, new in (
        ("2011年03月28日直接记入", "2011年03月28直接记入"),
        ("2011年03月28日直接记入", "2011年03月29日直接记入"),
        (account, "股东的资金账户"),
        (account, "第三方证券账户"),
        ("全体股东", "控股股东"),
        ("无限售条件", "有限售条件"),
        ("起始交易日为2011年3月28日", "起始交易日为2011年3月29日"),
        (credit + "于", "讨论" + credit + "于"),
        (credit + "于", "计划" + credit + "于"),
        (listing + "的无限售", "讨论" + listing + "的无限售"),
    ):
        with pytest.raises(ValueError):
            same_day_listing([notice.replace(old, new)], "600000", TITLE, RECORD, EX)
    for dated in ("2011年03月28日直接记入", "2011年3月28日。"):
        first, second = notice.rsplit(dated, 1)
        with pytest.raises(ValueError):
            same_day_listing([first + dated[:6], dated[6:] + second], "600000", TITLE, RECORD, EX)
    with pytest.raises(ValueError):
        same_day_listing(
            [notice + notice.replace("2011年03月28日直接记入", "2011年03月29日直接记入")],
            "600000",
            TITLE,
            RECORD,
            EX,
        )


@pytest.mark.parametrize("margin", ["", "title", "title-company"])
def test_credit_account_page_continuation_never_completes_dates_or_skips_text(margin):
    title = "2011年上半年权益分派实施公告"
    header = title if margin else ""
    if margin == "title-company":
        header += "测试股份有限公司"
    notice = NOTICE.replace(TITLE, title)

    def pages(text):
        first, second = text.split("账户", 1)
        return [header + first + "账", header + "户" + second]

    assert same_day_listing(pages(notice), "600000", title, RECORD, EX) == EX
    for old, new in (
        ("2011年03月28日直接记入", "2011年03月29日直接记入"),
        ("2011年03月28日直接记入", "2011年03月28直接记入"),
        ("2011年03月28日直接记入", "直接记入"),
        ("本次转增股于", "讨论本次转增股于"),
        ("本次转增股于", "预计本次转增股于"),
        ("全体股东", "控股股东"),
        ("证券账户", "资金账户"),
        ("起始交易日为2011年3月28日", "起始交易日为2011年3月29日"),
        ("无限售条件", "可流通"),
    ):
        with pytest.raises(ValueError):
            same_day_listing(pages(notice.replace(old, new)), "600000", title, RECORD, EX)
    for insertion in ("四、其他事项", "2011年3月29日", "。", "任意说明", "资金"):
        first, second = pages(notice)
        with pytest.raises(ValueError):
            same_day_listing(
                [first, header + insertion + second[len(header) :]], "600000", title, RECORD, EX
            )
    for dated in ("2011年3月25日下午", "2011年03月28日直接记入", "2011年3月28日。"):
        first, second = notice.rsplit(dated, 1)
        with pytest.raises(ValueError):
            same_day_listing(
                [header + first + dated[:6], header + dated[6:] + second],
                "600000",
                title,
                RECORD,
                EX,
            )
    if header:
        first, second = pages(notice)
        for wrong in ("讨论" + header, header.replace("2011年", "2012年")):
            with pytest.raises(ValueError):
                same_day_listing(
                    [first, wrong + second[len(header) :]], "600000", title, RECORD, EX
                )
        if margin == "title-company":
            with pytest.raises(ValueError):
                same_day_listing(
                    [first, second.replace("测试股份", "其他股份")], "600000", title, RECORD, EX
                )
    with pytest.raises(ValueError):
        same_day_listing(
            [
                *pages(notice),
                *pages(notice.replace("2011年03月28日直接记入", "2011年03月29日直接记入")),
            ],
            "600000",
            title,
            RECORD,
            EX,
        )


def test_issuer_running_header_requires_identical_complete_first_line_and_credit_date():
    header = "证券代码:600000 证券简称:测试股份 公告编号:2011-014\n"
    notice = NOTICE.replace("本次转增股于", "1、本次所(转增)股于")
    first, second = notice.split("1、本次所(转增)股于", 1)

    def pages(text=notice, second_header=header):
        before, after = text.split("1、本次所(转增)股于", 1)
        return [header + before, second_header + "1、本次所(转增)股于" + after]

    assert same_day_listing(pages(), "600000", TITLE, RECORD, EX) == EX
    for old, new in (
        ("2011年03月28日直接记入", "2011年03月29日直接记入"),
        ("2011年03月28日直接记入", "2011年03月28直接记入"),
        ("2011年03月28日直接记入", "直接记入"),
        ("1、本次所(转增)股于", "1、讨论本次所(转增)股于"),
        ("1、本次所(转增)股于", "1、拟本次所(转增)股于"),
        ("全体股东", "控股股东"),
        ("证券账户", "资金账户"),
        ("起始交易日为2011年3月28日", "起始交易日为2011年3月29日"),
        ("无限售条件", "有限售条件"),
    ):
        with pytest.raises(ValueError):
            same_day_listing(pages(notice.replace(old, new)), "600000", TITLE, RECORD, EX)
    for wrong in (
        header.replace("600000", "600001"),
        header.replace("测试股份", "其他股份"),
        header.replace("2011-014", "2012-014"),
        header.replace("2011-014", "2011-0141"),
        header.replace("公告编号:2011-014", ""),
        header.replace("\n", ""),
        "讨论" + header,
        "任意正文\n" + header,
    ):
        with pytest.raises(ValueError):
            same_day_listing(pages(second_header=wrong), "600000", TITLE, RECORD, EX)
    for insertion in ("说明", "2011年3月29日", "四、其他事项", "拟于"):
        with pytest.raises(ValueError):
            same_day_listing(
                [header + first, header + insertion + "1、本次所(转增)股于" + second],
                "600000",
                TITLE,
                RECORD,
                EX,
            )
    for dated in ("2011年03月28日直接记入", "2011年3月28日。"):
        before, after = notice.rsplit(dated, 1)
        with pytest.raises(ValueError):
            same_day_listing(
                [header + before + dated[:6], header + dated[6:] + after],
                "600000",
                TITLE,
                RECORD,
                EX,
            )
    with pytest.raises(ValueError):
        same_day_listing(
            [*pages(), *pages(notice.replace("2011年03月28日直接记入", "2011年03月29日直接记入"))],
            "600000",
            TITLE,
            RECORD,
            EX,
        )


def test_implemented_notice_header_alias_requires_identical_page_start_and_complete_date():
    title = "2010年度权益分派实施的公告"
    header = "测试股份有限公司" + title
    first, second = NOTICE.split("四、转增股本方法", 1)
    pages = [header + "1" + first, header + "2四、转增股本方法" + second]
    assert same_day_listing(pages, "600000", title, RECORD, EX) == EX
    for replacement in (
        header.replace("测试股份", "其他股份"),
        header.replace("2010年度", "2011年度"),
        "讨论" + header,
    ):
        with pytest.raises(ValueError):
            same_day_listing(
                [pages[0], pages[1].replace(header, replacement)], "600000", title, RECORD, EX
            )
    for old, new in (
        ("2011年03月28日直接记入", "2011年03月28直接记入"),
        ("2011年03月28日直接记入", "2011年03月29日直接记入"),
        ("全体股东", "控股股东"),
        ("无限售条件", "有限售条件"),
    ):
        with pytest.raises(ValueError):
            same_day_listing(
                [page.replace(old, new) for page in pages], "600000", title, RECORD, EX
            )
    before, after = NOTICE.split("2011年03月28日直接记入", 1)
    with pytest.raises(ValueError):
        same_day_listing(
            [header + "1" + before + "2011年03月", header + "228日直接记入" + after],
            "600000",
            title,
            RECORD,
            EX,
        )


@pytest.mark.parametrize(
    "metadata",
    [
        "二、股权登记日与除权除息日股权登记日:2011年3月25日"
        "除权除息日:2011年3月28日现金红利发放日:2011年3月28日",
        "二、股权登记日与除权除息日本次权益分派股权登记日为:2011年3月25日;"
        "除权除息日为:2011年3月28日",
    ],
)
def test_holder_complete_metadata_preserves_dates_sections_and_independent_share_roles(metadata):
    old_metadata = (
        "二、股权登记日与除权除息日\n股权登记日为2011年3月25日,除权除息日为2011年3月28日。"
    )
    notice = NOTICE.replace(old_metadata, metadata)
    assert same_day_listing([notice], "600000", TITLE, RECORD, EX) == EX
    for old, new in (
        ("二、股权登记日", "讨论二、股权登记日"),
        ("三、分派对象", "讨论三、分派对象"),
        ("本次权益分派对象为:", "拟将本次权益分派对象为:"),
        ("2011年3月25日下午", "2011年3月24日下午"),
        ("全体股东", "控股股东"),
        ("无限售条件流通股", "可流通股"),
        ("2011年03月28日直接记入", "2011年03月29日直接记入"),
        ("2011年03月28日直接记入", "2011年03月28直接记入"),
        ("三、分派对象", "五、说明这里不是日期元数据三、分派对象"),
        ("除权除息日:", "说明除权除息日:"),
        ("除权除息日为:", "说明除权除息日为:"),
    ):
        if old in notice:
            with pytest.raises(ValueError):
                same_day_listing([notice.replace(old, new)], "600000", TITLE, RECORD, EX)
    for dated in ("2011年3月25日", "2011年3月28日"):
        first, second = notice.split(dated, 1)
        with pytest.raises(ValueError):
            same_day_listing([first + dated[:6], dated[6:] + second], "600000", TITLE, RECORD, EX)
    for role_term in (
        "本次转增股于2011年03月28日直接记入股东证券账户。",
        "五、本次转增的无限售条件流通股的起始交易日为2011年3月28日。",
    ):
        with pytest.raises(ValueError):
            same_day_listing([notice.replace(role_term, "")], "600000", TITLE, RECORD, EX)
    with pytest.raises(ValueError):
        same_day_listing(
            [
                notice + "本次权益分派对象为:2011年3月24日下午交易所收市后,"
                "在登记结算公司登记在册的本公司全体股东。"
            ],
            "600000",
            TITLE,
            RECORD,
            EX,
        )


@pytest.mark.parametrize("layout", ["numbered", "unnumbered", "page-field", "guarantee-margin"])
def test_distribution_metadata_fields_never_supply_missing_share_dates(layout):
    metadata = "二、分红派息日期"
    if layout == "guarantee-margin":
        metadata += (
            "本公司及董事会全体成员保证信息披露的内容真实、准确、完整,没有虚假记载、"
            "误导性陈述或重大遗漏。§"
        )
    numbered = layout not in {"unnumbered", "page-field"}
    metadata += ("1、" if numbered else "") + "股权登记日:2011年3月25日"
    metadata += ("2、" if numbered else "") + "除权除息日:2011年3月28日"
    if layout == "page-field":
        metadata += "§"
    metadata += ("3、" if numbered else "") + "新增可流通股份上市日:2011年3月28日"
    metadata += ("4、" if numbered else "") + "现金红利发放日:2011年3月28日"
    old = (
        "二、股权登记日与除权除息日\n股权登记日为2011年3月25日,"
        "除权除息日为2011年3月28日。三、分派对象"
    )
    notice = NOTICE.replace(old, metadata + "三、分红派息对象")
    if layout == "page-field":
        notice = notice.replace("本次权益分派对象为:", "本次分红派息对象为:")
    if layout == "numbered":
        notice = notice.replace("本次权益分派对象为:", "截止")
    assert same_day_listing(notice.split("§"), "600000", TITLE, RECORD, EX) == EX
    for old, new in (
        ("二、分红派息日期", "讨论二、分红派息日期"),
        ("三、分红派息对象", "讨论三、分红派息对象"),
        ("三、分红派息对象", "五、讨论方案三、分红派息对象"),
        ("2011年3月25日下午", "2011年3月24日下午"),
        ("全体股东", "控股股东"),
        ("现金红利发放日", "讨论现金红利发放日"),
        ("新增可流通股份上市日", "预计新增可流通股份上市日"),
        ("重大遗漏。§", "重大遗漏。§其他说明"),
    ):
        if old in notice:
            with pytest.raises(ValueError):
                same_day_listing(notice.replace(old, new).split("§"), "600000", TITLE, RECORD, EX)
    for dated in ("2011年3月25日", "2011年3月28日", "2011年3月25日下午"):
        first, second = notice.rsplit(dated, 1)
        with pytest.raises(ValueError):
            same_day_listing(
                (first + dated[:6] + "§" + dated[6:] + second).split("§"),
                "600000",
                TITLE,
                RECORD,
                EX,
            )
    for term, role in (
        ("本次转增股于2011年03月28日直接记入股东证券账户。", "SHARE_CREDIT"),
        ("五、本次转增的无限售条件流通股的起始交易日为2011年3月28日。", "UNRESTRICTED_LISTING"),
    ):
        with pytest.raises(ValueError) as missing:
            same_day_listing(notice.replace(term, "").split("§"), "600000", TITLE, RECORD, EX)
        assert missing.value.__notes__ == [role]


@pytest.mark.parametrize(
    "credit",
    [
        "四、分红派息方法1、本次资本公积金转增股份将于2011年03月28日直接记入股东证券账户。",
        "五、分配、转增股本方法本次送转的股份于2011年03月28日直接计入股东证券账户。",
    ],
)
def test_distribution_share_credit_aliases_do_not_borrow_cash_account_dates(credit):
    original_credit = "四、转增股本方法\n本次转增股于2011年03月28日直接记入股东证券账户。"
    notice = NOTICE.replace(original_credit, credit)
    assert same_day_listing([notice], "600000", TITLE, RECORD, EX) == EX
    for old, new in (
        ("2011年03月28日", "2011年03月29日"),
        ("2011年03月28日", "2011年03月28"),
        ("证券账户", "资金账户"),
        ("本次", "拟实施本次"),
        ("本次", "讨论本次"),
        ("方法", "方法尚未通过"),
        ("无限售条件流通股", "可流通股"),
    ):
        with pytest.raises(ValueError):
            same_day_listing([notice.replace(old, new)], "600000", TITLE, RECORD, EX)
    first, second = notice.split("2011年03月28日直接", 1)
    with pytest.raises(ValueError):
        same_day_listing([first + "2011年03月", "28日直接" + second], "600000", TITLE, RECORD, EX)
    with pytest.raises(ValueError):
        same_day_listing(
            [
                NOTICE.replace(
                    original_credit,
                    "四、分红派息方法本次现金股利于2011年03月28日直接计入股东证券账户。",
                )
            ],
            "600000",
            TITLE,
            RECORD,
            EX,
        )


def test_legacy_ex_date_metadata_keeps_independent_holder_credit_and_listing_dates():
    # Reviewed 300062 notice: complete adjacent fields, including the literal 出息 label.
    metadata = (
        "二、股权登记日与除权除息日本次权益分派的股权登记日为:2011年3月25日"
        "除权出息日为:2011年3月28日"
    )
    notice = NOTICE.replace(
        "二、股权登记日与除权除息日\n股权登记日为2011年3月25日,除权除息日为2011年3月28日。",
        metadata,
    ).replace("三、分派对象", "三、分红派息对象")
    assert same_day_listing([notice], "600000", TITLE, RECORD, EX) == EX
    for old, new in (
        ("二、股权登记日", "讨论二、股权登记日"),
        ("本次权益分派的股权登记日", "拟将本次权益分派的股权登记日"),
        ("除权出息日为:", "其他说明除权出息日为:"),
        ("三、分红派息对象", "讨论三、分红派息对象"),
        ("2011年3月25日下午", "2011年3月24日下午"),
        ("全体股东", "控股股东"),
        ("2011年03月28日直接记入", "2010年03月28日直接记入"),
        ("2011年03月28日直接记入", "2011年03月29日直接记入"),
        ("2011年03月28日直接记入", "直接记入"),
        ("证券账户", "资金账户"),
        ("无限售条件流通股", "可流通股"),
        ("起始交易日为2011年3月28日", "起始交易日为2011年3月29日"),
    ):
        with pytest.raises(ValueError):
            same_day_listing([notice.replace(old, new)], "600000", TITLE, RECORD, EX)
    for dated in ("2011年3月25日", "2011年3月28日", "2011年3月25日下午"):
        first, second = notice.split(dated, 1)
        with pytest.raises(ValueError):
            same_day_listing([first + dated[:6], dated[6:] + second], "600000", TITLE, RECORD, EX)
    for term, role in (
        ("本次转增股于2011年03月28日直接记入股东证券账户。", "SHARE_CREDIT"),
        ("五、本次转增的无限售条件流通股的起始交易日为2011年3月28日。", "UNRESTRICTED_LISTING"),
    ):
        with pytest.raises(ValueError) as missing:
            same_day_listing([notice.replace(term, "")], "600000", TITLE, RECORD, EX)
        assert missing.value.__notes__ == [role]
    with pytest.raises(ValueError):
        same_day_listing(
            [
                notice + "本次权益分派对象为:2011年3月24日下午交易所收市后,"
                "在登记结算公司登记在册的本公司全体股东。"
            ],
            "600000",
            TITLE,
            RECORD,
            EX,
        )


@pytest.mark.parametrize("layout", ["numbered-title-margin", "object-heading-verb"])
def test_numbered_ex_metadata_and_object_heading_keep_all_five_date_roles(layout):
    # Complete reviewed 300055 / 300091 layouts, not per-security exceptions.
    notice = NOTICE
    if layout == "numbered-title-margin":
        notice = notice.replace(
            "二、股权登记日与除权除息日\n股权登记日为2011年3月25日,除权除息日为2011年3月28日。",
            "二、股权登记日与除权除息日1、本次权益分派股权登记日:2011年3月25日"
            "2、本次权益分派除权除息日:2011年3月28日",
        )
    else:
        notice = notice.replace("三、分派对象", "三、权益分派对象为")

    def source_pages(value):
        if layout == "object-heading-verb":
            return [value]
        first, second = value.split("登记在册", 1)
        return [
            TITLE + "\n1\n" + first + "登记在册",
            TITLE + "\n2\n" + second,
            TITLE + "\n3\n六、备查文件。",
        ]

    assert same_day_listing(source_pages(notice), "600000", TITLE, RECORD, EX) == EX
    for old, new in (
        ("二、股权登记日", "讨论二、股权登记日"),
        ("三、", "讨论三、"),
        ("2011年3月25日下午", "2011年3月24日下午"),
        ("全体股东", "控股股东"),
        ("本次权益分派对象为:", "拟将本次权益分派对象为:"),
        ("2011年03月28日直接记入", "2010年03月28日直接记入"),
        ("2011年03月28日直接记入", "2011年03月29日直接记入"),
        ("证券账户", "资金账户"),
        ("无限售条件流通股", "可流通股"),
        ("起始交易日为2011年3月28日", "起始交易日为2011年3月29日"),
        ("2、本次权益分派除权除息日:", "2、说明本次权益分派除权除息日:"),
        ("三、权益分派对象为", "三、权益分派对象为其他说明"),
    ):
        if old in notice:
            with pytest.raises(ValueError):
                same_day_listing(
                    source_pages(notice.replace(old, new)), "600000", TITLE, RECORD, EX
                )
    for term, role in (
        ("本次转增股于2011年03月28日直接记入股东证券账户。", "SHARE_CREDIT"),
        ("五、本次转增的无限售条件流通股的起始交易日为2011年3月28日。", "UNRESTRICTED_LISTING"),
    ):
        with pytest.raises(ValueError) as missing:
            same_day_listing(source_pages(notice.replace(term, "")), "600000", TITLE, RECORD, EX)
        assert missing.value.__notes__ == [role]
    for dated in ("2011年3月25日", "2011年3月28日", "2011年03月28日"):
        first, second = notice.split(dated, 1)
        with pytest.raises(ValueError):
            same_day_listing([first + dated[:6], dated[6:] + second], "600000", TITLE, RECORD, EX)
    conflict = notice + (
        "本次权益分派对象为:2011年3月24日下午交易所收市后,在登记结算公司登记在册的本公司全体股东。"
    )
    with pytest.raises(ValueError):
        same_day_listing(source_pages(conflict), "600000", TITLE, RECORD, EX)


def _manifest(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({**data, "manifest_sha256": canonical_sha256(data)}))


def test_opt_in_reconciliation_is_immutable_and_preserves_default_schedule(tmp_path, monkeypatch):
    # CLI provenance is relative to its own source, not the caller's working directory.
    monkeypatch.chdir(tmp_path)
    staging = tmp_path / "staging"
    root = staging / "full-distribution-notices-v1"
    bonus = staging / "full-bonus-inventory-v1"
    pdf = root / "pdf/notice.pdf"
    pdf.parent.mkdir(parents=True)
    pdf.write_bytes(b"synthetic source bytes for an offline parser boundary test")
    source_sha = sha256_file(pdf)
    cache = root / "batch-v1/text" / f"{source_sha}.json"
    cache.parent.mkdir(parents=True)
    cache.write_text(json.dumps({"source_sha256": source_sha, "pages": [NOTICE]}))
    doc = dict(
        issuer="600000",
        published_on="2011-03-22",
        title=TITLE,
        retrieval_status="PASS",
        url="https://static.cninfo.com.cn/finalpage/fixture.PDF",
        source_sha256=source_sha,
        source_path="pdf/notice.pdf",
        retrieved_at_utc="2026-10-03T00:00:00Z",
    )
    source = root / "source-manifest.json"
    _manifest(source, {"documents": [doc]})
    evidence = [{"ratio": "1.000"}]
    identity = dict(symbol="600000", record_date=RECORD, ex_date=EX)
    oracle = bonus / "source-oracle-v1.json"
    _manifest(
        oracle,
        {
            "rows": [
                {**identity, "evidence": evidence, "evidence_sha256": canonical_sha256(evidence)}
            ]
        },
    )
    boundary = bonus / "listing-boundary-check-v2.json"
    _manifest(boundary, {"source_sha256": sha256_file(oracle), "rows": []})
    master = staging / "full-code-transitions-v1/master-code-intervals.json"
    _manifest(
        master,
        {
            "records": [
                dict(
                    symbol="600000",
                    security_id="CN-A:SSE:600000",
                    effective_from="2000-01-01",
                    effective_to=None,
                    listing_date="2000-01-01",
                    delisting_date=None,
                )
            ]
        },
    )
    _manifest(
        staging / "full-instrument-scope-v1/classification-manifest-v3.json",
        {
            "source_master_sha256": sha256_file(master),
            "classifications": [
                {
                    "classification": {
                        "security_id": {"value": "CN-A:SSE:600000"},
                        "instrument_type": "COMMON_A_SHARE",
                    }
                }
            ],
        },
    )
    links = root / "date-links-2011.json"
    _manifest(
        links,
        {
            "year": 2011,
            "inputs": [{"path": str(source), "sha256": sha256_file(source)}],
            "results": [
                {
                    **identity,
                    "documents": [
                        {
                            "url": doc["url"],
                            "source_sha256": source_sha,
                            "extraction_sha256": sha256_file(cache),
                        }
                    ],
                }
            ],
        },
    )

    def run(name, *flags):
        output = tmp_path / name
        monkeypatch.setattr(
            sys,
            "argv",
            [
                "reconcile_retained_bonus",
                "--staging",
                str(staging),
                "--date-links",
                str(links),
                "--output",
                str(output),
                *flags,
            ],
        )
        reconcile_retained_bonus.main()
        return json.loads(output.read_bytes())

    assert run("default.json")["accepted_events"] == 0
    accepted = run("same-day.json", "--explicit-same-day")
    assert accepted["accepted_events"] == 1
    assert not accepted["full_dataset_created"]
    assert accepted["same_day_dependency_sha256"] == {
        name: sha256_file(Path(reconcile_retained_bonus.__file__).with_name(name))
        for name in (
            "link_distribution_notices.py",
            "audit_p1_retained_cash_sources.py",
            "audit_p1_orphan_cash_facts.py",
            "audit_p1_cash_census_counterexamples.py",
        )
    }
    event = accepted["events"][0]
    assert event["event"]["source_version"] == "INTEGER_RETAINED_BONUS_EXPLICIT_SAME_DAY_V21"
    assert event["event"]["listing_date"] == EX
    assert event["event"]["share_ratio"] == "1.000"
    assert not event["scheduled_listing_not_actual_tradability"]
    assert event["support_state"] == "SUPPORTED_FOR_INTEGER_HOLDINGS_EXPLICIT_SAME_DAY"
    assert run("same-day.json", "--explicit-same-day") == accepted
    assert (
        run("approved-integer.json", "--explicit-same-day", "--fraction-policy")["events"]
        == accepted["events"]
    )
    with pytest.raises(SystemExit) as error:
        run("unapproved-boundary.json", "--fraction-policy")
    assert error.value.code == 2

    # Opt-in broadens ratios, never official identity, dates, or registry certainty.
    originals = {path: path.read_bytes() for path in (oracle, boundary, cache, links)}
    for name, ratio, terms in (
        ("fractional", "0.6", "每10股转增6股"),
        ("combined-fractional", "2", "每股送0.8股、每股转增1.2股"),
    ):
        evidence = [{"ratio": ratio}]
        _manifest(
            oracle,
            {
                "rows": [
                    {
                        **identity,
                        "evidence": evidence,
                        "evidence_sha256": canonical_sha256(evidence),
                    }
                ]
            },
        )
        _manifest(boundary, {"source_sha256": sha256_file(oracle), "rows": []})

        def bind_pages(pages):
            cache.write_text(json.dumps({"source_sha256": source_sha, "pages": pages}))
            _manifest(
                links,
                {
                    "year": 2011,
                    "inputs": [{"path": str(source), "sha256": sha256_file(source)}],
                    "results": [
                        {
                            **identity,
                            "documents": [
                                {
                                    "url": doc["url"],
                                    "source_sha256": source_sha,
                                    "extraction_sha256": sha256_file(cache),
                                }
                            ],
                        }
                    ],
                },
            )

        notice = NOTICE.replace("每10股转增10股", terms)
        bind_pages([notice])
        assert run(name + "-default.json", "--explicit-same-day")["accepted_events"] == 0
        candidate = run(name + ".json", "--explicit-same-day", "--fraction-policy")
        assert candidate["accepted_events"] == 1 and not candidate["full_dataset_created"]
        receipt = candidate["events"][0]
        assert receipt["event"]["share_ratio"] == ratio
        assert receipt["event"]["listing_date"] == EX
        assert receipt["event"]["source_version"] == "FRACTION_RETAINED_BONUS_EXPLICIT_SAME_DAY_V1"
        assert receipt["policy_id"] == "CN_A_RETAINED_BONUS_FRACTIONAL_SHARE_POLICY_V1"
        assert receipt["accounting_scope"] == "WHOLE_POSITION_FLOOR_NO_CASH_BASIS_CONSERVED"
        assert not receipt["scheduled_listing_not_actual_tradability"]
        assert run(name + ".json", "--explicit-same-day", "--fraction-policy") == candidate
        bind_pages([notice.replace("2011年03月28日直接记入", "2011年03月29日直接记入")])
        rejected = run(name + "-delayed.json", "--explicit-same-day", "--fraction-policy")
        assert rejected["accepted_events"] == 0
        assert rejected["results"][0]["unresolved_documents"]
    for path, content in originals.items():
        path.write_bytes(content)
    # Later years must not overwrite another year's authority for the same PDF.
    pool = staging / "acquisition-pool"
    extra_source = pool / "batch-v2/source-manifest.json"
    _manifest(extra_source, {"documents": [{**doc, "issuer": "600001"}]})
    extra_link = pool / "batch-v2/date-links-2012.json"
    _manifest(
        extra_link,
        {
            "year": 2012,
            "inputs": [{"path": str(extra_source), "sha256": sha256_file(extra_source)}],
            "results": [],
        },
    )
    assert (
        run("multiple-years.json", "--explicit-same-day", "--date-links", str(extra_link))["events"]
        == accepted["events"]
    )
    _manifest(
        extra_link,
        {
            "year": 2012,
            "inputs": [{"path": str(extra_source), "sha256": sha256_file(extra_source)}],
            "results": [{**identity, "documents": []}],
        },
    )
    with pytest.raises(ValueError, match="DATE_LINK_ROW_YEAR_MISMATCH"):
        run("wrong-year.json", "--explicit-same-day", "--date-links", str(extra_link))
    original_links = json.loads(originals[links])
    original_links.pop("manifest_sha256")
    _manifest(links, {**original_links, "results": original_links["results"] * 2})
    with pytest.raises(ValueError, match="DUPLICATE_DATE_LINK_IDENTITY"):
        run("duplicate-row.json", "--explicit-same-day")
    links.write_bytes(originals[links])
    pool_pdf = pool / "batch-v1/pdf/notice.pdf"
    pool_pdf.parent.mkdir(parents=True)
    pool_pdf.write_bytes(pdf.read_bytes())
    pool_cache = pool / "batch-v1/text" / f"{source_sha}.json"
    pool_cache.parent.mkdir(parents=True)
    pool_cache.write_bytes(originals[cache])
    _manifest(extra_source, {"documents": [{**doc, "source_path": "batch-v1/pdf/notice.pdf"}]})
    _manifest(
        links,
        {
            "year": 2011,
            "inputs": [{"path": str(extra_source), "sha256": sha256_file(extra_source)}],
            "results": [
                {
                    **identity,
                    "documents": [
                        {
                            "url": doc["url"],
                            "source_sha256": source_sha,
                            "extraction_sha256": sha256_file(pool_cache),
                        }
                    ],
                }
            ],
        },
    )
    pooled = run("pooled.json", "--explicit-same-day", "--fraction-policy")
    assert pooled["accepted_events"] == 1
    assert pooled["events"][0]["event"]["source_document_sha256"] == source_sha
    assert pooled["events"][0]["event"]["listing_date"] == EX
    links.write_bytes(originals[links])
    _manifest(
        boundary,
        {
            "source_sha256": sha256_file(oracle),
            "rows": [
                {
                    "symbol": "600000",
                    "ex_date": EX,
                    "status": "NEXT_ACCEPTED_SESSION",
                    "next_session": "2011-03-29",
                }
            ],
        },
    )
    default = run("next-session.json")
    assert default["scope"] == "BOUNDED_INTEGER_NEXT_SESSION_BONUS_NOT_FULL_CENSUS"
    assert "same_day_dependency_sha256" not in default
    assert default["events"][0]["event"]["listing_date"] == "2011-03-29"
    assert default["events"][0]["scheduled_listing_not_actual_tradability"]
    assert (
        default["events"][0]["support_state"]
        == "SUPPORTED_FOR_INTEGER_HOLDINGS_NEXT_SESSION_SCHEDULE"
    )

    # Rebind outer manifests deliberately: the inner PDF/text identity must still agree.
    original_cache = json.loads(cache.read_bytes())
    for name, content in (
        ("wrong-inner-sha.json", {**original_cache, "source_sha256": "0" * 64}),
        ("fraction.json", {**original_cache, "pages": [NOTICE.replace("转增10股", "转增15股")]}),
        (
            "no-listing.json",
            {**original_cache, "pages": [NOTICE.replace("无限售条件", "有限售条件")]},
        ),
    ):
        cache.write_text(json.dumps(content))
        _manifest(
            links,
            {
                "year": 2011,
                "inputs": [{"path": str(source), "sha256": sha256_file(source)}],
                "results": [
                    {
                        **identity,
                        "documents": [
                            {
                                "url": doc["url"],
                                "source_sha256": source_sha,
                                "extraction_sha256": sha256_file(cache),
                            }
                        ],
                    }
                ],
            },
        )
        rejected = run(name, "--explicit-same-day")
        assert rejected["accepted_events"] == 0
        assert rejected["results"][0]["unresolved_documents"]
    cache.write_text(json.dumps(original_cache))
    for name, changed in (
        ("wrong-host.json", {**doc, "url": "https://example.invalid/fixture.PDF"}),
        ("wrong-issuer.json", {**doc, "issuer": "600001"}),
        ("late-published.json", {**doc, "published_on": EX}),
        ("path-escape.json", {**doc, "source_path": "../../escape.pdf"}),
    ):
        _manifest(source, {"documents": [changed]})
        _manifest(
            links,
            {
                "year": 2011,
                "inputs": [{"path": str(source), "sha256": sha256_file(source)}],
                "results": [
                    {
                        **identity,
                        "documents": [
                            {
                                "url": changed["url"],
                                "source_sha256": source_sha,
                                "extraction_sha256": sha256_file(cache),
                            }
                        ],
                    }
                ],
            },
        )
        if name == "wrong-host.json":
            assert run(name, "--explicit-same-day")["accepted_events"] == 0
        else:
            with pytest.raises(ValueError, match="BONUS_SOURCE_IDENTITY_CHANGED"):
                run(name, "--explicit-same-day")
