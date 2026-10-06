"""Fail-closed retained-share terms; exchange/date/lifecycle checks remain separate."""

import re
import unicodedata
from datetime import date
from decimal import Decimal, localcontext

from scripts.audit_p1_orphan_cash_facts import LEGACY_NOT_FINAL
from scripts.audit_p1_retained_cash_sources import NONFINAL_VARIANT, retained_final_title
from scripts.link_distribution_notices import EX_LABEL, LABEL_DATE_GAP, RECORD_LABELS, notice_dates
from scripts.reconcile_distribution_cash import issuer_code_matches, normalized_document


def same_day_listing(pages, symbol, title, record_date, ex_date):
    """Accept only explicit final all-holder credit and unrestricted listing on ex-date.

    This is not a next-session estimate or support for delayed/unknown tradability.
    Other notice layouts remain unresolved until their actual terms are reviewed.
    """
    normalized = normalized_document(pages)
    if (
        not retained_final_title(title)
        or NONFINAL_VARIANT.search(title)
        or LEGACY_NOT_FINAL.search(title)
        or not issuer_code_matches(normalized, symbol)
    ):
        raise ValueError("BONUS_SAME_DAY_FINAL_ISSUER_UNRESOLVED")
    if date.fromisoformat(record_date) >= date.fromisoformat(ex_date) or notice_dates(pages) != (
        [record_date],
        [ex_date],
    ):
        raise ValueError("BONUS_SAME_DAY_RECORD_EX_CONFLICT")
    # Keep page boundaries: a margin/page counter must never complete a date or term.
    text = "§".join(re.sub(r"\s+", "", unicodedata.normalize("NFKC", page)) for page in pages)
    if re.search(
        r"差异化分红送转:是|让渡|重整|缩股|吸收合并|另行公告|拟于|拟实施|B股|H股|"
        r"未确定|待定|另行通知|待通知|取消|撤销|终止|延期|暂停|暂缓|预计|预期|"
        r"拟新增|拟上市|拟转增|拟送|计划(?:本次)?(?:所)?(?:新增|资本公积金转增|转增|送|\(转(?:增)?\))",
        text,
    ):
        raise ValueError("BONUS_SAME_DAY_NONSTANDARD_OR_TENTATIVE")
    dated = r"(20\d{2})年(\d{1,2})月(\d{1,2})日"
    # A weekday annotation supplements a complete date, never supplies one.
    for year, month, day, weekday in re.findall(dated + r"\(星期([^()§。;]{1,4})\)", text):
        try:
            if (
                weekday.replace("天", "日")
                != "一二三四五六日"[date(int(year), int(month), int(day)).weekday()]
            ):
                raise ValueError("BONUS_SAME_DAY_WEEKDAY_CONFLICT")
        except ValueError as exc:
            raise ValueError("BONUS_SAME_DAY_WEEKDAY_CONFLICT") from exc
    patterns = (
        "(?:" + "|".join(RECORD_LABELS) + ")" + LABEL_DATE_GAP + dated,
        EX_LABEL + LABEL_DATE_GAP + dated,
        r"(?:本次(?:(?:权益)?分[派配]|分红派息及资本公积金转增股本)对象为:?(?:截[止至])?|"
        r"(?:^|[。;]|§\d*)(?:\d+[、.]红利发放日:?20\d{2}年\d{1,2}月\d{1,2}日)?"
        r"[一二三四五六七八九十]+、"
        r"分红派息及资本公积金转增股本对象:?截[止至]|"
        r"[一二三四五六七八九十]+、(?:分红派息|利润分配和转增)对象:?截[止至])"
        + dated
        + r"[^。;§]{0,200}?收市后[^。;§]{0,200}?登记在册[^。;§]{0,30}?全体股东",
        r"(?:(?:^|[。;]|§\d*)(?:[一二三四五六七八九十]+、"
        r"(?:转增股本方法|权益分[派配]方法|权益分派办法|"
        r"利润分配和(?:资本公积金)?转增股本方法|分配、转增股份方法|"
        r"分红派息及资本公积金转增股本方法):?)?(?:\d+[、.])?"
        r"本次(?:所|资本公积金)?(?:转增(?:的)?股(?:份)?|送(?:红)?股|新增股份|"
        r"(?:送)?\(转增\)(?:的)?股(?:份)?)|"
        r"(?:^|[。;§]|[一二三四五六七八九十]+、转增股本方法)资本公积金转增的股份)于"
        + dated
        + r"(?:\(星期[一二三四五六日天]\))?直接[记计]入股东证券[账帐]户",
        r"(?:(?:^|[。;§]|[一二三四五六七八九十]+、"
        r"(?:新增股份起始交易日|转增流通股上市日)?|\d+[、.])本次(?:所)?"
        r"(?:转增|送|新增(?:资本公积金转增股本)?|(?:送)?\(转(?:增)?\)股?)(?:的)?"
        r"无限售条件(?:的)?流通股(?:份)?(?:的)?"
        r"(?:起始交易(?:日|时间)|上市流通日)(?:为)?:?|"
        r"(?:^|[。;§])"
        r"(?:[一二三四五六七八九十]+、(?:股权登记日、除权除息日、"
        r"新增无限售条件流通股份上市日和红利发放日|分红派息日期)"
        r"1[、.]股权登记日(?:为)?:?20\d{2}年\d{1,2}月\d{1,2}日"
        r"2[、.]除权除息日(?:为)?:?20\d{2}年\d{1,2}月\d{1,2}日)?"
        r"(?:[一二三四五六七八九十]+、|\d+[、.])?"
        r"新增无限售条件流通股份上市(?:交易)?日:?)" + dated,
    )
    for pattern, expected in zip(
        patterns, (record_date, ex_date, record_date, ex_date, ex_date), strict=True
    ):
        matches = re.findall(pattern, text)
        try:
            values = {date(*map(int, match)).isoformat() for match in matches}
        except ValueError as exc:
            raise ValueError("BONUS_SAME_DAY_DATES_UNRESOLVED") from exc
        if values != {expected}:
            raise ValueError("BONUS_SAME_DAY_DATES_UNRESOLVED")
    return ex_date


def retained_ratio(pages, symbol, *, require_integral_components=False):
    normalized_pages = [unicodedata.normalize("NFKC", page) for page in pages]
    normalized = "\n".join(normalized_pages)
    if not issuer_code_matches(normalized, symbol):
        raise ValueError("BONUS_ISSUER_HEADER_MISMATCH")
    # Keep page boundaries so a page number cannot turn "10" + "2股" into "102股".
    text = "§".join(re.sub(r"\s+", "", page) for page in normalized_pages)
    text = text.replace("每§股", "每股")
    if "每每每每" in text and re.search(r"让渡|重整|转赠|缩股|吸收合并", text):
        raise ValueError("NONSTANDARD_ENTITLEMENT_REQUIRES_REVIEW")
    section = re.search(
        r"[一二三四五六七八九十]+、(?:\d{4}年(?:度)?)?(?:本次实施的)?"
        r"(?:权益分派|利润分配(?:及转增股本|和资本公积金?转增股本)?|"
        r"权益分配、转增股本|"
        r"分配(?:、转增股本)?|分红派息|(?:资本公积金?)?转增股本)方案"
        r"(?!具体实施日期)",
        text,
    )
    if section:
        current = text[section.end() :]
        next_section = re.search(r"[一二三四五六七八九十]+、", current)
        text = current[: next_section.start()] if next_section else current
    # Some final notices misspell 转增 as 转赠 in a heading while stating the
    # actual capital-reserve transfer and holder ratio explicitly in the body.
    if "资本公积金转赠股本" in text and re.search(r"每(?:10|1)?股转增\d+(?:\.\d+)?股", text):
        text = text.replace("资本公积金转赠股本", "资本公积金转增股本")
        text = text.replace("转赠股本实施办法", "转增股本实施办法")
    nonstandard = bool(re.search(r"差异化分红送转:?是|让渡|重整|转赠|缩股|吸收合并", text))
    if "扣税说明" in text:
        start = text.index("扣税说明")
        next_section = re.search(r"[一二三四五六七八九十]、", text[start:])
        text = text[:start] + (text[start + next_section.start() :] if next_section else "")
    if "每每每每" in text and "一、" in text:
        text = text[text.index("一、") :]
    corrected = list(
        re.finditer(
            r"(?:(?:公司)?按(?:公司)?(?:最新|现有)股本计算的"
            r"[^。;]{0,120}?(?:权益分派|利润分配|分配)方案为:?|"
            r"调整后的[^。;]{0,80}?权益分派方案为:?|"
            r"按最新股本总额计算的分配比例为:?|"
            r"方案相应调整为:?|"
            r"分派方案由[^。;]{0,100}?变更为|"
            r"本公司\d{4}年?年度权益分派方案为:?)",
            text,
        )
    )
    if corrected:
        text = text[corrected[-1].end() :]
    components = []
    explicit_values = set()
    conflicting = False
    for patterns in (
        (
            r"每(10|1)?股(?:派送(?:红股|股票)?|送(?:红股|股)?)(?:比例为?)?"
            r"(\d+(?:\.\d+)?)股",
            r"每(10|1)?股送股数:?(\d+(?:\.\d+)?)(?:股)?",
            r"每(10|1)?股派发股票股利(\d+(?:\.\d+)?)股",
            r"向全体股东实施(10|1)股送(\d+(?:\.\d+)?)股",
            r"每(10|1)?股[^。;]{0,80}?送(?:红股|股)?(\d+(?:\.\d+)?)股",
            r"每(10|1)?股[^。;]{0,60}?送(\d+(?:\.\d+)?)股[,、]转增\d+(?:\.\d+)?股",
        ),
        (
            r"每(10|1)?股转增(?:股本|股)?(?:比例为?)?(\d+(?:\.\d+)?)股",
            r"每(10|1)?股转增(?:股数|比例):?(\d+(?:\.\d+)?)(?:股)?",
            r"每(10|1)?股分配比例[^。;]{0,50}?转增(\d+(?:\.\d+)?)股",
            r"每(10|1)?股(?:资本公积金|资本公积|公积金)转增(?:股本)?(\d+(?:\.\d+)?)股",
            r"每(10|1)?股送(?:红股|股)?\d+(?:\.\d+)?股[,、]转增(\d+(?:\.\d+)?)股",
            r"每(10|1)?股[^。;]{0,60}?送\d+(?:\.\d+)?股[,、]转增(\d+(?:\.\d+)?)股",
        ),
    ):
        values = set()
        for pattern in patterns:
            for base, value in re.findall(pattern, text):
                with localcontext() as context:
                    context.prec = 50
                    values.add(Decimal(value) / Decimal(base or "1"))
        explicit_values.update(values)
        conflicting |= len(values) > 1
        components.append(min(values) if values else Decimal(0))
    if not any(components):
        if re.search(
            r"不送(?:红股|股)|无送股和转增|"
            r"不(?:进行)?(?:以|用)?(?:资本公积金?|公积金)?转增",
            text,
        ):
            return Decimal(0)
        unsupported = re.search(
            r"(?:送(?:红股|股)|转增|股票股利)"
            r"[^。;\d]{0,30}\d+(?:\.\d+)?股",
            text,
        )
        if unsupported:
            raise ValueError(
                "NONSTANDARD_ENTITLEMENT_REQUIRES_REVIEW"
                if nonstandard
                else "UNSUPPORTED_BONUS_RATIO"
            )
        raise ValueError("NO_EXPLICIT_BONUS_RATIO")
    if nonstandard:
        raise ValueError("NONSTANDARD_ENTITLEMENT_REQUIRES_REVIEW")
    if require_integral_components and any(
        value != value.to_integral_value() for value in components
    ):
        raise ValueError("FRACTIONAL_COMPONENT_ALLOCATION_UNRESOLVED")
    with localcontext() as context:
        context.prec = 50
        parsed = sum(components, Decimal(0))
        capital_pairs = {
            (int(post.replace(",", "")), int(increase.replace(",", "")))
            for post, increase in re.findall(r"实施后总股本为([\d,]+)股,?增加([\d,]+)股", text)
        }
        if len(capital_pairs) == 1:
            post, increase = next(iter(capital_pairs))
            if 0 < increase < post:
                capital_ratio = Decimal(increase) / Decimal(post - increase)
                correction = "上述分配方案为" in text or "调整后" in text
                if (
                    capital_ratio in explicit_values
                    and (parsed != capital_ratio or conflicting)
                    and (not conflicting or correction)
                ):
                    return capital_ratio
                if parsed != capital_ratio:
                    raise ValueError("BONUS_SHARE_CAPITAL_MISMATCH")
        if conflicting:
            raise ValueError("CONFLICTING_BONUS_COMPONENT")
        return parsed
