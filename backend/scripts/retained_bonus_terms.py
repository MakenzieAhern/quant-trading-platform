"""Fail-closed retained-share terms; exchange/date/lifecycle checks remain separate."""

import re
import unicodedata
from decimal import Decimal, localcontext


def retained_ratio(pages, symbol):
    normalized = unicodedata.normalize("NFKC", "\n".join(pages))
    header = re.search(r"(?:证券|股票)代码\s*:\s*(\d{6})(?!\d)", normalized[:600])
    if not header or header[1] != symbol:
        raise ValueError("BONUS_ISSUER_HEADER_MISMATCH")
    text = re.sub(r"\s+", "", normalized)
    if re.search(r"差异化|让渡|重整|转赠|缩股|吸收合并", text):
        raise ValueError("NONSTANDARD_ENTITLEMENT_REQUIRES_REVIEW")
    components = []
    for verb in (r"(?:派送|送)(?:红股)?", r"转增(?:股本)?"):
        values = set()
        for base, value in re.findall(r"每(10|1)股" + verb + r"(\d+(?:\.\d+)?)股", text):
            with localcontext() as context:
                context.prec = 50
                values.add(Decimal(value) / Decimal(base))
        if len(values) > 1:
            raise ValueError("CONFLICTING_BONUS_COMPONENT")
        components.append(next(iter(values)) if values else Decimal(0))
    if not any(components):
        raise ValueError("NO_EXPLICIT_BONUS_RATIO")
    with localcontext() as context:
        context.prec = 50
        return sum(components, Decimal(0))
