"""Close 002075 no-row dates with original SZSE suspension/restoration notices."""

import argparse
import json
import re
import unicodedata
from collections import Counter
from pathlib import Path

import pymupdf

from scripts.reconcile_sse_cninfo import canonical, save, sha

BASE_SHA = "85d19024f2781cdaa50a766ebbe1e6302938830005ec088a9b798dd22dc07a44"
SOURCES = {
    "suspension": (
        "1f248ba308629a85ac6436bf0c83a1adfcfd81d7a2045d0bd6460e92ad083b02",
        "https://epaper.stcn.com/paper/zqsb/page/1/2010-04-30/A005/15261272570054687.pdf",
        "2010-04-30",
    ),
    "restoration": (
        "da36a8ecbd4a3e91ec2f46dc79a30600dc9176ef1d8c6abdb1fe43e7309bd8c2",
        "https://epaper.stcn.com/paper/zqsb/page/1/2011-03-30/A011/26641301427899657.pdf",
        "2011-03-30",
    ),
}
SECURITY_ID = "CN-A:SZSE:002075"
START = "2010-05-07"
END = "2011-04-08"


def notice_block(page_text: str, title: str, next_title: str, required: tuple[str, ...]) -> str:
    text = re.sub(r"\s+", "", unicodedata.normalize("NFKC", page_text))
    if text.count(title) != 1 or text.count(next_title) != 1:
        raise ValueError("ORIGINAL_EXCHANGE_NOTICE_BOUNDARY_CHANGED")
    start, end = text.index(title), text.index(next_title)
    block = text[start:end]
    if start >= end or not all(term in block for term in required):
        raise ValueError("ORIGINAL_EXCHANGE_INTERVAL_NOT_PROVEN")
    return block


def source(path: Path, name: str) -> tuple[bytes, dict]:
    expected_sha, url, published_on = SOURCES[name]
    raw = path.read_bytes()
    receipt = json.loads(path.with_name(path.name + ".meta.json").read_bytes())
    if (
        not raw.startswith(b"%PDF-")
        or sha(raw) != expected_sha
        or receipt["sha256"] != expected_sha
        or receipt["url"] != url
        or receipt["http_status"] != 200
        or not receipt["retrieved_at_utc"].endswith("+00:00")
    ):
        raise ValueError(f"ORIGINAL_EXCHANGE_SOURCE_CHANGED:{name}")
    return raw, {
        "url": url,
        "sha256": expected_sha,
        "receipt_sha256": sha(path.with_name(path.name + ".meta.json").read_bytes()),
        "retrieved_at_utc": receipt["retrieved_at_utc"],
        "published_on": published_on,
        "pdf_page": 1,
        "role": name + "_exchange_notice",
    }


def close_report(
    base: dict, evidence: list[dict], block_hashes: list[str], expected_rows: int = 216
) -> dict:
    if (
        base["report_version"] != "SZSE_OFFICIAL_ROW_GAPS_CORRECTED_V4"
        or base["raw_authority_promoted"]
    ):
        raise ValueError("WRONG_BASE_REPORT")
    if any(item["security_id"] == SECURITY_ID for item in base["official_intervals"]):
        raise ValueError("DUPLICATE_OFFICIAL_INTERVAL")
    matched = [row for row in base["unresolved_rows"] if row["security_id"] == SECURITY_ID]
    if (
        len(matched) != expected_rows
        or len({row["date"] for row in matched}) != expected_rows
        or any(
            row["reason"] != "UNKNOWN_RESUMPTION_NOT_CLOSED" or not START <= row["date"] < END
            for row in matched
        )
    ):
        raise ValueError("SOURCE_INTERVAL_OR_COUNT_CHANGED:002075")
    counts = Counter(base["classification_counts"])
    counts["UNKNOWN_RESUMPTION_NOT_CLOSED"] -= len(matched)
    counts["OFFICIAL_2010PLUS_LISTING_SUSPENSION"] += len(matched)
    remaining = [row for row in base["unresolved_rows"] if row["security_id"] != SECURITY_ID]
    if min(counts.values()) < 0 or sum(counts.values()) != base["missing_rows"]:
        raise ValueError("MISSING_ROW_CONSERVATION_FAILED")
    report = {
        **base,
        "report_version": "SZSE_OFFICIAL_ROW_GAPS_CORRECTED_V5",
        "parser_sha256": sha(Path(__file__).read_bytes()),
        "base_report_sha256": BASE_SHA,
        "base_manifest_sha256": base["manifest_sha256"],
        "classification_counts": dict(sorted(counts.items())),
        "official_intervals": [
            *base["official_intervals"],
            {
                "security_id": SECURITY_ID,
                "suspended_from": START,
                "first_trading_day": END,
                "corrected_closed_rows": len(matched),
                "classification": "OFFICIAL_2010PLUS_LISTING_SUSPENSION",
                "evidence_temporality": "ORIGINAL_EXCHANGE_NOTICES_NOT_SIGNAL_INPUT",
                "notice_block_sha256": block_hashes,
                "evidence": evidence,
            },
        ],
        "unresolved_rows": remaining,
        "unresolved_symbols": dict(
            sorted(Counter(row["security_id"].split(":")[-1] for row in remaining).items())
        ),
        "unresolved_by_year": dict(sorted(Counter(row["date"][:4] for row in remaining).items())),
        "raw_authority_promoted": False,
    }
    report.pop("manifest_sha256")
    report["manifest_sha256"] = sha(canonical(report))
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("base-report", "suspension-pdf", "restoration-pdf", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    base_raw = args.base_report.read_bytes()
    base = json.loads(base_raw)
    if (
        sha(base_raw) != BASE_SHA
        or sha(canonical({key: value for key, value in base.items() if key != "manifest_sha256"}))
        != base["manifest_sha256"]
    ):
        raise ValueError("AUDITED_BASE_REPORT_CHANGED")
    suspension_raw, suspension_source = source(args.suspension_pdf, "suspension")
    restoration_raw, restoration_source = source(args.restoration_pdf, "restoration")
    with pymupdf.open(stream=suspension_raw, filetype="pdf") as document:
        if len(document) != 1 or "2010年4月30日星期五" not in re.sub(
            r"\s+", "", unicodedata.normalize("NFKC", document[0].get_text())
        ):
            raise ValueError("SUSPENSION_PAPER_MASTHEAD_CHANGED")
        suspension = notice_block(
            document[0].get_text(),
            "关于高新张铜股份有限公司股票暂停上市的公告",
            "编者按:",
            (
                "高新张铜股份有限公司2007年、2008年、2009年连续三年亏损",
                "本所决定该公司股票自2010年5月7日起暂停上市",
                "深圳证券交易所二O一O年四月二十八日",
            ),
        )
    with pymupdf.open(stream=restoration_raw, filetype="pdf") as document:
        if len(document) != 1 or "2011年3月30日星期三" not in re.sub(
            r"\s+", "", unicodedata.normalize("NFKC", document[0].get_text())
        ):
            raise ValueError("RESTORATION_PAPER_MASTHEAD_CHANGED")
        restoration = notice_block(
            document[0].get_text(),
            "关于同意江苏沙钢股份有限公司股票恢复上市的公告",
            "关于支付2009年辽宁省政府债券",
            (
                "江苏沙钢股份有限公司(原高新张铜股份有限公司)",
                "本所决定江苏沙钢股份有限公司(原高新张铜股份有限公司)股票自2011年4月8日起恢复上市",
                "深圳证券交易所二O一一年三月三十日",
            ),
        )
    report = close_report(
        base,
        [suspension_source, restoration_source],
        [sha(suspension.encode()), sha(restoration.encode())],
    )
    save(args.output, report)
    print(
        json.dumps(
            {
                "classification_counts": report["classification_counts"],
                "unresolved_rows": len(report["unresolved_rows"]),
                "unresolved_symbols": len(report["unresolved_symbols"]),
                "manifest_sha256": report["manifest_sha256"],
            }
        )
    )


if __name__ == "__main__":
    main()
