"""Bind official issuer cash terms to a unique official exchange-dated event."""

import argparse
import json
import re
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

from app.data.catalog.checksums import canonical_json_bytes, canonical_sha256, sha256_file
from app.data.catalog.freeze import write_immutable
from scripts import reconcile_distribution_cash
from scripts.reconcile_distribution_cash import (
    cash_event,
    differentiated_cash,
    exchange_cash_amounts,
    gross_cash,
    normalized_document,
    verified,
)

END = "2025-12-31"
RETROSPECTIVE_POLICY = "OFFICIAL_NOTICE_EXCHANGE_ANNUAL_REPORT_COMPOSITE_V1"
APPROVAL_POLICY = "OFFICIAL_SHAREHOLDER_APPROVAL_PLUS_EXCHANGE_IMPLEMENTATION_EVENT_V1"


def extraction_cache(root, source_sha256):
    alternate = root / "batch-v1/text-pymupdf" / (source_sha256 + ".json")
    return alternate if alternate.exists() else root / "batch-v1/text" / (source_sha256 + ".json")


def is_final_implementation_title(title):
    if re.search(r"董事会20\d{2}年度分红派息公告$", title):
        return True
    rejected = r"预案|股东大会|董事会|监事会|实施细则|实施结果|理财产品|调整.*(?:回购|转股).*价格"
    if re.search(rejected, title):
        return False
    return bool(
        re.search(
            r"(?:权益分派|权益分配|利润分配|利润分派|分红派息|现金红利|"
            r"现金分配|红利分配|A股派息|股息派发|年度分配|分红|分配).*实施|"
            r"权益实施分派公告$|"
            r"A股派发.*股息.*实施|"
            r"(?:关于)?现金股利实施(?:的)?公告$|"
            r"(?:分红派息|权益分派|利润分配|现金红利|A股派息)(?:的)?公告$|"
            r"权益分派方案公告$|"
            r"利润分配(?:及资本公积金?转增股本)?(?:的)?公告$|"
            r"(?:关于)?派发.+股息(?:的)?公告$|(?:A股)?(?:红利|股息)分派公告$|"
            r"(?:年度|中期)分红公告$|权益分派$|特别派息实施公告$",
            title,
        )
    )


def is_final_implementation_document(title, text):
    return is_final_implementation_title(title) or (
        title == "董事会公告"
        and all(
            marker in text
            for marker in ("股权登记日", "除息日", "分红派息具体实施日期", "分红派息实施办法")
        )
    )


def is_shareholder_approval_title(title):
    return bool(re.search(r"(?:年度|临时)股东大会决议公告$", title))


def approved_distribution_periods(text):
    compact = re.sub(r"\s+", "", text)
    return set(
        re.findall(
            r"(?:审议通过|通过了)[^。]{0,500}?"
            r"(?=(20\d{2}年(?:半年度|度|中期))[^。]{0,200}?(?:利润分配|分红))",
            compact,
        )
    )


def distribution_periods(text):
    return set(
        re.findall(
            r"(?=(20\d{2}年(?:半年度|度|中期))[^。]{0,200}?(?:利润分配|分红))",
            re.sub(r"\s+", "", text),
        )
    )


def authoritative_evidence(evidence):
    corrected = [item for item in evidence if re.search(r"更正|修订", item["source"]["title"])]
    return corrected or evidence


def unique_event_match(amount, affected_events, exchange):
    matches = []
    for event in affected_events:
        kind, symbol, record_date, ex_date = event.split(":")
        if kind != "CASH":
            raise ValueError("NON_CASH_CANDIDATE")
        key = symbol, record_date, ex_date
        if amount in exchange.get(key, set()):
            matches.append(key)
    return matches[0] if len(set(matches)) == 1 else None


def unique_candidate_event(affected_events, exchange):
    matches = []
    for event in affected_events:
        kind, symbol, record_date, ex_date = event.split(":")
        if kind != "CASH":
            raise ValueError("NON_CASH_CANDIDATE")
        key = symbol, record_date, ex_date
        if key in exchange:
            matches.append(key)
    return matches[0] if len(set(matches)) == 1 else None


def unique_official_event(amount, affected_events, exchange):
    return unique_event_match(amount, affected_events, exchange) or unique_candidate_event(
        affected_events, exchange
    )


def retrospective_completion(text, title, ex_date):
    fiscal = re.search(r"(20\d{2})年(?:度|年度|半年度|中期)", title)
    if not fiscal:
        return False
    compact = re.sub(r"\s+", "", text)
    return bool(
        re.search(
            rf"{fiscal[1]}年度.{{0,1500}}?"
            r"(?:实施(?:完成|完毕)|已于[^。]{0,40}?实施了?[^。]{0,80}?方案|"
            r"完成了?[^。]{0,80}?(?:权益分派|利润分配|分配)方案)",
            compact,
        )
    )


def exchange_with_historical_symbols(exchange, master):
    enriched = dict(exchange)
    aliases = []
    for row in master:
        current_symbol = row["security_id"].rsplit(":", 1)[-1]
        if row["symbol"] == current_symbol:
            continue
        for (symbol, record_date, ex_date), amounts in exchange.items():
            if (
                symbol == current_symbol
                and row["effective_from"] <= record_date <= ex_date
                and ex_date <= (row["effective_to"] or END)
            ):
                alias = row["symbol"], record_date, ex_date
                enriched.setdefault(alias, set()).update(amounts)
                aliases.append(
                    dict(
                        security_id=row["security_id"],
                        historical_symbol=row["symbol"],
                        official_source_symbol=current_symbol,
                        record_date=record_date,
                        ex_date=ex_date,
                    )
                )
    return enriched, sorted(aliases, key=lambda row: tuple(row.values()))


def affected_cash_events(document, by_symbol):
    explicit = [
        event
        for event in document["affected_events"]
        if event.startswith("CASH:") and len(event.split(":")) == 4
    ]
    if explicit:
        return explicit
    published = date.fromisoformat(document["published_on"])
    return [
        f"CASH:{symbol}:{record_date}:{ex_date}"
        for symbol, record_date, ex_date in by_symbol[document["issuer"]]
        if published <= date.fromisoformat(record_date)
        and (date.fromisoformat(record_date) - published).days <= 60
        and ex_date <= END
    ]


def reconcile(root, documents, exchange, retrospective_documents=()):
    by_symbol = defaultdict(list)
    for key in exchange:
        by_symbol[key[0]].append(key)
    linked = defaultdict(list)
    outcomes = []
    for document in documents:
        outcome = dict(
            source_sha256=document["source_sha256"],
            issuer=document["issuer"],
            title=document["title"],
        )
        if document["retrieval_status"] != "PASS":
            outcome["status"] = document["retrieval_status"]
            outcomes.append(outcome)
            continue
        pdf = root / document["source_path"]
        cache = extraction_cache(root, document["source_sha256"])
        if sha256_file(pdf) != document["source_sha256"] or not cache.exists():
            raise ValueError("CANDIDATE_SOURCE_CHANGED")
        extracted = json.loads(cache.read_bytes())
        if extracted["source_sha256"] != document["source_sha256"]:
            raise ValueError("CANDIDATE_EXTRACTION_CHANGED")
        try:
            text = normalized_document(extracted["pages"])
            compact = re.sub(r"\s+", "", text)
            approved = is_shareholder_approval_title(document["title"])
            if not is_final_implementation_document(document["title"], text) and not approved:
                raise ValueError("NOT_FINAL_IMPLEMENTATION_TITLE")
            if approved and not (
                "向全体股东" in compact
                and re.search(r"(?:审议通过|通过了)[^。]{0,500}?(?:利润分配|分红)", compact)
            ):
                raise ValueError("NOT_APPROVED_DISTRIBUTION_TERMS")
            affected = affected_cash_events(document, by_symbol)
            if "差异化分红送转:是" in compact:
                amount = differentiated_cash(
                    extracted["pages"], document["issuer"], document["title"]
                )
                match = unique_official_event(amount, affected, exchange)
                differentiated = True
            else:
                expected = {
                    value
                    for event in affected
                    for value in exchange.get(tuple(event.split(":")[1:]), set())
                }
                amount = gross_cash(
                    extracted["pages"], document["issuer"], expected, trusted_issuer=True
                )
                exact_match = unique_event_match(amount, affected, exchange)
                match = unique_official_event(amount, affected, exchange)
                differentiated = False
            if match is None:
                raise ValueError("NO_UNIQUE_EXCHANGE_EVENT_AMOUNT_MATCH")
        except ValueError as exc:
            outcome["status"] = str(exc)
            outcomes.append(outcome)
            continue
        outcome.update(
            status=(
                "UNIQUE_OFFICIAL_DIFFERENTIATED_COMPOSITE_MATCH"
                if differentiated
                else (
                    "UNIQUE_OFFICIAL_APPROVAL_EXCHANGE_MATCH"
                    if approved
                    else "UNIQUE_OFFICIAL_COMPOSITE_MATCH"
                )
            ),
            event=list(match),
        )
        outcomes.append(outcome)
        evidence = dict(cash_per_share=str(amount), source=document)
        if differentiated:
            evidence.update(
                holder_class="ORDINARY_EXCHANGE_TRADABLE_A_SHARE_PUBLIC_HOLDER",
                policy_id="DIFFERENTIATED_CASH_ORDINARY_PUBLIC_A_V1",
            )
        else:
            evidence["exchange_amount_corroborated"] = match == exact_match and exchange[match] == {
                amount
            }
            if approved:
                evidence["source_substitution_policy"] = APPROVAL_POLICY
        linked[match].append(evidence)

    documents_by_issuer = defaultdict(list)
    for document in documents:
        if document["retrieval_status"] == "PASS":
            documents_by_issuer[document["issuer"]].append(document)
    outcome_by_sha = {row["source_sha256"]: row for row in outcomes}
    for approval in documents:
        if approval["retrieval_status"] != "PASS" or not is_shareholder_approval_title(
            approval["title"]
        ):
            continue
        approval_cache = extraction_cache(root, approval["source_sha256"])
        approval_text = normalized_document(json.loads(approval_cache.read_bytes())["pages"])
        periods = approved_distribution_periods(approval_text)
        affected = affected_cash_events(approval, by_symbol)
        match = unique_candidate_event(affected, exchange)
        if (
            not periods
            or not match
            or any(
                item.get("approval_source", {}).get("source_sha256") == approval["source_sha256"]
                or item["source"]["source_sha256"] == approval["source_sha256"]
                for item in linked.get(match, [])
            )
        ):
            continue
        proposals = []
        for proposal in documents_by_issuer[approval["issuer"]]:
            if proposal["published_on"] > approval["published_on"] or not re.search(
                r"董事会.*决议", proposal["title"]
            ):
                continue
            proposal_cache = extraction_cache(root, proposal["source_sha256"])
            proposal_pages = json.loads(proposal_cache.read_bytes())["pages"]
            if not periods.intersection(distribution_periods(normalized_document(proposal_pages))):
                continue
            try:
                amount = gross_cash(
                    proposal_pages,
                    proposal["issuer"],
                    exchange[match],
                    trusted_issuer=True,
                )
            except ValueError:
                continue
            if (
                unique_event_match(amount, affected_cash_events(proposal, by_symbol), exchange)
                == match
            ):
                proposals.append((proposal, amount))
        if not proposals:
            continue
        proposal, amount = sorted(
            proposals, key=lambda item: (item[0]["published_on"], item[0]["url"])
        )[-1]
        linked[match].append(
            dict(
                cash_per_share=str(amount),
                source=proposal,
                approval_source=approval,
                source_substitution_policy=APPROVAL_POLICY,
                exchange_amount_corroborated=exchange[match] == {amount},
            )
        )
        outcome_by_sha[approval["source_sha256"]].update(
            status="UNIQUE_OFFICIAL_APPROVAL_PROPOSAL_EXCHANGE_MATCH", event=list(match)
        )
        outcome_by_sha[proposal["source_sha256"]].update(
            status="OFFICIAL_PROPOSAL_TERMS_USED_BY_APPROVAL_COMPOSITE", event=list(match)
        )
    for document in retrospective_documents:
        outcome = dict(
            source_sha256=document["source_sha256"],
            issuer=document["issuer"],
            title=document["title"],
        )
        try:
            if (
                document["retrieval_status"] != "PASS"
                or document.get("queue_type") != "CASH_OFFICIAL_RETROSPECTIVE_CORROBORATION"
                or not document["url"].startswith("https://static.cninfo.com.cn/finalpage/")
            ):
                raise ValueError("INVALID_RETROSPECTIVE_SOURCE")
            pdf = root / document["source_path"]
            cache = extraction_cache(root, document["source_sha256"])
            if sha256_file(pdf) != document["source_sha256"] or not cache.exists():
                raise ValueError("RETROSPECTIVE_SOURCE_CHANGED")
            extracted = json.loads(cache.read_bytes())
            originals = documents_by_issuer[document["issuer"]]
            affected = affected_cash_events(document, by_symbol)
            expected = {
                value
                for event in affected
                for value in exchange.get(tuple(event.split(":")[1:]), set())
            }
            amount = gross_cash(
                extracted["pages"], document["issuer"], expected, trusted_issuer=True
            )
            match = unique_event_match(amount, affected, exchange)
            matched_originals = (
                [
                    original
                    for original in originals
                    if f"CASH:{':'.join(match)}" in affected_cash_events(original, by_symbol)
                ]
                if match
                else []
            )
            if (
                not match
                or not matched_originals
                or not any(
                    retrospective_completion(
                        normalized_document(extracted["pages"]), original["title"], match[2]
                    )
                    for original in matched_originals
                )
            ):
                raise ValueError("NO_UNIQUE_RETROSPECTIVE_COMPLETION_MATCH")
            valid_originals = []
            for original in matched_originals:
                original_pdf = root / original["source_path"]
                original_cache = extraction_cache(root, original["source_sha256"])
                if (
                    original["published_on"] > match[1]
                    or sha256_file(original_pdf) != original["source_sha256"]
                    or not original_cache.exists()
                ):
                    continue
                try:
                    original_pages = json.loads(original_cache.read_bytes())["pages"]
                    if (
                        gross_cash(
                            original_pages,
                            original["issuer"],
                            {amount},
                            trusted_issuer=True,
                        )
                        == amount
                    ):
                        valid_originals.append(original)
                except ValueError:
                    continue
            if not valid_originals:
                raise ValueError("NO_VALID_ORIGINAL_TERMS_SOURCE")
        except ValueError as exc:
            outcome["status"] = str(exc)
            outcomes.append(outcome)
            continue
        original = sorted(
            valid_originals,
            key=lambda row: (
                not is_shareholder_approval_title(row["title"]),
                row["published_on"],
                row["url"],
            ),
        )[0]
        linked[match].append(
            dict(
                cash_per_share=str(amount),
                source=original,
                retrospective_source=document,
                source_substitution_policy=RETROSPECTIVE_POLICY,
                exchange_amount_corroborated=True,
            )
        )
        outcome.update(status="UNIQUE_OFFICIAL_RETROSPECTIVE_COMPOSITE_MATCH", event=list(match))
        outcomes.append(outcome)
    linked = {
        key: sorted(
            value,
            key=lambda item: (
                item["source"]["url"],
                item["source"]["source_sha256"],
                item.get("retrospective_source", {}).get("url", ""),
            ),
        )
        for key, value in sorted(linked.items())
    }
    return linked, sorted(outcomes, key=lambda row: (row["source_sha256"], row["status"]))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--source-manifest", type=Path, required=True)
    parser.add_argument("--sse-audit", type=Path, required=True)
    parser.add_argument("--szse-audit", type=Path, required=True)
    parser.add_argument("--master", type=Path, required=True)
    parser.add_argument("--instruments", type=Path, required=True)
    parser.add_argument("--retrospective-manifest", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    paths = [
        args.source_manifest,
        args.sse_audit,
        args.szse_audit,
        args.master,
        args.instruments,
    ]
    sources, sse, szse, master, instruments = map(verified, paths)
    retrospective = verified(args.retrospective_manifest) if args.retrospective_manifest else None
    exchange, symbol_aliases = exchange_with_historical_symbols(
        exchange_cash_amounts(sse, szse), master["records"]
    )
    retrospective_documents = retrospective["documents"] if retrospective else []
    linked, outcomes = reconcile(args.root, sources["documents"], exchange, retrospective_documents)
    reversed_result = reconcile(
        args.root,
        list(reversed(sources["documents"])),
        exchange,
        list(reversed(retrospective_documents)),
    )
    if (linked, outcomes) != reversed_result:
        raise ValueError("INPUT_ORDER_CHANGED")

    members = defaultdict(list)
    for member in master["records"]:
        members[member["symbol"]].append(member)
    ordinary = {
        row["classification"]["security_id"]["value"]
        for row in instruments["classifications"]
        if row["classification"]["instrument_type"] == "COMMON_A_SHARE"
    }
    events = []
    conflicting_events = []
    for (symbol, record_date, ex_date), evidence in sorted(linked.items()):
        evidence = authoritative_evidence(evidence)
        differentiated = any("policy_id" in item for item in evidence)
        cash_amounts = {item["cash_per_share"] for item in evidence}
        if (
            differentiated != all("policy_id" in item for item in evidence)
            or len(cash_amounts) != 1
        ):
            conflicting_events.append(
                dict(
                    symbol=symbol,
                    record_date=record_date,
                    ex_date=ex_date,
                    source_sha256=sorted(item["source"]["source_sha256"] for item in evidence),
                    reason=(
                        "CONFLICTING_COMPOSITE_CASH_CLASSIFICATION"
                        if differentiated != all("policy_id" in item for item in evidence)
                        else "CONFLICTING_COMPOSITE_CASH_TERMS"
                    ),
                )
            )
            continue
        row = dict(
            symbol=symbol,
            record_date=record_date,
            ex_date=ex_date,
            exchange_amounts=sorted(
                str(amount) for amount in exchange[symbol, record_date, ex_date]
            ),
            evidence=sorted(evidence, key=lambda item: item["source"]["url"]),
            unresolved_documents=[],
            status=(
                "SUPPORTED_ORDINARY_A_PUBLIC_TERM"
                if differentiated
                else (
                    "EXACT_GROSS_CASH_CORROBORATED"
                    if all(item["exchange_amount_corroborated"] for item in evidence)
                    else "SUPPORTED_OFFICIAL_IMPLEMENTATION_TERM"
                )
            ),
            binding_policy="OFFICIAL_EXCHANGE_DATES_PLUS_UNIQUE_ISSUER_IMPLEMENTATION_AMOUNT_V1",
        )
        if differentiated:
            row.update(
                holder_class="ORDINARY_EXCHANGE_TRADABLE_A_SHARE_PUBLIC_HOLDER",
                policy_id="DIFFERENTIATED_CASH_ORDINARY_PUBLIC_A_V1",
            )
        action = cash_event(row, members[symbol], ordinary)
        events.append(
            dict(
                event=action.model_dump(mode="json"),
                event_checksum=action.event_checksum,
                policy_id=row.get("policy_id", "EXISTING_ACCEPTED_CASH_DIVIDEND"),
                support_state=(
                    "SUPPORTED_DIFFERENTIATED_OFFICIAL_COMPOSITE_EX_DATE_CASH_POLICY"
                    if differentiated
                    else "SUPPORTED_OFFICIAL_COMPOSITE_EX_DATE_CASH_POLICY"
                ),
                metadata_only_gaps=["PAYMENT_DATE_NOT_NORMALIZED"],
                source_terms_sha256=canonical_sha256(row),
            )
        )
    report = dict(
        parser_version="OFFICIAL_COMPOSITE_CASH_GAP_RECONCILIATION_V1",
        parser_sha256=sha256_file(Path(__file__)),
        cash_parser_sha256=sha256_file(Path(reconcile_distribution_cash.__file__)),
        binding_policy="OFFICIAL_EXCHANGE_DATES_PLUS_UNIQUE_ISSUER_IMPLEMENTATION_AMOUNT_V1",
        inputs=[
            dict(path=str(path), sha256=sha256_file(path))
            for path in [*paths, *([args.retrospective_manifest] if retrospective else [])]
        ],
        document_counts=dict(sorted(Counter(row["status"] for row in outcomes).items())),
        document_results=outcomes,
        exchange_symbol_aliases=symbol_aliases,
        accepted_events=len(events),
        conflicting_composite_events=conflicting_events,
        events=events,
        input_order_reproducibility="PASS",
        full_dataset_created=False,
    )
    report["manifest_sha256"] = canonical_sha256(report)
    write_immutable(args.output, canonical_json_bytes(report) + b"\n")
    print(
        json.dumps(
            {key: value for key, value in report.items() if not isinstance(value, list)},
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
