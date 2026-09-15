"""Reconcile explicit gross-cash terms to exchange rows; never assume missing terms."""

import argparse
import json
import re
import unicodedata
from collections import Counter, defaultdict
from decimal import Decimal, localcontext
from pathlib import Path

from app.data.catalog.checksums import canonical_json_bytes, canonical_sha256, sha256_file
from app.data.catalog.freeze import write_immutable
from app.domain.markets.corporate_actions import CorporateAction, require_supported_corporate_action


def issuer_code_matches(normalized, symbol):
    header = re.search(
        r"(?:(?:A\s*股|证\s*(?:券|劵)|(?<!债)券|股\s*票|公\s*司)\s*){1,4}"
        r"(?:(?:代\s*码|代\s*号|号\s*码)\s*){1,4}"
        r"(?:\(A/H\))?\s*:?\s*([^\n]{0,120})",
        normalized[:600],
    )
    code_field = re.split(r"简称|编号|债券代码", header[1], maxsplit=1)[0] if header else ""
    exact = re.search(r"(?<!\d)" + r"[ \t]*".join(symbol) + r"(?!\d)", code_field)
    digits = re.sub(r"\D", "", code_field)
    repeated = len(digits) in (12, 18, 24) and digits == symbol * (len(digits) // 6)
    return bool(exact or repeated or (len(digits) == 12 and digits.startswith(symbol)))


def normalized_document(pages):
    normalized_pages = [unicodedata.normalize("NFKC", p) for p in pages]
    if len(pages) > 1:
        for template in (r"{page}", r"{page}\s*/\s*{total}", r"-\s*{page}\s*-"):
            counters = [
                re.match(r"^\s*" + template.format(page=i, total=len(pages)) + r"[ \t]*\n", p)
                for i, p in enumerate(normalized_pages, 1)
            ]
            if all(counters):
                normalized_pages = [
                    p[m.end() :] for p, m in zip(normalized_pages, counters, strict=True)
                ]
                break
    return "\n".join(normalized_pages)


def differentiated_cash(pages, symbol, title):
    normalized = normalized_document(pages)
    if not issuer_code_matches(normalized, symbol):
        raise ValueError("CONFLICTING_AUTHORITY")
    text = re.sub(r"\s+", "", normalized)
    if "差异化分红送转:是" not in text:
        raise ValueError("CONFLICTING_AUTHORITY")
    if "实施公告" not in title:
        raise ValueError("MISSING_FINAL_IMPLEMENTATION_TERMS")
    match = re.search(r"每股分配比例(.{0,500}?)(?:相关日期|差异化分红送转)", text)
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
        r"流通A股股东|普通A股股东|A股公众股东|境内上市人民币普通股股东|"
        r"持有首次公开发行A股股票的流通股股东|流通股股东)"
    )

    def amounts_for(prefix):
        return [
            Decimal(value) for value in re.findall(prefix + r".{0,30}?" + per_share, summary)
        ] + [
            Decimal(value) / Decimal(10)
            for value in re.findall(prefix + r".{0,30}?" + per_ten, summary)
        ]

    special = (
        r"控股股东|实际控制人|国有股东|法人发起人|限售(?:条件)?(?:A股|股)?股东|"
        r"非公开发行|定向增发|员工持股|董事|监事|高级管理人员|债权人|重整|补偿"
    )
    amounts = amounts_for(public_label)
    if not amounts and not re.search(special, summary):
        amounts = amounts_for(r"A股")
    if not amounts and re.search(r"股份类别.{0,80}?A股", text) and not re.search(special, summary):
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
    if not any(marker in text for marker in ("含税", "税前", "暂不扣缴个人所得税")):
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
    elif row["status"] != "EXACT_GROSS_CASH_CORROBORATED" or values != {
        Decimal(a) for a in row["exchange_amounts"]
    }:
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
                else "OFFICIAL_ISSUER_CNINFO_EXCHANGE_RECONCILED"
            ),
            source_version=(
                "DIFFERENTIATED_CASH_ORDINARY_PUBLIC_A_V1"
                if differentiated
                else "GROSS_CASH_OFFICIAL_V1"
            ),
            source_record_hash=canonical_sha256(canonical_row),
            completeness="COMPLETE",
        )
    )
    require_supported_corporate_action(action)
    if CorporateAction.model_validate_json(action.model_dump_json()) != action:
        raise ValueError("CASH_EVENT_SERIALIZATION_CHANGED")
    return action


def gross_cash(pages, symbol):
    normalized = normalized_document(pages)
    if not issuer_code_matches(normalized, symbol):
        raise ValueError("CASH_ISSUER_HEADER_MISMATCH")
    text = re.sub(r"\s+", "", normalized)
    if re.search(r"差异化分红送转:是", text):
        raise ValueError("DIFFERENTIATED_DISTRIBUTION_REQUIRES_REVIEW")
    sections = list(
        re.finditer(
            r"(?m)^\s*[一二三四五六七八九十]+、\s*本次实施的(?:权益分派|利润分配)方案\s*$",
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
            section_texts.append(
                re.sub(r"\s+", "", remaining[: next_heading.start()] if next_heading else remaining)
            )
    else:
        section_texts = [text]
    number = r"(\d+(?:\.\d+)?)"
    base = r"每(10|1)?股(?:送(?:红股)?\d+(?:\.\d+)?股[、,]?)?"
    gross_basis = r"[。,]?(?:\(|\[)(?:含税|税前|含适用税项)"
    matches = []
    for section_text in section_texts:
        section_matches = []
        for pattern in (
            base + r"(?:派发|派送|分派|分配|派)?(?:人民币)?"
            r"(?:现金红利|现金股利|现金股息|红利|股息|现金)"
            r"(?:人民币)?" + number + r"元(?:人民币)?(?:现金(?:红利|股利)?)?" + gross_basis,
            base
            + r"派(?:发|送)?(?:人民币)?"
            + number
            + r"元(?:人民币)?现金(?:红利|股利)?(?:、送\d+(?:\.\d+)?股红股)?"
            + gross_basis,
            base + r"派(?:发|送)?(?:人民币)?" + number + r"元(?:人民币)?" + gross_basis,
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
        if not section_matches and re.search(
            r"每(?:10|1)?股[^。;]{0,100}\d[^。;]{0,40}元", section_text
        ):
            raise ValueError("NO_UNIQUE_EXPLICIT_GROSS_CASH")
        matches.extend(section_matches)
    values = set(matches)
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


def preserve_accepted_events(current, prior, source_keys):
    """Keep accepted identities only after fresh source and economic corroboration."""

    def key(row):
        event = row["event"]
        return event["security_id"]["value"], event["ex_date"], event["action_type"]

    def terms(row):
        result = {
            k: v
            for k, v in row["event"].items()
            if not k.startswith("source_") and k not in {"announcement_date", "retrieved_at"}
        }
        result["cash_per_share"] = Decimal(result["cash_per_share"])
        return result

    rows = {key(row): row for row in current}
    if len(rows) != len(current) or len({key(row) for row in prior}) != len(prior):
        raise ValueError("DUPLICATE_CASH_EVENT")
    for row in prior:
        action = CorporateAction.model_validate(row["event"])
        require_supported_corporate_action(action)
        if (
            action.event_checksum != row["event_checksum"]
            or row["policy_id"] != "EXISTING_ACCEPTED_CASH_DIVIDEND"
            or (action.source_url, action.source_document_sha256) not in source_keys
            or key(row) not in rows
            or terms(row) != terms(rows[key(row)])
            or action.record_date is None
            or action.announcement_date > action.record_date
        ):
            raise ValueError("PRIOR_CASH_EVENT_NOT_RECORROBORATED")
        rows[key(row)] = row
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
                    amount = gross_cash(extracted["pages"], link["symbol"])
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
        if (
            sha256_file(policy)
            != "8e4269e5b62a7a738e4e46a0f0caada47fe07af98b482ae3f81fd946cf759c79"
        ):
            raise ValueError("APPROVED_CASH_POLICY_CHANGED")
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
