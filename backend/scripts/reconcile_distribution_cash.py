"""Reconcile explicit gross-cash terms to exchange rows; never assume missing terms."""

import argparse
import json
import re
import unicodedata
from collections import Counter, defaultdict
from decimal import ROUND_HALF_UP, Decimal, localcontext
from pathlib import Path

from app.data.catalog.checksums import canonical_json_bytes, canonical_sha256, sha256_file
from app.data.catalog.freeze import write_immutable
from app.domain.markets.corporate_actions import CorporateAction, require_supported_corporate_action


def issuer_code_matches(normalized, symbol):
    header = re.search(
        r"(?:(?:A\s*股|证\s*(?:券|劵)|(?<!债)券|股\s*票|公\s*司)\s*){1,4}"
        r"(?:(?:代\s*码|代\s*号|号\s*码)\s*){1,4}"
        r"(?:\(A/H\))?\s*:?\s*([^\n]{0,120})",
        normalized,
    )
    code_field = re.split(r"简称|编号|债券代码", header[1], maxsplit=1)[0] if header else ""
    exact = re.search(r"(?<!\d)" + r"[ \t]*".join(symbol) + r"(?!\d)", code_field)
    digits = re.sub(r"\D", "", code_field)
    repeated = len(digits) in (12, 18, 24) and digits == symbol * (len(digits) // 6)
    doubled = "".join(character * 2 for character in symbol) in digits
    leading = re.match(r"^\s*" + r"[ \t]*".join(symbol) + r"(?:\s+|\n)", normalized)
    visible_header = normalized[:1200]
    compact_visible = re.sub(r"\s+", "", visible_header)
    labeled_spaced = re.match(
        r"^\s*(?:证券|股票)\s*代码\s*:?\s*" + r"\s*".join(symbol) + r"(?!\d)",
        visible_header,
    )
    compact_codes = set(re.findall(r"(?:证券|股票)代码:?([036]\d{5})(?!\d)", compact_visible))
    compact_labeled = compact_codes == {symbol}
    doubled_visible = "代代码码" in visible_header and (
        "".join(character * 2 for character in symbol) in re.sub(r"\D", "", visible_header)
    )
    leading_visible = re.match(r"^\s*(?:\d{1,2}\s+)?" + symbol + r"(?:\s+|$)", visible_header)
    standalone_visible = re.search(r"(?m)^\s*" + symbol + r"\s*$", visible_header)
    return bool(
        exact
        or repeated
        or doubled
        or labeled_spaced
        or compact_labeled
        or doubled_visible
        or leading_visible
        or standalone_visible
        or (len(digits) == 12 and digits.startswith(symbol))
        or leading
    )


def normalized_document(pages):
    normalized_pages = [unicodedata.normalize("NFKC", p) for p in pages]
    if len(pages) > 1:
        counters_removed = False
        for template in (r"{page}", r"{page}\s*/\s*{total}", r"-\s*{page}\s*-"):
            counters = [
                re.match(r"^\s*" + template.format(page=i, total=len(pages)) + r"[ \t]*\n", p)
                for i, p in enumerate(normalized_pages, 1)
            ]
            if all(counters):
                normalized_pages = [
                    p[m.end() :] for p, m in zip(normalized_pages, counters, strict=True)
                ]
                counters_removed = True
                break
        if not counters_removed:
            counters = [
                re.match(r"^\s*(?:\d+\s*/\s*\d+|-\s*\d+\s*-|\d{1,3})[ \t]*\n", page)
                for page in normalized_pages
            ]
            if all(counters):
                numbers = [int(re.search(r"\d+", match[0])[0]) for match in counters]
                repeated_margin = len(set(numbers)) == 1 and numbers[0] > len(pages)
                reset_footer = (
                    len(pages) >= 4
                    and numbers[:-1] == list(range(1, len(pages)))
                    and numbers[-1] == 2
                    and not re.search(r"每(?:10|1)?股|现金红利|现金股利", normalized_pages[-1])
                )
                if not (repeated_margin or reset_footer):
                    raise ValueError("INVALID_PAGE_COUNTER_SEQUENCE")
    return "\n".join(normalized_pages)


def differentiated_cash(pages, symbol, title):
    normalized = normalized_document(pages)
    if not issuer_code_matches(normalized, symbol):
        raise ValueError("CONFLICTING_AUTHORITY")
    text = re.sub(r"\s+", "", normalized)
    if "差异化分红送转:是" not in text:
        raise ValueError("CONFLICTING_AUTHORITY")
    if not re.search(r"实施|权益分派(?:的)?公告$|利润分配公告$", title):
        raise ValueError("MISSING_FINAL_IMPLEMENTATION_TERMS")
    match = re.search(r"(?:每股)?分配比例(.{0,500}?)(?:相关日期|差异化分红送转)", text)
    if not match:
        raise ValueError("MISSING_FINAL_IMPLEMENTATION_TERMS")
    summary = match[1]
    per_share = r"每股(?:实际)?(?:分派|分配|派发)?现金红利(?:人民币)?(\d+(?:\.\d+)?)元"
    per_ten = (
        r"每10股(?:派发|派送|分配|分派|派)?(?:现金红利|现金股利)?"
        r"(?:人民币)?(\d+(?:\.\d+)?)元"
    )
    public_label = (
        r"(?:社会公众股(?:股东)?|无限售(?:条件)?(?:流通)?(?:A股|股)?股东|"
        r"流通A股股东|普通A股股东|A股公众股东|中小股东|境内上市人民币普通股股东|"
        r"持有首次公开发行A股股票的流通股股东|流通股股东)"
    )

    def amounts_for(prefix):
        return [
            Decimal(value) for value in re.findall(prefix + r".{0,30}?" + per_share, summary)
        ] + [
            Decimal(value) / Decimal(10)
            for value in re.findall(prefix + r".{0,30}?" + per_ten, summary)
        ]

    leading = re.match(
        r"[,\uff0c\u3001]?(?:每股转增比例)?(A股)?" + per_share,
        summary,
    )
    if leading and (leading[1] or len(set(amounts_for(""))) == 1):
        if not any(
            marker in text for marker in ("含税", "税前", "暂不扣缴个人所得税", "暂不扣缴所得税")
        ):
            raise ValueError("MISSING_FINAL_IMPLEMENTATION_TERMS")
        return Decimal(leading[2])

    special = (
        r"控股股东|实际控制人|国有股东|法人发起人|限售(?:条件)?(?:A股|股)?股东|"
        r"非公开发行|定向增发|员工持股|董事|监事|高级管理人员|债权人|重整|补偿"
    )
    amounts = amounts_for(public_label)
    if not amounts and not re.search(special, summary):
        amounts = amounts_for(r"A股")
    if not amounts and re.search(r"股份类别.{0,80}?A股", text) and not re.search(special, summary):
        amounts = amounts_for("")
    structural = r"让渡|重整|债权人|补偿|缩股|吸收合并"
    if (
        not amounts
        and not re.search(special, summary)
        and not re.search(structural, text)
        and (not re.search(r"B股|H股", text) or "A股" in title)
    ):
        amounts = amounts_for("")
    values = set(amounts)
    if len(values) > 1:
        raise ValueError("DIFFERENTIATED_PUBLIC_A_CLASS_AMBIGUOUS")
    if not values:
        if re.search(r"股份类别.{0,80}?(?:B股|H股)", text) and "A股" not in summary:
            raise ValueError("OUT_OF_SCOPE_INSTRUMENT")
        if re.search(special, summary):
            raise ValueError("NON_APPLICABLE_SPECIAL_HOLDER_CLASS")
        raise ValueError("MISSING_FINAL_IMPLEMENTATION_TERMS")
    if not any(
        marker in text for marker in ("含税", "税前", "暂不扣缴个人所得税", "暂不扣缴所得税")
    ):
        raise ValueError("MISSING_FINAL_IMPLEMENTATION_TERMS")
    return next(iter(values))


def cash_event(row, members, ordinary_ids):
    values = {Decimal(e["cash_per_share"]) for e in row["evidence"]}
    differentiated = row["status"] == "SUPPORTED_ORDINARY_A_PUBLIC_TERM"
    if row["unresolved_documents"] or len(values) != 1:
        raise ValueError("CASH_TERMS_NOT_RECONCILED")
    if differentiated:
        if (
            row.get("policy_id") != "DIFFERENTIATED_CASH_ORDINARY_PUBLIC_A_V1"
            or row.get("holder_class") != "ORDINARY_EXCHANGE_TRADABLE_A_SHARE_PUBLIC_HOLDER"
        ):
            raise ValueError("DIFFERENTIATED_CASH_POLICY_NOT_BOUND")
    elif row["status"] == "EXACT_GROSS_CASH_CORROBORATED":
        if values != {Decimal(a) for a in row["exchange_amounts"]}:
            raise ValueError("CASH_TERMS_NOT_RECONCILED")
    elif row["status"] != "SUPPORTED_OFFICIAL_IMPLEMENTATION_TERM":
        raise ValueError("CASH_TERMS_NOT_RECONCILED")
    applicable = [
        m
        for m in members
        if m["symbol"] == row["symbol"]
        and m["effective_from"] <= row["record_date"] <= row["ex_date"]
        and row["ex_date"] <= (m["effective_to"] or "2025-12-31")
        and m["listing_date"] <= row["record_date"]
        and row["ex_date"] <= (m["delisting_date"] or "2025-12-31")
    ]
    if len(applicable) != 1 or applicable[0]["security_id"] not in ordinary_ids:
        raise ValueError("CASH_LIFECYCLE_OR_INSTRUMENT_UNRESOLVED")
    evidence = sorted(
        row["evidence"],
        key=lambda e: (
            e.get("policy_id") != "DIFFERENTIATED_CASH_ORDINARY_PUBLIC_A_V1",
            e["source"]["url"],
        ),
    )
    canonical_row = {
        **row,
        "evidence": evidence,
        "exchange_amounts": sorted(row["exchange_amounts"]),
    }
    source = evidence[0]["source"]
    action = CorporateAction.model_validate(
        dict(
            security_id={"value": applicable[0]["security_id"]},
            action_type="CASH_DIVIDEND",
            announcement_date=source["published_on"],
            effective_date=row["ex_date"],
            record_date=row["record_date"],
            ex_date=row["ex_date"],
            cash_per_share=evidence[0]["cash_per_share"],
            source_document=source["title"],
            source_url=source["url"],
            source_document_sha256=source["source_sha256"],
            retrieved_at=source["retrieved_at_utc"],
            source_provider=(
                "OFFICIAL_ISSUER_CNINFO_DIFFERENTIATED_PUBLIC_A"
                if differentiated
                else "OFFICIAL_ISSUER_CNINFO_EXCHANGE_DATED"
            ),
            source_version=(
                "DIFFERENTIATED_CASH_ORDINARY_PUBLIC_A_V1"
                if differentiated
                else (
                    "GROSS_CASH_OFFICIAL_V1"
                    if row["status"] == "EXACT_GROSS_CASH_CORROBORATED"
                    else "OFFICIAL_ISSUER_GROSS_CASH_EXCHANGE_DATES_V1"
                )
            ),
            source_record_hash=canonical_sha256(canonical_row),
            completeness="COMPLETE",
        )
    )
    require_supported_corporate_action(action)
    if CorporateAction.model_validate_json(action.model_dump_json()) != action:
        raise ValueError("CASH_EVENT_SERIALIZATION_CHANGED")
    return action


def gross_cash(pages, symbol, expected_amounts=None, trusted_issuer=False):
    normalized = normalized_document(pages)
    visible_codes = set(re.findall(r"(?<!\d)[036]\d{5}(?!\d)", normalized[:1200]))
    swapped = re.search(
        r"(?:证\s*(?:券|劵)|股\s*票)\s*简\s*称\s*:?\s*" + r"[ \t]*".join(symbol) + r"(?!\d)",
        normalized,
    )
    if not issuer_code_matches(normalized, symbol) and (
        not trusted_issuer
        or (visible_codes and symbol not in visible_codes)
        or (not swapped and visible_codes)
    ):
        raise ValueError("CASH_ISSUER_HEADER_MISMATCH")
    text = re.sub(r"\s+", "", normalized)
    if re.search(r"差异化分红送转:是", text):
        raise ValueError("DIFFERENTIATED_DISTRIBUTION_REQUIRES_REVIEW")
    headline = re.search(r"重要内容提示:(.*?)(?:一、|二、|1、)", text)
    headline_gross = {
        Decimal(value)
        for value in re.findall(
            r"每股派发现金红利\(含税\):?(?:人民币)?(\d+(?:\.\d+)?)元",
            headline[1] if headline else "",
        )
    }
    if len(headline_gross) == 1:
        return next(iter(headline_gross))

    def matches_exchange_precision(amount):
        return any(
            amount == expected
            or amount.quantize(
                Decimal(1).scaleb(expected.as_tuple().exponent), rounding=ROUND_HALF_UP
            )
            == expected
            for expected in expected_amounts or ()
        )

    adjusted = {
        Decimal(value) / Decimal(denominator)
        for denominator, value in re.findall(
            r"(?:变动至|调整为[^。\uff1b;]{0,40}?)(?:每)(10|1)股"
            r"(?:派发|派送|分派|分配|派)?(?:现金红利)?约?(\d+(?:\.\d+)?)元"
            r"[^。\uff1b;]{0,20}(?:含税|税前|扣税前)",
            text,
        )
    }
    adjusted.update(
        Decimal(value) / Decimal(denominator)
        for denominator, value in re.findall(
            r"(?:公司)?按(?:公司)?(?:最新|现有)股本计算的[^。\uff1b;]{0,220}?"
            r"每(10|1)股(?:派发|派送|分派|分配|派)?(?:现金红利)?"
            r"(\d+(?:\.\d+)?)元[^。\uff1b;]{0,30}(?:含税|税前|扣税前)",
            text,
        )
    )
    if len(adjusted) == 1:
        return next(iter(adjusted))
    combined = {
        Decimal(value) / Decimal(denominator or "1")
        for denominator, value in re.findall(
            r"以上\d+[、,]\d+项合计[^。]{0,300}?每(10|1)?股[^。]{0,80}?"
            r"派发现金(\d+(?:\.\d+)?)元\(含税",
            text,
        )
    }
    combined.update(
        Decimal(value) / Decimal(denominator or "1")
        for denominator, value in re.findall(
            r"合并实施方案为[^。]{0,220}?每(10|1)?股合计派"
            r"(\d+(?:\.\d+)?)元(?:人民币)?现金\(含税",
            text,
        )
    )
    if len(combined) == 1:
        return next(iter(combined))
    if expected_amounts:
        expected_matches = set()
        preferred_expected_matches = set()
        declared = re.compile(
            r"每(10(?:\.0+)?|1(?:\.0+)?)?股([^。\uff1b;]{0,100}?)(\d+(?:\.\d+)?)元"
            r"([^。\uff1b;]{0,50})"
        )
        for match in declared.finditer(text):
            context = text[max(0, match.start() - 45) : match.start()] + match[2]
            if re.search(
                r"现金|红利|股息|股利|派息|派现|派发|派送|分派|分配|派", match[2]
            ) and not re.search(
                r"扣税后|税后|先按|补缴|应纳税|应扣税|除权|参考价格|应以|摊薄|计算公式",
                context,
            ):
                amount = Decimal(match[3]) / Decimal(match[1] or "1")
                if matches_exchange_precision(amount):
                    expected_matches.add(amount)
                    final_context = text[max(0, match.start() - 500) : match.start()]
                    final_markers = list(
                        re.finditer(
                            r"(?:调整后|方案实际为|实施方案为|具体实施方案为|"
                            r"重新计算|方案调整|调整如下|变更为|"
                            r"按最新股本计算|总额不变[^。]{0,120}调整|"
                            r"(?:总额|金额)[^。]{0,160}固定不变[^。]{0,160}方案为|"
                            r"本次实施(?:的)?(?:权益分派|利润分配|分配)方案)",
                            final_context,
                        )
                    )
                    if (
                        not re.search(r"调整前[^。\uff1b;]{0,30}$", final_context)
                        and final_markers
                        and len(final_context) - final_markers[-1].end() <= 100
                    ):
                        preferred_expected_matches.add(amount)
        for pattern in (
            r"(?:实际)?(?:发放|派发)现金红利为?(?:税前)?每(10|1)?股(?:人民币)?"
            r"(\d+(?:\.\d+)?)元",
            r"每(10|1)?股派(?:发|送)?(?:人民币)?(\d+(?:\.\d+)?)元(?:人民币)?现金",
            r"每(10|1)?股[^。]{0,120}?(?:同时[,\uff0c]?)?派(?:发|送)?(?:人民币)?"
            r"(\d+(?:\.\d+)?)元(?:人民币)?现金",
            r"向全体股东(10|1)股派(?:发|送)?(?:人民币)?(?:现金红利|现金股利|现金)?"
            r"(\d+(?:\.\d+)?)元",
            r"(10|1)股(?:送(?:红股)?\d+(?:\.\d+)?股)?派发现金股利"
            r"(\d+(?:\.\d+)?)元",
            r"每(10|1)?股派(?:发|送)?现金红利(\d+(?:\.\d+)?)(?=\(含税)",
            r"每(10|1)?股派发[^。\uff1b;]{0,250}?现金红利(?:人民币)?"
            r"(\d+(?:\.\d+)?)元\(含税\)",
            r"每(10|1)?股派(\d+(?:\.\d+)?)元[^。\uff1b;]{0,180}?人民币现金\(含税",
        ):
            for denominator, value in re.findall(pattern, text):
                amount = Decimal(value) / Decimal(denominator or "1")
                if matches_exchange_precision(amount):
                    expected_matches.add(amount)
        for value in re.findall(r"(?:扣税前){2,}.{0,120}?(\d+\.\d+)(?:\1){3}", text):
            amount = Decimal(value)
            if matches_exchange_precision(amount):
                expected_matches.add(amount)
        gross_components = {
            Decimal(value) / Decimal(denominator or "1")
            for denominator, value in re.findall(
                r"每(10|1)?股派(?:发|送)?现金红利(\d+(?:\.\d+)?)元\(含税\)",
                text,
            )
        }
        if len(gross_components) > 1 and matches_exchange_precision(sum(gross_components)):
            expected_matches.add(sum(gross_components))
        changed = {
            Decimal(value) / Decimal(denominator or "1")
            for denominator, value in re.findall(
                r"每(10|1)?股[^。\uff1b;]{0,100}?元(?:\(含税\))?变更为"
                r"(\d+(?:\.\d+)?)元(?:\(含税\))?",
                text,
            )
            if matches_exchange_precision(Decimal(value) / Decimal(denominator or "1"))
        }
        if len(changed) == 1:
            return next(iter(changed))
        if len(preferred_expected_matches) == 1:
            return next(iter(preferred_expected_matches))
        if len(expected_matches) == 1:
            return next(iter(expected_matches))
    heading = (
        r"(?:本次实施的(?:权益分派|利润分配|分红派息|分配)|"
        r"本次(?:权益分派|分红派息)实施|"
        r"权益分派|利润分配(?:及转增股本|和资本公积金?转增股本)?|"
        r"分红派息|分配(?:、转增股本)?|"
        r"(?:资本公积金?)?转增股本)方案"
    )
    sections = list(
        re.finditer(
            r"(?m)^\s*[一二三四五六七八九十]+、\s*(?:\d{4}\s*年(?:度)?\s*)?" + heading + r"\s*$",
            normalized,
        )
    )
    if not sections:
        sections = list(
            re.finditer(
                r"(?m)^\s*[一二三四五六七八九十]+、\s*(?:权益分派|利润分配)方案\s*$",
                normalized,
            )
        )
    section_texts = []
    if sections:
        for section in sections:
            remaining = normalized[section.end() :]
            next_heading = re.search(r"(?m)^\s*[一二三四五六七八九十]+、", remaining)
            body = re.sub(
                r"\s+",
                "",
                remaining[: next_heading.start()] if next_heading else remaining,
            )
            note = re.search(r"【(?:[a-zA-Z]?注|特别说明)", body)
            section_texts.append(
                re.sub(
                    r"本公司及董事会全体成员保证(?:信息披露的)?内容真实、?准确、?"
                    r"完整[,\uff0c]?没有虚假记载、?误导性陈述或重大遗漏[。.]?",
                    "",
                    body[: note.start()] if note else body,
                )
            )
    else:
        section_texts = [text]
    first_heading = re.search(r"(?m)^\s*[一二三四五六七八九十]+、", normalized)
    summary = normalized[: first_heading.start()] if first_heading else ""
    number = r"(\d+(?:\.\d+)?)"
    base = r"每(10(?:\.0+)?|1(?:\.0+)?)?股(?:送(?:红股)?\d+(?:\.\d+)?股[、,]?)?"
    gross_basis = (
        r"(?:[。,]?(?:\(|\[)?(?:含税|扣税前|税前|含适用税项)|"
        r"(?=\((?:扣税后|税后)[,\uff0c]))"
    )

    def extract(texts):
        matches = []
        for section_text in texts:
            section_matches = []
            for pattern in (
                r"(?:派发)?(?:现金红利|现金股利|现金股息|红利|股息)"
                r"(?:\((?:扣税前|税前)\))?[:\uff1a]?每(10|1)?股(?:人民币)?"
                + number
                + r"元"
                + gross_basis,
                r"(?:派发)?(?:现金红利|现金股利|现金股息|红利|股息)"
                r"\((?:扣税前|税前)\)[:\uff1a]?每(10|1)?股(?:人民币)?" + number + r"元",
                base + r"(?:现金红利|现金股利|现金股息|红利|股息|现金分红)"
                r"[:\uff1a]?(?:\(|\[)?(?:扣税前|税前)(?:\)|\])?[:\uff1a]?" + number + r"(?:元)?",
                r"(?:扣税前|税前)每(10|1)?股(?:派发|派送|分派|分配|派)?(?:人民币)?"
                r"(?:现金红利|现金股利|现金股息|红利|股息|现金)?(?:金额)?(?:人民币)?"
                + number
                + r"元",
                r"每(10|1)?股(?:扣税前|税前)(?:现金红利|现金股利|现金股息|红利|股息|现金)"
                r"(?:金额)?(?:人民币)?" + number + r"元",
                base + r"(?:派发|派送|分派|分配|派)?(?:人民币)?"
                r"(?:现金红利|现金股利|现金股息|红利|股息|现金)"
                r"[:\uff1a]?(?:人民币)?"
                + number
                + r"元(?:人民币)?(?:现金(?:红利|股利)?)?"
                + gross_basis,
                base
                + r"派(?:发|送)?(?:人民币)?"
                + number
                + r"元(?:人民币)?现金(?:红利|股利)?(?:、送\d+(?:\.\d+)?股红股)?"
                + gross_basis,
                base + r"派(?:发|送)?(?:人民币)?" + number + r"元(?:人民币)?" + gross_basis,
                base + number + r"元人民币现金" + gross_basis,
                base + r"派(?:发|送)?" + number + r"人民币现金" + gross_basis,
                r"(?:分配)?(?:现金股利|现金红利|现金股息)为" + base + number + r"元" + gross_basis,
                base + r"派" + number + r"元人民币的方式进行利润分配" + gross_basis,
                base
                + r"(?:派发|派送|分派|派)?(?:现金红利|现金股利|现金股息|红利|股息|现金)人民币"
                + number
                + r"(?:元)?"
                + gross_basis,
            ):
                for denominator, value in re.findall(pattern, section_text):
                    with localcontext() as ctx:
                        ctx.prec = 50
                        section_matches.append(Decimal(value) / Decimal(denominator or "1"))
            declared = re.compile(
                r"每(10(?:\.0+)?|1(?:\.0+)?)?股(?=[^。;\uff1b]{0,90}(?:现金|红利|股息|股利|派息|派现))[^。;\uff1b元]{0,70}?"
                r"(?:(?:派送|送)红股\d+(?:\.\d+)?股[、,](?:并)?(?:派发)?现金红利|"
                r"(?:派发|派送|分派|分配|派息|派现|派|送现金|现金分红)"
                r"(?:现金红利|现金股利|现金股息|红利|股息|现金)?)"
                r"(?:人民币)?" + number + r"元(?:人民币)?(?:现金(?:红利|股利|股息)?)?"
            )
            declared_matches, preferred_matches = [], []
            for match in declared.finditer(section_text):
                prefix = section_text[max(0, match.start() - 80) : match.start()]
                suffix = section_text[match.end() : match.end() + 240]
                if re.search(r"(?:扣税后|税后)[^。;\uff1b]{0,80}$", prefix) or not re.search(
                    r"含税|税前", suffix
                ):
                    continue
                denominator, value = match.groups()
                with localcontext() as ctx:
                    ctx.prec = 50
                    amount = Decimal(value) / Decimal(denominator or "1")
                declared_matches.append(amount)
                context = section_text[max(0, match.start() - 300) : match.start()]
                if re.search(
                    r"(?:实际向全体股东|股本调整后|调整后(?:的)?(?:权益分派|利润分配|分配)?方案|"
                    r"(?:公司)?按(?:公司)?(?:最新|现有)股本计算的"
                    r"[^。;\uff1b]{0,120}方案|"
                    r"按(?:公司)?(?:最新|现有)股本(?:总额)?计算的"
                    r"[^。;\uff1b]{0,120}(?:方案|分配比例)(?:调整)?为|"
                    r"以现有总股本计算的[^。;\uff1b]{0,100}方案为|"
                    r"(?:权益分派|利润分配)[^。;\uff1b]{0,80}按照如下方案实施|"
                    r"本次实施[^。;\uff1b]{0,120}方案(?:实际|调整)?为|"
                    r"(?:权益分派|利润分配|分配)方案调整如下|"
                    r"现金分红实施方案为|"
                    r"(?:以|按)(?:公司)?(?:现有|最新)(?:总股本|股本|股本总额)"
                    r"[^。;\uff1b]{0,220}(?:为基数|计算)[^。;\uff1b]{0,100}向全体股东|"
                    r"(?:分派变更如下|方案调整如下)[^。;\uff1b]{0,260}向全体股东|"
                    r"(?:总额|金额)固定不变[^。;\uff1b]{0,220}"
                    r"(?:方案(?:为|如下)|分配比例(?:调整)?为)|"
                    r"按照(?:现金分红)?总额固定不变的原则,?实际|"
                    r"(?:调整后|调整为|变动至|实施调整为|重新计算(?:后|的)|最终确定|方案实际为)"
                    r"[^。;\uff1b]{0,180})[^。;\uff1b]{0,120}$",
                    context,
                ) or re.search(
                    r"(?:方案调整为|(?:总额|金额)[^。]{0,400}固定不变[^。]{0,400}"
                    r"(?:权益分派|利润分配)方案(?:调整)?为)[^。]{0,250}$",
                    context,
                ):
                    preferred_matches.append(amount)
            if preferred_matches:
                section_matches = preferred_matches
            else:
                section_matches.extend(declared_matches)
            if not section_matches and re.search(
                r"每(?:10|1)?股[^。;\uff1b]{0,100}\d[^。;\uff1b]{0,40}元", section_text
            ):
                raise ValueError("NO_UNIQUE_EXPLICIT_GROSS_CASH")
            matches.extend(section_matches)
        return matches

    compact_summary = re.sub(r"\s+", "", summary)
    if summary and not re.search(r"原方案|调整|变更|固定不变", compact_summary):
        try:
            summary_values = set(extract([compact_summary]))
        except ValueError:
            summary_values = set()
        if len(summary_values) == 1 and next(iter(summary_values)) > 0:
            return next(iter(summary_values))
    matches = extract(section_texts)
    values = set(matches)
    if len(values) != 1 and expected_amounts is not None:
        values = {value for value in values if matches_exchange_precision(value)}
    if not values and not any(
        re.search(r"现金红利|现金股利|现金股息|派息|派现|股息", section_text)
        for section_text in section_texts
    ):
        raise ValueError("NO_EXPLICIT_GROSS_CASH")
    if not values and any(
        re.search(
            r"不(?:进行|分配)?(?:现金分红|现金股利|派发现金|派现)|"
            r"现金红利为0",
            section_text,
        )
        for section_text in section_texts
    ):
        return Decimal(0)
    if len(values) != 1 or next(iter(values)) <= 0:
        raise ValueError("NO_UNIQUE_EXPLICIT_GROSS_CASH")
    return next(iter(values))


def verified(path):
    content = json.loads(path.read_bytes())
    if content["manifest_sha256"] != canonical_sha256(
        {k: v for k, v in content.items() if k != "manifest_sha256"}
    ):
        raise ValueError("INPUT_MANIFEST_CHANGED")
    return content


def require_approved_cash_policy(path):
    # Exact approved bytes only: original catalog and published v1.1 revision 3.
    if sha256_file(path) not in {
        "8e4269e5b62a7a738e4e46a0f0caada47fe07af98b482ae3f81fd946cf759c79",
        "f7c959ea29bbb6aa1e712ff897947d2cfb2932506ace2e2bef1ce567aec9a754",
    }:
        raise ValueError("APPROVED_CASH_POLICY_CHANGED")


def exchange_cash_amounts(sse, szse):
    exchange = defaultdict(set)
    for group in sse["groups"]:
        if group["key"][0] != "dividend":
            continue
        for evidence in group["evidence"]:
            row = evidence["normalized"]
            exchange[row["source_symbol"], row["record_date"], row["ex_date"]].add(
                Decimal(row["amount"])
            )
    for row in szse["rows"]:
        if (
            row["symbol"].startswith(("0", "3"))
            and row["raw_cells"][5].strip()
            and Decimal(row["raw_cells"][5]) > 0
        ):
            exchange[row["symbol"], row["record_date"], row["ex_date"]].add(
                Decimal(row["raw_cells"][5])
            )
    return exchange


def secondary_timing_only(doc, pages, has_primary):
    if not has_primary:
        return False
    text = re.sub(r"\s+", "", normalized_document(pages))
    if "更正公告" in doc["title"]:
        return all(
            token in text
            for token in ("更正前", "更正后", "其他内容不变", "股权登记日", "除权除息日")
        ) and not any(
            token in text
            for token in (
                "每股派",
                "每10股派",
                "现金红利",
                "现金股利",
                "现金分红",
                "派现",
                "转增",
                "送股",
                "送红股",
                "配股",
                "让渡",
                "合并",
            )
        )
    if "提示性公告" not in doc["title"]:
        return False
    return (
        "A股利润分配时间安排" in text
        and re.search(r"A股(?:\d{4}年年度)?(?:利润分配|权益分派)实施公告将在", text)
        and "另行发布" in text
    )


def accepted_event_key(row):
    event = row["event"]
    return event["security_id"]["value"], event["ex_date"], event["action_type"]


def accepted_event_terms(row):
    result = {
        key: value
        for key, value in row["event"].items()
        if not key.startswith("source_") and key not in {"announcement_date", "retrieved_at"}
    }
    result["cash_per_share"] = Decimal(result["cash_per_share"])
    return result


def preserve_accepted_events(current, prior, source_keys):
    """Keep accepted identities only after fresh source and economic corroboration."""

    rows = {accepted_event_key(row): row for row in current}
    if len(rows) != len(current) or len({accepted_event_key(row) for row in prior}) != len(prior):
        raise ValueError("DUPLICATE_CASH_EVENT")
    for row in prior:
        action = CorporateAction.model_validate(row["event"])
        require_supported_corporate_action(action)
        if (
            action.event_checksum != row["event_checksum"]
            or row["policy_id"]
            not in {"EXISTING_ACCEPTED_CASH_DIVIDEND", "DIFFERENTIATED_CASH_ORDINARY_PUBLIC_A_V1"}
            or (action.source_url, action.source_document_sha256) not in source_keys
            or accepted_event_key(row) not in rows
            or row["policy_id"] != rows[accepted_event_key(row)]["policy_id"]
            or accepted_event_terms(row) != accepted_event_terms(rows[accepted_event_key(row)])
            or action.record_date is None
            or action.announcement_date > action.record_date
        ):
            raise ValueError("PRIOR_CASH_EVENT_NOT_RECORROBORATED")
        rows[accepted_event_key(row)] = row
    return [rows[k] for k in sorted(rows)]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--source-manifest", type=Path, required=True)
    parser.add_argument("--date-links", type=Path, required=True)
    parser.add_argument("--sse-audit", type=Path, required=True)
    parser.add_argument("--szse-audit", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--master", type=Path)
    parser.add_argument("--instruments", type=Path)
    parser.add_argument(
        "--accepted-prior", type=Path, help="Preserve recorroborated event identities"
    )
    parser.add_argument(
        "--prior", type=Path, help="Reuse previously corroborated rows without reparsing their PDFs"
    )
    args = parser.parse_args()
    inputs = [args.source_manifest, args.date_links, args.sse_audit, args.szse_audit]
    sources, links, sse, szse = map(verified, inputs)
    prior_rows = {}
    if args.prior:
        prior = verified(args.prior)
        prior_inputs = {r["path"]: r["sha256"] for r in prior["inputs"]}
        if any(prior_inputs.get(str(p)) != sha256_file(p) for p in inputs):
            raise ValueError("PRIOR_CASH_INPUTS_CHANGED")
        prior_rows = {
            (r["symbol"], r["record_date"], r["ex_date"]): r
            for r in prior["results"]
            if r["status"] == "EXACT_GROSS_CASH_CORROBORATED"
        }
        inputs.append(args.prior)
    documents = {
        (r["url"], r["source_sha256"]): r
        for r in sources["documents"]
        if r["retrieval_status"] == "PASS"
    }
    exchange = exchange_cash_amounts(sse, szse)
    results = []
    for link in sorted(
        links["results"], key=lambda r: (r["symbol"], r["record_date"], r["ex_date"])
    ):
        key = link["symbol"], link["record_date"], link["ex_date"]
        if key not in exchange:
            continue
        if key in prior_rows:
            results.append(prior_rows[key])
            continue
        amounts = exchange[key]
        evidence, failures, differentiated_documents = [], [], 0
        secondary = []
        has_primary = any(
            "提示性公告" not in documents[item["url"], item["source_sha256"]]["title"]
            for item in link["documents"]
        )
        for matched in sorted(link["documents"], key=lambda d: (d["url"], d["source_sha256"])):
            sha = matched["source_sha256"]
            doc = documents[matched["url"], sha]
            if (
                doc["issuer"] != link["symbol"]
                or not doc["published_on"] <= link["record_date"] < link["ex_date"]
            ):
                raise ValueError("CASH_SOURCE_IDENTITY_OR_DATE_CHANGED")
            path = (args.root / doc["source_path"]).resolve()
            # Downloader may reuse another verified source queue within staging.
            if not path.is_relative_to(args.root.parent.resolve()) or sha256_file(path) != sha:
                raise ValueError("CASH_SOURCE_CHANGED")
            cache = args.root / "batch-v1/text" / f"{sha}.json"
            if sha256_file(cache) != matched["extraction_sha256"]:
                raise ValueError("CASH_EXTRACTION_CHANGED")
            extracted = json.loads(cache.read_bytes())
            try:
                if secondary_timing_only(doc, extracted["pages"], has_primary):
                    secondary.append(
                        dict(
                            source_sha256=sha,
                            url=doc["url"],
                            reason=(
                                "DATE_ONLY_CORRECTION_FINAL_PRIMARY_PRESENT"
                                if "更正公告" in doc["title"]
                                else "A_H_DATE_ONLY_FINAL_TO_FOLLOW"
                            ),
                        )
                    )
                    continue
                compact = re.sub(r"\s+", "", normalized_document(extracted["pages"]))
                if "差异化分红送转:是" in compact:
                    differentiated_documents += 1
                    amount = differentiated_cash(extracted["pages"], link["symbol"], doc["title"])
                    evidence.append(
                        dict(
                            cash_per_share=str(amount),
                            holder_class="ORDINARY_EXCHANGE_TRADABLE_A_SHARE_PUBLIC_HOLDER",
                            policy_id="DIFFERENTIATED_CASH_ORDINARY_PUBLIC_A_V1",
                            source=doc,
                        )
                    )
                else:
                    amount = gross_cash(extracted["pages"], link["symbol"], amounts)
                    evidence.append(dict(cash_per_share=str(amount), source=doc))
            except ValueError as exc:
                failures.append(dict(source_sha256=sha, reason=str(exc)))
        values = {Decimal(e["cash_per_share"]) for e in evidence}
        row = dict(
            symbol=key[0],
            record_date=key[1],
            ex_date=key[2],
            exchange_amounts=sorted(str(a) for a in amounts),
            evidence=evidence,
            unresolved_documents=failures,
        )
        if secondary:
            row["secondary_date_only_documents"] = secondary
        if differentiated_documents:
            reasons = {failure["reason"] for failure in failures}
            if evidence and failures:
                row["status"] = "CONFLICTING_AUTHORITY"
            elif len(values) == 1 and not failures:
                row.update(
                    status="SUPPORTED_ORDINARY_A_PUBLIC_TERM",
                    holder_class="ORDINARY_EXCHANGE_TRADABLE_A_SHARE_PUBLIC_HOLDER",
                    policy_id="DIFFERENTIATED_CASH_ORDINARY_PUBLIC_A_V1",
                )
            elif len(reasons) == 1:
                row["status"] = next(iter(reasons))
            else:
                row["status"] = "CONFLICTING_AUTHORITY"
        else:
            row["status"] = (
                "EXACT_GROSS_CASH_CORROBORATED"
                if len(values) == 1 and values == amounts and not failures
                else "UNRESOLVED_CASH_TERMS"
            )
        results.append(row)
    accepted = []
    if bool(args.master) != bool(args.instruments):
        raise ValueError("BOTH_MASTER_AND_INSTRUMENTS_REQUIRED")
    if args.master and args.instruments:
        members = verified(args.master)["records"]
        instruments = verified(args.instruments)
        if instruments["source_master_sha256"] != sha256_file(args.master):
            raise ValueError("INSTRUMENT_MASTER_CHANGED")
        policy = (
            Path(__file__).resolve().parents[2] / ".research/corporate_action_policy_matrix_v1.json"
        )
        require_approved_cash_policy(policy)
        by_symbol = defaultdict(list)
        for member in members:
            by_symbol[member["symbol"]].append(member)
        ordinary = {
            r["classification"]["security_id"]["value"]
            for r in instruments["classifications"]
            if r["classification"]["instrument_type"] == "COMMON_A_SHARE"
        }
        for row in results:
            if row["status"] not in {
                "EXACT_GROSS_CASH_CORROBORATED",
                "SUPPORTED_ORDINARY_A_PUBLIC_TERM",
            }:
                continue
            try:
                event = cash_event(row, by_symbol[row["symbol"]], ordinary)
                if event != cash_event(row, list(reversed(by_symbol[row["symbol"]])), ordinary):
                    raise ValueError("CASH_MASTER_ORDER_CHANGED")
                accepted.append(
                    dict(
                        event=event.model_dump(mode="json"),
                        event_checksum=event.event_checksum,
                        policy_id=row.get("policy_id", "EXISTING_ACCEPTED_CASH_DIVIDEND"),
                        support_state=(
                            "SUPPORTED_DIFFERENTIATED_ORDINARY_PUBLIC_A_EX_DATE_CASH_POLICY"
                            if row["status"] == "SUPPORTED_ORDINARY_A_PUBLIC_TERM"
                            else "SUPPORTED_EXISTING_EX_DATE_CASH_POLICY"
                        ),
                        metadata_only_gaps=["PAYMENT_DATE_NOT_NORMALIZED"],
                        source_terms_sha256=canonical_sha256(row),
                    )
                )
            except ValueError as exc:
                row["acceptance_issue"] = str(exc)
        inputs.extend([args.master, args.instruments, policy])
    if args.accepted_prior:
        accepted_prior = verified(args.accepted_prior)
        accepted = preserve_accepted_events(accepted, accepted_prior["events"], set(documents))
        inputs.append(args.accepted_prior)
    report = dict(
        parser_version="DISTRIBUTION_GROSS_CASH_RECONCILIATION_V2",
        parser_sha256=sha256_file(Path(__file__)),
        results=results,
        counts=dict(sorted(Counter(r["status"] for r in results).items())),
        inputs=[dict(path=str(p), sha256=sha256_file(p)) for p in inputs],
        accepted_events=len(accepted),
        reused_corroborated_rows=len(prior_rows),
        events=accepted,
        full_dataset_created=False,
        scope="EXISTING_GROSS_EX_DATE_CASH_POLICY_ONLY_NOT_FULL_CORPORATE_ACTION_CENSUS",
    )
    report["manifest_sha256"] = canonical_sha256(report)
    write_immutable(args.output, canonical_json_bytes(report) + b"\n")
    print(json.dumps({k: v for k, v in report.items() if k not in {"results", "inputs", "events"}}))


if __name__ == "__main__":
    main()
