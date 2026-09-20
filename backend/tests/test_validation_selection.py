from scripts.evaluate_validation import select


def test_validation_uses_s4_fallback_when_no_candidate_passes() -> None:
    evaluations = [
        {"candidate": candidate, "all_gates_pass": False} for candidate in ("S2", "S3", "S4")
    ]
    assert select(evaluations, {}) == (
        "S4",
        "NO_CANDIDATE_PASSED_ALL_GATES_S4_REFERENCE_FALLBACK",
    )


def test_close_information_ratios_fall_through_to_sharpe() -> None:
    evaluations = [{"candidate": candidate, "all_gates_pass": True} for candidate in ("S2", "S3")]
    results = {
        "S2": {
            "metrics": {
                "information_ratio": "0.500",
                "sharpe_ratio": "0.7",
                "maximum_drawdown": "-0.2",
                "turnover": "2",
            },
            "config": {"factor_names": ["MOM_12_1"]},
        },
        "S3": {
            "metrics": {
                "information_ratio": "0.505",
                "sharpe_ratio": "0.9",
                "maximum_drawdown": "-0.3",
                "turnover": "3",
            },
            "config": {"factor_names": ["TREND_120", "LOW_VOL"]},
        },
    }
    assert select(evaluations, results) == ("S3", "VALIDATION_GATE_SELECTION")
