"""Audit the bounded 600832→600637 ordinary-A non-electing conversion."""

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
    "targeted-parent-fraction-v2/600637-2015-revised-merger-report.pdf": {
        46: ("换股比例为3.05:1",),
        47: ("取得的百视通之股份应为整数",),
    },
    "targeted-parent-fraction-v2/600832-2015-cash-choice-result.pdf": {
        0: ("没有异议股东申报行使现金选择权",),
        1: ("文广科技和尚世影业已事先出具承诺", "自愿行使现金选择权"),
    },
    "targeted-parent-fraction-v2/600637-2015-progress.pdf": {
        0: ("2015年4月30日起开始停牌", "股权登记日为2015年5月20日"),
        2: ("小数点后尾数大小排序", "计算机系统随机发放"),
    },
    "targeted-parent-fraction-v2/600637-2015-result.pdf": {
        0: ("每3.05股东方明珠股份换1股百视通新增股份", "2015年6月3日", "2015年5月27日"),
    },
    "targeted-parent-fraction-v2/600637-2016-tradability-confirmation.pdf": {
        4: ("于2015年6月3日上市流通",),
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
    rows = json.loads(path.read_text().split("=", 1)[-1])["data"]["sh" + code]["day"]
    dates = [row[0] for row in rows if "2015-04-01" <= row[0] <= "2015-06-10"]
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
        case["parent_last_trading_date"]
        < case["continuous_suspension_from"]
        <= case["record_date"]
        < case["registry_date"]
        < case["effective_date"]
        == case["successor_shares_tradable_from"]
    ):
        raise ValueError("EVENT_DATE_ORDER_MISMATCH")
    master = json.loads(args.master.read_bytes())
    for code, expected, field in (
        ("600832", case["parent_delisting_date"], "effective_to"),
        ("600637", case["successor_listing_date"], "effective_from"),
    ):
        records = [row for row in master if row["security_id"] == f"CN-A:SSE:{code}"]
        if len(records) != 1 or records[0][field] != expected:
            raise ValueError("MASTER_LIFECYCLE_MISMATCH")
    raw_paths = {
        code: args.staging / f"targeted-parent-fraction-v2/{code}-2015-boundary.json"
        for code in ("600832", "600637")
    }
    parent, successor = (boundary_dates(raw_paths[code], code) for code in raw_paths)
    if (
        not parent
        or parent[-1] != case["parent_last_trading_date"]
        or "2015-06-03" not in successor
    ):
        raise ValueError("TRADING_BOUNDARY_MISMATCH")
    retrospective = next(
        row for row in review["documents"] if row.get("audit_only_after_effective_date")
    )
    if retrospective["published_on"] <= case["effective_date"] or any(
        source.sha256 == retrospective["sha256"] for source in event.sources
    ):
        raise ValueError("RETROSPECTIVE_SOURCE_LEAKAGE")
    report = {
        "parser_version": "MERGER_600832_OFFICIAL_RECOVERY_V2",
        "parser_sha256": sha256_file(Path(__file__)),
        "review_sha256": sha256_file(args.review),
        "master_sha256": sha256_file(args.master),
        "raw_boundary_sha256": {code: sha256_file(path) for code, path in raw_paths.items()},
        "event_checksum": event.event_checksum,
        "source_audit_manifest_sha256": sources["manifest_sha256"],
        "source_bytes_verified": True,
        "source_terms_verified": True,
        "retrospective_confirmation_audit_only": True,
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
