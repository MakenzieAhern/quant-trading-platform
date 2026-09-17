"""Fail-closed retained-share terms; exchange/date/lifecycle checks remain separate."""

import re
import unicodedata
from decimal import Decimal, localcontext

from scripts.reconcile_distribution_cash import issuer_code_matches


def retained_ratio(pages, symbol):
    normalized_pages = [unicodedata.normalize("NFKC", page) for page in pages]
    normalized = "\n".join(normalized_pages)
    if not issuer_code_matches(normalized, symbol):
        raise ValueError("BONUS_ISSUER_HEADER_MISMATCH")
    # Keep page boundaries so a page number cannot turn "10" + "2股" into "102股".
    text = "§".join(re.sub(r"\s+", "", page) for page in normalized_pages)
    text = text.replace("每§股", "每股")
    # Some final notices misspell 转增 as 转赠 in a heading while stating the
    # actual capital-reserve transfer and holder ratio explicitly in the body.
    if "资本公积金转赠股本" in text and re.search(r"每(?:10|1)?股转增\d+(?:\.\d+)?股", text):
        text = text.replace("资本公积金转赠股本", "资本公积金转增股本")
        text = text.replace("转赠股本实施办法", "转增股本实施办法")
    if re.search(r"差异化分红送转:?是|让渡|重整|转赠|缩股|吸收合并", text):
        raise ValueError("NONSTANDARD_ENTITLEMENT_REQUIRES_REVIEW")
    if "每每每每" in text and "一、" in text:
        text = text[text.index("一、") :]
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
            r"每(10|1)?股[^。;]{0,60}?送(\d+(?:\.\d+)?)股[,、]转增\d+(?:\.\d+)?股",
        ),
        (
            r"每(10|1)?股转增(?:股本)?(?:比例为?)?(\d+(?:\.\d+)?)股",
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
        raise ValueError("NO_EXPLICIT_BONUS_RATIO")
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
