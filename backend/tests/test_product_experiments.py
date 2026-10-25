import csv
import io
import json
from dataclasses import replace
from datetime import UTC, date, datetime
from decimal import ROUND_DOWN, ROUND_HALF_EVEN, ROUND_UP, Context, Decimal, Inexact, localcontext
from threading import Event
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.application.experiments.data import (
    DEMO_END,
    DEMO_ID,
    DEMO_SHA,
    DEMO_START,
    HISTORICAL_ECONOMIC_GAP_SHA,
    HISTORICAL_ID,
    ExperimentDatasetRegistry,
    ExperimentInputError,
    SyntheticExperimentDataset,
    current_dataset_quality,
    current_source_integrity,
)
from app.application.experiments.models import CreateExperimentRequest
from app.application.experiments.runner import (
    ExperimentCancelled,
    build_plan_preview,
    json_value,
    run_experiment,
)
from app.data.catalog.checksums import canonical_sha256
from app.data.catalog.freeze import MARKER
from app.domain.markets.corporate_actions import OrdinaryDistributionInputError


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


@pytest.mark.parametrize(
    ("dataset_id", "sha", "expected"),
    [
        (HISTORICAL_ID, HISTORICAL_ECONOMIC_GAP_SHA, "KNOWN_ECONOMIC_COVERAGE_GAP"),
        (HISTORICAL_ID, "a" * 64, "HISTORICAL_DATASET_QUALITY_UNKNOWN"),
        (HISTORICAL_ID, None, "HISTORICAL_DATASET_QUALITY_UNKNOWN"),
        (HISTORICAL_ID, [HISTORICAL_ECONOMIC_GAP_SHA], "HISTORICAL_DATASET_QUALITY_UNKNOWN"),
        (DEMO_ID, HISTORICAL_ECONOMIC_GAP_SHA, None),
        ("cn-a-pilot-akshare-20230101-20240731-v1", HISTORICAL_ECONOMIC_GAP_SHA, None),
    ],
)
def test_later_dataset_quality_uses_saved_exact_identity_not_mode_or_mounted_sha(
    dataset_id, sha, expected
):
    assert current_dataset_quality(dataset_id, sha) == expected
    assert (
        current_source_integrity(dataset_id, sha)
        == {
            "KNOWN_ECONOMIC_COVERAGE_GAP": "SOURCE_CONTRACT_INTEGRITY_FAILED",
            "HISTORICAL_DATASET_QUALITY_UNKNOWN": "SOURCE_CONTRACT_INTEGRITY_UNVERIFIED",
            None: None,
        }[expected]
    )


@pytest.mark.parametrize("sha", [HISTORICAL_ECONOMIC_GAP_SHA, "b" * 64])
async def test_read_and_export_quality_do_not_rewrite_original_summary_or_plan(monkeypatch, sha):
    from app.api.routes import experiments
    from app.application.experiments.export import export_csv, export_json

    summary = {
        "metrics": {"cumulative_return": "-0.123456789123456789"},
        "limitations": [],
        "simulation_plan": {"dataset_sha256": sha, "account": {"cash": "123.000000000000001"}},
    }
    configuration = json_value(demo_request().model_dump())
    row = SimpleNamespace(
        id=uuid4(),
        name="Saved result",
        status="SUCCEEDED",
        mode="historical_exploration",
        dataset_id=HISTORICAL_ID,
        dataset_sha256=sha,
        summary=summary,
        configuration=configuration,
        configuration_sha256="c" * 64,
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
        completed_at=None,
    )
    manager = SimpleNamespace(
        get=AsyncMock(return_value=row), collection=AsyncMock(return_value=([], 0))
    )
    monkeypatch.setattr(experiments, "experiment_manager", manager)
    before = json.dumps([summary, configuration], sort_keys=True)
    read = await experiments.experiment_result(row.id, None)
    quality = current_dataset_quality(HISTORICAL_ID, sha)
    assert read is not summary and read["current_dataset_quality"] == quality
    integrity = current_source_integrity(HISTORICAL_ID, sha)
    assert read["current_source_integrity"] == integrity
    assert {
        k: v
        for k, v in read.items()
        if k not in {"current_dataset_quality", "current_source_integrity"}
    } == summary
    exported = json.loads("".join([part async for part in export_json(manager, row, None, None)]))
    assert exported["metadata"]["current_dataset_quality"] == quality
    assert exported["metadata"]["current_source_integrity"] == integrity
    assert exported["full_period_summary"] == summary
    csv_text = "".join([part async for part in export_csv(manager, row, "trades", None, None)])
    metadata = {item["field"]: item["value"] for item in csv.DictReader(io.StringIO(csv_text))}
    assert metadata["current_dataset_quality"] == quality
    assert metadata["current_source_integrity"] == integrity
    assert json.loads(metadata["full_period_summary"]) == summary
    assert json.dumps([summary, configuration], sort_keys=True) == before


@pytest.mark.parametrize(
    "dataset_id,sha",
    [
        (HISTORICAL_ID, HISTORICAL_ECONOMIC_GAP_SHA),
        (HISTORICAL_ID, "b" * 64),
        (DEMO_ID, HISTORICAL_ECONOMIC_GAP_SHA),
        ("cn-a-pilot-akshare-20230101-20240731-v1", HISTORICAL_ECONOMIC_GAP_SHA),
    ],
)
def test_formal_quality_projection_keeps_saved_lineage_manifest_and_diagnostics(dataset_id, sha):
    from app.api.routes.research import _dataset, _run

    now = datetime(2026, 1, 1, tzinfo=UTC)
    dataset = SimpleNamespace(
        dataset_id=dataset_id,
        provider="audited",
        provider_version="1",
        retrieval_timestamp=now,
        coverage_start=date(2010, 1, 1),
        coverage_end=date(2025, 12, 31),
        security_count=1,
        canonical_sha256=sha,
        rule_version="1",
        adjustment_method="separate",
        readiness_status="READY",
        frozen=True,
        manifest={"checksum": "original"},
    )
    run = SimpleNamespace(
        id=uuid4(),
        dataset_id=dataset_id,
        dataset_checksum=sha,
        status="SUCCEEDED",
        period_kind="VALIDATION",
        git_commit="a" * 40,
        provider="audited",
        provider_version="1",
        market_rule_version="1",
        strategy_id="saved",
        strategy_config_hash="a" * 64,
        transaction_cost_config={"rate": "0.000300000000000001"},
        benchmark_id="CSI300",
        benchmark_version="1",
        temporal_split_hash="b" * 64,
        random_seed=0,
        created_at=now,
        started_at=None,
        completed_at=None,
        failure_code=None,
        diagnostics={"candidate": "S0"},
    )
    before = canonical_sha256(json_value([vars(dataset), vars(run)]))
    expected = current_dataset_quality(dataset_id, sha)
    assert _dataset(dataset, detail=True).current_dataset_quality == expected
    integrity = current_source_integrity(dataset_id, sha)
    assert _dataset(dataset, detail=True).current_source_integrity == integrity
    result = _run(run)
    assert result.current_dataset_quality == expected and result.dataset_checksum == sha
    assert result.current_source_integrity == integrity
    assert result.diagnostics == run.diagnostics
    assert _dataset(dataset, detail=True).manifest == dataset.manifest
    assert canonical_sha256(json_value([vars(dataset), vars(run)])) == before


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


def test_non_object_historical_freeze_marker_does_not_block_demo(tmp_path, monkeypatch):
    archive = tmp_path / HISTORICAL_ID
    archive.mkdir()
    (archive / "manifest.json").write_text("{}")
    (archive / MARKER).write_text("null")
    monkeypatch.setattr(
        "app.application.experiments.data.load_manifest",
        lambda _: SimpleNamespace(dataset_id=HISTORICAL_ID, canonical_sha256="sha", partitions=()),
    )

    registry = ExperimentDatasetRegistry(tmp_path)
    historical, demo = registry.capabilities()["datasets"]
    assert historical["available"] is False
    assert historical["reason_code"] == "DATASET_INTEGRITY_FAILED"
    assert demo["available"] is True
    with pytest.raises(ExperimentInputError, match="DATASET_INTEGRITY_FAILED"):
        registry.resolve(HISTORICAL_ID)


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


@pytest.mark.parametrize("specific", (True, False))
def test_distribution_input_failure_keeps_safe_code_without_promoting_other_value_errors(
    tmp_path, monkeypatch, specific
):
    failure = (
        OrdinaryDistributionInputError("private source diagnostics")
        if specific
        else ValueError("private source diagnostics")
    )

    def fail(*args):
        raise failure

    monkeypatch.setattr("app.research.engine.ResearchExecutionEngine.process_session", fail)
    phases = []
    with pytest.raises(ExperimentInputError if specific else ValueError) as caught:
        run_experiment(
            ExperimentDatasetRegistry(tmp_path),
            demo_request(),
            DEMO_SHA,
            Event(),
            lambda *p: phases.append(p),
        )
    if specific:
        assert caught.value.code == OrdinaryDistributionInputError.code
        assert "private" not in str(caught.value)
        assert caught.value.context is None
    else:
        assert caught.value is failure
    assert phases == [("VERIFYING_DATA", 0, None), ("EXECUTING", 0, 340)]


def test_reference_failure_preserves_observed_context_without_advancing_progress(
    tmp_path, monkeypatch
):
    from app.research.engine import UnexplainedReferenceAdjustment

    def fail(_engine, session):
        raise UnexplainedReferenceAdjustment(
            session.trading_date, ("CN-A:SSE:600000", "CN-A:SZSE:000001")
        )

    monkeypatch.setattr("app.research.engine.ResearchExecutionEngine.process_session", fail)
    phases = []
    with pytest.raises(ExperimentInputError) as caught:
        run_experiment(
            ExperimentDatasetRegistry(tmp_path),
            demo_request(),
            DEMO_SHA,
            Event(),
            lambda *p: phases.append(p),
        )
    assert caught.value.code == UnexplainedReferenceAdjustment.code
    assert caught.value.context.model_dump(mode="json") == {
        "trading_date": DEMO_START.isoformat(),
        "security_ids": ["CN-A:SSE:600000", "CN-A:SZSE:000001"],
        "security_count": 2,
    }
    assert str(caught.value) == UnexplainedReferenceAdjustment.code
    assert phases == [("VERIFYING_DATA", 0, None), ("EXECUTING", 0, 340)]


def test_failure_context_rejects_invalid_or_unbounded_untrusted_diagnostics():
    from app.application.experiments.models import ExperimentFailureContext

    valid = {"trading_date": "2024-01-04", "security_ids": ["CN-A:SSE:600000"], "security_count": 1}
    assert ExperimentFailureContext.model_validate(valid).model_dump(mode="json") == valid
    for change in (
        {"trading_date": "2024-02-30"},
        {"security_ids": []},
        {"security_ids": ["private/path"]},
        {"security_count": True},
        {"security_count": 0},
        {"security_count": 2},
        {"traceback": "private"},
        {"security_ids": ["CN-A:SZSE:000001", "CN-A:SSE:600000"], "security_count": 2},
        {"security_ids": ["CN-A:SSE:600000"] * 2, "security_count": 2},
        {"security_ids": [f"CN-A:SSE:{i:06d}" for i in range(101)], "security_count": 101},
    ):
        with pytest.raises(ValidationError):
            ExperimentFailureContext.model_validate({**valid, **change})
    prefix = [f"CN-A:SSE:{i:06d}" for i in range(100)]
    assert (
        ExperimentFailureContext.model_validate(
            {**valid, "security_ids": prefix, "security_count": 101}
        ).security_count
        == 101
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
    assert plan["account_snapshot_trading_date"] == as_of.isoformat()
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
    assert plan["account_snapshot_trading_date"] is None
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
    assert same_day["account_snapshot_trading_date"] == "2024-01-03"
    assert same_day["account"]["cash"] == "10000.000000000000000001"


@pytest.mark.parametrize("precision", [6, 28, 50])
@pytest.mark.parametrize("rounding", [ROUND_DOWN, ROUND_HALF_EVEN, ROUND_UP])
def test_plan_projection_is_independent_of_callers_decimal_context(precision, rounding):
    from app.application.experiments.runner import _holdings_row
    from app.execution import FixedCommission
    from app.research import ResearchExecutionEngine
    from tests.test_research_execution_engine import CALENDAR, OneTargetStrategy, _session

    request = demo_request(start_date="2024-01-02", end_date="2024-01-03")
    with localcontext(Context(prec=28, rounding=ROUND_HALF_EVEN)):
        engine = ResearchExecutionEngine(
            OneTargetStrategy(),
            initial_cash=Decimal("10000"),
            commission_model=FixedCommission(Decimal("5.123456789123456789")),
            calendar=CALENDAR,
        )
        buy = engine.process_session(_session(date(2024, 1, 2), opening="10"))
        held = engine.process_session(_session(date(2024, 1, 3), opening="9.9"))

        def projection():
            return (
                build_plan_preview(
                    request,
                    DEMO_SHA,
                    "synthetic_demo",
                    buy,
                    buy.target,
                    date(2024, 1, 3),
                    253,
                ),
                build_plan_preview(
                    request,
                    DEMO_SHA,
                    "synthetic_demo",
                    held,
                    held.target,
                    date(2024, 1, 4),
                    254,
                ),
                _holdings_row(0, held.snapshot),
            )

        expected = projection()
    assert expected[0]["estimated_cash_required"] == "1005.123456789123456789"
    assert expected[1]["account"]["positions"][0]["weight"] == ("0.09905074822284500934353395374")
    snapshots = (buy.snapshot.model_dump(), held.snapshot.model_dump())
    with localcontext(Context(prec=precision, rounding=rounding)) as context:
        before_flags = context.flags.copy()
        assert projection() == expected
        assert context.flags == before_flags
        assert context.prec == precision and context.rounding == rounding
        context.traps[Inexact] = True
        assert projection() == expected
    assert (buy.snapshot.model_dump(), held.snapshot.model_dump()) == snapshots


@pytest.mark.parametrize("precision", [6, 28, 50])
@pytest.mark.parametrize("rounding", [ROUND_DOWN, ROUND_HALF_EVEN, ROUND_UP])
@pytest.mark.parametrize("equity,quantity", [("9999.999", "0"), ("10000.001", "100")])
def test_exploratory_lot_sizing_owns_decimal_context(
    monkeypatch, precision, rounding, equity, quantity
):
    from app.application.experiments.runner import ExploratoryStrategy
    from app.research.models import PortfolioTarget, TargetPosition
    from app.research.strategy import ChinaAMomentumLowVolResearchStrategy
    from tests.test_research_execution_engine import SECURITY_ID, _session

    request = demo_request(start_date="2024-01-02", end_date="2024-01-03")
    session = _session(date(2024, 1, 2), opening="10")
    parent_target = PortfolioTarget(
        positions=(
            TargetPosition(
                security_id=SECURITY_ID,
                target_weight=Decimal("0.1"),
                quantity=Decimal(0),
                reference_price=Decimal(10),
            ),
        ),
        residual_cash=Decimal(equity),
    )
    monkeypatch.setattr(
        ChinaAMomentumLowVolResearchStrategy,
        "target_for_completed_session",
        lambda *args: parent_target,
    )
    with localcontext(Context(prec=28, rounding=ROUND_HALF_EVEN)):
        expected = ExploratoryStrategy(request).target_for_completed_session(
            session, Decimal(equity)
        )
    assert expected.positions[0].quantity == Decimal(quantity)
    with localcontext(Context(prec=precision, rounding=rounding)) as context:
        before_flags = context.flags.copy()
        context.traps[Inexact] = True
        actual = ExploratoryStrategy(request).target_for_completed_session(session, Decimal(equity))
        assert actual == expected
        assert context.prec == precision and context.rounding == rounding
        assert context.flags == before_flags
    assert parent_target.positions[0].quantity == 0


@pytest.mark.parametrize("precision", [6, 28, 50])
@pytest.mark.parametrize("rounding", [ROUND_DOWN, ROUND_HALF_EVEN, ROUND_UP])
def test_experiment_aggregate_output_owns_decimal_context(monkeypatch, precision, rounding):
    from app.application.experiments import runner
    from tests.test_research_execution_engine import CALENDAR, OneTargetStrategy, _session

    request = demo_request(start_date="2024-01-02", end_date="2024-01-04", initial_cash="10000")
    sessions = tuple(
        _session(date(2024, 1, day), opening=price)
        for day, price in ((2, "10"), (3, "9.9"), (4, "9.99"))
    )
    days = tuple(session.trading_date for session in sessions)
    data = SimpleNamespace(
        calendar_days=days,
        calendar=CALENDAR,
        next_session=None,
        sessions=lambda: iter(sessions),
        cost_model=SimpleNamespace(schedules=(sessions[0].trading_rules[0].cost_schedule,)),
        benchmark=dict(
            zip(
                (day.isoformat() for day in days),
                (Decimal("100"), Decimal("101.123456789"), Decimal("102.234567891")),
                strict=True,
            )
        ),
    )
    registry = SimpleNamespace(
        resolve=lambda _: {
            "sha256": DEMO_SHA,
            "mode": "synthetic_demo",
            "benchmark_id": "synthetic",
        }
    )
    monkeypatch.setattr(runner, "load_experiment_dataset", lambda *args: data)
    monkeypatch.setattr(runner, "_implementation_checksum", lambda: "b" * 64)
    monkeypatch.setattr(runner, "ExploratoryStrategy", lambda *args: OneTargetStrategy())
    with localcontext(Context(prec=28, rounding=ROUND_HALF_EVEN)):
        expected = run_experiment(registry, request, DEMO_SHA, Event(), lambda *args: None)
    assert expected.rows["equity"][-1]["benchmark"] == "10223.4567891"
    assert expected.summary["metrics"]["turnover"] == "0.09900336545440301333976679647"
    with localcontext(Context(prec=precision, rounding=rounding)) as context:
        actual = run_experiment(registry, request, DEMO_SHA, Event(), lambda *args: None)
        assert actual == expected
        assert context.prec == precision and context.rounding == rounding


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
