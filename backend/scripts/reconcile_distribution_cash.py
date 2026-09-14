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


def cash_event(row, members, ordinary_ids):
    values = {Decimal(e["cash_per_share"]) for e in row["evidence"]}
    if (
        row["status"] != "EXACT_GROSS_CASH_CORROBORATED"
        or row["unresolved_documents"]
        or len(values) != 1
        or values != {Decimal(a) for a in row["exchange_amounts"]}
    ):
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
    evidence = sorted(row["evidence"], key=lambda e: e["source"]["url"])
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
            source_provider="OFFICIAL_ISSUER_CNINFO_EXCHANGE_RECONCILED",
            source_version="GROSS_CASH_OFFICIAL_V1",
            source_record_hash=canonical_sha256(canonical_row),
            completeness="COMPLETE",
        )
    )
    require_supported_corporate_action(action)
    if CorporateAction.model_validate_json(action.model_dump_json()) != action:
        raise ValueError("CASH_EVENT_SERIALIZATION_CHANGED")
    return action


def gross_cash(pages, symbol):
    normalized = unicodedata.normalize("NFKC", "\n".join(pages))
    header = re.search(
        r"(?:证券|股票|公司)代码(?:\(A/H\))?\s*:\s*((?:\d[ \t]*){6})(?!\d)",
        normalized[:600],
    )
    if not header or re.sub(r"\s+", "", header[1]) != symbol:
        raise ValueError("CASH_ISSUER_HEADER_MISMATCH")
    text = re.sub(r"\s+", "", normalized)
    if re.search(r"差异化分红送转:是", text):
        raise ValueError("DIFFERENTIATED_DISTRIBUTION_REQUIRES_REVIEW")
    number = r"(\d+(?:\.\d+)?)"
    base = r"每(10|1)?股(?:送(?:红股)?\d+(?:\.\d+)?股[、,])?"
    matches = []
    for pattern in (
        base + r"(?:派发|派送|派)?(?:现金红利|现金股利|现金股息|红利|股息|现金)"
        r"(?:人民币)?" + number + r"元(?:人民币)?(?:现金红利)?\(含税[);,]",
        base + r"派(?:发|送)?(?:人民币)?" + number + r"元(?:人民币)?现金(?:红利|股利)?\(含税[);,]",
        base + r"派(?:发|送)?" + number + r"元\(含税[);,]",
    ):
        for denominator, value in re.findall(pattern, text):
            with localcontext() as ctx:
                ctx.prec = 50
                matches.append(Decimal(value) / Decimal(denominator or "1"))
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
        evidence, failures = [], []
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
                amount = gross_cash(extracted["pages"], link["symbol"])
                evidence.append(dict(cash_per_share=str(amount), source=doc))
            except ValueError as exc:
                failures.append(dict(source_sha256=sha, reason=str(exc)))
        values = {Decimal(e["cash_per_share"]) for e in evidence}
        status = (
            "EXACT_GROSS_CASH_CORROBORATED"
            if len(values) == 1 and values == amounts and not failures
            else "UNRESOLVED_CASH_TERMS"
        )
        results.append(
            dict(
                symbol=key[0],
                record_date=key[1],
                ex_date=key[2],
                exchange_amounts=sorted(str(a) for a in amounts),
                evidence=evidence,
                unresolved_documents=failures,
                status=status,
            )
        )
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
            != "3784d6817fb7ab30081e57d9693bc1ac7adbfbaccebe200e2903e7021d8a0352"
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
            if row["status"] != "EXACT_GROSS_CASH_CORROBORATED":
                continue
            try:
                event = cash_event(row, by_symbol[row["symbol"]], ordinary)
                if event != cash_event(row, list(reversed(by_symbol[row["symbol"]])), ordinary):
                    raise ValueError("CASH_MASTER_ORDER_CHANGED")
                accepted.append(
                    dict(
                        event=event.model_dump(mode="json"),
                        event_checksum=event.event_checksum,
                        policy_id="EXISTING_ACCEPTED_CASH_DIVIDEND",
                        support_state="SUPPORTED_EXISTING_EX_DATE_CASH_POLICY",
                        metadata_only_gaps=["PAYMENT_DATE_NOT_NORMALIZED"],
                        source_terms_sha256=canonical_sha256(row),
                    )
                )
            except ValueError as exc:
                row["acceptance_issue"] = str(exc)
        inputs.extend([args.master, args.instruments, policy])
    report = dict(
        parser_version="DISTRIBUTION_GROSS_CASH_RECONCILIATION_V1",
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
