"""Close 000732 no-row dates using its original designated-paper issuer notice."""

import argparse
import json
import re
import unicodedata
from collections import Counter
from pathlib import Path

import pymupdf

from scripts.reconcile_sse_cninfo import canonical, save, sha

BASE_SHA = "c0612a6f95e0726c16caa42217a7e563eda876fd273f40c1b3f8de7f8d53fc8a"
SOURCES = {
    "cninfo_query": (
        "1abe46eb7498b25b07fbe21700aa496714e960716bc0b6274c6d1cdb026e9c1b",
        "https://www.cninfo.com.cn/new/hisAnnouncement/query",
    ),
    "designated_paper": (
        "50d68eb468aeb32a226d53ecc2057c510c945d4a35bb2d44a61601105b9eb23d",
        "https://epaper.stcn.com/paper/zqsb/page/1/2010-09-21/B011/46401285013079368.pdf",
    ),
    "szse_designation": (
        "351795ac6f8626a1891c6f099a2b22b33d7b809be356f22cd2208380ca8d1b33",
        "https://disc.static.szse.cn/disc/disk01/finalpage/2010-10-18/f9668df4-481c-4b49-85f5-0c05205b2f2d.PDF",
    ),
}
SECURITY_ID = "CN-A:SZSE:000732"
START = "2007-05-11"
END = "2010-09-30"
NOTICE_HEADER = "证券代码:000732证券简称:*ST三农公告编号:2010-29号"
NEXT_HEADER = "证券代码:000732证券简称:*ST三农公告编号:2010-30号"


def normalized(text: str) -> str:
    return re.sub(r"\s+", "", unicodedata.normalize("NFKC", text))


def notice_block(page_text: str) -> str:
    text = normalized(page_text)
    if text.count(NOTICE_HEADER) != 1 or text.count(NEXT_HEADER) != 1:
        raise ValueError("DESIGNATED_PAPER_NOTICE_BOUNDARY_CHANGED")
    start, end = text.index(NOTICE_HEADER), text.index(NEXT_HEADER)
    block = text[start:end]
    if start >= end or not all(
        term in block
        for term in (
            "福建三农集团股份有限公司关于公司股票恢复上市的公告",
            "公司选定的信息披露报纸:《证券时报》《中国证券报》",
            "深证上[2010]310号",
            "本所决定你公司股票自2010年9月30日起恢复上市",
            "因2004、2005、2006年连续三年亏损,公司股票自2007年5月11日起被深交所暂停上市",
            "福建三农集团股份有限公司董事会2010年9月20日",
        )
    ):
        raise ValueError("DESIGNATED_PAPER_OFFICIAL_INTERVAL_NOT_PROVEN")
    return block


def source(path: Path, name: str) -> tuple[bytes, dict]:
    expected_sha, url = SOURCES[name]
    raw = path.read_bytes()
    receipt = json.loads(path.with_name(path.name + ".meta.json").read_bytes())
    if (
        sha(raw) != expected_sha
        or receipt["sha256"] != expected_sha
        or receipt["url"] != url
        or receipt["http_status"] != 200
        or not receipt["retrieved_at_utc"].endswith("+00:00")
        or (name != "cninfo_query" and not raw.startswith(b"%PDF-"))
    ):
        raise ValueError(f"OFFICIAL_SOURCE_CHANGED:{name}")
    return raw, {
        "url": url,
        "sha256": expected_sha,
        "receipt_sha256": sha(path.with_name(path.name + ".meta.json").read_bytes()),
        "retrieved_at_utc": receipt["retrieved_at_utc"],
    }


def close_report(base: dict, evidence: dict, notice_sha: str, expected_rows: int = 177) -> dict:
    if (
        base["report_version"] != "SZSE_OFFICIAL_ROW_GAPS_CORRECTED_V3"
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
            row["reason"] != "NO_MATCHING_HALT_SOURCE" or not START <= row["date"] < END
            for row in matched
        )
    ):
        raise ValueError("SOURCE_INTERVAL_OR_COUNT_CHANGED:000732")
    counts = Counter(base["classification_counts"])
    counts["NO_MATCHING_HALT_SOURCE"] -= len(matched)
    counts["OFFICIAL_PRE2010_LISTING_SUSPENSION"] += len(matched)
    remaining = [row for row in base["unresolved_rows"] if row["security_id"] != SECURITY_ID]
    if min(counts.values()) < 0 or sum(counts.values()) != base["missing_rows"]:
        raise ValueError("MISSING_ROW_CONSERVATION_FAILED")
    report = {
        **base,
        "report_version": "SZSE_OFFICIAL_ROW_GAPS_CORRECTED_V4",
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
                "classification": "OFFICIAL_PRE2010_LISTING_SUSPENSION",
                "evidence_temporality": "ORIGINAL_2010_RETROSPECTIVE_2007_NOT_SIGNAL_INPUT",
                "issuer_notice_block_sha256": notice_sha,
                "cninfo_original_pdf_bytes_verified": False,
                "evidence": evidence["pdfs"],
                "cninfo_official_notice_index": evidence["cninfo_official_notice_index"],
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
    for name in ("base-report", "cninfo-query", "designated-paper", "szse-designation", "output"):
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
    query_raw, query_source = source(args.cninfo_query, "cninfo_query")
    paper_raw, paper_source = source(args.designated_paper, "designated_paper")
    designation_raw, designation_source = source(args.szse_designation, "szse_designation")
    query = json.loads(query_raw)
    matches = [
        row
        for row in query["announcements"]
        if row["secCode"] == "000732"
        and row["announcementId"] == "58461621"
        and row["announcementTitle"] == "关于公司股票恢复上市的公告"
        and row["adjunctUrl"] == "finalpage/2010-09-21/58461621.PDF"
        and row["announcementTime"] == 1285021800000
    ]
    if len(matches) != 1:
        raise ValueError("CNINFO_ISSUER_NOTICE_INDEX_NOT_UNIQUE")
    with pymupdf.open(stream=paper_raw, filetype="pdf") as paper:
        if len(paper) != 1:
            raise ValueError("DESIGNATED_PAPER_PAGE_COUNT_CHANGED")
        block = notice_block(paper[0].get_text())
    with pymupdf.open(stream=designation_raw, filetype="pdf") as designation:
        if len(designation) != 1 or not all(
            token in normalized(designation[0].get_text())
            for token in (
                "证券代码:000732",
                "福建三农集团股份有限公司",
                "《中国证券报》《证券时报》和巨潮资讯网",
                "为公司选定的信息披露媒体",
            )
        ):
            raise ValueError("SZSE_HOSTED_ISSUER_DESIGNATION_CHANGED")
    report = close_report(
        base,
        {
            "cninfo_official_notice_index": {
                **query_source,
                "announcement_id": "58461621",
                "indexed_original_pdf_url": "https://static.cninfo.com.cn/finalpage/2010-09-21/58461621.PDF",
                "indexed_original_pdf_bytes_verified": False,
            },
            "pdfs": [
                {**paper_source, "pdf_page": 1, "role": "original_issuer_designated_paper"},
                {**designation_source, "pdf_page": 1, "role": "szse_hosted_issuer_designation"},
            ],
        },
        sha(block.encode()),
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
