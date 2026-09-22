"""Reconcile one SZSE/Pilot day with official block trades; do not promote authority."""

import argparse
import json
import re
import warnings
from collections import defaultdict
from decimal import Decimal
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from openpyxl import load_workbook

from scripts.reconcile_sse_cninfo import canonical, save, sha

DAY = "2023-04-10"
ZERO = Decimal(0)
GUIDANCE_URL = "https://investor.szse.cn/index/update/t20200827_581076.html"
TECHNICAL_URL = "https://www.szse.cn/marketServices/technicalservice/notice/t20200508_576947.html"


class Text(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []

    def handle_data(self, data: str) -> None:
        self.parts.append(data)


def number(value: object) -> Decimal:
    return Decimal(str(value).replace(",", ""))


def workbook(path: Path) -> list[tuple]:
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", message="Workbook contains no default style")
        book = load_workbook(path, read_only=True, data_only=True)
    sheet = book.active
    sheet.reset_dimensions()  # SZSE exports an incorrect A1-only dimension.
    return list(sheet.values)


def official_source(path: Path, url: str, required: tuple[str, ...]) -> dict:
    raw = path.read_bytes()
    meta = json.loads(path.with_suffix(path.suffix + ".meta.json").read_bytes())
    parser = Text()
    parser.feed(raw.decode())
    text = re.sub(r"\s+", "", "".join(parser.parts))
    if (
        meta["url"] != url
        or meta["sha256"] != sha(raw)
        or not meta["retrieved_at_utc"].endswith(("Z", "+00:00"))
        or any(claim not in text for claim in required)
    ):
        raise ValueError(f"OFFICIAL_SCOPE_SOURCE_CHANGED: {path.name}")
    return meta


def classify(row: dict, block: tuple[Decimal, Decimal], close: Decimal) -> str:
    volume, amount = number(row["volume_gap"]), number(row["amount_gap"])
    if abs(volume) <= 100 and abs(amount) <= 100:
        return "DIRECT_DAILY_WITHIN_DISPLAY_PRECISION"
    residual_volume, residual_amount = volume - block[0], amount - block[1]
    if block != (ZERO, ZERO) and abs(residual_volume) <= 100 and abs(residual_amount) <= 150:
        return "OFFICIAL_BLOCK_RECONCILED_WITHIN_DISPLAY_PRECISION"
    if (
        row["symbol"].startswith(("300", "301"))
        and residual_volume >= -100
        and residual_amount >= -150
        and any(
            abs(residual_amount - (residual_volume + offset) * close) <= 150 for offset in (0, 100)
        )
    ):
        return "OFFICIAL_POST_CLOSE_FIXED_PRICE_SIGNATURE"
    return "UNEXPLAINED_SCOPE_GAP"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pilot-audit", type=Path, required=True)
    parser.add_argument("--daily-export", type=Path, required=True)
    parser.add_argument("--block-root", type=Path, required=True)
    parser.add_argument("--post-close-guidance", type=Path, required=True)
    parser.add_argument("--close-file-notice", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    scope_sources = [
        official_source(
            args.post_close_guidance,
            GUIDANCE_URL,
            (
                "盘后定价交易是创业板新增的交易方式",
                "以当日收盘价对盘后定价买卖申报逐笔连续撮合",
                "盘后定价交易成交量、成交金额在盘后定价交易结束后计入该股票当日总成交量、总成交金额",
            ),
        ),
        official_source(
            args.close_file_notice,
            TECHNICAL_URL,
            (
                "盘后定价交易行情快照中的成交总量（TotalVolumeTrade）、成交总金额（TotalValueTrade）仅为盘后定价交易业务的成交总量和成交总金额",  # noqa: RUF001
                "现货证券收盘行情文件（cashsecurityclosemd_YYYYMMDD.xml）中证券的成交总量（TotalVolumeTrade）、成交总金额（TotalValueTrade）不含盘后定价交易业务的成交总量和成交总金额",  # noqa: RUF001
            ),
        ),
    ]
    pilot_bytes = args.pilot_audit.read_bytes()
    pilot = json.loads(pilot_bytes)
    if pilot["day"] != DAY or pilot["status"] != "SCOPE_CROSSCHECK_ONLY_NOT_AUTHORITY":
        raise ValueError("PILOT_SCOPE_AUDIT_CHANGED")
    if sha(args.daily_export.read_bytes()) != pilot["official_sha256"]:
        raise ValueError("OFFICIAL_DAILY_SOURCE_CHANGED")
    daily_rows = workbook(args.daily_export)
    if daily_rows[0][1:3] != ("证券代码", "证券简称"):
        raise ValueError("OFFICIAL_DAILY_COLUMNS_CHANGED")
    closes = {row[1]: number(row[7]) for row in daily_rows[1:] if row[0] == DAY}
    if len(closes) != len(daily_rows) - 1:
        raise ValueError("OFFICIAL_DAILY_CODE_OR_DATE_CHANGED")

    tables = {}
    source_hashes = {}
    for tab in ("tab1", "tab2", "tab3"):
        path = args.block_root / f"{tab}.xlsx"
        raw = path.read_bytes()
        meta = json.loads(path.with_suffix(".xlsx.meta.json").read_bytes())
        url = urlparse(meta["url"])
        query = parse_qs(url.query)
        if (
            sha(raw) != meta["sha256"]
            or url.netloc != "www.szse.cn"
            or url.path != "/api/report/ShowReport"
            or query.get("CATALOGID") != ["1932_dzjyzqjy_after"]
            or query.get("SHOWTYPE") != ["XLSX"]
            or query.get("TABKEY") != [tab]
            or query.get("txtStart") != [DAY]
            or query.get("txtEnd") != [DAY]
            or not meta["retrieved_at_utc"].endswith("+00:00")
        ):
            raise ValueError(f"OFFICIAL_BLOCK_SOURCE_CHANGED: {tab}")
        tables[tab] = workbook(path)
        source_hashes[tab] = sha(raw)
        if any(row[0] != DAY for row in tables[tab][1:]):
            raise ValueError(f"OFFICIAL_BLOCK_DATE_CHANGED: {tab}")
    if (len(tables["tab1"][0]), len(tables["tab2"][0]), len(tables["tab3"][0])) != (
        5,
        8,
        5,
    ):
        raise ValueError("OFFICIAL_BLOCK_COLUMNS_CHANGED")

    summary = {
        row[1]: (number(row[4]) * 10000, number(row[3]) * 10000) for row in tables["tab1"][1:]
    }
    if len(summary) != len(tables["tab1"]) - 1:
        raise ValueError("OFFICIAL_BLOCK_SUMMARY_DUPLICATE_CODE")
    detail = defaultdict(lambda: [ZERO, ZERO])
    for row in tables["tab2"][1:]:
        detail[row[1]][0] += number(row[4]) * 10000
        detail[row[1]][1] += number(row[5]) * 10000
    for row in tables["tab3"][1:]:
        detail[row[1]][0] += number(row[4]) * 10000
        detail[row[1]][1] += number(row[3]) * 10000
    if set(summary) != set(detail) or any(
        abs(volume - detail[symbol][0]) > 100 or abs(amount - detail[symbol][1]) > 100
        for symbol, (volume, amount) in summary.items()
    ):
        raise ValueError("OFFICIAL_BLOCK_SUMMARY_DETAIL_CONFLICT")

    results = []
    for row in sorted(pilot["results"], key=lambda item: item["symbol"]):
        if row["status"] != "COMPARED":
            continue
        symbol = row["symbol"]
        category = classify(row, summary.get(symbol, (ZERO, ZERO)), closes[symbol])
        results.append({"symbol": symbol, "classification": category})
    if len(results) != pilot["compared"]:
        raise ValueError("PILOT_COMPARISON_COUNT_CHANGED")
    counts = {
        category: sum(row["classification"] == category for row in results)
        for category in (
            "DIRECT_DAILY_WITHIN_DISPLAY_PRECISION",
            "OFFICIAL_BLOCK_RECONCILED_WITHIN_DISPLAY_PRECISION",
            "OFFICIAL_POST_CLOSE_FIXED_PRICE_SIGNATURE",
            "UNEXPLAINED_SCOPE_GAP",
        )
    }
    report = {
        "report_version": "SZSE_DAILY_TRANSACTION_SCOPE_CONTROL_V2",
        "status": "SOURCE_SCOPE_EXPLAINED_NOT_RAW_AUTHORITY",
        "day": DAY,
        "parser_sha256": sha(Path(__file__).read_bytes()),
        "pilot_scope_audit_sha256": sha(pilot_bytes),
        "official_daily_sha256": pilot["official_sha256"],
        "official_block_sha256s": source_hashes,
        "official_post_close_sources": scope_sources,
        "block_summary_symbols": len(summary),
        "block_detail_rows": len(tables["tab2"]) + len(tables["tab3"]) - 2,
        "compared": len(results),
        "classification_counts": counts,
        "post_close_scope_signature_proven": True,
        "post_close_per_security_values_directly_observed": False,
        "transaction_scope_gap_unexplained": counts["UNEXPLAINED_SCOPE_GAP"],
        "raw_authority_promoted": False,
        "results": results,
    }
    report["manifest_sha256"] = sha(canonical(report))
    save(args.output, report)
    print(json.dumps({"status": report["status"], "classification_counts": counts}))


if __name__ == "__main__":
    main()
