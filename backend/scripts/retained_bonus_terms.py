"""Fail-closed retained-share terms; exchange/date/lifecycle checks remain separate."""

import re
import unicodedata
from decimal import Decimal, localcontext

from scripts.reconcile_distribution_cash import issuer_code_matches


def retained_ratio(pages, symbol):
    normalized = unicodedata.normalize("NFKC", "\n".join(pages))
    if not issuer_code_matches(normalized, symbol):
        raise ValueError("BONUS_ISSUER_HEADER_MISMATCH")
    text = re.sub(r"\s+", "", normalized)
    if re.search(r"差异化|让渡|重整|转赠|缩股|吸收合并", text):
        raise ValueError("NONSTANDARD_ENTITLEMENT_REQUIRES_REVIEW")
    components = []
    for patterns in (
        (
            r"每(10|1)?股(?:派送(?:红股|股票)?|送(?:红股|股)?)(?:比例为?)?"
            r"(\d+(?:\.\d+)?)股",
            r"每(10|1)?股送股数:?(\d+(?:\.\d+)?)(?:股)?",
        ),
        (
            r"每(10|1)?股转增(?:股本)?(?:比例为?)?(\d+(?:\.\d+)?)股",
            r"每(10|1)?股转增(?:股数|比例):?(\d+(?:\.\d+)?)(?:股)?",
            r"每(10|1)?股分配比例[^。;]{0,50}?转增(\d+(?:\.\d+)?)股",
        ),
    ):
        values = set()
        for pattern in patterns:
            for base, value in re.findall(pattern, text):
                with localcontext() as context:
                    context.prec = 50
                    values.add(Decimal(value) / Decimal(base or "1"))
        if len(values) > 1:
            raise ValueError("CONFLICTING_BONUS_COMPONENT")
        components.append(next(iter(values)) if values else Decimal(0))
    if not any(components):
        raise ValueError("NO_EXPLICIT_BONUS_RATIO")
    with localcontext() as context:
        context.prec = 50
        return sum(components, Decimal(0))
