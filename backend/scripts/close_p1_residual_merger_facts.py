"""Close residual merger facts supported by retained official CNINFO bytes."""

import argparse
import json
import re
import unicodedata
from pathlib import Path

import pymupdf

from app.data.catalog.checksums import canonical_json_bytes, canonical_sha256, sha256_file
from app.data.catalog.freeze import write_immutable
from scripts.audit_p1_public_fact_requirements import verified

POLICY = "CN_A_MERGER_FRACTIONAL_SHARE_POLICY_V1"

CASES = {
    "MERGER:000578:000792": {
        "classification": "OFFICIAL_LINKED_DISTRIBUTION_AND_MERGER_CHAIN",
        "facts": {
            "parent_security_id": "CN-A:SZSE:000578",
            "successor_security_id": "CN-A:SZSE:000792",
            "eligible_public_share_bonus_ratio": "0.2071671",
            "bonus_registration_date": "2011-03-09",
            "parent_last_trading_date": "2011-02-18",
            "merger_record_date": "2011-03-15",
            "conversion_ratio": "1/2.90",
            "converted_shares_queryable_from": "2011-03-16",
            "converted_shares_tradable_from": "2011-03-28",
            "official_fractional_method": "GLOBAL_REMAINDER_RANKING_RANDOM_TIES",
            "research_fractional_method": ("FLOOR_NO_CASH_COMPENSATION_RESEARCH_CONVENTION"),
        },
        "documents": (
            (
                "000578-additional-share-v1/59050230.pdf",
                "d07defd66ea17065d166ac451352cd2256a2bf19a1d4326fad9629b89b751cd7",
                ("每10股将获得2.071671股追送股份",),
            ),
            (
                "000578-additional-share-v1/59107015.pdf",
                "3eec399726b2082fbdee80c8e6d662d807929d0a7f43a923dbcb352d4492924c",
                ("本次追加对价股份变更登记日为2011年3月9日",),
            ),
            (
                (
                    "batch-v1/pdf/"
                    "765cbfd3cf051a910fba626f808c440909da19476a930f26c7052ff9955b1ae2.pdf"
                ),
                "5cce6de76bf8d0d5eaddaa303af178fb875f00d0e59bd62370185b26316192ce",
                (
                    "换股变更登记日为2011年3月15日",
                    "2.90股盐湖集团股份将转换为1股盐湖钾肥的股份",
                    "不足1股的零碎股",
                ),
            ),
            (
                (
                    "batch-v1/pdf/"
                    "e6320bf6cab61dc64a9ea934cd6e4d41495e0a2f27ad7e09d80f78a8fa7edf50.pdf"
                ),
                "9ec122484a407753f964a78ce4581346de8abb5f08fb73e54b8f2274cc07dd5b",
                ("2011年3月28日(周一)起上市",),
            ),
        ),
    },
    "MERGER_NEW:600253:600056": {
        "classification": "OFFICIAL_PARENT_IMPLEMENTATION_AND_LISTING_CHAIN",
        "facts": {
            "parent_security_id": "CN-A:SSE:600253",
            "successor_security_id": "CN-A:SSE:600056",
            "parent_last_trading_date": "2013-06-06",
            "parent_termination_date": "2013-07-15",
            "conversion_ratio": "0.313",
            "registration_completed_date": "2013-07-26",
            "converted_shares_tradable_from": "2013-08-01",
            "official_fractional_method": "NOT_INDIVIDUALLY_REPRODUCIBLE",
            "research_fractional_method": ("FLOOR_NO_CASH_COMPENSATION_RESEARCH_CONVENTION"),
        },
        "documents": (
            (
                "older-merger-metadata-v1/62559538.pdf",
                "f5b1e310c3ed6f3640b5e2bfd61170b04e4987712c04773b6b6d2a64c4eaa59c",
                ("2013年6月6日为本公司股票最后一个交易日",),
            ),
            (
                "older-merger-metadata-v1/62823703.pdf",
                "6ce015c4c6570e048b52153b8f3cc35eef674763f3c24e272d8506e77ec86844",
                ("2013年7月15日起终止本公司股票上市交易", "按照1:0.313的比例自动转换"),
            ),
            (
                (
                    "batch-v1/pdf/"
                    "e91265a2d73d7f53f6d2b3e4b66f3883868ee80b9b77a72bb8f8c1d8fe9209f3.pdf"
                ),
                "cf1ea099c123bdd90cf1eaebde9a2da1b9d06c969fbb1bc13cc257f24dbc4e93",
                (
                    "2013年7月26日",
                    "办理完成了新增股份的登记过户手续",
                    "上市流通日期为2013年08月01日",
                ),
            ),
        ),
    },
}


def compact(value: str) -> str:
    return re.sub(r"\s+", "", unicodedata.normalize("NFKC", value))


def verify_documents(staging: Path, cases: dict = CASES) -> dict:
    evidence = {}
    for event_id, case in cases.items():
        documents = []
        for relative, expected_sha, terms in case["documents"]:
            path = staging / relative
            if sha256_file(path) != expected_sha:
                raise ValueError(f"OFFICIAL_MERGER_SOURCE_CHANGED:{relative}")
            receipt = json.loads(path.with_suffix(path.suffix + ".meta.json").read_bytes())
            if receipt["http_status"] != 200 or receipt["sha256"] != expected_sha:
                raise ValueError(f"OFFICIAL_MERGER_RECEIPT_CHANGED:{relative}")
            with pymupdf.open(path) as document:
                text = compact("".join(page.get_text() for page in document))
            missing = [term for term in terms if compact(term) not in text]
            if missing:
                raise ValueError(f"OFFICIAL_MERGER_TERMS_MISSING:{relative}")
            documents.append(
                {
                    "path": relative,
                    "url": receipt["url"],
                    "sha256": expected_sha,
                    "retrieved_at_utc": receipt["retrieved_at_utc"],
                    "verified_terms": list(terms),
                }
            )
        evidence[event_id] = documents
    return evidence


def close(requirements: dict, evidence: dict, cases: dict = CASES) -> dict:
    closed = []
    for event_id, case in sorted(cases.items()):
        matches = [
            row for row in requirements["documents"] if row.get("affected_events") == [event_id]
        ]
        if len(matches) != 1 or matches[0]["priority"] != "P1":
            raise ValueError(f"P1_MERGER_REQUIREMENT_NOT_UNIQUE:{event_id}")
        documents = evidence.get(event_id)
        if not documents or len(documents) != len(case["documents"]):
            raise ValueError(f"P1_MERGER_EVIDENCE_INCOMPLETE:{event_id}")
        facts = {**case["facts"], "policy": POLICY}
        closed.append(
            {
                "document_id": matches[0]["document_id"],
                "affected_events": [event_id],
                "classification": case["classification"],
                "facts": facts,
                "fact_checksum": canonical_sha256(facts),
                "documents": documents,
            }
        )
    return {
        "closed": closed,
        "closed_facts": len(closed),
        "new_economic_events_created": 0,
        "approved_policy_reused": POLICY,
        "input_order_reproducibility": "PASS",
        "full_census_certified": False,
        "full_dataset_created": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--requirements", required=True, type=Path)
    parser.add_argument("--staging", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    requirements = verified(args.requirements)
    evidence = verify_documents(args.staging)
    report = close(requirements, evidence)
    if report != close(requirements, dict(reversed(tuple(evidence.items())))):
        raise ValueError("INPUT_ORDER_CHANGED")
    report.update(
        report_version="P1_RESIDUAL_MERGER_FACT_CLOSURE_V2",
        parser_sha256=sha256_file(Path(__file__)),
        requirements_sha256=sha256_file(args.requirements),
    )
    report["manifest_sha256"] = canonical_sha256(report)
    write_immutable(args.output, canonical_json_bytes(report) + b"\n")
    print(json.dumps({key: value for key, value in report.items() if key != "closed"}))


if __name__ == "__main__":
    main()
