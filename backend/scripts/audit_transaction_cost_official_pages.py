"""Bind retained official transaction-cost pages to the R5 evidence ledger."""

import argparse
import html
import json
import re
import unicodedata
from pathlib import Path

from app.data.catalog.checksums import canonical_json_bytes, canonical_sha256, sha256_file
from app.data.catalog.freeze import write_immutable

SOURCES = (
    {
        "file": "chinaclear-transfer-fee-2012-04.pdf",
        "url": "https://www.chinaclear.cn/old_files/1335773025208.pdf",
        "retrieved_at_utc": "2026-09-19T18:20:36.290254+00:00",
        "sha256": "c569a05620befe5bd008d3bb9aed07c883d2e30b82fbb6b88ba46e626e4aab60",
        "format": "PDF",
        "page": 1,
        "validation": "SHA256_PLUS_VISUAL_PAGE_REVIEW",
        "claims": [
            "SSE_TRANSFER_2012_06_01_FACE_VALUE_0.375_PER_MILLE",
            "SZSE_TRANSFER_NOTIONAL_0.0255_PER_MILLE_UNCHANGED",
        ],
    },
    {
        "file": "chinaclear-transfer-fee-2012-08.pdf",
        "url": "https://www.chinaclear.cn/old_files/1343899420865.pdf",
        "retrieved_at_utc": "2026-09-19T18:20:35.685819+00:00",
        "sha256": "755ec86ff5974f62c9b001f5a5a7f4fa46e91ff8b2181ebadbfe8abb45657e6e",
        "format": "PDF",
        "page": 1,
        "validation": "SHA256_PLUS_VISUAL_PAGE_REVIEW",
        "claims": [
            "SSE_TRANSFER_2012_09_01_FACE_VALUE_0.3_PER_MILLE",
            "SZSE_TRANSFER_NOTIONAL_0.0255_PER_MILLE_UNCHANGED",
        ],
    },
    {
        "file": "csrc-2012-04-30.html",
        "url": "https://www.csrc.gov.cn/csrc/c100028/c1002502/content.shtml",
        "retrieved_at_utc": "2026-09-19T17:06:05Z",
        "sha256": "26d4671c896d797ceaffbbc0f3f0359a35c42c7cd487e8bacc84414ef3314d45",
        "tokens": ("0.087‰", "成交面额的0.375‰", "6月1日实施"),
    },
    {
        "file": "sse-regulator-2012.html",
        "url": "https://www.sse.com.cn/aboutus/mediacenter/hotandd/c/c_20150912_3988604.shtml",
        "retrieved_at_utc": "2026-09-19T17:06:07Z",
        "sha256": "3acd79ef5ed3d40af36604c81ef36baaee697318f6d358a8bddfcd48f5a23d6b",
        "tokens": ("2012年1月1日起", "0.04‰", "0.02‰"),
    },
    {
        "file": "szse-handling-2012-09.html",
        "url": "https://www.szse.cn/aboutus/trends/news/t20120802_518315.html",
        "retrieved_at_utc": "2026-09-19T17:06:05Z",
        "sha256": "6649ebac5fef17aba268355c17554dd0ac2b88f936f7530aadd560f6adaad83d",
        "tokens": ("2012年9月1日", "0.087‰", "0.0696‰"),
    },
    {
        "file": "sse-costs-2015-08.html",
        "url": "https://www.sse.com.cn/aboutus/mediacenter/hotandd/c/c_20150912_3988866.shtml",
        "retrieved_at_utc": "2026-09-19T17:06:06Z",
        "sha256": "68d86fbded6d151eac74501ed285ce7c24a0746cd09a791ea927d81172266796",
        "tokens": ("成交面值0.3‰", "成交金额0.0255‰", "8月1日起正式实施"),
    },
    {
        "file": "csrc-guangdong-commission-scope-2012.html",
        "url": "https://www.csrc.gov.cn/guangdong/c100961/c1294826/content.shtml",
        "retrieved_at_utc": "2026-09-20T03:22:08Z",
        "sha256": "63fac201a039ae3f0ff044d5e92f907c5cd5cee51d8b5928883892078ed352e0",
        "tokens": (
            "按照净佣金(不含规费)方式收取证券交易佣金",
            "名义上约定按全佣金(包含规费)方式收取证券交易佣金",
            "按照客户佣金实际收取方式",
        ),
    },
    {
        "file": "csrc-commission-scope-2023.html",
        "url": "https://www.csrc.gov.cn/csrc/c105938/c905d6f8c17234a5e8c17e41de0d05e8f/content.shtml",
        "retrieved_at_utc": "2026-09-19T17:06:05Z",
        "sha256": "8e52a93ee4a4912ac5a2c39d04b0abd32d0f4820fa36d172f74477b3fd34697d",
        "tokens": ("2015年7月9日", "成交金额的0.002%", "该费用已实际包含在佣金中"),
    },
)


def normalized_text(raw: bytes) -> str:
    text = re.sub(r"<[^>]+>", "", raw.decode("utf-8"))
    return unicodedata.normalize("NFKC", html.unescape(text)).replace(" ", "").replace("\n", "")


def validate_tokens(text: str, tokens: tuple[str, ...]) -> None:
    missing = [token for token in tokens if token not in text]
    if missing:
        raise ValueError(f"OFFICIAL_SOURCE_TOKENS_MISSING:{missing}")


def validate_source(source_root: Path, item: dict) -> None:
    path = source_root / item["file"]
    if sha256_file(path) != item["sha256"]:
        raise ValueError(f"OFFICIAL_SOURCE_CHANGED:{item['file']}")
    if tokens := item.get("tokens"):
        validate_tokens(normalized_text(path.read_bytes()), tokens)


def audit(source_root: Path) -> dict:
    sources = []
    for item in SOURCES:
        validate_source(source_root, item)
        sources.append({key: value for key, value in item.items() if key != "tokens"})
    body = {
        "report_id": "FULL_TRANSACTION_COST_OFFICIAL_SOURCES_V5",
        "status": "PARTIAL_ACCOUNT_CONTRACT_AND_INTERVAL_SCOPE",
        "requested_coverage": ["2010-01-01", "2025-12-31"],
        "parser_version": "transaction-cost-official-pages-v5",
        "sources": sources,
        "accepted_claims": [
            "SSE_TRANSFER_2012_06_01_FACE_VALUE_0.375_PER_MILLE",
            "SSE_TRANSFER_2012_09_01_FACE_VALUE_0.3_PER_MILLE",
            "SZSE_TRANSFER_NOTIONAL_0.0255_PER_MILLE_UNCHANGED_IN_2012",
            "HANDLING_2012_06_01",
            "REGULATOR_2012_01_01",
            "HANDLING_2012_09_01",
            "HANDLING_AND_TRANSFER_2015_08_01",
            "POST_2015_TRANSFER_INCLUDED_IN_COMMISSION_ACCOUNT_EXAMPLE",
            "CUSTOMER_COMMISSION_NET_OR_ALL_IN_DEPENDS_ON_ACCOUNT_AGREEMENT_AND_PRACTICE",
        ],
        "resolved_claim_groups": [
            "TRANSFER_2012_BASE_CONTRADICTION",
            "CUSTOMER_COMMISSION_PUBLIC_RULE_SCOPE",
        ],
        "authority_resolution": {
            "conflict": "CSRC_2012_NEWS_SAID_TRADED_AMOUNT",
            "accepted_source": "CHINACLEAR_2012_OPERATIVE_NOTICES",
            "accepted_basis": "TRADED_FACE_VALUE",
            "reason": "FEE_COLLECTOR_ORIGINAL_OPERATIVE_NOTICE_CONTROLS_NEWS_SUMMARY",
        },
        "remaining_gaps": [
            "TRANSFER_MINIMUM_AFTER_REDUCTIONS",
            "TRANSFER_PRE_2015_EFFECTIVE_INTERVALS",
            "FULL_PERIOD_NON_HANDLING_INTERVAL_COMPLETENESS",
        ],
        "human_input_required": ["RESEARCH_COMMISSION_CONVENTION_OR_ACCOUNT_CONTRACT"],
        "input_order_reproducibility": "PASS",
        "source_checksum_repeatability": "PASS",
        "full_transaction_cost_authority": "PARTIAL",
        "executable_rules_changed": False,
        "dataset_or_strategy_run": False,
    }
    return {**body, "manifest_sha256": canonical_sha256(body)}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = audit(args.source_root)
    write_immutable(args.output, canonical_json_bytes(report) + b"\n")
    print(json.dumps({key: report[key] for key in ("status", "manifest_sha256")}))


if __name__ == "__main__":
    main()
