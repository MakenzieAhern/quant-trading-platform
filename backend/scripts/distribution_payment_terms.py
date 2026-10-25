"""Explicit issuer-declared cash payment date, not proof of actual holder receipts."""

import re
import unicodedata
from datetime import date

from scripts.audit_p1_retained_cash_sources import NONFINAL_VARIANT, retained_final_title
from scripts.link_distribution_notices import labeled_dates, notice_dates
from scripts.reconcile_distribution_cash import issuer_code_matches

DATED = r"20[0-9]{2}年[0-9]{1,2}月[0-9]{1,2}日"
PAYMENT_LABEL = re.compile(r"现金红利发放日[:为]*(?P<day>" + DATED + r")")
FULL_PAYER = "中国证券登记结算有限责任公司深圳分公司"
SHORT_PAYER = "中国结算深圳分公司"
PAYMENT = re.compile(
    r"(?:^|(?<=[。;§]))(?:[0-9]+[、.])?本公司此次委托"
    + r"(?P<payer>"
    + FULL_PAYER
    + "|"
    + SHORT_PAYER
    + r")"
    r"代派的股息将于(?P<day>" + DATED + r")通过股东托管证券公司"
    r"(?:\(或其他托管机构\))?直接划入其资金[账帐]户[。;]"
)
UNCERTAIN = re.compile(
    r"假设|假如|如果|如遇|如未|如需|如有|若|倘|示例|例如|原定|原计划|原方案|"
    r"拟于|拟实施|预计|预期|暂定|待定|计划于|尚未确定|未确定|待通知|"
    r"尚未通知|尚未公告|仅供参考|仅适用|仅限|部分股东|部分投资者|"
    r"历史方案|历史文件|模拟|非实际|并非|另行|延期|暂停|暂缓|取消|撤销|终止|"
    r"不发放|不支付|不适用|不会"
)


def compact(text: str) -> str:
    return re.sub(r"\s+", "", unicodedata.normalize("NFKC", text))


def dated(value: str) -> str:
    return date(*map(int, re.findall(r"[0-9]+", value))).isoformat()


def cash_payment_date(
    pages: list[str], symbol: str, title: str, record_date: str, ex_date: str
) -> str:
    """Caller binds source bytes; only the reviewed SZSE agency-payment layout is supported."""
    if (
        not pages
        or not re.fullmatch(r"[0-9]{6}", symbol)
        or not retained_final_title(title)
        or NONFINAL_VARIANT.search(title)
        or not issuer_code_matches(pages[0], symbol)
        or re.match(
            r"证券代码:" + re.escape(symbol) + r"(?:证券简称:[\u4e00-\u9fffA-Za-z*]{1,30})?"
            r"(?:公告编号:?[0-9]{4}-[0-9]+)?"
            r"(?:[\u4e00-\u9fff]{2,80}股份有限公司)?"
            + re.escape(compact(title))
            + r"(?=本公司|重要(?:内容)?提示|[一二三四五六七八九十]+、|[0-9]+[、.]|"
            r"股权登记日|除权除息日|现金红利发放日|$)",
            compact(pages[0]),
        )
        is None
    ):
        raise ValueError("CASH_PAYMENT_FINAL_ISSUER_UNRESOLVED")
    record, ex = date.fromisoformat(record_date), date.fromisoformat(ex_date)
    page_dates = [notice_dates([page]) for page in pages]
    if (
        record.isoformat() != record_date
        or ex.isoformat() != ex_date
        or record >= ex
        or notice_dates(pages) != ([record_date], [ex_date])
        or {value for records, _ in page_dates for value in records} != {record_date}
        or {value for _, ex_days in page_dates for value in ex_days} != {ex_date}
    ):
        raise ValueError("CASH_PAYMENT_EVENT_DATES_UNRESOLVED")
    # A page boundary can never complete a date or turn separate clauses into one.
    text = "§".join(compact(page) for page in pages)
    if UNCERTAIN.search(text):
        raise ValueError("CASH_PAYMENT_NONFINAL_OR_CONDITIONAL")
    labels = list(PAYMENT_LABEL.finditer(text))
    if not labels or len(labels) != text.count("现金红利发放日"):
        raise ValueError("CASH_PAYMENT_LABEL_UNRESOLVED")
    declared = {dated(match["day"]) for match in labels}
    # Reuse the established label parser, but only inside each complete page.
    extracted = {value for page in pages for value in labeled_dates(page, r"现金红利发放日")}
    if len(declared) != 1 or declared != extracted:
        raise ValueError("CASH_PAYMENT_LABEL_CONFLICT")
    payments = list(PAYMENT.finditer(text))
    if len(payments) != 1:
        raise ValueError("CASH_PAYMENT_AGENCY_CLAUSE_UNRESOLVED")
    payment = payments[0]
    if (
        payment["payer"] == SHORT_PAYER
        and (FULL_PAYER + "(以下简称“" + SHORT_PAYER + "”)") not in text
    ):
        raise ValueError("CASH_PAYMENT_AGENCY_ALIAS_UNRESOLVED")
    result = dated(payment["day"])
    if declared != {result} or result < ex_date:
        raise ValueError("CASH_PAYMENT_DATE_CONFLICT")
    remaining = PAYMENT_LABEL.sub("", PAYMENT.sub("", text))
    if re.search(
        r"代派|派息日|支付日|(?:现金红利|股息)(?:将于|于)|"
        r"(?:现金|股息|股利|红利)[^。;§]{0,30}(?:支付|到账|划入|发放)|"
        r"(?:个人|机构|其余|部分)(?:投资者|股东)[^。;§]{0,30}"
        + DATED
        + r"[^。;§]{0,20}(?:领取|收到|到账|支付|派发|发放|划入)",
        remaining,
    ):
        raise ValueError("CASH_PAYMENT_UNCONSUMED_PAYMENT_CLAUSE")
    return result
