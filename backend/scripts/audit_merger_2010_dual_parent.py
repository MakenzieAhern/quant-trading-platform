"""Audit bounded 600607/600842→stable 601607 ordinary-A conversions."""

import argparse
import json
from pathlib import Path

import pymupdf

from app.data.catalog.checksums import canonical_json_bytes, canonical_sha256, sha256_file
from app.data.catalog.freeze import write_immutable
from scripts.audit_merger_600832 import compact
from scripts.audit_merger_evidence import audit
from scripts.reconcile_merger_implementation_batch import event_from_review

COMMON_TERMS = {
    "full-merger-v1/targeted-parent-fraction-v2/600849-2010-merger-report.pdf": {
        81: (
            "上实医药与上海医药的换股比例确定为1:1.61",
            "中西药业与上海医药的换股比例确定为1:0.96",
            "不足一股的余股",
        ),
    },
    "full-merger-v1/600849-2010-result.pdf": {
        0: ("2010年2月23日完成", "上市流通日期为2010年3月1日", "3月9日左右复牌交易"),
    },
    "full-code-transitions-v1/600849-implementation.pdf": {
        0: ("2010年3月5日起变更证券代码", "600849", "601607"),
    },
    "full-merger-v1/targeted-parent-fraction-v2/601607-2010-resumption.pdf": {
        0: ("2010年3月9日复牌交易", "426,736,088股"),
    },
}
PARENT_TERMS = {
    "600607": {
        "full-merger-v1/targeted-parent-fraction-v4/600607-choice-implementation.pdf": {
            0: ("2010年2月3日", "2010年2月4日起开始连续停牌"),
            6: ("未行使现金选择权", "1:1.61", "按证券登记公司相关办法处理"),
        },
        "full-merger-v1/targeted-parent-fraction-v4/600607-choice-result.pdf": {
            0: ("YKB", "160,440,885股", "没有其他股东申报行使现金选择权"),
        },
        "full-merger-v1/targeted-parent-fraction-v4/600607-choice-execution.pdf": {
            0: ("160,440,885股", "没有其他股东行使现金选择权"),
        },
        "full-merger-v1/targeted-parent-fraction-v4/600607-termination.pdf": {
            0: ("自2010年2月12日起终止", "1:1.61"),
        },
    },
    "600842": {
        "full-merger-v1/targeted-parent-fraction-v4/600842-choice-implementation.pdf": {
            0: ("2010年2月3日", "2010年2月4日起开始连续停牌"),
            6: ("未行使现金选择权", "1:0.96", "按证券登记公司相关办法处理"),
        },
        "full-merger-v1/targeted-parent-fraction-v4/600842-choice-result.pdf": {
            0: ("没有股东申报行使现金选择权",),
        },
        "full-merger-v1/targeted-parent-fraction-v4/600842-termination.pdf": {
            0: ("自2010年2月12日起终止", "1:0.96"),
        },
    },
}


def require_terms(pages: dict[str, dict[int, str]], parent: str) -> None:
    for path, expected_pages in {**COMMON_TERMS, **PARENT_TERMS[parent]}.items():
        for page, expected in expected_pages.items():
            actual = compact(pages[path][page])
            if any(compact(term) not in actual for term in expected):
                raise ValueError(f"OFFICIAL_MERGER_TERM_MISMATCH:{path}:{page + 1}")


def raw_dates(path: Path, code: str) -> list[str]:
    receipt = json.loads(path.with_suffix(path.suffix + ".meta.json").read_bytes())
    if receipt["sha256"] != sha256_file(path) or receipt["http_status"] != 200:
        raise ValueError("RAW_BOUNDARY_RECEIPT_CHANGED")
    rows = json.loads(path.read_text().split("=", 1)[-1])["data"]["sh" + code]["day"]
    dates = [row[0] for row in rows if "2010-01-01" <= row[0] <= "2010-03-15"]
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
    parent = case["parent"]
    if parent not in PARENT_TERMS or case["successor"] != "600849":
        raise ValueError("DUAL_PARENT_CASE_NOT_REVIEWED")
    event = event_from_review(case)
    sources = audit(review, event, args.staging)
    reversed_sources = audit(
        {**review, "documents": list(reversed(review["documents"]))},
        event.model_copy(update={"sources": tuple(reversed(event.sources))}),
        args.staging,
    )
    if sources != reversed_sources:
        raise ValueError("INPUT_ORDER_REPRODUCIBILITY_FAILED")
    terms = {**COMMON_TERMS, **PARENT_TERMS[parent]}
    pages = {}
    for path, expected in terms.items():
        with pymupdf.open(args.staging / path) as document:
            pages[path] = {page: document[page].get_text() for page in expected}
    require_terms(pages, parent)
    if (
        not (
            case["record_date"]
            == case["parent_last_trading_date"]
            < case["continuous_suspension_from"]
            < case["parent_delisting_date"]
            < case["registry_date"]
            < case["new_shares_listed_on"]
            < case["code_transition_date"]
            < case["effective_date"]
            == case["successor_shares_tradable_from"]
        )
        or case["successor_security_id"] != "CN-A:SSE:601607"
    ):
        raise ValueError("EVENT_DATE_OR_STABLE_ID_MISMATCH")
    master = json.loads(args.master.read_bytes())
    parent_rows = [row for row in master if row["security_id"] == f"CN-A:SSE:{parent}"]
    successor_rows = [row for row in master if row["security_id"] == case["successor_security_id"]]
    if (
        len(parent_rows) != 1
        or parent_rows[0]["effective_to"] != case["parent_delisting_date"]
        or {(row["symbol"], row["effective_from"], row["effective_to"]) for row in successor_rows}
        != {
            ("600849", case["successor_listing_date"], "2010-03-04"),
            ("601607", case["code_transition_date"], None),
        }
    ):
        raise ValueError("MASTER_LIFECYCLE_MISMATCH")
    raw_paths = {
        code: args.staging / f"full-merger-v1/targeted-parent-fraction-v4/{code}-2010-boundary.json"
        for code in (parent, "601607")
    }
    parent_dates, successor_dates = (raw_dates(raw_paths[code], code) for code in raw_paths)
    if (
        not parent_dates
        or parent_dates[-1] != case["parent_last_trading_date"]
        or case["effective_date"] not in successor_dates
        or any(
            case["continuous_suspension_from"] <= d < case["effective_date"]
            for d in successor_dates
        )
    ):
        raise ValueError("TRADING_BOUNDARY_MISMATCH")
    if case["affiliated_elector_shares_excluded"] != (160440885 if parent == "600607" else 0):
        raise ValueError("CASH_ELECTION_SCOPE_MISMATCH")
    report = {
        "parser_version": "MERGER_2010_DUAL_PARENT_RECOVERY_V1",
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
        "successor_security_id": case["successor_security_id"],
        "affiliated_elector_shares_excluded": case["affiliated_elector_shares_excluded"],
        "full_census_certified": False,
        "full_dataset_created": False,
    }
    report["manifest_sha256"] = canonical_sha256(report)
    write_immutable(args.output, canonical_json_bytes(report) + b"\n")
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
