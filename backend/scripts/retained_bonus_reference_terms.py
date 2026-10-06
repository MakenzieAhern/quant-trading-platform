"""Issuer-declared ex-price inputs, separate from ordinary-holder entitlements."""

import re
import unicodedata
from decimal import Context, Decimal, localcontext

from scripts.audit_p1_retained_cash_sources import NONFINAL_VARIANT, retained_final_title
from scripts.link_distribution_notices import notice_dates
from scripts.reconcile_distribution_cash import issuer_code_matches, normalized_document


def repurchase_reference_basis(pages, symbol, title, record_date, ex_date):
    """Require an explicit numeric final formula; never infer inputs from observed prices."""
    if (
        not retained_final_title(title)
        or NONFINAL_VARIANT.search(title)
        or not issuer_code_matches(normalized_document(pages), symbol)
        or record_date >= ex_date
        or notice_dates(pages) != ([record_date], [ex_date])
    ):
        raise ValueError("REFERENCE_FINAL_ISSUER_DATES_UNRESOLVED")
    # A margin/page boundary cannot manufacture a number or complete a formula.
    text = "§".join(re.sub(r"\s+", "", unicodedata.normalize("NFKC", p)) for p in pages)
    if (
        not re.search(r"回购[^。;§]{0,100}?不参与", text)
        or not re.search(r"按[^。;§]{0,60}?总股本[^。;§]{0,60}?折算", text)
        or re.search(r"差异化分红送转:?是|让渡|重整|缩股|吸收合并|B股|H股", text)
    ):
        raise ValueError("REFERENCE_REPURCHASE_BASIS_UNRESOLVED")
    price = (
        r"(?:股权登记日收盘价(?:格)?|"
        r"除权除息日(?:的)?(?:前一交易日|前一日|前一|前)?收盘价(?:格)?)"
    )
    pattern = (
        r"=\(" + price + r"-(\d+(?:\.\d+)?)(?:元(?:/股)?)?\)"
        r"(?:÷|/)(?:\(1\+(\d+(?:\.\d+)?)\)|(\d+(?:\.\d+)?))"
        r"(?=[。;]|$)"
    )
    matches = list(re.finditer(pattern, text))
    symbolic = (
        r"(?:=\(" + price + r"-(?:每股现金红利|按资本公积金转增前总股本折算每股现金分红)\)"
        r"(?:÷|/)\(1\+(?:股份变动比例|按资本公积金转增前总股本折算的每股股份变动比例)\))?"
    )
    implemented = (
        r"(?:(?:综上,在保证本次权益分派方案不变的前提下,|公司)"
        r"20\d{2}年?年度权益分派实施后的除权除息价格"
        r"按照上述原则及计算方式执行,即|\d+[、.])?"
        r"(?:本次)?权益分派实施后(?:的)?除权除息(?:参考)?价(?:格)?" + symbolic
    )
    authorized = []
    header = re.match(
        r"证券代码:" + re.escape(symbol) + r"证券简称:[^。;§]{1,40}?公告编号:\d{4}-\d+",
        text,
    )
    for match in matches:
        # Only the final implemented ex-price declaration authorizes its equation.
        start = max(text.rfind(boundary, 0, match.start()) for boundary in ("。", ";", "§"))
        declaration = text[start + 1 : match.start()]
        if start >= 0 and text[start] == "§" and header:
            declaration = declaration.removeprefix(header[0])
        if re.fullmatch(implemented, declaration):
            authorized.append(match)
    if not authorized:
        raise ValueError("REFERENCE_IMPLEMENTED_DECLARATION_UNRESOLVED")
    with localcontext(Context(prec=50)):
        values = {(Decimal(m[1]), Decimal(m[2]) if m[2] else Decimal(m[3]) - 1) for m in matches}
    if len(values) != 1:
        raise ValueError("REFERENCE_NUMERIC_FORMULA_MISSING_OR_CONFLICTING")
    cash, ratio = next(iter(values))
    if cash < 0 or ratio <= 0:
        raise ValueError("REFERENCE_NUMERIC_FORMULA_INVALID")
    return {
        "cash_per_total_old_share": str(cash),
        "share_ratio_per_total_old_share": str(ratio),
        "basis": "ISSUER_EXPLICIT_TOTAL_CAPITAL_REPURCHASE_EXCLUDED",
        "formulas": sorted({m[0] for m in authorized}),
        "changes_holder_entitlements": False,
    }
