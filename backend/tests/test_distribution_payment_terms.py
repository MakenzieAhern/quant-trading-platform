"""Synthetic source-text boundaries; real cached PDFs are checked separately."""

import pytest

from scripts.distribution_payment_terms import FULL_PAYER, SHORT_PAYER, cash_payment_date

TITLE = "2010年度权益分派实施公告"
RECORD = "2011-05-05"
EX = "2011-05-06"
LABEL = "现金红利发放日:2011年5月6日"
CLAUSE = (
    "2、本公司此次委托中国结算深圳分公司代派的股息将于2011年05月06日通过"
    "股东托管证券公司(或其他托管机构)直接划入其资金账户。"
)


def source(symbol="300155"):
    return [
        f"证券代码:{symbol}\n证券简称:测试\n公告编号:2011-037\n{TITLE}\n"
        "股权登记日:2011年5月5日。除权除息日:2011年5月6日。"
        + LABEL
        + "。每10股派发现金红利8元(含税)。",
        "三、利润分配方案具体实施日期\n1、股权登记日:2011年5月5日。"
        "2、除权除息日:2011年5月6日。3、"
        + LABEL
        + "。四、分派对象\n在"
        + FULL_PAYER
        + "(以下简称“"
        + SHORT_PAYER
        + "”)登记在册的全体股东。五、分配实施办法\n"
        "1、本次所(转增)股于2011年05月06日直接记入股东证券账户。"
        + CLAUSE
        + "六、本次所(转增)的无限售条件流通股起始交易日为2011年05月06日。",
    ]


def parse(pages, **kwargs):
    return cash_payment_date(
        pages,
        kwargs.get("symbol", "300155"),
        kwargs.get("title", TITLE),
        kwargs.get("record_date", RECORD),
        kwargs.get("ex_date", EX),
    )


def test_matching_repeated_labels_and_actual_agency_clause():
    assert parse(source()) == EX
    assert parse(source("000001"), symbol="000001") == EX
    pages = source()
    pages[1] = pages[1].replace(CLAUSE, CLAUSE.replace(SHORT_PAYER, FULL_PAYER))
    assert parse(pages) == EX


def test_later_explicit_payment_is_not_replaced_with_ex_date():
    pages = [page.replace(LABEL, LABEL.replace("5月6日", "5月9日")) for page in source()]
    pages[1] = pages[1].replace("股息将于2011年05月06日", "股息将于2011年05月09日")
    assert parse(pages) == "2011-05-09"


def test_whitespace_and_fullwidth_punctuation_do_not_change_terms():
    pages = [
        page.replace(":", "\uff1a").replace("(", "\uff08").replace(")", "\uff09")
        for page in source()
    ]
    pages[1] = pages[1].replace("2011年05月06日通过", "2011 年 05 月 06 日 通\n过")
    assert parse(pages) == EX


@pytest.mark.parametrize(
    "kwargs",
    [
        {"symbol": "300147"},
        {"symbol": "3001550"},
        {"title": "2010年度利润分配预案"},
        {"title": "董事会权益分派实施公告"},
        {"title": "2011年度权益分派实施公告"},
        {"record_date": "2011-05-04"},
        {"record_date": "2011-05-06"},
        {"ex_date": "2011-05-07"},
        {"ex_date": "2011-5-6"},
    ],
)
def test_issuer_title_and_event_dates_are_bound(kwargs):
    with pytest.raises(ValueError):
        parse(source(), **kwargs)


def test_quoted_other_title_does_not_replace_actual_notice_title():
    pages = source()
    pages[0] += "本次公告引用《2099年度权益分派实施公告》。"
    with pytest.raises(ValueError, match="ISSUER"):
        parse(pages, title="2099年度权益分派实施公告")


@pytest.mark.parametrize("suffix", ["(草案)", "(征求意见稿)", "补充说明"])
def test_actual_title_must_end_before_body_not_a_qualifying_suffix(suffix):
    pages = source()
    pages[0] = pages[0].replace(TITLE, TITLE + suffix)
    with pytest.raises(ValueError, match="ISSUER"):
        parse(pages)


def test_holder_tax_amount_is_not_a_separate_payment_date():
    pages = source()
    pages[0] += (
        "每10股派发现金红利8元(含税,扣税后个人、证券投资基金、"
        "合格境外机构投资者实际每10股派现金红利7.2元),共计派发股利576,000,000元。"
    )
    assert parse(pages) == EX


@pytest.mark.parametrize(
    "change",
    [
        "no_pages",
        "no_labels",
        "no_clause",
        "no_alias",
        "wrong_branch",
        "no_date",
        "no_account",
        "conflicting_labels",
        "conflicting_clause",
        "duplicate_clause",
    ],
)
def test_missing_or_inconsistent_terms_are_not_guessed(change):
    pages = source()
    if change == "no_pages":
        pages = []
    elif change == "no_labels":
        pages = [page.replace(LABEL, "") for page in pages]
    elif change == "no_clause":
        pages[1] = pages[1].replace(CLAUSE, "")
    elif change == "no_alias":
        pages[1] = pages[1].replace("(以下简称“" + SHORT_PAYER + "”)", "")
    elif change == "wrong_branch":
        pages[1] = pages[1].replace("深圳分公司", "上海分公司")
    elif change == "no_date":
        pages[1] = pages[1].replace("股息将于2011年05月06日", "股息将于")
    elif change == "no_account":
        pages[1] = pages[1].replace("直接划入其资金账户", "进行处理")
    elif change == "conflicting_labels":
        pages[1] = pages[1].replace(LABEL, LABEL.replace("5月6日", "5月9日"))
    elif change == "conflicting_clause":
        pages[1] = pages[1].replace("股息将于2011年05月06日", "股息将于2011年05月09日")
    else:
        pages[1] += CLAUSE
    with pytest.raises(ValueError):
        parse(pages)


@pytest.mark.parametrize(
    "phrase",
    ["预计", "暂定", "拟于", "如果条件满足,", "假设", "原定", "例如", "若获得批准,", "另行公告"],
)
@pytest.mark.parametrize("where", ["document", "clause"])
def test_tentative_and_counterfactual_terms_fail_closed(phrase, where):
    pages = source()
    if where == "document":
        pages[0] = phrase + pages[0]
    else:
        pages[1] = pages[1].replace(CLAUSE, phrase + CLAUSE)
    with pytest.raises(ValueError):
        parse(pages)


@pytest.mark.parametrize("split", ["2011年05月", "股息将于", "直接划入其资金"])
def test_payout_clause_cannot_be_completed_across_pages(split):
    pages = source()
    offset = pages[1].index(split, pages[1].index("2、本公司")) + len(split)
    pages[1:] = [pages[1][:offset], pages[1][offset:]]
    with pytest.raises(ValueError):
        parse(pages)


def test_partial_label_cannot_be_hidden_by_another_complete_label():
    pages = source()
    offset = pages[0].index("2011年5月6日", pages[0].index("现金红利发放日")) + len("2011年5月")
    pages[:1] = [pages[0][:offset], pages[0][offset:]]
    with pytest.raises(ValueError, match="LABEL_UNRESOLVED"):
        parse(pages)


@pytest.mark.parametrize(
    "label,day", [("股权登记日", "2011年5月5日"), ("除权除息日", "2011年5月6日")]
)
def test_record_and_ex_dates_cannot_be_completed_across_pages(label, day):
    pages = source()
    pages[1] = pages[1].replace(label + ":" + day + "。", "")
    offset = pages[0].index(day, pages[0].index(label)) + len("2011年5月")
    pages[:1] = [pages[0][:offset], pages[0][offset:]]
    with pytest.raises(ValueError, match="EVENT_DATES"):
        parse(pages)


@pytest.mark.parametrize(
    "extra",
    [
        "现金红利于2011年5月9日到账。",
        "现金红利实际发放日为2011年5月9日。",
        "股息支付日为2011年5月9日。",
        "其余股东另行支付。",
        "上述股息安排仅适用于机构投资者,个人投资者于2011年5月9日领取。",
        "上述日期仅供参考,实际执行时间尚未通知。",
        "个人投资者于2011年5月9日领取。",
    ],
)
def test_unconsumed_payment_changes_are_not_ignored(extra):
    pages = source()
    pages[1] += extra
    with pytest.raises(ValueError):
        parse(pages)


@pytest.mark.parametrize("day", ["2011年2月30日", "2011年13月6日", "2011年5月4日"])
def test_invalid_or_pre_ex_payment_day_fails(day):
    pages = [page.replace(LABEL, "现金红利发放日:" + day) for page in source()]
    pages[1] = pages[1].replace("股息将于2011年05月06日", "股息将于" + day)
    with pytest.raises(ValueError):
        parse(pages)
