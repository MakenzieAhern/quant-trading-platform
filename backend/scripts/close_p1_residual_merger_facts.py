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
    "MERGER:000522:600332": {
        "classification": "OFFICIAL_CROSS_MARKET_MERGER_WITH_PENDING_ENTITLEMENT",
        "facts": {
            "parent_security_id": "CN-A:SZSE:000522",
            "successor_security_id": "CN-A:SSE:600332",
            "merger_record_date": "2013-04-26",
            "parent_termination_date": "2013-04-26",
            "conversion_ratio": "0.95",
            "converted_shares_tradable_from": "2013-05-23",
            "official_fractional_method": "NOT_INDIVIDUALLY_REPRODUCIBLE",
            "research_fractional_method": ("FLOOR_NO_CASH_COMPENSATION_RESEARCH_CONVENTION"),
            "accounting_policy": "NON_TRADABLE_PENDING_ACCOUNTING_V1",
            "boundary_policy": "FIRST_POST_EVENT_TRADING_BOUNDARY_V1",
            "account_scope": "EXISTING_ORDINARY_A_SHARE_CASH_ACCOUNT_MODEL",
            "exception_treatment": "SUPPLEMENTAL_REGISTRATION_PENDING",
        },
        "documents": (
            (
                (
                    "batch-v1/pdf/"
                    "0b2e3b903227144634fd83910b7cc3302c1048f5636982feeb63d3c3bd300718.pdf"
                ),
                "8224260c2906e450c17f93eb9d4c95d35fbc06df1763d9b4ce22901badb7172d",
                (
                    "本次换股吸收合并的换股股权登记日为2013年4月26日",
                    "每1股白云山股份可换取0.95股广州药业的A股股份",
                    "余股补登记完成后",
                    "相应股份于次一交易日内在上海证券交易所上市流通",
                ),
            ),
            (
                (
                    "batch-v1/pdf/"
                    "34003fd31bf24d8b767f7503e4eded2356bd50e17ec26cb70973a930ecf19891.pdf"
                ),
                "8107b66af8cae17d5ba950f9cf0304a7f794c40659450fdb58290e882e766ab9",
                (
                    "广州药业本次新增A股股份上市流通日期为2013年5月23日",
                    "未完成初始登记的原白云山投资者所持有的转换后的广州药业A股股票暂时不能上市交易",
                ),
            ),
        ),
    },
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
    "MERGER:002013:600372": {
        "classification": "OFFICIAL_CROSS_MARKET_MERGER_WITH_PENDING_ENTITLEMENT",
        "facts": {
            "parent_security_id": "CN-A:SZSE:002013",
            "successor_security_id": "CN-A:SSE:600372",
            "merger_record_date": "2023-03-16",
            "parent_termination_date": "2023-03-17",
            "conversion_ratio": "0.6647",
            "registration_completed_date": "2023-04-13",
            "converted_shares_tradable_from": "2023-04-19",
            "official_fractional_method": "GLOBAL_REMAINDER_RANKING_RANDOM_TIES",
            "research_fractional_method": ("FLOOR_NO_CASH_COMPENSATION_RESEARCH_CONVENTION"),
            "accounting_policy": "NON_TRADABLE_PENDING_ACCOUNTING_V1",
            "boundary_policy": "FIRST_POST_EVENT_TRADING_BOUNDARY_V1",
            "account_scope": "EXISTING_ORDINARY_A_SHARE_CASH_ACCOUNT_MODEL",
            "exception_treatment": "SELL_ONLY_ACCOUNT_OR_SUPPLEMENTAL_REGISTRATION_PENDING",
        },
        "documents": (
            (
                (
                    "batch-v1/pdf/"
                    "7ef89e89f492b6bf51bae6e565da291259c1ebc105aa934249682b96dbf5849a.pdf"
                ),
                "81694ee8c91683932fa759c1559cd7ece5a712c821d19917fb74b8bed45af7d0",
                (
                    "本次吸收合并的换股股权登记日为2023年3月16日",
                    "每1股中航机电股票将转换为0.6647股中航电子股票",
                    "向每一位股东依次发放一股",
                ),
            ),
            (
                "2022-2023-boundary-v1/1216135996.pdf",
                "4b9718e035130bb6fc69049cff969cdeebda0a65f8c5bc6e9ac44f4ca9085c9b",
                (
                    "配发账户仅能用于持有、卖出证券",
                    "投资者后续取得原托管机构确认后",
                    "向中航电子提交补登记申请",
                ),
            ),
            (
                (
                    "batch-v1/pdf/"
                    "e1b76287da64503647d354649122a8640ef4bb61d146348fb5b8c1fab267cd41.pdf"
                ),
                "bf814210966eface055120ca0ae96601299837278396c53b0f412ae2c0afd578",
                (
                    "2023年4月13日取得中国证券登记结算有限责任公司上海分公司出具的《证券变更登记证明》",
                    "本次合并后新增无限售流通股的上市流通日期为2023年4月19日",
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
        report_version="P1_RESIDUAL_MERGER_FACT_CLOSURE_V3",
        parser_sha256=sha256_file(Path(__file__)),
        requirements_sha256=sha256_file(args.requirements),
    )
    report["manifest_sha256"] = canonical_sha256(report)
    write_immutable(args.output, canonical_json_bytes(report) + b"\n")
    print(json.dumps({key: value for key, value in report.items() if key != "closed"}))


if __name__ == "__main__":
    main()
