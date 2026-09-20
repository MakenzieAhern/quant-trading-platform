from decimal import Decimal
from hashlib import sha256

from openpyxl import Workbook

from scripts.audit_adjustment_factor_economics import (
    economics,
    factor_source_symbols,
    szse_pre_closes,
)
from scripts.probe_szse_official_daily import HEADERS


def test_exact_terms_factor_economics() -> None:
    pre_close = Decimal("19.24")
    cash = Decimal("0.17")
    bonus = Decimal("0.6")
    expected = pre_close * (Decimal(1) + bonus) / (pre_close - cash)
    assert economics(pre_close, cash, bonus, expected)["status"] == (
        "GROSS_TERMS_FACTOR_PARITY_PASS"
    )
    assert economics(pre_close, cash, bonus, Decimal("1"))["status"] == (
        "GROSS_TERMS_FACTOR_PARITY_CONFLICT"
    )
    precise_cash = Decimal("0.0247411")
    normalized_source = pre_close / (pre_close - Decimal("0.024741"))
    assert economics(pre_close, precise_cash, Decimal(0), normalized_source)["status"] == (
        "GROSS_TERMS_FACTOR_PARITY_PASS_PROVIDER_CASH_PRECISION"
    )
    tie_cash = Decimal("0.1994985")
    tie_source = pre_close / (pre_close - Decimal("0.199498"))
    assert economics(pre_close, tie_cash, Decimal(0), tie_source)["status"] == (
        "GROSS_TERMS_FACTOR_PARITY_PASS_PROVIDER_CASH_PRECISION"
    )
    combined_source = pre_close * (Decimal(1) + Decimal("0.2")) / (pre_close - Decimal("0.024741"))
    assert economics(pre_close, precise_cash, Decimal("0.2"), combined_source)["status"] == (
        "GROSS_TERMS_FACTOR_PARITY_PASS_PROVIDER_CASH_PRECISION"
    )


def test_szse_pre_close_uses_prior_session_actual_close(tmp_path) -> None:
    sources = []
    for day, adjusted_pre_close, actual_close in (
        ("2014-06-11", "11.75", "11.78"),
        ("2014-06-12", "9.68", "9.71"),
    ):
        workbook = Workbook()
        sheet = workbook.active
        sheet.append(HEADERS)
        sheet.append(
            (day, "000001", "平安银行", adjusted_pre_close, 1, 1, 1, actual_close, 0, 1, 1, 1)
        )
        path = tmp_path / f"{day}.xlsx"
        workbook.save(path)
        sources.append({"date": day, "source_sha256": sha256(path.read_bytes()).hexdigest()})

    assert szse_pre_closes(
        tmp_path,
        {"results": sources},
        {("000001", "2014-06-12")},
    ) == {("000001", "2014-06-12"): Decimal("11.78")}

    assert factor_source_symbols(
        {
            "intervals": [
                {
                    "security_id": "CN-A:SZSE:001914",
                    "symbol": "sz000043",
                    "in_interval_variants": {"one": {"change_dates": ["2014-05-16"]}},
                }
            ]
        }
    ) == {("CN-A:SZSE:001914", "2014-05-16"): "000043"}
