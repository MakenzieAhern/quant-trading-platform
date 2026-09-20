from decimal import Decimal

from scripts.audit_szse_monthly_raw_gap import parse_monthly_publication, reconstruct_row


def test_official_monthly_bounds_close_volume_and_amount_without_inventing_open():
    candidate = {
        "raw_open": "22.16",
        "raw_close": "20.73",
        "raw_high": "22.16",
        "raw_low": "20.49",
        "volume": "1869849",
        "amount": "38846400",
    }
    other_days = [
        {
            "date": "2011-07-26" if index == 0 else f"other-{index}",
            "pre_close": Decimal("20.73"),
            "high": Decimal("24.00"),
            "low": Decimal("20.00"),
            "volume": Decimal("928555"),
            "amount": Decimal("20784355"),
        }
        for index in range(20)
    ]
    result = reconstruct_row(
        "300001",
        candidate,
        {
            "open": Decimal("21.97"),
            "close": Decimal("20.34"),
            "low": Decimal("19.98"),
            "high": Decimal("24.25"),
            "volume": Decimal("20440900"),
            "amount": Decimal("454533543"),
        },
        other_days,
        minimum_liquidity_margin=Decimal("365"),
    )
    assert result["candidate_close_matches_official"] is True
    assert result["candidate_volume_within_official_interval"] is True
    assert result["candidate_amount_within_official_interval"] is True
    assert result["maximum_20_session_average_perturbation_cny"] == "102.2"
    assert result["liquidity_decision_invariant_over_official_interval"] is True
    assert result["official_target_high"] == "24.25"
    assert result["official_target_low"] == "19.98"
    assert result["official_target_open"] is None
    assert result["factor_inputs_officially_bounded"] is True
    assert result["full_ohlcv_officially_reconstructed"] is False

    assert (
        reconstruct_row(
            "300001",
            candidate,
            {
                "open": Decimal("21.97"),
                "close": Decimal("20.34"),
                "low": Decimal("19.98"),
                "high": Decimal("24.25"),
                "volume": Decimal("20440900"),
                "amount": Decimal("454533543"),
            },
            other_days,
            minimum_liquidity_margin=Decimal("100"),
        )["factor_inputs_officially_bounded"]
        is False
    )

    stat = (
        "<table><tr>"
        + "".join(
            f"<td>{value}</td>"
            for value in (
                "300023",
                "name",
                "1",
                "2",
                "3",
                "4",
                "5",
                "6",
                "",
                "24.25",
                "19.98",
                "20.34",
                "1",
                "2044",
                "45453",
                "2",
            )
        )
        + "</tr></table>"
    ).encode("gb18030")
    value = (
        "<table><tr>"
        + "".join(
            f"<td>{item}</td>"
            for item in (
                "300023",
                "name",
                "45453.35",
                "1",
                "2",
                "3",
                "4",
                "5",
                "6",
                "7",
                "8",
                "9",
                "10",
                "11",
                "12",
            )
        )
        + "</tr></table>"
    ).encode("gb18030")
    assert parse_monthly_publication(stat, value)["300023"]["amount"] == Decimal("454533500")
