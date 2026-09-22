from datetime import date
from decimal import Decimal
from threading import Event

import pytest
from pydantic import ValidationError

from app.application.experiments.data import (
    DEMO_END,
    DEMO_ID,
    DEMO_SHA,
    ExperimentDatasetRegistry,
    SyntheticExperimentDataset,
)
from app.application.experiments.models import CreateExperimentRequest
from app.application.experiments.runner import ExperimentCancelled, json_value, run_experiment
from app.data.catalog.checksums import canonical_sha256


def demo_request(**changes):
    return CreateExperimentRequest.model_validate(
        {
            "name": "My first experiment",
            "dataset_id": DEMO_ID,
            "start_date": "2030-12-20",
            "end_date": DEMO_END.isoformat(),
            **changes,
        }
    )


def test_experiment_validation_rejects_numbers_invalid_dates_and_unsupported_parameters():
    for change in (
        {"initial_cash": 100000},
        {"initial_cash": "NaN"},
        {"initial_cash": "0.000000000000000000000000000000000000001"},
        {"end_date": "2029-01-01"},
        {"name": "  "},
        {"strategy": {"leverage": "2"}},
        {"costs": {"commission_rate": "-1"}},
        {"risk": {"max_drawdown": "0.1"}},
        {"risk": {"max_position_weight": "2"}},
    ):
        with pytest.raises(ValidationError):
            demo_request(**change)
    left = canonical_sha256(json_value(demo_request(initial_cash="100000.000").model_dump()))
    right = canonical_sha256(json_value(demo_request(initial_cash="100000").model_dump()))
    assert left == right


def test_clean_install_capability_is_explicit_synthetic_demo(tmp_path):
    catalog = ExperimentDatasetRegistry(tmp_path)
    historical, demo = catalog.datasets()
    assert historical["available"] is False
    assert historical["reason_code"] == "DATASET_NOT_MOUNTED"
    assert demo["available"] and demo["mode"] == "synthetic_demo"
    source = SyntheticExperimentDataset(DEMO_END)
    assert len(source.calendar_days) == 340
    assert source.calendar_days[-1] == date.fromisoformat(demo["coverage_end"])


def test_real_engine_demo_has_exact_money_costs_progress_and_repeatable_results(tmp_path):
    registry = ExperimentDatasetRegistry(tmp_path)
    phases = []
    request = demo_request()
    output = run_experiment(registry, request, DEMO_SHA, Event(), lambda *p: phases.append(p))
    repeat = run_experiment(registry, request, DEMO_SHA, Event(), lambda *p: None)
    assert phases[0] == ("VERIFYING_DATA", 0, None)
    assert phases[-1] == ("EXECUTING", 340, 340)
    assert output.summary == repeat.summary
    assert output.rows["equity"] == repeat.rows["equity"]
    assert output.summary["execution"]["fills"] > 0
    assert Decimal(output.summary["metrics"]["transaction_costs"]) > 0
    traded = sum(
        (Decimal(f["quantity"]) * Decimal(f["price"]) for f in output.rows["trades"]), Decimal(0)
    )
    mean_equity = sum((Decimal(p["equity"]) for p in output.rows["equity"]), Decimal(0)) / Decimal(
        len(output.rows["equity"])
    )
    assert Decimal(output.summary["metrics"]["turnover"]) == traded / mean_equity
    assert traded > 0
    assert output.rows["equity"][0]["equity"] == "100000"
    assert output.rows["equity"][0]["benchmark"] == "100000"
    assert "SYNTHETIC_DEMO_NOT_MARKET_OR_RESEARCH_EVIDENCE" in output.summary["limitations"]
    for fill in output.rows["trades"]:
        assert isinstance(fill["quantity"], str)
        assert Decimal(fill["quantity"]) % 100 == 0
        assert fill["timestamp"][:10] >= request.start_date.isoformat()


def test_cancellation_interrupts_at_completed_session_boundary(tmp_path):
    cancelled = Event()

    def progress(phase, completed, total):
        if completed == 10:
            cancelled.set()

    with pytest.raises(ExperimentCancelled):
        run_experiment(
            ExperimentDatasetRegistry(tmp_path), demo_request(), DEMO_SHA, cancelled, progress
        )


def test_cost_configuration_changes_actual_result_and_not_just_metadata(tmp_path):
    registry = ExperimentDatasetRegistry(tmp_path)
    normal = run_experiment(registry, demo_request(), DEMO_SHA, Event(), lambda *p: None)
    free = run_experiment(
        registry,
        demo_request(costs={"commission_rate": "0", "minimum_commission": "0"}),
        DEMO_SHA,
        Event(),
        lambda *p: None,
    )
    assert free.summary["metrics"]["transaction_costs"] == "0"
    assert Decimal(normal.summary["metrics"]["transaction_costs"]) > 0
    assert normal.summary["metrics"]["final_equity"] != free.summary["metrics"]["final_equity"]
