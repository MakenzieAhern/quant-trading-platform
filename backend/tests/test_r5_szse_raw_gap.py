import json
from datetime import date, timedelta

from scripts.probe_r5_szse_raw_gap import (
    TARGET_DATE,
    comparison,
    liquidity_window_check,
    parse_tencent_target,
    tencent_amount_history,
)


def test_tencent_target_parser_and_cross_source_precision():
    start = date.fromisoformat(TARGET_DATE) - timedelta(days=10)
    rows = [
        [
            (start + timedelta(days=offset)).isoformat(),
            "22.16",
            "20.73",
            "22.16",
            "20.49",
            "18698.49",
            {},
            "3.06",
            "2000.00",
        ]
        for offset in range(21)
    ]
    rows[10][8] = "3884.64"
    raw = (
        "kline_day2011="
        + json.dumps(
            {
                "code": 0,
                "data": {"sz300001": {"day": rows}},
            }
        )
    ).encode()
    tencent = parse_tencent_target(raw, "300001")
    assert tencent["volume"] == "1869849.00"
    assert tencent["amount"] == "38846400.00"
    assert comparison(tencent, {**tencent, "amount": "38846300"}) == {
        "price_parity": True,
        "volume_parity": True,
        "amount_difference_cny": "100.00",
        "amount_within_accepted_uncertainty_interval": True,
    }
    assert liquidity_window_check(tencent_amount_history(raw, "300001")) == {
        "liquidity_windows_checked": 2,
        "liquidity_decision_invariant": True,
        "minimum_distance_to_threshold_cny": "10942320.00",
    }
