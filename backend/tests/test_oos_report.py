from scripts.build_oos_report import calendar_regimes


def test_calendar_regime_excess_is_strategy_minus_benchmark() -> None:
    assert calendar_regimes({"2022": "0.05"}, {"2022": "-0.10"}) == [
        {
            "year": "2022",
            "regime": "CSI300_DOWN_YEAR",
            "strategy_return": "0.05",
            "csi300_return": "-0.10",
            "excess_return": "0.15",
        }
    ]
