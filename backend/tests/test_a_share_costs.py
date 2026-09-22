from datetime import UTC, date, datetime
from decimal import Decimal

import pytest

from app.domain.markets import TransactionCostSchedule
from app.domain.trading import OrderSide
from app.research.costs import EffectiveDatedAShareCommission


def _schedule(
    *,
    valid_from: date,
    valid_to: date | None,
    stamp: str,
) -> TransactionCostSchedule:
    return TransactionCostSchedule(
        commission_rate=Decimal("0.0003"),
        minimum_commission=Decimal("5"),
        sell_stamp_duty_rate=Decimal(stamp),
        transfer_fee_rate=Decimal("0.00001"),
        valid_from=valid_from,
        valid_to=valid_to,
        source_version=f"cost-{valid_from.isoformat()}",
    )


def test_cost_schedule_is_effective_dated_and_stamp_duty_is_sell_only() -> None:
    model = EffectiveDatedAShareCommission(
        (
            _schedule(valid_from=date(2008, 9, 19), valid_to=date(2023, 8, 27), stamp="0.001"),
            _schedule(valid_from=date(2023, 8, 28), valid_to=None, stamp="0.0005"),
        )
    )
    timestamp = datetime(2024, 1, 2, tzinfo=UTC)
    buy = model.calculate_for_fill(Decimal(1000), Decimal(10), OrderSide.BUY, timestamp)
    sell = model.calculate_for_fill(Decimal(1000), Decimal(10), OrderSide.SELL, timestamp)
    assert buy == Decimal("5.10000")
    assert sell == Decimal("10.10000")


def test_historical_stamp_duty_is_not_retroactively_replaced() -> None:
    model = EffectiveDatedAShareCommission(
        (
            _schedule(valid_from=date(2008, 9, 19), valid_to=date(2023, 8, 27), stamp="0.001"),
            _schedule(valid_from=date(2023, 8, 28), valid_to=None, stamp="0.0005"),
        )
    )
    old = model.calculate_for_fill(
        Decimal(1000), Decimal(10), OrderSide.SELL, datetime(2020, 1, 2, tzinfo=UTC)
    )
    new = model.calculate_for_fill(
        Decimal(1000), Decimal(10), OrderSide.SELL, datetime(2024, 1, 2, tzinfo=UTC)
    )
    assert old - new == Decimal("5.00000")


def test_cost_schedule_rejects_overlap() -> None:
    with pytest.raises(ValueError, match="must not overlap"):
        EffectiveDatedAShareCommission(
            (
                _schedule(valid_from=date(2020, 1, 1), valid_to=None, stamp="0.001"),
                _schedule(valid_from=date(2023, 1, 1), valid_to=None, stamp="0.0005"),
            )
        )


def test_approved_research_account_cost_convention_covers_full_dataset() -> None:
    model = EffectiveDatedAShareCommission(
        (
            _schedule(valid_from=date(2008, 9, 19), valid_to=date(2023, 8, 27), stamp="0.001"),
            _schedule(valid_from=date(2023, 8, 28), valid_to=None, stamp="0.0005"),
        )
    )
    assert model.calculate_for_fill(
        Decimal(1000), Decimal(10), OrderSide.SELL, datetime(2010, 1, 4, tzinfo=UTC)
    ) == Decimal("15.10000")
    assert model.calculate_for_fill(
        Decimal(1000), Decimal(10), OrderSide.SELL, datetime(2025, 12, 31, tzinfo=UTC)
    ) == Decimal("10.10000")
