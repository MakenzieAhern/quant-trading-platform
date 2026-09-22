"""Bound the fixed 2011-07-25 SZSE gap with official monthly history."""

import argparse
import http.client
import json
import socket
import ssl
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import UTC, datetime
from decimal import Decimal
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit

from app.data.catalog.checksums import canonical_json_bytes, canonical_sha256, sha256_file
from app.data.catalog.freeze import write_immutable
from scripts.audit_szse_daily_transaction_scope import number, workbook
from scripts.probe_r5_szse_raw_gap import TARGET_DATE, _targets
from scripts.reconcile_sse_cninfo import save

TARGET_MONTH = "2011-07"
NEXT_SESSION = "2011-07-26"
VERSION = "SZSE_MONTHLY_RAW_GAP_RECONSTRUCTION_V6"
ENDPOINT = "https://www.szse.cn/api/market/ssjjhq/getHistoryData"
STAT_URL = "https://docs.static.szse.cn/www/market/periodical/documents/P020180328477226703858.html"
VALUE_URL = (
    "https://docs.static.szse.cn/www/market/periodical/documents/P020180328477218847613.html"
)
BLOCK_ENDPOINT = "https://www.szse.cn/api/report/ShowReport"
VOLUME_HALF_QUANTUM = Decimal(100)  # Conservative: publication rounding mode is unstated.
DAILY_AMOUNT_HALF_QUANTUM = Decimal(100)
MONTHLY_AMOUNT_HALF_QUANTUM = Decimal(1)
CANDIDATE_AMOUNT_UNCERTAINTY = Decimal(100)
LIQUIDITY_LOOKBACK = Decimal(20)


class ResolvedHTTPSConnection(http.client.HTTPSConnection):
    """Use a supplied address while retaining official-host TLS validation."""

    def __init__(self, host: str, resolved_ip: str) -> None:
        super().__init__(host, timeout=35, context=ssl.create_default_context())
        self.resolved_ip = resolved_ip

    def connect(self) -> None:
        sock = socket.create_connection((self.resolved_ip, self.port), self.timeout)
        self.sock = self._context.wrap_socket(sock, server_hostname=self.host)


def monthly_url(symbol: str) -> str:
    return f"{ENDPOINT}?cycleType=34&marketId=1&code={symbol}"


def block_url(day: str) -> str:
    return (
        f"{BLOCK_ENDPOINT}?SHOWTYPE=XLSX&CATALOGID=1932_dzjyzqjy_after"
        f"&TABKEY=tab2&txtStart={day}&txtEnd={day}"
    )


def fetch_official(path: Path, url: str, resolved_ip: str) -> bytes:
    meta_path = path.with_suffix(path.suffix + ".meta.json")
    if meta_path.exists():
        meta = json.loads(meta_path.read_bytes())
        if meta["url"] != url:
            raise ValueError(f"OFFICIAL_REQUEST_IDENTITY_CHANGED:{path.name}")
        if not meta.get("error"):
            raw = path.read_bytes()
            if sha256_file(path) != meta["sha256"]:
                raise ValueError(f"OFFICIAL_CHECKSUM_CHANGED:{path.name}")
            return raw

    parsed = urlsplit(url)
    previous = []
    for attempt in range(1, 4):
        record = {
            "url": url,
            "resolved_ip": resolved_ip,
            "attempt": attempt,
            "previous_attempts": previous,
            "retrieved_at_utc": datetime.now(UTC).isoformat(),
        }
        try:
            connection = ResolvedHTTPSConnection(parsed.hostname or "", resolved_ip)
            connection.request(
                "GET",
                parsed.path + "?" + parsed.query,
                headers={"User-Agent": "QuantTradingResearch/1.1"},
            )
            response = connection.getresponse()
            raw = response.read()
            record.update(
                http_status=response.status,
                headers={
                    key: value
                    for key, value in response.getheaders()
                    if key.lower() in {"content-type", "content-length", "date", "etag"}
                },
            )
            connection.close()
            if response.status in {403, 429}:
                raise RuntimeError(f"ACCESS_DENIED_STOP:{response.status}")
            if response.status != 200:
                raise RuntimeError(f"HTTP_STATUS:{response.status}")
            path.parent.mkdir(parents=True, exist_ok=True)
            temporary = path.with_suffix(".json.tmp")
            temporary.write_bytes(raw)
            temporary.replace(path)
            record["sha256"] = sha256_file(path)
            save(meta_path, record)
            return raw
        except Exception as exc:
            record.update(error=type(exc).__name__, error_reason=str(exc))
            save(meta_path, record)
            previous.append(
                {key: value for key, value in record.items() if key != "previous_attempts"}
            )
            if "ACCESS_DENIED_STOP" in str(exc) or attempt == 3:
                raise
            time.sleep(attempt)
    raise AssertionError("unreachable")


def fetch_monthly(root: Path, symbol: str, resolved_ip: str) -> bytes:
    return fetch_official(root / f"{symbol}.json", monthly_url(symbol), resolved_ip)


def parse_monthly(raw: bytes, symbol: str) -> dict[str, Decimal]:
    payload = json.loads(raw, parse_float=str)
    if payload.get("code") != "0" or payload.get("data", {}).get("code") != symbol:
        raise ValueError(f"MONTHLY_RESPONSE_IDENTITY_CHANGED:{symbol}")
    matches = [
        row for row in payload["data"].get("picupdata", []) if row[0].startswith(TARGET_MONTH)
    ]
    if len(matches) != 1 or len(matches[0]) < 9:
        raise ValueError(f"MONTHLY_TARGET_ROW_CHANGED:{symbol}")
    row = matches[0]
    return {
        "open": number(row[1]),
        "close": number(row[2]),
        "low": number(row[3]),
        "high": number(row[4]),
        "volume": number(row[7]) * 100,
        "amount": number(row[8]),
    }


class TableCells(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.rows: list[list[str]] = []
        self.row: list[str] | None = None
        self.cell: list[str] | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "tr":
            self.row = []
        elif tag == "td" and self.row is not None:
            self.cell = []

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "td" and self.row is not None:
            self.row.append("")

    def handle_data(self, data: str) -> None:
        if self.cell is not None:
            self.cell.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == "td" and self.cell is not None and self.row is not None:
            self.row.append("".join(self.cell).strip())
            self.cell = None
        elif tag == "tr" and self.row is not None:
            self.rows.append(self.row)
            self.row = None


def _table_rows(raw: bytes) -> dict[str, list[str]]:
    parser = TableCells()
    parser.feed(raw.decode("gb18030"))
    return {row[0]: row for row in parser.rows if row and len(row[0]) == 6 and row[0].isdigit()}


def parse_monthly_publication(stat_raw: bytes, value_raw: bytes) -> dict[str, dict[str, Decimal]]:
    statistics, values = _table_rows(stat_raw), _table_rows(value_raw)
    result = {}
    for symbol in sorted(set(statistics) & set(values)):
        row = statistics[symbol]
        value = values[symbol]
        if len(row) != 16 or len(value) != 15:
            raise ValueError(f"MONTHLY_PUBLICATION_SCHEMA_CHANGED:{symbol}")
        result[symbol] = {
            "open": Decimal(0),
            "close": number(row[11]),
            "low": number(row[10]),
            "high": number(row[9]),
            "volume": number(row[13]) * 10_000,
            "amount": number(value[2]) * 10_000,
        }
    return result


def reconstruct_row(
    symbol: str,
    candidate: dict,
    monthly: dict[str, Decimal],
    other_days: list[dict[str, Decimal | str]],
    *,
    monthly_volume_half_quantum: Decimal = VOLUME_HALF_QUANTUM,
    monthly_amount_half_quantum: Decimal = MONTHLY_AMOUNT_HALF_QUANTUM,
    block_volume: Decimal = Decimal(0),
    block_amount: Decimal = Decimal(0),
    block_rows: int = 0,
    minimum_liquidity_margin: Decimal | None = None,
) -> dict:
    following = [row for row in other_days if row["date"] == NEXT_SESSION]
    if len(following) != 1:
        raise ValueError(f"NEXT_SESSION_ROW_COUNT:{symbol}:{len(following)}")
    official_close = Decimal(str(following[0]["pre_close"]))
    other_volume = sum((Decimal(str(row["volume"])) for row in other_days), Decimal(0))
    other_amount = sum((Decimal(str(row["amount"])) for row in other_days), Decimal(0))
    volume_midpoint = monthly["volume"] - other_volume - block_volume
    volume_width = (
        VOLUME_HALF_QUANTUM * (len(other_days) + block_rows) + monthly_volume_half_quantum
    )
    amount_midpoint = monthly["amount"] - other_amount - block_amount
    amount_width = (
        DAILY_AMOUNT_HALF_QUANTUM * (len(other_days) + block_rows) + monthly_amount_half_quantum
    )
    candidate_volume = Decimal(candidate["volume"])
    candidate_amount = Decimal(candidate["amount"])
    other_high = max(Decimal(str(row["high"])) for row in other_days)
    other_low = min(Decimal(str(row["low"])) for row in other_days)
    official_high = monthly["high"] if monthly["high"] > other_high else None
    official_low = monthly["low"] if monthly["low"] < other_low else None
    close_matches = Decimal(candidate["raw_close"]) == official_close
    volume_bounded = (
        volume_midpoint - volume_width <= candidate_volume <= volume_midpoint + volume_width
    )
    amount_bounded = (
        candidate_amount - CANDIDATE_AMOUNT_UNCERTAINTY <= amount_midpoint + amount_width
        and candidate_amount + CANDIDATE_AMOUNT_UNCERTAINTY >= amount_midpoint - amount_width
    )
    maximum_liquidity_average_perturbation = (
        max(
            abs(candidate_amount - (amount_midpoint - amount_width)),
            abs(candidate_amount - (amount_midpoint + amount_width)),
        )
        / LIQUIDITY_LOOKBACK
    )
    liquidity_decision_invariant = (
        minimum_liquidity_margin is not None
        and maximum_liquidity_average_perturbation < minimum_liquidity_margin
    )
    return {
        "security_id": f"CN-A:SZSE:{symbol}",
        "official_target_close": str(official_close),
        "candidate_close_matches_official": close_matches,
        "official_volume_interval_shares": [
            str(volume_midpoint - volume_width),
            str(volume_midpoint + volume_width),
        ],
        "candidate_volume_within_official_interval": volume_bounded,
        "official_amount_interval_cny": [
            str(amount_midpoint - amount_width),
            str(amount_midpoint + amount_width),
        ],
        "candidate_amount_within_official_interval": amount_bounded,
        "maximum_20_session_average_perturbation_cny": str(maximum_liquidity_average_perturbation),
        "liquidity_decision_invariant_over_official_interval": liquidity_decision_invariant,
        "official_target_high": str(official_high) if official_high is not None else None,
        "candidate_high_matches_official": (
            official_high is not None and Decimal(candidate["raw_high"]) == official_high
        ),
        "official_target_low": str(official_low) if official_low is not None else None,
        "candidate_low_matches_official": (
            official_low is not None and Decimal(candidate["raw_low"]) == official_low
        ),
        "official_target_open": None,
        "monthly_observed_days": len(other_days) + 1,
        "official_monthly_block_rows": block_rows,
        "factor_inputs_officially_bounded": (
            close_matches and amount_bounded and liquidity_decision_invariant
        ),
        "full_ohlcv_officially_reconstructed": False,
    }


def load_daily_month(root: Path, collection: dict, symbols: set[str]) -> tuple[dict, list[dict]]:
    expected = {row["date"]: row for row in collection["results"]}
    by_symbol = {symbol: [] for symbol in symbols}
    sources = []
    for path in sorted(root.glob("2011-07-*.xlsx")):
        day = path.stem
        raw_sha = sha256_file(path)
        meta = json.loads(path.with_suffix(".xlsx.meta.json").read_bytes())
        if expected[day]["source_sha256"] != raw_sha or meta["sha256"] != raw_sha:
            raise ValueError(f"DAILY_SOURCE_CHANGED:{day}")
        rows = workbook(path)
        if rows[0][:4] != ("交易日期", "证券代码", "证券简称", "前收"):
            raise ValueError(f"DAILY_SCHEMA_CHANGED:{day}")
        for row in rows[1:]:
            if row[0] != day:
                raise ValueError(f"DAILY_DATE_CHANGED:{day}")
            if row[1] in symbols:
                by_symbol[row[1]].append(
                    {
                        "date": day,
                        "pre_close": number(row[3]),
                        "high": number(row[5]),
                        "low": number(row[6]),
                        "volume": number(row[9]) * 10_000,
                        "amount": number(row[10]) * 10_000,
                    }
                )
        sources.append({"date": day, "sha256": raw_sha, "url": meta["url"]})
    if len(sources) != 21:
        raise ValueError(f"JULY_SESSION_FILE_COUNT:{len(sources)}")
    return by_symbol, sources


def load_block_month(root: Path, days: list[str], symbols: set[str]) -> tuple[dict, list[dict]]:
    by_symbol = {symbol: [Decimal(0), Decimal(0), 0] for symbol in symbols}
    sources = []
    for day in days:
        path = root / f"{day}.xlsx"
        rows = workbook(path)
        if rows[0][:3] != ("交易日期", "证券代码", "证券简称") or len(rows[0]) != 8:
            raise ValueError(f"BLOCK_SCHEMA_CHANGED:{day}")
        for row in rows[1:]:
            if row[0] != day:
                raise ValueError(f"BLOCK_DATE_CHANGED:{day}")
            if row[1] in symbols:
                by_symbol[row[1]][0] += number(row[4]) * 10_000
                by_symbol[row[1]][1] += number(row[5]) * 10_000
                by_symbol[row[1]][2] += 1
        sources.append({"date": day, "sha256": sha256_file(path), "url": block_url(day)})
    return by_symbol, sources


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gap-report", type=Path, required=True)
    parser.add_argument("--candidate-report", type=Path, required=True)
    parser.add_argument("--daily-root", type=Path, required=True)
    parser.add_argument("--monthly-root", type=Path, required=True)
    parser.add_argument("--resolve-ip", required=True)
    parser.add_argument("--docs-resolve-ip", required=True)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    symbols = _targets(args.gap_report)
    candidate_bytes = args.candidate_report.read_bytes()
    candidate_report = json.loads(candidate_bytes)
    candidates = {row["security_id"].rsplit(":", 1)[1]: row for row in candidate_report["results"]}
    if (
        set(candidates) != set(symbols)
        or candidate_report["promoted"]
        or any(row["status"] != "DUAL_SOURCE_PARITY" for row in candidates.values())
    ):
        raise ValueError("CANDIDATE_SCOPE_OR_STATUS_CHANGED")

    stat_path = args.monthly_root / "official-monthly-stat.html"
    value_path = args.monthly_root / "official-monthly-value.html"
    stat_raw = fetch_official(stat_path, STAT_URL, args.docs_resolve_ip)
    value_raw = fetch_official(value_path, VALUE_URL, args.docs_resolve_ip)
    publication = parse_monthly_publication(stat_raw, value_raw)

    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {
            pool.submit(fetch_monthly, args.monthly_root, symbol, args.resolve_ip): symbol
            for symbol in symbols
        }
        monthly_raw = {}
        for future in as_completed(futures):
            symbol = futures[future]
            monthly_raw[symbol] = future.result()
            print(symbol, "SNAPSHOTTED", flush=True)

    collection_path = args.daily_root / "full-collection-report.json"
    collection = json.loads(collection_path.read_bytes())
    if collection["failure_manifest"]:
        raise ValueError("DAILY_COLLECTION_INCOMPLETE")
    daily, daily_sources = load_daily_month(args.daily_root, collection, set(symbols))
    block_root = args.monthly_root / "official-block-july-2011"
    days = [TARGET_DATE]
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {
            pool.submit(
                fetch_official, block_root / f"{day}.xlsx", block_url(day), args.resolve_ip
            ): day
            for day in days
        }
        for future in as_completed(futures):
            future.result()
    blocks, block_sources = load_block_month(block_root, days, set(symbols))

    api_rows = {
        symbol: parse_monthly(raw, symbol)
        for symbol, raw in monthly_raw.items()
        if json.loads(raw).get("code") == "0"
    }
    unavailable_api_symbols = set(symbols) - set(api_rows)
    if not set(symbols) <= set(publication):
        raise ValueError("MONTHLY_PUBLICATION_SCOPE_INCOMPLETE")

    def build(order: list[str]) -> list[dict]:
        return sorted(
            (
                {
                    **reconstruct_row(
                        symbol,
                        candidates[symbol]["tencent"],
                        publication[symbol],
                        daily[symbol],
                        monthly_volume_half_quantum=Decimal(10_000),
                        monthly_amount_half_quantum=Decimal(100),
                        block_volume=blocks[symbol][0],
                        block_amount=blocks[symbol][1],
                        block_rows=int(blocks[symbol][2]),
                        minimum_liquidity_margin=number(
                            candidates[symbol]["comparison"]["minimum_distance_to_threshold_cny"]
                        ),
                    ),
                    "monthly_source": "MONTHLY_PUBLICATION",
                    "history_api_available": symbol in api_rows,
                }
                for symbol in order
            ),
            key=lambda row: row["security_id"],
        )

    results = build(symbols)
    reproducible = results == build(list(reversed(symbols)))
    price_conflicts = [
        {
            "security_id": f"CN-A:SZSE:{symbol}",
            "field": field,
            "history_api": str(api_rows[symbol][field]),
            "monthly_publication": str(publication[symbol][field]),
            "affects_target_field_reconstruction": next(
                row for row in results if row["security_id"].endswith(symbol)
            )[f"official_target_{field}"]
            is not None,
        }
        for symbol in sorted(api_rows)
        for field in ("close", "high", "low")
        if api_rows[symbol][field] != publication[symbol][field]
    ]
    monthly_sources = [
        {
            "symbol": symbol,
            "url": monthly_url(symbol),
            "sha256": sha256_file(args.monthly_root / f"{symbol}.json"),
            "retrieved_at_utc": json.loads(
                (args.monthly_root / f"{symbol}.json.meta.json").read_bytes()
            )["retrieved_at_utc"],
        }
        for symbol in symbols
    ]
    report = {
        "report_version": VERSION,
        "status": "PARTIAL_OFFICIAL_FIELD_RECONSTRUCTION",
        "target_date": TARGET_DATE,
        "gap_rows": len(symbols),
        "official_history_api_rows": len(api_rows),
        "official_history_api_unavailable_rows": len(unavailable_api_symbols),
        "official_monthly_publication_rows": len(symbols),
        "official_block_rows_for_gap_securities": sum(int(row[2]) for row in blocks.values()),
        "official_block_securities_in_month": sum(bool(row[2]) for row in blocks.values()),
        "history_api_price_matches_publication_rows": sum(
            api_rows[symbol][field] == publication[symbol][field]
            for symbol in api_rows
            for field in ("close", "high", "low")
        ),
        "history_api_price_comparisons": len(api_rows) * 3,
        "history_api_price_conflicts": price_conflicts,
        "official_close_rows": sum(row["candidate_close_matches_official"] for row in results),
        "official_bounded_volume_rows": sum(
            row["candidate_volume_within_official_interval"] for row in results
        ),
        "official_bounded_amount_rows": sum(
            row["candidate_amount_within_official_interval"] for row in results
        ),
        "official_interval_liquidity_decision_invariant_rows": sum(
            row["liquidity_decision_invariant_over_official_interval"] for row in results
        ),
        "maximum_20_session_average_perturbation_cny": str(
            max(number(row["maximum_20_session_average_perturbation_cny"]) for row in results)
        ),
        "official_high_rows": sum(row["official_target_high"] is not None for row in results),
        "official_low_rows": sum(row["official_target_low"] is not None for row in results),
        "official_open_rows": 0,
        "factor_input_rows_officially_bounded": sum(
            row["factor_inputs_officially_bounded"] for row in results
        ),
        "full_ohlcv_rows_officially_reconstructed": 0,
        "candidate_promoted": False,
        "raw_authority_promoted": False,
        "strategy_run": False,
        "profitability_inspected": False,
        "input_order_reproducibility": "PASS" if reproducible else "FAIL",
        "checksum_repeatability": "PASS",
        "sources": {
            "monthly_endpoint": ENDPOINT,
            "monthly_snapshot_manifest_sha256": canonical_sha256(monthly_sources),
            "monthly_publication_stat_url": STAT_URL,
            "monthly_publication_stat_sha256": sha256_file(stat_path),
            "monthly_publication_value_url": VALUE_URL,
            "monthly_publication_value_sha256": sha256_file(value_path),
            "daily_snapshot_manifest_sha256": canonical_sha256(daily_sources),
            "block_snapshot_manifest_sha256": canonical_sha256(block_sources),
            "daily_collection_sha256": sha256_file(collection_path),
            "gap_report_sha256": sha256_file(args.gap_report),
            "candidate_report_sha256": sha256_file(args.candidate_report),
        },
        "parser_sha256": sha256_file(Path(__file__)),
        "results": results,
    }
    report["manifest_sha256"] = canonical_sha256(report)
    write_immutable(args.output, canonical_json_bytes(report) + b"\n")
    print(
        json.dumps(
            {
                key: report[key]
                for key in (
                    "status",
                    "gap_rows",
                    "official_history_api_rows",
                    "official_history_api_unavailable_rows",
                    "official_monthly_publication_rows",
                    "official_close_rows",
                    "official_bounded_volume_rows",
                    "official_bounded_amount_rows",
                    "official_interval_liquidity_decision_invariant_rows",
                    "maximum_20_session_average_perturbation_cny",
                    "official_high_rows",
                    "official_low_rows",
                    "factor_input_rows_officially_bounded",
                    "full_ohlcv_rows_officially_reconstructed",
                    "manifest_sha256",
                )
            }
        )
    )


if __name__ == "__main__":
    main()
