"""Bounded official SZSE daily-OHLCV controls; no full-range source promotion."""

import argparse
from io import BytesIO
from pathlib import Path
from urllib.parse import urlencode

from openpyxl import load_workbook

from scripts.reconcile_sse_cninfo import fetch, save

CONTROLS = (
    ("2010-01-04", "1815_stock"),
    ("2023-04-10", "1815_stock"),
    ("2025-08-29", "1815_stock"),
    ("2025-09-01", "1815_stock_snapshot"),
    ("2025-12-31", "1815_stock_snapshot"),
)
HEADERS = (
    "交易日期",
    "证券代码",
    "证券简称",
    "前收",
    "开盘",
    "最高",
    "最低",
    "今收",
    "涨跌幅\uff08%\uff09",
    "成交量(万股)",
    "成交金额(万元)",
    "市盈率",
)


def inspect(raw: bytes, day: str) -> dict[str, object]:
    workbook = load_workbook(BytesIO(raw), read_only=True, data_only=True)
    sheet = workbook.active
    # SZSE currently emits an incorrect <dimension ref="A1" />.
    sheet.reset_dimensions()
    rows = sheet.values
    if tuple(next(rows)) != HEADERS:
        raise ValueError("unexpected official SZSE daily-export columns")
    count = 0
    codes = set()
    sample = None
    for row in rows:
        if row[0] != day or not isinstance(row[1], str) or row[1] in codes:
            raise ValueError("SZSE daily-export date/code mismatch or duplicate")
        codes.add(row[1])
        count += 1
        if row[1] == "000001":
            sample = dict(zip(HEADERS, row, strict=True))
    if not count or sample is None:
        raise ValueError("empty official SZSE daily export or missing control")
    return {"rows": count, "unique_codes": len(codes), "control_000001": sample}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = {"status": "BOUNDED_PROBE_ONLY_NOT_ACCEPTED", "controls": []}
    for day, catalog in CONTROLS:
        query = {
            "SHOWTYPE": "XLSX",
            "CATALOGID": catalog,
            "txtBeginDate": day,
            "TABKEY": "tab1",
        }
        if catalog == "1815_stock_snapshot":
            query["txtEndDate"] = day
        url = "https://www.szse.cn/api/report/ShowReport?" + urlencode(query)
        referer = (
            "https://www.szse.cn/market/trend/"
            + ("archive/" if catalog == "1815_stock" else "")
            + "index.html"
        )
        raw = fetch(args.output, day + ".xlsx", url, referer=referer)
        result = {"date": day, "catalog": catalog, **inspect(raw, day)}
        report["controls"].append(result)
        save(args.output / "report.json", report)
        print(f"{day}: {result['rows']} unique securities", flush=True)


if __name__ == "__main__":
    main()
