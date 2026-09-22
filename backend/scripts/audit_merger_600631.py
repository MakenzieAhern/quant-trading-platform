"""Audit the bounded 600631→600827 ordinary-A non-electing conversion."""

import argparse
import json
from pathlib import Path

import pymupdf

from app.data.catalog.checksums import canonical_json_bytes, canonical_sha256, sha256_file
from app.data.catalog.freeze import write_immutable
from scripts.audit_merger_600832 import compact
from scripts.audit_merger_evidence import audit
from scripts.reconcile_merger_implementation_batch import event_from_review

TERMS = {
    "targeted-parent-fraction-v2/600827-2011-revised-merger-report.pdf": {
        76: ("1\u22360.861", "不足一股的余股", "上交所关于余股处理"),
    },
    "targeted-parent-fraction-v3/600631-2011-cash-choice-implementation.pdf": {
        0: ("2011年8月4日为本公司股票的最后一个交易日", "2011年8月5日起开始连续停牌"),
        5: ("未行使现金选择权", "1:0.861"),
        6: ("按证券登记公司相关办法处理",),
    },
    "older-merger-metadata-v1/59762741.pdf": {
        0: ("2011年8月5日", "2011年8月4日为本公司股票最后一个交易日"),
    },
    "targeted-parent-fraction-v3/600631-2011-cash-choice-result.pdf": {
        0: ("没有股东申报行使现金选择权",),
    },
    "batch-v1/pdf/04f8be7484ab606f380c916e80fbc0bd3ab9769ca6440e50c05d1f389e463c98.pdf": {
        0: ("自2011年8月23日起终止上市", "1:0.861"),
    },
    "targeted-parent-fraction-v2/600827-2011-result.pdf": {
        0: ("2011年8月26日完成", "2011年8月31日"),
        1: ("新增无限售条件流通股上市流通时间为2011年8月31日",),
    },
}


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
    rows = json.loads(path.read_text().split("=", 1)[-1])["data"]["sh" + code]["day"]
    dates = [row[0] for row in rows if "2011-07-01" <= row[0] <= "2011-09-02"]
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
    sources = audit(review, event, args.staging)
    reversed_sources = audit(
        {**review, "documents": list(reversed(review["documents"]))},
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
    if not (
        case["record_date"]
        == case["parent_last_trading_date"]
        < case["continuous_suspension_from"]
        < case["parent_delisting_date"]
        < case["registry_date"]
        < case["effective_date"]
        == case["successor_shares_tradable_from"]
    ):
        raise ValueError("EVENT_DATE_ORDER_MISMATCH")
    master = json.loads(args.master.read_bytes())
    for code, expected, field in (
        ("600631", case["parent_delisting_date"], "effective_to"),
        ("600827", case["successor_listing_date"], "effective_from"),
    ):
        records = [row for row in master if row["security_id"] == f"CN-A:SSE:{code}"]
        if len(records) != 1 or records[0][field] != expected:
            raise ValueError("MASTER_LIFECYCLE_MISMATCH")
    raw_paths = {
        code: args.staging / f"targeted-parent-fraction-v3/{code}-2011-boundary.json"
        for code in ("600631", "600827")
    }
    parent, successor = (boundary_dates(raw_paths[code], code) for code in raw_paths)
    if (
        not parent
        or parent[-1] != case["parent_last_trading_date"]
        or case["effective_date"] not in successor
    ):
        raise ValueError("TRADING_BOUNDARY_MISMATCH")
    report = {
        "parser_version": "MERGER_600631_OFFICIAL_RECOVERY_V2",
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
