import argparse
import socket
import tempfile
from datetime import UTC, date, datetime
from importlib import import_module
from pathlib import Path
from typing import Any

from app.data.catalog import finalize_manifest, write_canonical_parquet, write_manifest
from app.data.security_master import load_security_master
from app.domain.markets import (
    Board,
    DailySecurityStatus,
    Exchange,
    Market,
    SecurityId,
    TradingRuleResolver,
    historical_cn_a_rules,
    is_locked_one_price_bar,
)
from app.domain.trading import OrderSide, OrderType
from app.integrations.baostock import BaoStockAdapter

DATASET_ID = "cn-a-pilot-baostock-20230101-20240731-v1"
START = date(2023, 1, 1)
END = date(2024, 7, 31)
SECURITIES = {
    SecurityId(value="CN-A:SSE:600000"): Board.SSE_MAIN,
    SecurityId(value="CN-A:SSE:688001"): Board.SSE_STAR,
    SecurityId(value="CN-A:SZSE:000001"): Board.SZSE_MAIN,
    SecurityId(value="CN-A:SZSE:300001"): Board.SZSE_CHINEXT,
}


class _PilotBoards:
    def resolve(self, security_id: SecurityId, as_of: date) -> Board:
        del as_of
        return SECURITIES[security_id]


def _rows(result: Any) -> list[dict[str, str]]:
    if result.error_code != "0":
        raise RuntimeError("BAOSTOCK_QUERY_FAILED")
    output = []
    while result.next():
        output.append(dict(zip(result.fields, result.get_row_data(), strict=True)))
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest the bounded, non-research A-share pilot")
    parser.add_argument("--pilot", action="store_true", required=True)
    parser.add_argument("--root", type=Path, default=Path("data/research"))
    parser.add_argument(
        "--security-master-root",
        type=Path,
        default=Path("/home/yuchen/data/research/staging/security-master-pilot"),
    )
    args = parser.parse_args()
    master = load_security_master(args.security_master_root)
    for security_id, board in SECURITIES.items():
        if security_id not in master.eligible_universe(START):
            raise SystemExit("PILOT_SECURITY_MASTER_MEMBER_MISSING")
        if master.board_on(security_id, START) != board:
            raise SystemExit("PILOT_SECURITY_MASTER_BOARD_MISMATCH")
    socket.setdefaulttimeout(15)
    bs: Any = import_module("baostock")
    login = bs.login()
    if login.error_code != "0":
        raise SystemExit("BAOSTOCK_LOGIN_FAILED")
    try:
        _ingest(args.root, bs)
    finally:
        bs.logout()


def _ingest(root: Path, bs: Any) -> None:
    adapter = BaoStockAdapter(
        bs,
        provider_version=str(getattr(bs, "__version__", "unknown")),
        boards=_PilotBoards(),
    )
    root.mkdir(parents=True, exist_ok=True)
    dataset_root = root / DATASET_ID
    if dataset_root.exists():
        raise RuntimeError("immutable pilot dataset already exists")
    with tempfile.TemporaryDirectory(prefix="a-share-pilot-", dir=root) as staging:
        _write_dataset(Path(staging) / DATASET_ID, dataset_root, adapter, bs)


def _write_dataset(dataset_root: Path, final_root: Path, adapter: BaoStockAdapter, bs: Any) -> None:
    calendar = tuple(adapter.trading_calendar(START, END))
    resolver = TradingRuleResolver(historical_cn_a_rules())
    bars: list[dict[str, Any]] = []
    statuses: list[dict[str, object]] = []
    actions: list[dict[str, Any]] = []
    securities = []
    for security_id, board in SECURITIES.items():
        basic = _rows(bs.query_stock_basic(code=_provider_code(security_id)))
        if len(basic) != 1:
            raise RuntimeError("BAOSTOCK_SECURITY_BASIC_INVALID")
        securities.append(
            {
                "security_id": str(security_id),
                "symbol": security_id.value.rsplit(":", 1)[1],
                "exchange": security_id.value.split(":")[1],
                "board": board.value,
                "listing_date": basic[0]["ipoDate"],
                "delisting_date": basic[0].get("outDate") or None,
            }
        )
        security_bars = tuple(adapter.daily_bars(security_id, START, END))
        status_by_date = {
            item.status.trading_date: item.status
            for item in adapter.daily_status(security_id, START, END)
        }
        for bar in security_bars:
            status = status_by_date[bar.trading_date]
            exchange = Exchange.SSE if ":SSE:" in security_id.value else Exchange.SZSE
            rules = resolver.resolve(
                security_id=security_id,
                market=Market.CN_A,
                exchange=exchange,
                board=board,
                trading_date=bar.trading_date,
                side=OrderSide.BUY,
                order_type=OrderType.MARKET,
                security_status=status,
                listing_age_sessions=999,
            )
            status = status.model_copy(
                update={
                    "is_one_price_limit": is_locked_one_price_bar(
                        raw_open=bar.raw_open,
                        raw_high=bar.raw_high,
                        raw_low=bar.raw_low,
                        raw_close=bar.raw_close,
                        pre_close=bar.pre_close,
                        rules=rules,
                    )
                }
            )
            bars.append(bar.model_dump(mode="python"))
            statuses.append(_status_row(status))
        actions.extend(
            action.model_dump(mode="python")
            for action in adapter.corporate_actions(security_id, START, END)
        )
    benchmark = tuple(adapter.benchmark_bars("CSI300", START, END))
    memberships = tuple(adapter.benchmark_membership("CSI300", END))
    partitions = (
        _write(dataset_root, "securities", securities, ("security_id",)),
        _write(
            dataset_root, "calendar", (item.model_dump() for item in calendar), ("session_date",)
        ),
        _write(dataset_root, "daily-bars", bars, ("security_id", "trading_date")),
        _write(dataset_root, "daily-status", statuses, ("security_id", "trading_date")),
        _write(
            dataset_root, "corporate-actions", actions, ("security_id", "ex_date", "action_type")
        ),
        _write(
            dataset_root,
            "csi300-bars",
            (item.model_dump() for item in benchmark),
            ("trading_date",),
        ),
        _write(
            dataset_root,
            "csi300-membership",
            (item.model_dump() for item in memberships),
            ("security_id",),
        ),
    )
    manifest = finalize_manifest(
        {
            "dataset_id": DATASET_ID,
            "provider": "BaoStock",
            "provider_version": adapter.provider_version,
            "retrieval_timestamp": datetime.now(UTC),
            "coverage_start": START,
            "coverage_end": END,
            "security_count": len(SECURITIES),
            "symbols": tuple(sorted(item.value.rsplit(":", 1)[1] for item in SECURITIES)),
            "exchanges": (Exchange.SSE, Exchange.SZSE),
            "fields": tuple(sorted({key for row in bars for key in row})),
            "adjustment_method": "BaoStock adjustflag=2 factors; adjustflag=3 raw execution",
            "rule_version": historical_cn_a_rules().version,
            "source_lineage": ("BaoStock direct API", "bounded pilot; not official research"),
            "partitions": tuple(sorted(partitions, key=lambda item: item.relative_path)),
            "known_limitations": ("pilot only", "not a complete historical universe"),
        }
    )
    write_manifest(dataset_root / "manifest.json", manifest)
    dataset_root.replace(final_root)
    print(f"{manifest.dataset_id} {manifest.logical_content_sha256}")


def _write(root: Path, name: str, rows: Any, sort_keys: tuple[str, ...]):
    materialized = tuple(rows)
    fields = tuple(sorted(set(sort_keys) | {key for row in materialized for key in row}))
    return write_canonical_parquet(
        root / f"{name}.parquet", fieldnames=fields, rows=materialized, sort_keys=sort_keys
    )


def _status_row(status: DailySecurityStatus) -> dict[str, object]:
    return {
        "security_id": str(status.security_id),
        "trading_date": status.trading_date,
        "is_st": status.is_st,
        "is_suspended": status.is_suspended,
        "is_one_price_limit": status.is_one_price_limit,
        "source_version": status.source_version,
    }


def _provider_code(security_id: SecurityId) -> str:
    _, exchange, symbol = security_id.value.split(":")
    return f"{'sh' if exchange == 'SSE' else 'sz'}.{symbol}"


if __name__ == "__main__":
    main()
