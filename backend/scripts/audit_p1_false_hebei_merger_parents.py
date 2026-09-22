"""Reject two falsely attributed 000709 merger parents using official identities."""

import argparse
import html
import json
import re
from pathlib import Path

import pymupdf

from app.data.catalog.checksums import canonical_json_bytes, canonical_sha256, sha256_file
from app.data.catalog.freeze import write_immutable
from scripts.audit_merger_600832 import compact
from scripts.audit_p1_public_fact_requirements import verified

PARENTS = {"000761": "本钢板材", "000898": "鞍钢股份"}
ISSUER_URL = "https://static.cninfo.com.cn/finalpage/2010-01-20/57521518.PDF"
SSE_URL = "https://www.sse.com.cn/market/sseindex/diclosure/c/c_20150911_3984987.shtml"


def source(path: Path, url: str) -> dict:
    meta = json.loads(path.with_suffix(path.suffix + ".meta.json").read_bytes())
    if (
        meta.get("url") != url
        or meta.get("http_status") != 200
        or sha256_file(path) != meta["sha256"]
    ):
        raise ValueError("OFFICIAL_SOURCE_RECEIPT_CHANGED")
    return {"url": url, "sha256": meta["sha256"], "retrieved_at_utc": meta["retrieved_at_utc"]}


def classify(requirements: list[dict], master: list[dict], issuer: str, sse: str) -> list[dict]:
    issuer, sse = compact(issuer), compact(sse)
    if not all(term in issuer for term in ("股票代码:000709", "换股吸收合并邯郸钢铁和承德钒钛")):
        raise ValueError("ISSUER_MERGER_IDENTITY_CHANGED")
    if not all(term in sse for term in ("邯郸钢铁(600001)", "承德钒钛(600357)")):
        raise ValueError("SSE_PARENT_IDENTITIES_CHANGED")
    result = []
    for code, name in sorted(PARENTS.items()):
        event = f"MERGER_NEW:{code}:000709"
        matches = [row for row in requirements if row.get("affected_events") == [event]]
        rows = [row for row in master if row["security_id"] == f"CN-A:SZSE:{code}"]
        if (
            len(matches) != 1
            or matches[0]["priority"] != "P1"
            or "HEBEI_STEEL" not in " ".join(matches[0]["why_required"])
            or len(rows) != 1
            or rows[0]["symbol"] != code
            or rows[0]["source_observed_name"] != name
            or rows[0]["effective_from"] > "2010-01-25"
            or rows[0]["effective_to"] is not None
            or rows[0]["instrument_type"] != "COMMON_A_SHARE"
        ):
            raise ValueError("FALSE_PARENT_REQUIREMENT_OR_MASTER_CHANGED")
        result.append(
            {
                "document_id": matches[0]["document_id"],
                "affected_events": [event],
                "classification": "FALSE_PARENT_IDENTITY_NOT_A_MERGER_EVENT",
                "actual_official_parents": ["CN-A:SSE:600001", "CN-A:SSE:600357"],
                "unrelated_security_id": rows[0]["security_id"],
                "unrelated_security_name": name,
            }
        )
    return sorted(result, key=lambda row: row["document_id"])


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("requirements", "master", "p0-report", "issuer-pdf", "sse-notice", "output"):
        parser.add_argument("--" + name, required=True, type=Path)
    args = parser.parse_args()
    requirements, p0 = (verified(path) for path in (args.requirements, args.p0_report))
    master = json.loads(args.master.read_bytes())
    if canonical_sha256(master) != p0["reconstructed_master_sha256"]:
        raise ValueError("P0_MASTER_CHANGED")
    sources = [source(args.issuer_pdf, ISSUER_URL), source(args.sse_notice, SSE_URL)]
    with pymupdf.open(args.issuer_pdf) as document:
        issuer = "\n".join(page.get_text() for page in document)
    sse = html.unescape(re.sub(r"<[^>]*>", "", args.sse_notice.read_text()))
    rows = classify(requirements["documents"], master, issuer, sse)
    if rows != classify(
        list(reversed(requirements["documents"])), list(reversed(master)), issuer, sse
    ):
        raise ValueError("INPUT_ORDER_CHANGED")
    report = {
        "report_version": "P1_FALSE_HEBEI_MERGER_PARENTS_V1",
        "parser_sha256": sha256_file(Path(__file__)),
        "input_sha256s": {
            name: sha256_file(path)
            for name, path in (
                ("requirements", args.requirements),
                ("master", args.master),
                ("p0_report", args.p0_report),
            )
        },
        "official_sources": sources,
        "closed": rows,
        "new_economic_events_created": 0,
        "inventory_admitted": False,
        "full_census_certified": False,
        "full_dataset_created": False,
        "input_order_reproducibility": "PASS",
    }
    report["manifest_sha256"] = canonical_sha256(report)
    write_immutable(args.output, canonical_json_bytes(report) + b"\n")
    print(json.dumps({key: value for key, value in report.items() if key != "closed"}))


if __name__ == "__main__":
    main()
