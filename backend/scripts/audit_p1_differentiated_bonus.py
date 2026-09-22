"""Cross-check differentiated issuer bonus notices without accepting accounting."""

import argparse
import json
import re
import unicodedata
from collections import Counter
from datetime import date
from decimal import Decimal
from pathlib import Path

from app.data.catalog.checksums import canonical_json_bytes, canonical_sha256, sha256_file
from app.data.catalog.freeze import write_immutable
from scripts.audit_p1_public_fact_requirements import verified
from scripts.reconcile_distribution_cash import issuer_code_matches


def terms(pages):
    original = unicodedata.normalize("NFKC", "\n".join(pages))
    text = re.sub(r"\s+", "", original)
    header = text[:1800]
    amounts = {
        Decimal(value)
        for value in re.findall(r"每股(?:转增(?:股份)?|派送红股)(\d+(?:\.\d+)?)股", header)
    } | {
        Decimal(value) / 10
        for value in re.findall(r"每10股(?:以资本公积(?:金)?)?(?:转增|送)(\d+(?:\.\d+)?)股", header)
    }
    dates = set()
    for match in re.findall(r"(20\d{2})/(\d{1,2})/(\d{1,2})", original):
        try:
            dates.add(date(*map(int, match)).isoformat())
        except ValueError:
            continue
    no_cash = bool(
        re.search(
            r"不派发现金红利|不进行现金分红|不派发现金股利|现金红利为0|"
            r"不分配现金|不派现|不进行红利派发|不分配利润|每10股派发现金红利(?:人民币)?0元",
            text,
        )
    )
    return (
        amounts,
        dates,
        no_cash,
        "RED_STOCK_DIVIDEND" if "每股派送红股" in header else "CAPITAL_RESERVE_CONVERSION",
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    for name in (
        "differentiated",
        "triage",
        "closure",
        "oracle",
        "master",
        "source-manifest",
        "source-root",
        "output",
    ):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    diff, triage, closure, oracle, sources = (
        verified(path)
        for path in (
            args.differentiated,
            args.triage,
            args.closure,
            args.oracle,
            args.source_manifest,
        )
    )
    master = json.loads(args.master.read_bytes())
    if any(
        diff["input_sha256s"][name] != sha256_file(path)
        for name, path in (
            ("triage", args.triage),
            ("closure", args.closure),
            ("master", args.master),
            ("source_manifest", args.source_manifest),
        )
    ):
        raise ValueError("DIFFERENTIATED_BONUS_INPUT_CHANGED")
    by_id = {row["document_id"]: row for row in triage["documents"]}
    by_req = {row["document_id"]: row for row in closure["remaining_cash_documents"]}
    by_url = {row["url"]: row for row in sources["documents"]}
    if (
        len(by_id) != len(triage["documents"])
        or len(by_req) != len(closure["remaining_cash_documents"])
        or len(by_url) != len(sources["documents"])
        or len({(row["symbol"], row["record_date"], row["ex_date"]) for row in oracle["rows"]})
        != len(oracle["rows"])
    ):
        raise ValueError("DIFFERENTIATED_BONUS_IDENTITY_AMBIGUOUS")
    by_symbol = {}
    for row in oracle["rows"]:
        by_symbol.setdefault(row["symbol"], []).append(row)
    classified = []
    for item in diff["classifications"]:
        if item["status"] != "MISSING_FINAL_IMPLEMENTATION_TERMS":
            continue
        row, requirement, source = (
            by_id[item["document_id"]],
            by_req[item["document_id"]],
            by_url[item["url"]],
        )
        pdf = Path(source["source_path"])
        if not pdf.is_absolute():
            pdf = args.source_root / pdf
        pdf = pdf.resolve()
        cache = args.source_root / "batch-v1/text" / f"{row['source_sha256']}.json"
        if (
            not pdf.is_relative_to(args.source_root.parent.resolve())
            or source["retrieval_status"] != "PASS"
            or source["issuer"] != requirement["issuer"]
            or source["title"] != requirement["title"]
            or source["published_on"] != requirement["published_on"]
            or sha256_file(pdf) != row["source_sha256"]
            or sha256_file(cache) != row["text_cache_sha256"]
        ):
            raise ValueError(f"DIFFERENTIATED_BONUS_SOURCE_CHANGED:{row['document_id']}")
        extracted = json.loads(cache.read_bytes())
        if extracted["source_sha256"] != row["source_sha256"]:
            raise ValueError("DIFFERENTIATED_BONUS_TEXT_CHANGED")
        amounts, dates, no_cash, action_type = terms(extracted["pages"])
        matches = [
            candidate
            for candidate in by_symbol.get(requirement["issuer"], [])
            if requirement["published_on"]
            <= candidate["record_date"]
            < candidate["ex_date"]
            <= "2025-12-31"
            and {candidate["record_date"], candidate["ex_date"]} == dates
            and {Decimal(e["ratio"]) for e in candidate["evidence"]} == amounts
            and candidate["ratio_consistency"] == "SINGLE_DISPLAYED_RATIO"
        ]
        result = {
            "document_id": row["document_id"],
            "issuer": requirement["issuer"],
            "url": row["url"],
            "source_sha256": row["source_sha256"],
            "text_cache_sha256": row["text_cache_sha256"],
            "cash_explicitly_zero": no_cash,
            "action_type": action_type,
        }
        if (
            not issuer_code_matches("\n".join(extracted["pages"]), requirement["issuer"])
            or len(matches) != 1
        ):
            result["status"] = "OFFICIAL_TERMS_NOT_UNIQUE"
        else:
            matched = matches[0]
            identities = {
                member["security_id"]
                for member in master
                if member["symbol"] == requirement["issuer"]
                and member["instrument_type"] == "COMMON_A_SHARE"
                and member["effective_from"]
                <= matched["record_date"]
                < matched["ex_date"]
                <= (member["effective_to"] or "2025-12-31")
            }
            result.update(
                record_date=matched["record_date"],
                ex_date=matched["ex_date"],
                bonus_ratio=str(next(iter(amounts))),
                exchange_evidence_sha256=matched["evidence_sha256"],
            )
            result["status"] = (
                "EXPLICIT_ZERO_CASH_BONUS_SOURCE_TERMS_ACCOUNTING_PENDING"
                if no_cash and len(identities) == 1
                else "CASH_OR_IDENTITY_NOT_CLOSED"
            )
            if len(identities) == 1:
                result["security_id"] = next(iter(identities))
        classified.append(result)
    classified.sort(key=lambda row: row["document_id"])
    if len(classified) != diff["classification_counts"]["MISSING_FINAL_IMPLEMENTATION_TERMS"]:
        raise ValueError("DIFFERENTIATED_BONUS_CLASSIFICATION_INCOMPLETE")
    report = {
        "report_version": "P1_DIFFERENTIATED_BONUS_SOURCE_TERMS_V1",
        "parser_sha256": sha256_file(Path(__file__)),
        "input_sha256s": {
            name: sha256_file(path)
            for name, path in (
                ("differentiated", args.differentiated),
                ("triage", args.triage),
                ("closure", args.closure),
                ("oracle", args.oracle),
                ("master", args.master),
                ("source_manifest", args.source_manifest),
            )
        },
        "candidate_documents": len(classified),
        "classification_counts": dict(sorted(Counter(row["status"] for row in classified).items())),
        "action_type_counts": dict(
            sorted(Counter(row["action_type"] for row in classified).items())
        ),
        "classified": classified,
        "new_economic_events_created": 0,
        "p1_requirements_closed": 0,
        "input_order_reproducibility": "NOT_REPLAYED",
    }
    report["manifest_sha256"] = canonical_sha256(report)
    write_immutable(args.output, canonical_json_bytes(report) + b"\n")
    print(json.dumps({key: value for key, value in report.items() if key != "classified"}))


if __name__ == "__main__":
    main()
