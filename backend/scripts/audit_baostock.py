import json
import socket
from datetime import date
from importlib import import_module
from typing import Any


def _rows(result: Any) -> list[dict[str, str]]:
    if result.error_code != "0":
        return [{"error": result.error_code, "message": result.error_msg}]
    output = []
    while result.next():
        output.append(dict(zip(result.fields, result.get_row_data(), strict=True)))
    return output


def main() -> None:
    socket.setdefaulttimeout(15)
    bs: Any = import_module("baostock")
    login = bs.login()
    if login.error_code != "0":
        raise SystemExit("BAOSTOCK_LOGIN_FAILED")
    targets = (
        "2010-12-31",
        "2012-12-31",
        "2015-12-31",
        "2018-12-31",
        "2020-12-31",
        "2022-12-31",
        "2024-12-31",
        "2025-12-31",
    )
    calendar = _rows(bs.query_trade_dates(start_date="2010-12-20", end_date=targets[-1]))
    open_days = [row["calendar_date"] for row in calendar if row.get("is_trading_day") == "1"]
    snapshots: dict[str, dict[str, object]] = {}
    codes_by_date: dict[str, set[str]] = {}
    for target in targets:
        trading_day = max(day for day in open_days if day <= target)
        rows = _rows(bs.query_all_stock(day=trading_day))
        codes = {
            row["code"] for row in rows if row.get("code", "").startswith(("sh.6", "sz.0", "sz.3"))
        }
        codes_by_date[trading_day] = codes
        snapshots[trading_day] = {"all_rows": len(rows), "equity_like_rows": len(codes)}

    earliest, latest = min(codes_by_date), max(codes_by_date)
    old_only = sorted(codes_by_date[earliest] - codes_by_date[latest])[:12]
    exited = {}
    for code in old_only:
        bars = _rows(
            bs.query_history_k_data_plus(
                code,
                "date,code,close,tradestatus,isST",
                start_date="2010-01-01",
                end_date=targets[-1],
                frequency="d",
                adjustflag="3",
            )
        )
        exited[code] = {
            "basic": _rows(bs.query_stock_basic(code=code)),
            "bar_count": len(bars),
            "first_bar": bars[0] if bars else None,
            "last_bar": bars[-1] if bars else None,
        }

    focus = "sh.600000"
    capabilities = {
        "stock_basic": _rows(bs.query_stock_basic(code=focus)),
        "trade_dates_1990": _rows(
            bs.query_trade_dates(start_date="1990-01-01", end_date="1990-12-31")
        ),
        "trade_dates_1991": _rows(
            bs.query_trade_dates(start_date="1991-01-01", end_date="1991-12-31")
        ),
        "adjust_factor": _rows(
            bs.query_adjust_factor(code=focus, start_date="1999-01-01", end_date=targets[-1])
        ),
        "dividend_2024": _rows(bs.query_dividend_data(code=focus, year="2024", yearType="report")),
        "hs300_2010": _rows(bs.query_hs300_stocks(date="2010-12-31")),
        "zz500_2010": _rows(bs.query_zz500_stocks(date="2010-12-31")),
        "sz50_2010": _rows(bs.query_sz50_stocks(date="2010-12-31")),
        "history_1990s": _rows(
            bs.query_history_k_data_plus(
                focus,
                "date,code,open,close,tradestatus,isST",
                start_date="1990-01-01",
                end_date="1999-12-31",
                frequency="d",
                adjustflag="3",
            )
        ),
    }
    print(
        json.dumps(
            {
                "audit_date": date.today().isoformat(),
                "sdk_version": getattr(bs, "__version__", "unknown"),
                "snapshots": snapshots,
                "exited_security_sample": exited,
                "capabilities": capabilities,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    bs.logout()


if __name__ == "__main__":
    main()
