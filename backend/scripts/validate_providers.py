"""Cross-check a deterministic raw daily-bar sample without writing market data to Git."""

import argparse
import json
from datetime import date
from decimal import Decimal
from importlib import import_module
from typing import Any


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", type=date.fromisoformat, default=date(2018, 1, 2))
    parser.add_argument("--end", type=date.fromisoformat, default=date(2018, 1, 12))
    args = parser.parse_args()
    symbols = (("sh.600000", "600000"), ("sz.000001", "000001"), ("sz.300001", "300001"))

    bao: Any = import_module("baostock")
    ak: Any = import_module("akshare")
    login = bao.login()
    if login.error_code != "0":
        raise RuntimeError("BAOSTOCK_LOGIN_FAILED")
    try:
        results = []
        for pair in symbols:
            try:
                results.append(_compare(bao, ak, pair, args.start, args.end))
            except Exception:
                # Provider/network exception text is intentionally not emitted.
                results.append(
                    {
                        "symbol": pair[1],
                        "status": "PROVIDER_QUERY_FAILED",
                    }
                )
    finally:
        bao.logout()
    print(
        json.dumps(
            {
                "baostock_sdk": str(getattr(bao, "__version__", "unknown")),
                "akshare_sdk": str(ak.__version__),
                "start": args.start.isoformat(),
                "end": args.end.isoformat(),
                "samples": results,
            },
            ensure_ascii=False,
            indent=2,
        )
    )


def _compare(
    bao: Any, ak: Any, symbols: tuple[str, str], start: date, end: date
) -> dict[str, object]:
    bao_symbol, ak_symbol = symbols
    fields = "date,open,high,low,close,volume,amount"
    query = bao.query_history_k_data_plus(
        bao_symbol,
        fields,
        start_date=start.isoformat(),
        end_date=end.isoformat(),
        frequency="d",
        adjustflag="3",
    )
    if query.error_code != "0":
        raise RuntimeError("BAOSTOCK_QUERY_FAILED")
    bao_rows: dict[str, list[str]] = {}
    while query.next():
        row = query.get_row_data()
        bao_rows[row[0]] = row[1:]

    frame = ak.stock_zh_a_hist(
        symbol=ak_symbol,
        period="daily",
        start_date=start.strftime("%Y%m%d"),
        end_date=end.strftime("%Y%m%d"),
        adjust="",
    )
    ak_rows = {str(row["日期"]): row for row in frame.to_dict("records")}
    common = sorted(set(bao_rows) & set(ak_rows))
    ohlc_disagreements = 0
    volume_disagreements = 0
    amount_disagreements = 0
    maximum_volume_share_difference = Decimal(0)
    maximum_amount_difference = Decimal(0)
    for trading_date in common:
        bao_row = bao_rows[trading_date]
        ak_row = ak_rows[trading_date]
        ak_ohlc = (ak_row["开盘"], ak_row["最高"], ak_row["最低"], ak_row["收盘"])
        if any(
            Decimal(bao_row[index]) != Decimal(str(value)) for index, value in enumerate(ak_ohlc)
        ):
            ohlc_disagreements += 1
        volume_difference = abs(Decimal(bao_row[4]) - Decimal(str(ak_row["成交量"])) * 100)
        maximum_volume_share_difference = max(maximum_volume_share_difference, volume_difference)
        if volume_difference >= 100:
            volume_disagreements += 1
        amount_difference = abs(Decimal(bao_row[5]) - Decimal(str(ak_row["成交额"])))
        maximum_amount_difference = max(maximum_amount_difference, amount_difference)
        if amount_difference > Decimal("1"):
            amount_disagreements += 1
    return {
        "symbol": ak_symbol,
        "status": "COMPLETED",
        "baostock_rows": len(bao_rows),
        "akshare_rows": len(ak_rows),
        "common_rows": len(common),
        "ohlc_disagreements": ohlc_disagreements,
        "volume_disagreements_after_akshare_lot_to_share_conversion": volume_disagreements,
        "maximum_volume_share_difference": format(maximum_volume_share_difference, "f"),
        "amount_disagreements": amount_disagreements,
        "maximum_amount_difference_yuan": format(maximum_amount_difference, "f"),
    }


if __name__ == "__main__":
    main()
