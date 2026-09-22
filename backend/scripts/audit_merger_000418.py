"""Reverify the 000418→000333 official A-share conversion, not a merger census."""

import argparse
import json
import re
import unicodedata
from pathlib import Path

import pymupdf

from app.data.catalog.checksums import canonical_json_bytes, canonical_sha256, sha256_file
from app.data.catalog.freeze import write_immutable
from scripts.audit_merger_evidence import audit
from scripts.reconcile_merger_implementation_batch import event_from_review

TERMS = {
    "targeted-parent-fraction-v1/000418-2019-revised-merger-report.pdf": {
        61: ("零碎股处理方法", "尾数相同者多于余股", "计算机系统随机发放"),
    },
    "targeted-parent-fraction-v1/000418-2019-continuous-halt.pdf": {
        0: ("2019年5月7日为本公司股票的最后一个交易日", "2019年5月8日起开始停牌"),
    },
    "targeted-parent-fraction-v1/000333-2019-final-ratio-adjustment.pdf": {
        2: ("1:1.15144821", "除以上调整外", "其他事项均无变化"),
    },
    "batch-v1/pdf/6048ff33976e18cdaef41ff453c641707615e7251aad02eb86775eb11f258e5a.pdf": {
        3: ("1:1.15144821",),
        4: ("2019年6月21日", "321,293,876股", "2,363,600股"),
        26: ("没有投资者申报行使小天鹅A股现金选择权", "2019年6月20日"),
    },
}


def compact(text: str) -> str:
    return re.sub(r"\s+", "", unicodedata.normalize("NFKC", text))


def require_terms(pages: dict[str, dict[int, str]]) -> None:
    for path, expected_pages in TERMS.items():
        for page, expected in expected_pages.items():
            actual = compact(pages[path][page])
            if any(compact(term) not in actual for term in expected):
                raise ValueError(f"OFFICIAL_MERGER_TERM_MISMATCH:{path}:{page + 1}")


def boundary_dates(path: Path, code: str) -> list[str]:
    receipt = json.loads(path.with_suffix(path.suffix + ".meta.json").read_bytes())
    if receipt["sha256"] != sha256_file(path) or receipt["http_status"] != 200:
        raise ValueError("RAW_BOUNDARY_RECEIPT_CHANGED")
    rows = json.loads(path.read_text().split("=", 1)[-1])["data"]["sz" + code]["day"]
    dates = [row[0] for row in rows if "2019-05-01" <= row[0] <= "2019-06-30"]
    if dates != sorted(set(dates)):
        raise ValueError("RAW_BOUNDARY_DATES_INVALID")
    return dates


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("staging", "review", "master", "output"):
        parser.add_argument("--" + name, required=True, type=Path)
    args = parser.parse_args()
    review = json.loads(args.review.read_bytes())
    case = review["case"]
    event = event_from_review(case)
    sources = audit({**review, "reviewed_terms": case}, event, args.staging)
    reversed_sources = audit(
        {**review, "documents": list(reversed(review["documents"])), "reviewed_terms": case},
        event.model_copy(update={"sources": tuple(reversed(event.sources))}),
        args.staging,
    )
    if sources != reversed_sources:
        raise ValueError("INPUT_ORDER_REPRODUCIBILITY_FAILED")
    pages = {}
    for path, expected in TERMS.items():
        with pymupdf.open(args.staging / path) as document:
            pages[path] = {page: document[page].get_text() for page in expected}
    require_terms(pages)
    master = json.loads(args.master.read_bytes())
    for code, boundary, field in (
        ("000418", "2019-06-21", "effective_to"),
        ("000333", "2013-09-18", "effective_from"),
    ):
        records = [row for row in master if row["security_id"] == f"CN-A:SZSE:{code}"]
        if len(records) != 1 or records[0][field] != boundary:
            raise ValueError("MASTER_LIFECYCLE_MISMATCH")
    raw_paths = {
        code: args.staging / f"targeted-parent-fraction-v1/{code}-2019-boundary.json"
        for code in ("000418", "000333")
    }
    parent, successor = (boundary_dates(raw_paths[code], code) for code in raw_paths)
    if (
        not parent
        or parent[-1] != case["parent_last_trading_date"]
        or "2019-06-21" not in successor
    ):
        raise ValueError("TRADING_BOUNDARY_MISMATCH")
    if not (
        case["parent_last_trading_date"]
        < case["continuous_suspension_from"]
        <= case["record_date"]
        < case["effective_date"]
    ):
        raise ValueError("EVENT_DATE_ORDER_MISMATCH")
    report = {
        "parser_version": "MERGER_000418_OFFICIAL_RECOVERY_V2",
        "parser_sha256": sha256_file(Path(__file__)),
        "review_sha256": sha256_file(args.review),
        "master_sha256": sha256_file(args.master),
        "raw_boundary_sha256": {code: sha256_file(path) for code, path in raw_paths.items()},
        "event_checksum": event.event_checksum,
        "source_audit_manifest_sha256": sources["manifest_sha256"],
        "source_bytes_verified": True,
        "source_terms_verified": True,
        "input_order_reproducibility": "PASS",
        "scope": case["scope"],
        "full_census_certified": False,
        "full_dataset_created": False,
    }
    report["manifest_sha256"] = canonical_sha256(report)
    write_immutable(args.output, canonical_json_bytes(report) + b"\n")
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
