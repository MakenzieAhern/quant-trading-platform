"""Derived date-only context for an explicit original/correction chain, never event authority."""

import re
from datetime import date
from urllib.parse import urlsplit

from app.data.catalog.checksums import canonical_sha256
from scripts.audit_p1_retained_cash_sources import retained_final_title
from scripts.link_distribution_notices import compact_document, current_notice_dates
from scripts.reconcile_distribution_cash import issuer_code_matches

DATED = r"20\d{2}年\d{1,2}月\d{1,2}日"
FIELDS = ("股权登记日", "除权除息日", "现金红利发放日", "新增股份上市日")
PAIR = re.compile(r"(" + "|".join(FIELDS) + r"):(" + DATED + r")\1:(" + DATED + ")")


def iso_date(value):
    return date(*map(int, re.findall(r"\d+", value))).isoformat()


def timing_corrected_context(original_pages, correction_pages, original, correction):
    """Caller must verify raw PDF/cache checksums; retain both originals and this derived view."""
    symbol = original["issuer"]
    for source, pages in ((original, original_pages), (correction, correction_pages)):
        url = urlsplit(source["url"])
        expected = r"/finalpage/" + re.escape(source["published_on"]) + r"/\d+\.[Pp][Dd][Ff]"
        if (
            source["issuer"] != symbol
            or not pages
            or not issuer_code_matches(pages[0], symbol)
            or url.scheme != "https"
            or url.netloc != "static.cninfo.com.cn"
            or not re.fullmatch(expected, url.path)
            or url.query
            or url.fragment
            or not re.fullmatch(r"[0-9a-f]{64}", source["source_sha256"])
        ):
            raise ValueError("TIMING_CORRECTION_SOURCE_UNRESOLVED")
    if (
        not retained_final_title(original["title"])
        or not correction["title"].endswith("更正公告")
        or original["source_sha256"] == correction["source_sha256"]
        or not date.fromisoformat(original["published_on"])
        < date.fromisoformat(correction["published_on"])
    ):
        raise ValueError("TIMING_CORRECTION_SOURCE_UNRESOLVED")
    pages = [compact_document(page) for page in original_pages]
    corrected = [compact_document(page) for page in correction_pages]
    text = "§".join(corrected)
    references = re.findall(r"于(" + DATED + r")在[^《§]{1,80}公告了(?:公司)?《([^》§]+)》", text)
    if len(references) != 1 or references[0][1] != compact_document(original["title"]):
        raise ValueError("TIMING_CORRECTION_REFERENCE_UNRESOLVED")
    if iso_date(references[0][0]) != original["published_on"]:
        raise ValueError("TIMING_CORRECTION_REFERENCE_UNRESOLVED")
    tables = re.findall(r"更正前更正后([^§]+?)2、原公告", text)
    if len(tables) != 1:
        raise ValueError("TIMING_CORRECTION_TABLE_UNRESOLVED")
    pairs = list(PAIR.finditer(tables[0]))
    if (
        len(pairs) != len(FIELDS)
        or {match[1] for match in pairs} != set(FIELDS)
        or "".join(match[0] for match in pairs) != tables[0]
    ):
        raise ValueError("TIMING_CORRECTION_TABLE_UNRESOLVED")
    changes = []

    def replace_exact(before, after, role):
        if sum(page.count(before) for page in pages) != 1:
            raise ValueError("TIMING_CORRECTION_ORIGINAL_CONTENT_UNRESOLVED")
        pages[:] = [page.replace(before, after) for page in pages]
        changes.append(dict(role=role, before=before, after=after))

    fields = {}
    date_pairs = set()
    for match in pairs:
        label, before, after = match.groups()
        fields[label] = iso_date(after)
        date_pairs.add((iso_date(before), iso_date(after)))
        replace_exact(label + ":" + before, label + ":" + after, label)
    quoted_matches = list(re.finditer(r"中“([^”§]+)”[,]?现更正为:?“([^”§]+)”", text))
    quoted = [match.groups() for match in quoted_matches]
    if len(quoted) != 2 or text.count("现更正为") != len(quoted):
        raise ValueError("TIMING_CORRECTION_QUOTED_CONTENT_UNRESOLVED")
    # Consume the whole amendment body, not only recognizable dates: an extra
    # amount/ratio/holder change must never silently become a date-only context.
    bodies = text.split("更正内容如下:")
    intro = re.fullmatch(
        r"(?:更正公告)?证券代码:"
        + re.escape(symbol)
        + r"证券简称:[\u4e00-\u9fff]{1,30}编号:20\d{2}-\d+"
        r"(?:(?P<company>[\u4e00-\u9fff]{2,60}股份有限公司)更正公告"
        r"(?P=company)\(以下简称“公司”\)|公司)于"
        + DATED
        + r"在(?:中国证监会)?指定的网站公告了公司《"
        + re.escape(compact_document(original["title"]))
        + r"》,(?:经核查发现公告中由于工作人员的疏忽存在部分笔误,)?",
        bodies[0],
    )
    if len(bodies) != 2 or not intro:
        raise ValueError("TIMING_CORRECTION_UNCONSUMED_CONTENT")
    company = intro["company"]
    signature = r"1§更正公告" + re.escape(company) + "董事会" + DATED + "2" if company else r"(?!)"
    body_pattern = (
        r"1、原公告第一页“三、分红派息日期”需进行更正,详细如下表:更正前更正后"
        + re.escape(tables[0])
        + r"2、原公告第一页“四、权益分派对象”"
        + re.escape(quoted_matches[0][0])
        + r"。3、原公告第二页“五、权益分派方法”"
        + re.escape(quoted_matches[1][0])
        + r"。(?:公司今后将加强对外披露公告的核查力度,避免类似错误再次发生。"
        r"本公司对以上错误给投资者带来的不便深表歉意。)?(?:特此公告。)?" + "(?:" + signature + ")?"
    )
    if len(bodies) != 2 or not re.fullmatch(body_pattern, bodies[1]):
        raise ValueError("TIMING_CORRECTION_UNCONSUMED_CONTENT")
    for before, after in quoted:
        old, new = re.findall(DATED, before), re.findall(DATED, after)
        if (
            len(old) != 1
            or len(new) != 1
            or re.sub(DATED, "DATE", before) != re.sub(DATED, "DATE", after)
            or (iso_date(old[0]), iso_date(new[0])) not in date_pairs
        ):
            raise ValueError("TIMING_CORRECTION_NON_DATE_OR_CONFLICTING_CHANGE")
        replace_exact(before, after, "EXPLICIT_QUOTED_DATE_CHANGE")
    if re.search(
        r"每(?:10|1)?股|取消|撤销|终止|延期|暂停|暂缓|待定|预计|拟于|"
        r"让渡|重整|缩股|吸收合并",
        text,
    ):
        raise ValueError("TIMING_CORRECTION_NON_DATE_OR_CONFLICTING_CHANGE")
    record, ex, cash, listed = (fields[label] for label in FIELDS)
    if (
        not correction["published_on"] <= record < ex <= cash
        or listed < ex
        or current_notice_dates(pages, correction["published_on"]) != ([record], [ex])
    ):
        raise ValueError("TIMING_CORRECTION_DATE_ORDER_UNRESOLVED")
    return dict(
        scope="DERIVED_DATE_ONLY_CONTEXT_NOT_RAW_SOURCE_OR_EVENT_ADMISSION",
        derived_pages=pages,
        changes=changes,
        available_on=correction["published_on"],
        record_date=record,
        ex_date=ex,
        cash_pay_date=cash,
        declared_listing_date=listed,
        original_document=original,
        correction_document=correction,
        original_text_sha256=canonical_sha256(original_pages),
        correction_text_sha256=canonical_sha256(correction_pages),
        derived_text_sha256=canonical_sha256(pages),
        event_admitted=False,
    )
