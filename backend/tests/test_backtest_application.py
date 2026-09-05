from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.api.schemas.backtests import CreateBacktestRequest
from app.application.backtests.models import (
    BacktestRunStatus,
    CreateBacktestCommand,
    require_transition,
)
from app.application.backtests.service import BacktestApplicationService
from app.domain.risk import RiskConfig


@pytest.mark.parametrize(
    ("current", "target"),
    [
        (BacktestRunStatus.CREATED, BacktestRunStatus.RUNNING),
        (BacktestRunStatus.RUNNING, BacktestRunStatus.SUCCEEDED),
        (BacktestRunStatus.RUNNING, BacktestRunStatus.FAILED),
    ],
)
def test_backtest_lifecycle_allows_only_documented_transitions(
    current: BacktestRunStatus, target: BacktestRunStatus
) -> None:
    require_transition(current, target)


@pytest.mark.parametrize(
    ("current", "target"),
    [
        (BacktestRunStatus.CREATED, BacktestRunStatus.SUCCEEDED),
        (BacktestRunStatus.CREATED, BacktestRunStatus.FAILED),
        (BacktestRunStatus.SUCCEEDED, BacktestRunStatus.RUNNING),
        (BacktestRunStatus.FAILED, BacktestRunStatus.SUCCEEDED),
        (BacktestRunStatus.RUNNING, BacktestRunStatus.CREATED),
    ],
)
def test_backtest_lifecycle_rejects_illegal_transitions(
    current: BacktestRunStatus, target: BacktestRunStatus
) -> None:
    with pytest.raises(ValueError, match="invalid backtest state transition"):
        require_transition(current, target)


def _request(value: object) -> dict[str, object]:
    return {
        "dataset_id": "AAPL_fixture",
        "symbol": "AAPL",
        "strategy": {
            "type": "moving_average_crossover",
            "parameters": {"short_period": 2, "long_period": 3},
        },
        "initial_cash": value,
        "default_order_quantity": "1",
    }


@pytest.mark.parametrize(
    "value",
    [
        "105.052500000000000001",
        "0.000000000000000001",
        "999999999999999999.123456789012345678",
    ],
)
def test_decimal_request_policy_accepts_exact_reference_values(value: str) -> None:
    request = CreateBacktestRequest.model_validate(_request(value))
    assert request.initial_cash == Decimal(value)


@pytest.mark.parametrize(
    "value",
    [
        1.0,
        "NaN",
        "Infinity",
        "-Infinity",
        "10000000000000000000000000000000000000000",
        "0.000000000000000000000000000000000000001",
    ],
)
def test_decimal_request_policy_rejects_float_nonfinite_overflow_and_scale(
    value: object,
) -> None:
    with pytest.raises(ValidationError):
        CreateBacktestRequest.model_validate(_request(value))


def _command(initial_cash: str, include_explicit_defaults: bool) -> CreateBacktestCommand:
    request_payload = _request(initial_cash)
    if include_explicit_defaults:
        request_payload["risk"] = {
            "max_order_notional": None,
            "max_position_quantity": None,
            "max_symbol_exposure": None,
            "max_gross_exposure": None,
            "max_leverage": None,
            "enforce_buying_power": False,
            "max_drawdown": None,
        }
    request = CreateBacktestRequest.model_validate(request_payload)
    return CreateBacktestCommand(
        dataset_id=request.dataset_id,
        symbol=request.symbol,
        strategy_type=request.strategy.type,
        strategy_parameters=request.strategy.parameters.model_dump(),
        initial_cash=request.initial_cash,
        default_order_quantity=request.default_order_quantity,
        risk=RiskConfig(**request.risk.model_dump()),
        start=request.start,
        end=request.end,
        client_request_id="same-key",
    )


def test_request_fingerprint_normalizes_decimal_text_and_explicit_defaults() -> None:
    first = _command("100000.0", False)
    second = _command("100000.000", True)
    assert BacktestApplicationService._request_hash(first) == (
        BacktestApplicationService._request_hash(second)
    )
