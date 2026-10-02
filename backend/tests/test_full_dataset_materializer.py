import hashlib
import json
from dataclasses import replace
from datetime import UTC, date, datetime
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch

import pytest

from app.data.catalog.normalized import _logical_hash
from app.data.full_dataset import FullDataset
from app.domain.markets import Board, Exchange, Market, SecurityId, TradingRuleResolver
from app.domain.markets.cn_a_rules import historical_cn_a_rules
from app.domain.trading import Order, OrderSide, OrderType
from app.research.execution_convention import rejection_reason
from scripts.materialize_full_dataset import (
    RAW_FIELDS,
    SecurityResolver,
    StreamingPartition,
    adjustment_rows,
    risk_from_name,
)


def test_streaming_partition_matches_catalog_logical_hash(tmp_path: Path) -> None:
    rows = [
        {**dict.fromkeys(RAW_FIELDS), "security_id": "a", "trading_date": "2020-01-01"},
        {**dict.fromkeys(RAW_FIELDS), "security_id": "b", "trading_date": "2020-01-01"},
    ]
    writer = StreamingPartition(tmp_path / "part.parquet", RAW_FIELDS, ("security_id",))
    writer.write(rows)
    receipt = writer.close("part.parquet")
    assert receipt.logical_sha256 == _logical_hash(RAW_FIELDS, rows)
    assert receipt.sha256 == hashlib.sha256((tmp_path / "part.parquet").read_bytes()).hexdigest()


def test_resolver_risk_and_official_cash_overlay_are_deterministic() -> None:
    master = [
        {
            "exchange": "SZSE",
            "symbol": "000001",
            "effective_from": "2000-01-01",
            "effective_to": None,
            "security_id": "CN-A:SZSE:000001",
        }
    ]
    assert SecurityResolver(master).resolve("SZSE", "000001", "2010-01-04") == "CN-A:SZSE:000001"
    assert risk_from_name("S *ST 示例") == "STAR_ST"
    assert risk_from_name("退市示例") == "DELISTING_PERIOD"
    inventory = {
        "intervals": [
            {
                "security_id": "CN-A:SZSE:000001",
                "effective_from": "2010-01-01",
                "effective_to": "2025-12-31",
                "in_interval_variants": {
                    "x": {"baseline": ["2009-01-01", "1"], "period_rows": [["2020-01-01", "2"]]}
                },
            }
        ]
    }
    authority = {
        "official_cash_overlay_events": [
            {
                "security_id": "CN-A:SZSE:000001",
                "effective_date": "2015-01-01",
                "factor_step": "1.1",
            }
        ]
    }
    first = adjustment_rows(inventory, authority)
    assert first == adjustment_rows(json.loads(json.dumps(inventory)), authority)
    assert [(row["effective_date"], row["hfq_factor"]) for row in first] == [
        ("2009-01-01", "1"),
        ("2015-01-01", "1.1"),
        ("2020-01-01", "2.2"),
    ]


def _cache_fixture(tmp_path: Path, flat_symbol: str) -> FullDataset:
    days = ("2011-01-04", "2011-01-05", "2011-01-06", "2011-01-07", "2011-01-10", "2011-01-11")
    symbols = ("600000", "600001")
    rows = [
        {
            "security_id": f"CN-A:SSE:{symbol}",
            "exchange": "SSE",
            "symbol": symbol,
            "trading_date": day,
            "raw_open": "10",
            "raw_high": "10" if symbol == flat_symbol and day == days[-1] else "10.5",
            "raw_low": "10" if symbol == flat_symbol and day == days[-1] else "9.5",
            "raw_close": "10",
            "pre_close": "10",
            "volume": "100000",
            "amount": "1000000",
            "source_name": "isolated-cache-fixture",
            "risk_status": "NORMAL",
            "source_lineage": "isolated-cache-fixture",
        }
        for day in days
        for symbol in symbols
    ]
    writer = StreamingPartition(
        tmp_path / "2011-01.parquet", RAW_FIELDS, ("trading_date", "security_id")
    )
    writer.write(rows)
    writer.close("2011-01.parquet")
    # Exercise the real loader with disposable data, not archive authority/hash validation.
    dataset = object.__new__(FullDataset)
    dataset.root = tmp_path
    dataset.paths = ("2011-01.parquet",)
    dataset.calendar_text = days
    dataset.calendar_days = tuple(date.fromisoformat(day) for day in days)
    dataset.calendar_index = {day: index for index, day in enumerate(days)}
    dataset.ids = {
        f"CN-A:SSE:{symbol}": SecurityId(value=f"CN-A:SSE:{symbol}") for symbol in symbols
    }
    dataset.members = {
        sid: [
            {
                "effective_from": days[0],
                "effective_to": None,
                "board": "SSE_MAIN",
                "exchange": "SSE",
            }
        ]
        for sid in dataset.ids
    }
    dataset.listing_dates = dict.fromkeys(dataset.ids, days[0])
    dataset.curves = {sid: ((days[0], days[-1], ((days[0], Decimal(1)),)),) for sid in dataset.ids}
    dataset.blocked_starts = {}
    dataset.features = {}
    dataset.actions = {}
    dataset.resolver = TradingRuleResolver(historical_cn_a_rules())
    return dataset


@pytest.mark.parametrize("flat_symbol", ["600000", "600001"])
def test_full_dataset_rule_cache_keeps_each_security_execution_status(
    tmp_path: Path, flat_symbol: str
) -> None:
    dataset = _cache_fixture(tmp_path, flat_symbol)
    sessions = tuple(dataset.sessions())
    assert len(sessions) == 6
    with patch.object(dataset.resolver, "resolve", side_effect=AssertionError("execution=False")):
        observations = tuple(dataset.sessions(execution=False))
    assert observations == tuple(
        replace(session, trading_rules=(), buy_lot_sizes=()) for session in sessions
    )

    session = sessions[-1]
    for bar, status_record, actual in zip(
        session.bars, session.statuses, session.trading_rules, strict=True
    ):
        status = status_record.status
        expected = dataset.resolver.resolve(
            security_id=bar.security_id,
            market=Market.CN_A,
            exchange=Exchange.SSE,
            board=Board.SSE_MAIN,
            trading_date=session.trading_date,
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            security_status=status,
            listing_age_sessions=5,
        )
        order = Order(
            strategy_id="isolated-cache-fixture",
            symbol=f"{str(bar.security_id).rsplit(':', 1)[1]}.SSE",
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            quantity=Decimal(100),
            price=Decimal(10),
            intended_execution_session=session.trading_date,
            created_at=datetime(2011, 1, 10, 7, tzinfo=UTC),
        )
        if status.is_one_price_limit:
            assert not expected.executable
            assert rejection_reason(order, bar, status, actual, Decimal(0)) is not None
            assert (
                rejection_reason(
                    order, bar, status, expected.model_copy(update={"executable": True}), Decimal(0)
                )
                == "SINGLE_PRICE_OR_LOCKED"
            )
        else:
            assert expected.executable
            assert rejection_reason(order, bar, status, expected, Decimal(0)) is None
            assert rejection_reason(order, bar, status, actual, Decimal(0)) is None
        assert actual == expected
