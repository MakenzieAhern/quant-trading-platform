import hashlib
import json
from dataclasses import replace
from datetime import UTC, date, datetime
from decimal import ROUND_DOWN, Decimal, localcontext
from pathlib import Path
from unittest.mock import patch

import pytest

from app.data.catalog.normalized import _logical_hash
from app.data.full_dataset import FullDataset, pa, pq
from app.domain.markets import Board, Exchange, Market, SecurityId, TradingRuleResolver
from app.domain.markets.cn_a_rules import historical_cn_a_rules
from app.domain.markets.corporate_actions import CorporateAction, cash_bonus_reference_price
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


def _cache_fixture(tmp_path: Path, flat_symbol: str, exchange: str = "SSE") -> FullDataset:
    days = ("2011-01-04", "2011-01-05", "2011-01-06", "2011-01-07", "2011-01-10", "2011-01-11")
    symbols = ("600000", "600001") if exchange == "SSE" else ("000001", "000002")
    rows = [
        {
            "security_id": f"CN-A:{exchange}:{symbol}",
            "exchange": exchange,
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
        f"CN-A:{exchange}:{symbol}": SecurityId(value=f"CN-A:{exchange}:{symbol}")
        for symbol in symbols
    }
    dataset.members = {
        sid: [
            {
                "effective_from": days[0],
                "effective_to": None,
                "board": f"{exchange}_MAIN",
                "exchange": exchange,
            }
        ]
        for sid in dataset.ids
    }
    dataset.listing_dates = dict.fromkeys(dataset.ids, days[0])
    dataset.curves = {sid: ((days[0], days[-1], ((days[0], Decimal(1)),)),) for sid in dataset.ids}
    dataset.suspension_open_states = {}
    dataset.features = {}
    dataset.actions = {}
    dataset.resolver = TradingRuleResolver(historical_cn_a_rules())
    return dataset


@pytest.mark.parametrize(
    "exchange,start,end,recorded,expected",
    (
        ("SSE", "2010-12-30", None, "1", (True, True, True, True, True, True)),
        ("SSE", "2011-01-05", "2011-01-07", "1", (False, True, True, True, False, False)),
        ("SSE", "2011-01-05", "2011-01-05", "1", (False, True, False, False, False, False)),
        ("SSE", "2011-01-05", "2011-01-07", "0", (False, False, True, True, False, False)),
        (
            "SZSE",
            "2011/01/05 09:30",
            "2011/01/07 09:30",
            "0",
            (False, True, True, False, False, False),
        ),
        (
            "SZSE",
            "2011/01/05 13:00",
            "2011/01/07 13:00",
            "1",
            (False, False, True, True, False, False),
        ),
        (
            "SZSE",
            "2011/01/05 即时",
            "2011-01-07",
            "0",
            (False, True, True, False, False, False),
        ),
        (
            "SZSE",
            "2011/01/05 09:30",
            "2011-01-07",
            None,
            (False, True, True, True, False, False),
        ),
        ("SZSE", "2010/12/30 09:30", None, None, (True, True, True, True, True, True)),
        ("SZSE", "2011/01/12 09:30", None, None, (False, False, False, False, False, False)),
    ),
)
def test_full_dataset_suspension_intervals_reach_status_and_execution(
    tmp_path, exchange, start, end, recorded, expected
):
    dataset = _cache_fixture(tmp_path, "", exchange)
    sid, other = tuple(dataset.ids)
    fields = (
        "security_id",
        "exchange",
        "suspended_at",
        "resumed_or_ended_at",
        "execution_open_blocked",
    )
    source = dict(zip(fields, (sid, exchange, start, end, recorded), strict=True))
    writer = StreamingPartition(tmp_path / "suspension-events.parquet", fields, ("security_id",))
    writer.write([source])
    writer.close("suspension-events.parquet")
    dataset.suspension_open_states = dataset._suspension_open_states(dataset.calendar_text[-1])
    sessions = tuple(dataset.sessions())
    assert sessions == tuple(dataset.sessions())
    for session, blocked in zip(sessions, expected, strict=True):
        statuses = {str(item.status.security_id): item.status for item in session.statuses}
        assert statuses[sid].is_suspended is blocked
        assert statuses[sid].is_tradeable is not blocked
        assert not statuses[other].is_suspended
        rules = {str(item.security_id): item for item in session.trading_rules}
        if blocked:
            assert not rules[sid].executable
            bar = next(item for item in session.bars if str(item.security_id) == sid)
            order = Order(
                strategy_id="isolated-suspension-fixture",
                symbol=f"{sid.rsplit(':', 1)[1]}.{exchange}",
                side=OrderSide.BUY,
                order_type=OrderType.LIMIT,
                quantity=Decimal(100),
                price=Decimal(10),
                intended_execution_session=session.trading_date,
                created_at=datetime(2011, 1, 3, 7, tzinfo=UTC),
            )
            assert rejection_reason(order, bar, statuses[sid], rules[sid], Decimal(0)) is not None
    observations = tuple(dataset.sessions(execution=False))
    assert [item.statuses for item in observations] == [item.statuses for item in sessions]


def test_suspension_unknown_overlap_order_and_future_boundaries(tmp_path):
    dataset = _cache_fixture(tmp_path, "")
    sid = next(iter(dataset.ids))
    fields = (
        "security_id",
        "exchange",
        "suspended_at",
        "resumed_or_ended_at",
        "execution_open_blocked",
    )
    rows = [
        dict(zip(fields, values, strict=True))
        for values in (
            (sid, "SSE", "2011-01-04", "2011-01-07", "1"),
            (sid, "SSE", "2011-01-06", "2011-01-06", "0"),
            (sid, "SSE", "2011-01-12", None, "1"),
        )
    ]
    original = None
    for ordered in (rows, list(reversed(rows))):
        # Deliberately unordered disposable input; the publisher correctly rejects it.
        pq.write_table(pa.Table.from_pylist(ordered), tmp_path / "suspension-events.parquet")
        states = dataset._suspension_open_states(dataset.calendar_text[-1])
        assert states == {
            (sid, "2011-01-04"): True,
            (sid, "2011-01-05"): True,
            (sid, "2011-01-06"): True,
            (sid, "2011-01-07"): None,
        }
        dataset.suspension_open_states = states
        sessions = tuple(dataset.sessions())
        assert original is None or sessions == original
        original = sessions
        unknown = sessions[3].statuses[0].status
        assert unknown.is_suspended and not unknown.is_tradeable
        assert unknown.source_version.endswith(":UNCERTAIN_OPEN")
        assert not sessions[4].statuses[0].status.is_suspended
        # Capping the loaded period inside an ongoing interval must not lose its start.
        assert dataset._suspension_open_states("2011-01-05") == {
            (sid, "2011-01-04"): True,
            (sid, "2011-01-05"): True,
        }


@pytest.mark.parametrize(
    "start,end",
    [(None, None), ("invalid", None), ("2011-02-30", None), ("2011-01-07", "2011-01-04")],
)
def test_suspension_invalid_boundaries_fail_closed_in_both_callers(tmp_path, start, end):
    from app.application.experiments.data import ExperimentInputError
    from app.application.markets import _suspension_evidence

    dataset = _cache_fixture(tmp_path, "")
    fields = (
        "security_id",
        "exchange",
        "suspended_at",
        "resumed_or_ended_at",
        "execution_open_blocked",
    )
    row = dict(zip(fields, (next(iter(dataset.ids)), "SSE", start, end, "1"), strict=True))
    writer = StreamingPartition(tmp_path / "suspension-events.parquet", fields, ("security_id",))
    writer.write([row])
    writer.close("suspension-events.parquet")
    with pytest.raises(ValueError):
        dataset._suspension_open_states(dataset.calendar_text[-1])
    with pytest.raises(ExperimentInputError, match="DATASET_INTEGRITY_FAILED"):
        _suspension_evidence(row, "2011-01-04")


def _reference_fixture(
    tmp_path: Path,
    *,
    boundary: str | None = None,
    cash_per_share: str = "5",
    previous_close: str = "10",
    reference_close: str = "5",
) -> FullDataset:
    dataset = _cache_fixture(tmp_path, "600001")
    days = ("2011-01-31", "2011-02-01", "2011-02-02")
    original = pq.read_table(tmp_path / dataset.paths[0]).to_pylist()[:2]
    for month in ("2011-01", "2011-02"):
        rows = []
        for day in days:
            if not day.startswith(month):
                continue
            for template in original:
                # No observation for the affected security on the intervening event day.
                if day == days[1] and template["symbol"] == "600000":
                    continue
                affected = day == days[-1] and template["symbol"] == "600000"
                price = (
                    str(Decimal(reference_close) + Decimal("0.1")) if affected else previous_close
                )
                rows.append(
                    {
                        **template,
                        "trading_date": day,
                        "raw_open": price,
                        "raw_close": price,
                        "raw_high": str(Decimal(price) + Decimal("0.1")),
                        "raw_low": str(Decimal(price) - Decimal("0.1")),
                        "pre_close": reference_close if affected else previous_close,
                    }
                )
        writer = StreamingPartition(
            tmp_path / f"{month}.parquet", RAW_FIELDS, ("trading_date", "security_id")
        )
        writer.write(rows)
        writer.close(f"{month}.parquet")
    dataset.paths = ("2011-02.parquet", "2011-01.parquet")
    dataset.calendar_text = days
    dataset.calendar_days = tuple(date.fromisoformat(day) for day in days)
    dataset.calendar_index = {day: index for index, day in enumerate(days)}
    dataset.curves = {sid: ((days[0], days[-1], ((days[0], Decimal(1)),)),) for sid in dataset.ids}
    if boundary:
        action = CorporateAction(
            security_id=dataset.ids["CN-A:SSE:600000"],
            action_type="CASH_DIVIDEND",
            ex_date=date.fromisoformat(boundary),
            cash_per_share=Decimal(cash_per_share),
            source_provider="isolated-fixture",
            source_version="1",
            source_record_hash="a" * 64,
            completeness="COMPLETE",
        )
        dataset.actions = {boundary: {"CORPORATE_ACTION": [action]}}
    return dataset


@pytest.mark.parametrize("boundary", [None, "2011-02-03"])
def test_reference_marker_crosses_months_without_future_event_or_replay_leak(tmp_path, boundary):
    dataset = _reference_fixture(tmp_path, boundary=boundary)
    first = tuple(dataset.sessions())
    repeated = tuple(dataset.sessions())
    assert first == repeated
    sid = dataset.ids["CN-A:SSE:600000"]
    assert [s.unexplained_reference_adjustment_ids for s in first] == [(), (), (sid,)]
    assert all(
        not s.unexplained_reference_adjustment_ids for s in dataset.sessions(execution=False)
    )


@pytest.mark.parametrize("boundary", ["2011-02-01", "2011-02-02"])
def test_only_observed_intervening_accepted_boundary_accounts_for_reference_change(
    tmp_path, boundary
):
    dataset = _reference_fixture(tmp_path, boundary=boundary)
    assert all(not s.unexplained_reference_adjustment_ids for s in dataset.sessions())


@pytest.mark.parametrize("boundary", ["2011-02-01", "2011-02-02"])
def test_cash_event_cannot_hide_an_unexplained_reference_component(tmp_path, boundary):
    dataset = _reference_fixture(tmp_path, boundary=boundary, cash_per_share="0.1")
    sid = dataset.ids["CN-A:SSE:600000"]
    assert [s.unexplained_reference_adjustment_ids for s in dataset.sessions()] == [(), (), (sid,)]


def test_cash_reference_explanation_uses_rule_tick_and_isolated_decimal_context(tmp_path):
    # 10 - 4.995 rounds to 5.01, not the observed official reference 5.00.
    dataset = _reference_fixture(tmp_path, boundary="2011-02-02", cash_per_share="4.995")
    sid = dataset.ids["CN-A:SSE:600000"]
    expected = [(), (), (sid,)]
    assert [s.unexplained_reference_adjustment_ids for s in dataset.sessions()] == expected
    with localcontext() as context:
        context.prec = 3
        assert [s.unexplained_reference_adjustment_ids for s in dataset.sessions()] == expected
    # A sub-tick accepted cash component may explain the rounded official reference.
    dataset.actions["2011-02-02"]["CORPORATE_ACTION"][0] = dataset.actions["2011-02-02"][
        "CORPORATE_ACTION"
    ][0].model_copy(update={"cash_per_share": Decimal("4.996")})
    assert all(not s.unexplained_reference_adjustment_ids for s in dataset.sessions())


def test_cash_bonus_reference_is_tick_exact_and_independent_of_context():
    for precision in (3, 50):
        with localcontext() as context:
            context.prec = precision
            context.rounding = ROUND_DOWN
            for previous, cash, ratio, expected in (
                ("43.45", "0", "1", "21.73"),
                ("58.16", "0.45", "1", "28.86"),
                ("10", "0.1", "1", "4.95"),
            ):
                assert cash_bonus_reference_price(
                    Decimal(previous),
                    cash_per_old_share=Decimal(cash),
                    aggregate_share_ratio=Decimal(ratio),
                    minimum_tick=Decimal("0.01"),
                ) == Decimal(expected)
            # Quantize to an actual tick multiple, not merely its exponent.
            assert cash_bonus_reference_price(
                Decimal("10.125"),
                cash_per_old_share=Decimal(0),
                aggregate_share_ratio=Decimal(0),
                minimum_tick=Decimal("0.05"),
            ) == Decimal("10.15")
    for values in (
        ("NaN", "0", "0", "0.01"),
        ("10", "Infinity", "0", "0.01"),
        ("10", "0", "NaN", "0.01"),
        ("10", "0", "0", "Infinity"),
        ("0", "0", "0", "0.01"),
        ("-1", "0", "0", "0.01"),
        ("10", "-0.1", "0", "0.01"),
        ("10", "0", "-1", "0.01"),
        ("10", "0", "0", "0"),
        ("10", "0", "0", "-0.01"),
        ("10", "10", "0", "0.01"),
        ("0.001", "0", "0", "0.01"),
    ):
        previous, cash, ratio, tick = map(Decimal, values)
        with pytest.raises(ValueError, match="INVALID_CASH_BONUS_REFERENCE_INPUT"):
            cash_bonus_reference_price(
                previous, cash_per_old_share=cash, aggregate_share_ratio=ratio, minimum_tick=tick
            )


@pytest.mark.parametrize(
    "previous,cash,ratio,reference,explained",
    (
        ("43.45", "0", "1", "21.73", True),
        ("58.16", "0.45", "1", "28.86", True),
        ("58.20", "0.45", "1", "28.86", False),  # Prior pre_close is not actual close.
        ("58.16", "0", "1", "28.86", False),
        ("58.16", "0.405", "1", "28.86", False),  # Tax-net cannot replace gross cash.
        ("58.16", "0.45", "0.9", "28.86", False),
    ),
)
def test_ordinary_mixed_reference_requires_both_exact_legs(
    tmp_path, previous, cash, ratio, reference, explained
):
    dataset = _reference_fixture(
        tmp_path,
        boundary="2011-02-01",
        cash_per_share=cash,
        previous_close=previous,
        reference_close=reference,
    )
    cash_action = dataset.actions["2011-02-01"]["CORPORATE_ACTION"][0]
    bonus = cash_action.model_copy(
        update={
            "action_type": type(cash_action.action_type).BONUS_SHARE,
            "cash_per_share": Decimal(0),
            "share_ratio": Decimal(ratio),
        }
    )
    dataset.actions["2011-02-01"]["CORPORATE_ACTION"].append(bonus)
    sid = cash_action.security_id
    expected = [(), (), () if explained else (sid,)]
    assert [s.unexplained_reference_adjustment_ids for s in dataset.sessions()] == expected
    dataset.actions["2011-02-01"]["CORPORATE_ACTION"].reverse()
    with localcontext() as context:
        context.prec = 3
        context.rounding = ROUND_DOWN
        assert [s.unexplained_reference_adjustment_ids for s in dataset.sessions()] == expected
    assert all(
        not s.unexplained_reference_adjustment_ids for s in dataset.sessions(execution=False)
    )


@pytest.mark.parametrize("with_rights", (False, True))
@pytest.mark.parametrize(
    "variant",
    (
        "duplicate_cash",
        "metadata_duplicate_cash",
        "duplicate_share",
        "two_share_kinds",
        "multiple_ex",
        "embedded_cash",
        "embedded_ratio",
    ),
)
def test_ambiguous_or_combined_distribution_does_not_get_structural_exemption(
    tmp_path, variant, with_rights
):
    dataset = _reference_fixture(
        tmp_path, boundary="2011-02-01", cash_per_share="0.1", reference_close="4.95"
    )
    cash = dataset.actions["2011-02-01"]["CORPORATE_ACTION"][0]
    bonus = cash.model_copy(
        update={
            "action_type": type(cash.action_type).BONUS_SHARE,
            "cash_per_share": Decimal(0),
            "share_ratio": Decimal(1),
        }
    )
    events = [cash, bonus]
    if variant == "duplicate_cash":
        events.append(cash)
    elif variant == "metadata_duplicate_cash":
        events.append(cash.model_copy(update={"source_version": "alternate-receipt"}))
        assert events[-1].event_checksum != cash.event_checksum
    elif variant == "duplicate_share":
        events.append(bonus)
    elif variant == "two_share_kinds":
        events.append(
            bonus.model_copy(
                update={
                    "action_type": type(bonus.action_type).STOCK_DIVIDEND,
                }
            )
        )
    elif variant == "multiple_ex":
        events.remove(bonus)
        dataset.actions["2011-02-02"] = {
            "CORPORATE_ACTION": [bonus.model_copy(update={"ex_date": date(2011, 2, 2)})]
        }
    elif variant == "embedded_cash":
        events = [bonus.model_copy(update={"cash_per_share": Decimal("0.1")})]
    elif variant == "embedded_ratio":
        events = [cash.model_copy(update={"share_ratio": Decimal(1)})]
    if with_rights:
        from app.domain.markets.corporate_actions import require_supported_corporate_action
        from tests.test_rights_issue_policy import rights

        right = rights(
            security_id=str(cash.security_id), ex_date="2011-02-01", effective_date="2011-02-01"
        )
        require_supported_corporate_action(right)
        events.append(right)
    dataset.actions["2011-02-01"]["CORPORATE_ACTION"] = events
    sid = cash.security_id
    assert [s.unexplained_reference_adjustment_ids for s in dataset.sessions()] == [(), (), (sid,)]


def test_cash_only_boundaries_keep_existing_multi_ex_sum(tmp_path):
    dataset = _reference_fixture(tmp_path, boundary="2011-02-01", cash_per_share="2.5")
    cash = dataset.actions["2011-02-01"]["CORPORATE_ACTION"][0]
    dataset.actions["2011-02-02"] = {
        "CORPORATE_ACTION": [cash.model_copy(update={"ex_date": date(2011, 2, 2)})]
    }
    assert all(not s.unexplained_reference_adjustment_ids for s in dataset.sessions())


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
