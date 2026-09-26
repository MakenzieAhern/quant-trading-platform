from dataclasses import replace
from datetime import UTC, date, datetime
from decimal import Decimal
from threading import Event

import pytest
from pydantic import ValidationError

from app.application.experiments.data import (
    DEMO_END,
    DEMO_ID,
    DEMO_SHA,
    DEMO_START,
    ExperimentDatasetRegistry,
    SyntheticExperimentDataset,
)
from app.application.experiments.models import CreateExperimentRequest
from app.application.experiments.runner import (
    ExperimentCancelled,
    build_plan_preview,
    json_value,
    run_experiment,
)
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
    assert output.summary["simulation_plan"]["status"] == "NEXT_SESSION_UNAVAILABLE"
    assert output.summary["simulation_plan"]["candidates"] == []
    assert output.summary["simulation_plan"]["estimated_cash_required"] is None
    assert output.rows["equity"] == repeat.rows["equity"]
    assert output.rows["holdings"] == repeat.rows["holdings"]
    assert len(output.summary["implementation_sha256"]) == 64
    assert output.summary["provenance"]["provider"] == "DETERMINISTIC_SYNTHETIC_GENERATOR"
    assert output.summary["effective_transaction_cost_schedules"][0]["commission_rate"] == "0.0003"
    assert output.summary["effective_risk_limits"]["max_position_weight"] == "0.1"
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
        assert fill["trading_date"] == fill["timestamp"][:10]
    assert any(s["positions"] for s in output.rows["holdings"])
    for snapshot, point in zip(output.rows["holdings"], output.rows["equity"], strict=True):
        assert snapshot["equity"] == point["equity"]
        assert snapshot["trading_date"] == point["trading_date"]
        assert Decimal(snapshot["cash"]) + Decimal(snapshot["market_value"]) == Decimal(
            snapshot["equity"]
        )
        position_value = sum(
            (Decimal(p["market_value"]) for p in snapshot["positions"]), Decimal(0)
        )
        assert position_value + Decimal(snapshot["pending_corporate_action_value"]) == Decimal(
            snapshot["market_value"]
        )
        for position in snapshot["positions"]:
            assert Decimal(position["market_value"]) == Decimal(position["quantity"]) * Decimal(
                position["market_price"]
            )
            assert Decimal(position["weight"]) == Decimal(position["market_value"]) / Decimal(
                snapshot["equity"]
            )


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


def test_no_fills_preserves_real_all_cash_snapshots(tmp_path):
    output = run_experiment(
        ExperimentDatasetRegistry(tmp_path),
        demo_request(
            start_date="2030-01-02", end_date="2030-01-10", initial_cash="100000.123456789123456789"
        ),
        DEMO_SHA,
        Event(),
        lambda *p: None,
    )
    assert output.rows["trades"] == []
    assert output.rows["holdings"]
    for snapshot in output.rows["holdings"]:
        assert snapshot["cash"] == snapshot["equity"] == "100000.123456789123456789"
        assert snapshot["positions"] == []
        assert snapshot["market_value"] == snapshot["pending_corporate_action_value"] == "0"


def test_final_session_plan_uses_replayed_account_oms_and_only_known_calendar(tmp_path):
    source = SyntheticExperimentDataset(DEMO_END)
    as_of, next_day = source.calendar_days[252:254]
    request = demo_request(start_date=DEMO_START.isoformat(), end_date=as_of.isoformat())
    output = run_experiment(
        ExperimentDatasetRegistry(tmp_path), request, DEMO_SHA, Event(), lambda *p: None
    )
    plan = output.summary["simulation_plan"]
    assert plan["status"] == "SIMULATION_PREVIEW"
    assert plan["as_of_trading_date"] == as_of.isoformat()
    assert plan["next_accepted_session"] == next_day.isoformat()
    assert plan["configuration_sha256"] == canonical_sha256(json_value(request.model_dump()))
    assert plan["data_snapshot_sha256"] != plan["account"]["snapshot_sha256"]
    assert plan["account"]["cash"] == output.rows["holdings"][-1]["cash"]
    assert plan["account"]["equity"] == output.rows["holdings"][-1]["equity"]
    assert plan["candidates"]
    assert all(
        item["reference_raw_close"] is None or isinstance(item["reference_raw_close"], str)
        for item in plan["candidates"]
    )
    assert plan["simulation_only"] is True and plan["submitted_to_account"] is False
    assert plan["not_today_advice"] is True
    assert all(
        item["risk_approved"] is not None
        for item in plan["candidates"]
        if item["proposed_quantity"] != "0"
    )

    early = run_experiment(
        ExperimentDatasetRegistry(tmp_path),
        demo_request(
            start_date=DEMO_START.isoformat(), end_date=source.calendar_days[10].isoformat()
        ),
        DEMO_SHA,
        Event(),
        lambda *p: None,
    ).summary["simulation_plan"]
    assert early["status"] == "INSUFFICIENT_WARMUP"
    assert early["candidates"] == []
    assert early["estimated_cash_required"] is None


def test_plan_does_not_relabel_prior_account_snapshot_as_current():
    from app.execution import FixedCommission
    from app.research import ResearchExecutionEngine, ResearchSession
    from tests.test_research_execution_engine import CALENDAR, OneTargetStrategy, _session

    engine = ResearchExecutionEngine(
        OneTargetStrategy(),
        initial_cash=Decimal("10000.000000000000000001"),
        commission_model=FixedCommission(Decimal(5)),
        calendar=CALENDAR,
    )
    first = engine.process_session(_session(date(2024, 1, 2), opening="10"))
    missing = engine.process_session(
        ResearchSession(trading_date=date(2024, 1, 3), bars=(), statuses=(), buy_lot_sizes=())
    )
    assert missing.snapshot is first.snapshot
    assert missing.snapshot is not None
    original = missing.snapshot.model_dump()
    plan = build_plan_preview(
        demo_request(start_date="2024-01-02", end_date="2024-01-03"),
        DEMO_SHA,
        "synthetic_demo",
        missing,
        missing.target,
        date(2024, 1, 4),
        253,
    )
    assert plan["as_of_trading_date"] == "2024-01-03"
    assert plan["status"] == "ACCOUNT_SNAPSHOT_UNAVAILABLE"
    assert plan["account"] is None
    assert plan["candidates"] == []
    assert plan["estimated_cash_required"] is None
    assert missing.snapshot.model_dump() == original

    # A UTC date one day earlier can still belong to this exchange trading date.
    current = replace(
        missing,
        snapshot=missing.snapshot.model_copy(
            update={"timestamp": datetime(2024, 1, 2, 16, tzinfo=UTC)}
        ),
    )
    same_day = build_plan_preview(
        demo_request(start_date="2024-01-02", end_date="2024-01-03"),
        DEMO_SHA,
        "synthetic_demo",
        current,
        current.target,
        date(2024, 1, 4),
        253,
    )
    assert same_day["status"] == "NOT_REBALANCE_SESSION"
    assert same_day["account"]["cash"] == "10000.000000000000000001"


@pytest.mark.parametrize(
    "value",
    ['=HYPERLINK("x")', "+SUM(1,2)", "-1+2", "@SUM(A1)", "  =1+1", "\tformula", "\n=1+1", "\r=1+1"],
)
def test_csv_neutralizes_formula_cells(value):
    from app.application.experiments.export import csv_cell

    assert csv_cell(value) == "'" + value


def test_csv_preserves_exact_numbers_unicode_and_null():
    from app.application.experiments.export import csv_cell

    for value in ["-0.123456789123456789", "999999999999999999999.123", "0", '收益,测试"一"']:
        assert csv_cell(value) == value
    assert csv_cell(None) == ""


def test_holdings_retains_pending_corporate_action_value_without_inventing_tradable_positions():
    from app.application.experiments.runner import _holdings_row
    from tests.test_demerger_accounting import at, event, funded

    portfolio, _ = funded("100")
    portfolio.recognize_demerger(event(), date(2010, 2, 26), at("2010-02-26"))
    actual = portfolio.snapshot_at(at("2010-03-01"))
    snapshot = _holdings_row(0, actual)
    assert snapshot["positions"] == []
    assert snapshot["pending_corporate_action_value"] == snapshot["market_value"] == "387"
    assert (
        Decimal(snapshot["cash"]) + Decimal(snapshot["pending_corporate_action_value"])
        == actual.equity
    )
    assert (
        Decimal(snapshot["corporate_action_realized_pnl"]) == actual.corporate_action_realized_pnl
    )
    assert Decimal(snapshot["total_pnl"]) == actual.total_pnl
