"""Corroborate two zero-cash differentiated transfers without booking shares."""

import argparse
import hashlib
import json
import re
import unicodedata
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import pymupdf

from app.data.catalog.checksums import canonical_json_bytes, canonical_sha256, sha256_file
from app.data.catalog.freeze import write_immutable
from scripts.audit_p1_public_fact_requirements import verified

CASES = (
    (
        "603703",
        "2023-04-21",
        "盛洋科技2022年度利润分配预案公告",
        "603703-2023-04-21-cs-paper-b103.pdf",
        "https://epaper.cs.com.cn/zgzqb/images/2023-04/21/B103/zqB10321.pdf",
        "de47f86dbf2befc1a088e187ee08cbf0352c75dbdbe35d5b5b7bef943af610dd",
    ),
    (
        "688368",
        "2024-04-18",
        "上海晶丰明源半导体股份有限公司2023年度利润分配及资本公积转增股本方案公告",
        "688368-2024-05-08-shareholder-material.pdf",
        "https://static.cninfo.com.cn/finalpage/2024-04-26/1219823808.PDF",
        "93f0ea0b97bae2c24f53c3756f34ab1e28a850c8fe37dba9041943b026d84606",
    ),
)


def compact(text: str) -> str:
    return re.sub(r"\s+", "", unicodedata.normalize("NFKC", text))


def source(root: Path, name: str, url: str) -> tuple[Path, dict]:
    path = root / name
    meta_path = path.with_suffix(path.suffix + ".meta.json")
    meta = json.loads(meta_path.read_bytes())
    if (
        meta["url"] != url
        or meta.get("error")
        or meta["http_status"] != 200
        or sha256_file(path) != meta["sha256"]
    ):
        raise ValueError(f"SOURCE_RECEIPT_INVALID:{name}")
    return path, {
        "url": url,
        "sha256": meta["sha256"],
        "receipt_sha256": sha256_file(meta_path),
        "retrieved_at_utc": meta["retrieved_at_utc"],
    }


def plan_block(code: str, path: Path) -> str:
    with pymupdf.open(path) as pdf:
        if code == "688368":
            if len(pdf) != 34:
                raise ValueError("SHAREHOLDER_MATERIAL_PAGE_COUNT_CHANGED")
            block = compact(pdf[12].get_text())
            required = (
                "公司2023年度资本公积转增股本预案的议案",
                "不进行现金分红,不送红股",
                "每10股转增4股",
                "回购专用证券账户",
                "2024年5月8日",
            )
        else:
            if len(pdf) != 1:
                raise ValueError("DESIGNATED_PAPER_PAGE_COUNT_CHANGED")
            text = compact(pdf[0].get_text())
            marker = "证券代码:603703"
            starts = [match.start() for match in re.finditer(marker, text)]
            matches = [
                start
                for start in starts
                if "公告编号:2023-013" in text[start : start + 150]
                and "2022年度利润分配预案公告" in text[start : start + 200]
            ]
            if len(matches) != 1:
                raise ValueError("ORIGINAL_ISSUER_NOTICE_NOT_UNIQUE")
            start = matches[0]
            end = text.find(marker, start + len(marker))
            block = text[start : end if end >= 0 else len(text)]
            required = (
                "浙江盛洋科技股份有限公司2022年度利润分配预案公告",
                "拟不进行现金分红和送红股",
                "每10股转增4股",
                "回购专用账户股份7,679,700股",
                "本次利润分配预案尚需提交公司2022年年度股东大会审议",
                "2023年4月21日",
            )
    if not all(token in block for token in required):
        raise ValueError(f"ZERO_CASH_PLAN_TERMS_NOT_UNIQUE:{code}")
    return block


def audit(root: Path, implementation_root: Path, baseline: dict, cases: tuple) -> dict:
    unresolved = {
        row["issuer"]: row
        for row in baseline["classified"]
        if row["status"] == "CASH_OR_IDENTITY_NOT_CLOSED"
    }
    if set(unresolved) != {"603703", "688368"} or len(baseline["classified"]) != 22:
        raise ValueError("BASELINE_UNRESOLVED_SET_CHANGED")
    rows = []
    for code, day, title, filename, url, final_sha in cases:
        index_name = f"{code}-{day}-sse-index.json"
        index_path = root / index_name
        index_meta = json.loads(index_path.with_suffix(".json.meta.json").read_bytes())
        query = parse_qs(urlparse(index_meta["url"]).query)
        if (
            not index_meta["url"].startswith(
                "https://query.sse.com.cn/security/stock/queryCompanyBulletinNew.do?"
            )
            or query.get("SECURITY_CODE") != [code]
            or query.get("START_DATE") != [day]
            or query.get("END_DATE") != [day]
        ):
            raise ValueError(f"SSE_INDEX_QUERY_CHANGED:{code}")
        _, index_receipt = source(root, index_name, index_meta["url"])
        index = json.loads(index_path.read_bytes())
        if index["pageHelp"]["pageCount"] != 1:
            raise ValueError(f"SSE_OFFICIAL_PLAN_INDEX_INCOMPLETE:{code}")
        matches = [
            row
            for group in index["pageHelp"]["data"]
            for row in group
            if row.get("SECURITY_CODE") == code
            and row.get("SSEDATE") == day
            and row.get("TITLE") == title
        ]
        if len(matches) != 1 or not matches[0]["URL"].startswith(
            "/disclosure/listedinfo/announcement/"
        ):
            raise ValueError(f"SSE_OFFICIAL_PLAN_INDEX_NOT_UNIQUE:{code}")
        plan_path, plan_receipt = source(root, filename, url)
        block = plan_block(code, plan_path)
        final = unresolved[code]
        if final["source_sha256"] != final_sha or final["bonus_ratio"] != "0.4":
            raise ValueError(f"FINAL_IMPLEMENTATION_IDENTITY_CHANGED:{code}")
        cache_path = implementation_root / "batch-v1/text" / f"{final_sha}.json"
        if sha256_file(cache_path) != final["text_cache_sha256"]:
            raise ValueError(f"FINAL_IMPLEMENTATION_CACHE_CHANGED:{code}")
        cache = json.loads(cache_path.read_bytes())
        final_text = compact("\n".join(cache["pages"]))
        if cache["source_sha256"] != final_sha or not all(
            token in final_text
            for token in (
                "每股转增0.4股",
                "股权登记日",
                "除权(息)日",
                "回购专用",
            )
        ):
            raise ValueError(f"FINAL_IMPLEMENTATION_TERMS_CHANGED:{code}")
        if code == "603703":
            if "(前收盘价格-0)" not in final_text or "2022年年度股东大会审议通过" not in final_text:
                raise ValueError("603703_FINAL_ZERO_CASH_CORROBORATION_CHANGED")
        elif "2024年5月8日的2023年年度股东大会审议通过" not in final_text:
            raise ValueError("688368_SHAREHOLDER_APPROVAL_CHANGED")
        rows.append(
            {
                "issuer": code,
                "security_id": final["security_id"],
                "document_id": final["document_id"],
                "record_date": final["record_date"],
                "ex_date": final["ex_date"],
                "bonus_ratio": final["bonus_ratio"],
                "classification": "OFFICIAL_ZERO_CASH_CORROBORATED_ACCOUNTING_PENDING",
                "plan_block_sha256": hashlib.sha256(block.encode()).hexdigest(),
                "sse_index": index_receipt,
                "sse_plan_url": "https://static.sse.com.cn" + matches[0]["URL"],
                "sse_plan_pdf_bytes_verified": False,
                "official_plan_or_issuer_notice": plan_receipt,
                "final_implementation_url": final["url"],
                "final_implementation_sha256": final_sha,
                "final_text_cache_sha256": final["text_cache_sha256"],
            }
        )
    rows.sort(key=lambda row: row["issuer"])
    return {
        "report_version": "P1_DIFFERENTIATED_ZERO_CASH_CORROBORATION_V2",
        "classification": "22_OF_22_ZERO_CASH_SOURCE_TERMS_CORROBORATED_ACCOUNTING_PENDING",
        "baseline_explicit_zero_cash": 20,
        "newly_corroborated_zero_cash": len(rows),
        "remaining_cash_source_unresolved": 0,
        "rows": rows,
        "p1_requirements_closed": 0,
        "new_economic_events_created": 0,
        "fractional_share_accounting": "HUMAN_METHODOLOGY_DECISION_REQUIRED",
        "input_order_reproducibility": "PASS",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("baseline", "source-root", "implementation-root", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    baseline = verified(args.baseline)
    report = audit(args.source_root, args.implementation_root, baseline, CASES)
    if report != audit(args.source_root, args.implementation_root, baseline, CASES[::-1]):
        raise ValueError("INPUT_ORDER_CHANGED")
    report["baseline_sha256"] = sha256_file(args.baseline)
    report["parser_sha256"] = sha256_file(Path(__file__))
    report["manifest_sha256"] = canonical_sha256(report)
    write_immutable(args.output, canonical_json_bytes(report) + b"\n")
    print(json.dumps({key: value for key, value in report.items() if key != "rows"}))


if __name__ == "__main__":
    main()
