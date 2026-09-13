"""Checkpoint official historical distribution tables; never promote rows to events."""

import argparse
import json
from pathlib import Path
from urllib.parse import urlencode

from app.data.catalog.checksums import canonical_json_bytes, canonical_sha256, sha256_file
from app.data.catalog.freeze import write_immutable
from scripts.reconcile_sse_cninfo import fetch


def checked_rows(pages):
    totals = {p["pageHelp"]["total"] for p in pages}
    rows = [r for p in pages for r in p["result"]]
    if totals != {len(rows)} or len({canonical_sha256(r) for r in rows}) != len(rows):
        raise ValueError("DISTRIBUTION_PAGINATION_INCOMPLETE_OR_DUPLICATED")
    return sorted(rows, key=canonical_sha256)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--current", action="store_true")
    args = parser.parse_args()
    records, failures = [], []
    for kind, sql in (
        ("dividend", "COMMON_SSE_GP_SJTJ_FHSG_AGFH_L_NEW"),
        ("bonus", "COMMON_SSE_GP_SJTJ_FHSG_SG_L_NEW"),
    ):
        for year in range(2022 if args.current else 2010, 2026):
            pages, sources = [], []
            page = 1
            try:
                while True:
                    query = {
                        "isPagination": "true",
                        "pageHelp.pageSize": 1000,
                        "pageHelp.pageNo": page,
                        "pageHelp.beginPage": page,
                        "pageHelp.cacheSize": 1,
                        "pageHelp.endPage": page,
                        "sqlId": sql,
                    }
                    query.update(
                        {"record_date_a": str(year), "security_code_a": ""}
                        if kind == "dividend"
                        else {"year1": str(year), "year2": str(year), "company_code": ""}
                    )
                    if args.current:
                        for key in (
                            "record_date_a",
                            "security_code_a",
                            "year1",
                            "year2",
                            "company_code",
                        ):
                            query.pop(key, None)
                        query.update(
                            dict(
                                sqlId="COMMON_SSE_SJ_GPSJ_FHSG_SSGSFHQK_L",
                                CONDITION_AG=1,
                                A_REG_DATE=str(year),
                            )
                            if kind == "dividend"
                            else dict(sqlId="COMMON_SSE_SJ_GPSJ_FHSG_SG_L", SEARCH_YEAR=str(year))
                        )
                    surface = "current" if args.current else "batch"
                    if args.current and year == 2022:
                        surface = "current-batch"
                    name = f"{kind}-{year}-{surface}-p{page:03}.json"
                    raw = fetch(
                        args.root,
                        name,
                        "https://query.sse.com.cn/commonQuery.do?" + urlencode(query),
                        referer="https://www.sse.com.cn/",
                    )
                    data = json.loads(raw)
                    pages.append(data)
                    sources.append(json.loads((args.root / (name + ".meta.json")).read_bytes()))
                    if sum(len(p["result"]) for p in pages) >= data["pageHelp"]["total"]:
                        break
                    if not data["result"] or page >= 100:
                        raise ValueError("DISTRIBUTION_PAGINATION_STALLED")
                    page += 1
                rows = checked_rows(pages)
                if rows != checked_rows(list(reversed(pages))):
                    raise ValueError("INPUT_ORDER_CHANGED")
                records.append(dict(kind=kind, year=year, rows=rows, sources=sources))
                print(kind, year, len(rows), flush=True)
            except Exception as exc:
                failures.append(dict(kind=kind, year=year, error=f"{type(exc).__name__}: {exc}"))
                print(kind, year, failures[-1]["error"], flush=True)
    report = dict(
        parser_version="SSE_DISTRIBUTION_CENSUS_V3",
        parser_sha256=sha256_file(Path(__file__)),
        status="SOURCE_ROWS_ONLY_NOT_ACCEPTED_EVENTS",
        records=records,
        failures=failures,
        full_dataset_created=False,
        full_dataset_frozen=False,
    )
    report["manifest_sha256"] = canonical_sha256(report)
    name = "source-census-current-v3.json" if args.current else "source-census-historical-v3.json"
    write_immutable(args.root / name, canonical_json_bytes(report) + b"\n")


if __name__ == "__main__":
    main()
