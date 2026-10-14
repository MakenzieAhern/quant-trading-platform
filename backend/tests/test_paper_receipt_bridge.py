"""Synthetic-only production factory -> cache/reader -> manager -> journal proofs.

No provider, source authority approval, real account or frozen archive.
No application database; dedicated disposable quant_test case below.
"""

import asyncio
import json
from contextlib import asynccontextmanager, suppress
from copy import deepcopy
from dataclasses import replace
from datetime import UTC, datetime, time, timedelta
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock
from uuid import NAMESPACE_URL, UUID, uuid5

import pytest
from pydantic import TypeAdapter

from app.application.market_updates.contracts import (
    AUTHORITY,
    FIELDS,
    PARSER_VERSION,
    PROVIDER,
    SDK_VERSION,
    SDK_WHEEL_SHA256,
    TERMS,
    parse_response,
    request_parameters,
)
from app.application.market_updates.service import MarketUpdateManager
from app.application.paper_trading import service
from app.application.paper_trading.receipt_source import (
    CanonicalReceiptReader,
    ReceiptSessionFactory,
    validate_commit_history,
)
from app.application.paper_trading.source_admission import (
    AUTHORITY_NAMES,
    AuthorityFrame,
    ForwardAdmissionRegistry,
)
from app.data.catalog.checksums import canonical_json_bytes, canonical_sha256, sha256_file
from app.db.models.market_updates import MarketObservationModel, MarketReceiptModel
from app.domain.risk import RiskConfig
from app.paper.a_share_fixture import simulated_a_share_fixture
from app.paper.models import CreatePaperSessionCommand, PaperEventRecord, PaperSessionStatus
from app.research.models import ResearchSession


def fixture(tmp_path, monkeypatch, *, fault=None, patch_repository=True):
    calendar, all_sessions, commission = simulated_a_share_fixture(session_count=255)
    warmup, forward = all_sessions[:253], all_sessions[253:255]
    days = [item.session_date for item in calendar.sessions]
    next_day = days[-1] + timedelta(days=1)
    while next_day.weekday() >= 5:
        next_day += timedelta(days=1)
    days.append(next_day)
    first, second = (item.trading_date for item in forward)
    clock = [datetime.combine(first, time(6), UTC)]
    receipts, observations, journal, batches = [], [], [], []
    current = [None]

    def write(name, value):
        path = tmp_path / name
        path.write_bytes(canonical_json_bytes(value))
        return {"path": name, "sha256": sha256_file(path)}

    evidence = write("synthetic-evidence.json", {"kind": "SYNTHETIC_TEST_ONLY_NOT_AUTHORITY"})
    authorities = {
        name: {
            "decision": "ADMITTED_FOR_PRIVATE_LOCAL_PAPER_EOD",
            "valid_from": days[0].isoformat(),
            "valid_to": days[-1].isoformat(),
            "known_at": "2029-01-01T00:00:00Z",
            "source_version": "SYNTHETIC_TEST_ONLY",
            "evidence": [evidence],
        }
        for name in sorted(AUTHORITY_NAMES)
    }
    authority_sha = canonical_sha256(authorities)
    schedule = [
        {
            "trading_date": day.isoformat(),
            "opens_at": datetime.combine(day, time(1, 30), UTC).isoformat(),
            "closes_at": datetime.combine(day, time(7), UTC).isoformat(),
        }
        for day in days
    ]

    def frame(session, warm=False):
        value = TypeAdapter(ResearchSession).dump_python(session, mode="json")
        value.pop("feature_only_observations")
        value.pop("unexplained_reference_adjustment_ids")
        bars = value.pop("bars")
        value["authorities_sha256"] = authority_sha
        value["adjustment_factors"] = {bar["security_id"]["value"]: "1" for bar in bars}
        if warm:
            for bar in bars:
                bar["adjustment_factor"] = "1"
            value["bars"] = bars
        return value

    contract = {
        "schema_version": "PAPER_FORWARD_ADMISSION_V1",
        "admission_id": "synthetic-receipt-bridge-only",
        "permission": {
            "decision": "PERMITTED",
            "permitted_scope": "PRIVATE_LOCAL_ANALYSIS_TRIAL",
            "use": "PRIVATE_LOCAL_PAPER_EOD",
            "provider": PROVIDER,
            "evidence": [evidence],
            "terms_sha256": evidence["sha256"],
        },
        "authorities": authorities,
        "first_forward_session": first.isoformat(),
        "last_forward_session": second.isoformat(),
        "schedule": write("schedule.json", schedule),
        "daily_context": write("context.json", [frame(item) for item in forward]),
        "warmup": write("warmup.json", [frame(item, True) for item in warmup]),
        "transaction_costs": [item.model_dump(mode="json") for item in commission.schedules],
    }
    write("admission.json", contract)
    registry = ForwardAdmissionRegistry(
        tmp_path / "admission.json", sha256_file(tmp_path / "admission.json")
    )

    class DB:
        async def scalars(self, statement):
            params = statement.compile().params
            if statement.column_descriptions[0]["entity"] is MarketObservationModel:
                self.day = params["trading_date_1"]
                return [item for item in observations if item.trading_date == self.day]
            return [
                item
                for item in receipts
                if item.evidence["parameters"]["start_date"]
                <= self.day.isoformat()
                <= item.evidence["parameters"]["end_date"]
            ]

    @asynccontextmanager
    async def database():
        yield DB()

    updates = MarketUpdateManager(
        database,
        None,
        SimpleNamespace(registry=SimpleNamespace(root=tmp_path / "archive")),
        tmp_path / "cache",
    )
    for item in forward:
        received = datetime.combine(item.trading_date, time(10), UTC)
        for bar in item.bars:
            sid = str(bar.security_id)
            raw = {
                "fields": FIELDS.split(","),
                "rows": [
                    [
                        item.trading_date.isoformat(),
                        "sh." + sid[-6:],
                        *[
                            str(value)
                            for value in (
                                bar.raw_open,
                                bar.raw_high,
                                bar.raw_low,
                                bar.raw_close,
                                bar.pre_close,
                                bar.volume,
                                bar.amount,
                            )
                        ],
                        "3",
                        "1",
                        "0",
                    ]
                ],
            }
            rows = parse_response(raw, sid, item.trading_date, item.trading_date)
            rid = uuid5(NAMESPACE_URL, sid + str(item.trading_date))
            ev = {
                "job_id": str(uuid5(NAMESPACE_URL, "synthetic-job")),
                "receipt_id": str(rid),
                "provider": PROVIDER,
                "sdk_version": SDK_VERSION,
                "parser_version": PARSER_VERSION,
                "sdk_release_wheel_sha256": SDK_WHEEL_SHA256,
                "source_endpoint": "public-api.baostock.com:10030",
                "security_id": sid,
                "parameters": request_parameters(sid, item.trading_date, item.trading_date),
                "requested_at_utc": (received - timedelta(seconds=2)).isoformat(),
                "response_completed_at_utc": (received - timedelta(seconds=1)).isoformat(),
                "received_at_utc": received.isoformat(),
                "first_received_at_utc": received.isoformat(),
                "attempt": 1,
                "raw_response_representation": "SDK_DECODED_FIELDS_AND_ROWS_NOT_WIRE_BYTES",
                "raw_response_sha256": canonical_sha256(raw),
                "logical_rows_sha256": canonical_sha256({"rows": rows}),
                "row_count": 1,
                "terms": {**TERMS, "terms_snapshot_sha256": evidence["sha256"]},
                "authority": deepcopy(AUTHORITY),
            }
            digest = updates.cache.publish(raw, rows, ev)
            receipts.append(
                MarketReceiptModel(
                    id=rid,
                    job_id=UUID(ev["job_id"]),
                    security_id=sid,
                    received_at=received,
                    manifest_sha256=digest,
                    evidence=ev,
                )
            )
            observations.append(
                MarketObservationModel(
                    provider=PROVIDER,
                    security_id=sid,
                    trading_date=item.trading_date,
                    receipt_id=rid,
                    payload=rows[0],
                )
            )

    class Repository:
        async def create(self, account):
            current[0] = account
            return account

        async def get(self, _):
            return current[0]

        async def get_by_client_request_id(self, _):
            return current[0]

        async def list_events(self, _, **kwargs):
            return tuple(journal)

        async def append_events(self, sid, events):
            if fault == "marker_failure" and events[0][0] == "input.committed":
                raise RuntimeError("synthetic marker commit failure")
            saved = tuple(
                PaperEventRecord(sid, len(journal) + index + 1, kind, ts, payload)
                for index, (kind, ts, payload) in enumerate(events)
            )
            journal.extend(saved)
            batches.append(saved)
            if events[0][0] == "market.session" and fault == "cross_open":
                clock[0] = datetime.combine(second, time(1, 30), UTC)
            if events[0][0] == "input.committed":
                clock[0] = datetime.combine(second, time(10), UTC)
            return saved

        async def transition_with_event(self, sid, expected, target, now, event_type, error):
            account = current[0]
            current[0] = replace(
                account,
                status=target,
                started_at=(account.started_at or now)
                if target is PaperSessionStatus.RUNNING
                else account.started_at,
                error_message=error,
            )
            events = await self.append_events(sid, ((event_type, now, {"status": target.value}),))
            if target is PaperSessionStatus.RUNNING:
                clock[0] = datetime.combine(
                    first if account.started_at is None else second, time(10), UTC
                )
            return current[0], events

    if patch_repository:
        monkeypatch.setattr(service, "SQLAlchemyPaperRepository", lambda _: Repository())
    manager = service.PaperTradingManager(
        database,
        MagicMock(),
        MagicMock(),
        forward_sources=ReceiptSessionFactory(registry, CanonicalReceiptReader(database, updates)),
        replay_interval_seconds=0,
        clock=lambda: clock[0],
    )
    command = CreatePaperSessionCommand(
        provider_type="forward_a_share",
        dataset_id=contract["admission_id"],
        symbol="CN-A",
        strategy_type="cn_a_cross_sectional_momentum_low_vol_v1",
        strategy_parameters={
            "start_date": first,
            "end_date": second,
            "rebalance_sessions": 1,
            "maximum_holdings": 20,
            "max_position_weight": Decimal("0.1"),
            "universe": "ALL",
            "commission_rate": Decimal(0),
            "minimum_commission": Decimal(0),
        },
        initial_cash=Decimal("1000000"),
        default_order_quantity=Decimal(1),
        risk=RiskConfig(
            enforce_buying_power=True, max_leverage=Decimal(1), max_drawdown=Decimal("-0.2")
        ),
    )
    return SimpleNamespace(
        manager=manager,
        command=command,
        journal=journal,
        batches=batches,
        registry=registry,
        current=current,
        clock=clock,
        receipts=receipts,
        observations=observations,
        updates=updates,
        first=first,
        second=second,
        contract=contract,
        write=write,
    )


async def run(case):
    account = await case.manager.create(case.command)
    await case.manager.start(account.id)
    await asyncio.wait_for(case.manager._tasks[account.id], timeout=20)
    return await case.manager.get(account.id)


async def test_real_factory_receipts_warmup_plan_risk_oms_next_session_fill(tmp_path, monkeypatch):
    case = fixture(tmp_path, monkeypatch)
    account = await run(case)
    assert account.status is PaperSessionStatus.STOPPED, account.error_message
    markets = [item for item in case.journal if item.event_type == "market.session"]
    assert [item.payload["trading_date"] for item in markets] == [
        case.first.isoformat(),
        case.second.isoformat(),
    ]
    financial_batches = [batch for batch in case.batches if batch[0].event_type == "market.session"]
    assert len(financial_batches) == 2
    plan = financial_batches[0][-1].payload["plan"]
    assert plan["status"] == "SIMULATION_PREVIEW" and plan["submitted_to_account"]
    assert plan["mode"] == "forward_paper" and plan["account_mode"] == "FORWARD_PAPER"
    assert any(
        item.event_type == "risk.decision" and item.payload["approved"]
        for item in financial_batches[0]
    )
    assert any(item.event_type == "order.updated" for item in financial_batches[0])
    assert not any(item.event_type == "fill.created" for item in financial_batches[0])
    assert any(item.event_type == "fill.created" for item in financial_batches[1])
    for batch in financial_batches:
        lineage = batch[0].payload["input_provenance"]
        assert batch[-1].payload["input_provenance"] == lineage
        assert batch[-1].payload["plan"]["input_provenance"] == lineage
        assert lineage["admission_sha256"] == case.registry.expected_sha256
        assert len(lineage["receipts"]) == 10
    assert validate_commit_history(tuple(case.journal), account) == {case.first, case.second}


@pytest.mark.parametrize("fault", ["cross_open", "marker_failure"])
async def test_commit_causal_failure_keeps_batch_and_never_consumes_next_day(
    tmp_path, monkeypatch, fault
):
    case = fixture(tmp_path, monkeypatch, fault=fault)
    account = await run(case)
    assert account.status is PaperSessionStatus.FAILED
    assert sum(item.event_type == "market.session" for item in case.journal) == 1
    assert not any(item.event_type in {"fill.created", "input.committed"} for item in case.journal)
    with pytest.raises(ValueError, match="ACKNOWLEDGEMENT_MISSING"):
        validate_commit_history(tuple(case.journal), account)


def test_missing_config_and_http_approval_do_not_register_source():
    with pytest.raises(ValueError, match="FORWARD_SOURCE_NOT_REGISTERED"):
        ForwardAdmissionRegistry(None, None).load("any-forward-source")


@pytest.mark.parametrize(
    "damage", ["authority", "calendar", "warmup", "path", "unknown_permission"]
)
def test_source_binding_and_coverage_fail_closed(tmp_path, monkeypatch, damage):
    case = fixture(tmp_path, monkeypatch)
    if damage == "authority":
        (tmp_path / "synthetic-evidence.json").write_bytes(b"changed")
    elif damage in {"calendar", "warmup"}:
        (tmp_path / ("schedule.json" if damage == "calendar" else "warmup.json")).write_bytes(b"[]")
    else:
        contract = deepcopy(case.contract)
        if damage == "path":
            contract["warmup"]["path"] = "../outside.json"
        else:
            contract["permission"]["decision"] = "UNKNOWN"
        case.write("admission.json", contract)
        case.registry.expected_sha256 = sha256_file(tmp_path / "admission.json")
    with pytest.raises(ValueError):
        case.registry.load(case.command.dataset_id)


def republish(case, original, *, hour=11, conflict=False, same_id=False):
    manifest, _ = case.updates.cache.read(original.manifest_sha256)
    raw = json.loads((case.updates.cache.root / manifest["raw"]["path"]).read_bytes())
    ev = deepcopy(original.evidence)
    if conflict:
        raw["rows"][0][7] = str(Decimal(raw["rows"][0][7]) + 1)
    day = datetime.fromisoformat(ev["received_at_utc"]).date()
    when = datetime.combine(day, time(hour), UTC)
    rid = original.id if same_id else uuid5(NAMESPACE_URL, str(original.id) + str(hour))
    ev.update(
        receipt_id=str(rid),
        requested_at_utc=(when - timedelta(seconds=2)).isoformat(),
        response_completed_at_utc=(when - timedelta(seconds=1)).isoformat(),
        received_at_utc=when.isoformat(),
        first_received_at_utc=when.isoformat(),
    )
    rows = parse_response(raw, original.security_id, day, day)
    ev.update(
        raw_response_sha256=canonical_sha256(raw),
        logical_rows_sha256=canonical_sha256({"rows": rows}),
    )
    digest = case.updates.cache.publish(raw, rows, ev)
    return MarketReceiptModel(
        id=rid,
        job_id=original.job_id,
        security_id=original.security_id,
        received_at=when,
        manifest_sha256=digest,
        evidence=ev,
    )


@pytest.mark.parametrize("conflict", [False, True])
async def test_additional_receipt_cannot_replace_original_or_hide_conflict(
    tmp_path, monkeypatch, conflict
):
    case = fixture(tmp_path, monkeypatch)
    original = case.receipts[0]
    case.receipts.append(republish(case, original, conflict=conflict))
    reader = case.manager._forward_factory.reader
    frame = case.registry.load(case.command.dataset_id).frames[0]
    if conflict:
        with pytest.raises(ValueError, match="FORWARD_CONFLICTING_RECEIPT"):
            await reader.read(frame)
    else:
        rows = await reader.read(frame)
        assert rows[0][1].id == original.id
        assert rows[0][1].received_at.hour == 10


async def test_canonical_observation_repointed_to_later_identical_receipt_is_rejected(
    tmp_path, monkeypatch
):
    case = fixture(tmp_path, monkeypatch)
    later = republish(case, case.receipts[0])
    case.receipts.append(later)
    case.observations[0].receipt_id = later.id
    with pytest.raises(ValueError, match="FORWARD_CANONICAL_FIRST_RECEIPT_CHANGED"):
        await case.manager._forward_factory.reader.read(
            case.registry.load(case.command.dataset_id).frames[0]
        )


@pytest.mark.parametrize("overflow", [False, True])
async def test_receipt_budget_scales_with_complete_universe_without_truncation(
    tmp_path, monkeypatch, overflow
):
    """Query-budget proof only; raw reparse is covered by the full factory fixture."""
    case = fixture(tmp_path, monkeypatch)
    data = case.registry.load(case.command.dataset_id).frames[0].model_dump(mode="json")
    count = 1001
    ids = [f"CN-A:SSE:{600000 + index:06d}" for index in range(count)]
    status, rule, lot = data["statuses"][0], data["trading_rules"][0], data["buy_lot_sizes"][0]
    data["statuses"], data["trading_rules"], data["buy_lot_sizes"] = [], [], []
    data["adjustment_factors"] = dict.fromkeys(ids, "1")
    receipts, observations, rows = [], [], {}
    for sid in ids:
        next_status, next_rule, next_lot = deepcopy(status), deepcopy(rule), deepcopy(lot)
        next_status["status"]["security_id"] = {"value": sid}
        next_rule["security_id"] = {"value": sid}
        next_lot[0] = {"value": sid}
        data["statuses"].append(next_status)
        data["trading_rules"].append(next_rule)
        data["buy_lot_sizes"].append(next_lot)
        rid = uuid5(NAMESPACE_URL, "budget-test:" + sid)
        row = {**case.observations[0].payload, "security_id": sid}
        rows[rid] = [row]
        receipts.append(
            MarketReceiptModel(id=rid, security_id=sid, received_at=case.receipts[0].received_at)
        )
        observations.append(
            MarketObservationModel(
                provider=PROVIDER,
                security_id=sid,
                trading_date=case.first,
                receipt_id=rid,
                payload=row,
            )
        )
    budget = count * 4  # Resource budget, not an admission/performance threshold.
    if overflow:
        receipts.extend(
            MarketReceiptModel(id=uuid5(NAMESPACE_URL, f"budget-extra:{index}"))
            for index in range(budget + 1 - count)
        )
    query_limits = []

    class DB:
        async def scalars(self, statement):
            if statement.column_descriptions[0]["entity"] is MarketObservationModel:
                return observations
            limit = statement._limit_clause.value
            query_limits.append(limit)
            return receipts[:limit]

    @asynccontextmanager
    async def database():
        yield DB()

    updates = SimpleNamespace(verify_receipt=AsyncMock(side_effect=lambda item: rows[item.id]))
    reader = CanonicalReceiptReader(database, updates)
    frame = AuthorityFrame.model_validate(data)
    if overflow:
        with pytest.raises(ValueError, match="FORWARD_RECEIPT_RECONCILIATION_LIMIT_EXCEEDED"):
            await reader.read(frame)
        updates.verify_receipt.assert_not_awaited()
    else:
        result = await reader.read(frame)
        assert len(result) == count
        assert [row["security_id"] for row, _ in result] == ids
        assert [receipt.id for _, receipt in result] == [receipt.id for receipt in receipts]
        assert updates.verify_receipt.await_count == count
    assert query_limits == [budget + 1]


@pytest.mark.parametrize(
    "damage", ["rate", "version", "frame_rate", "missing_forward", "missing_warmup", "overlap"]
)
def test_repinned_cost_declarations_must_match_execution_source_for_every_day(
    tmp_path, monkeypatch, damage
):
    case = fixture(tmp_path, monkeypatch)
    contract = deepcopy(case.contract)
    cost = contract["transaction_costs"][0]
    if damage == "rate":
        cost["transfer_fee_rate"] = "0.01"
    elif damage == "version":
        cost["source_version"] = "DIFFERENT_SOURCE_NOT_SILENTLY_EQUIVALENT"
    elif damage == "frame_rate":
        data = json.loads((tmp_path / "context.json").read_bytes())
        data[0]["trading_rules"][0]["cost_schedule"]["commission_rate"] = "0.001"
        contract["daily_context"] = case.write("context.json", data)
    elif damage == "missing_forward":
        cost["valid_to"] = (case.first - timedelta(days=1)).isoformat()
    elif damage == "missing_warmup":
        cost["valid_from"] = case.first.isoformat()
    else:
        contract["transaction_costs"].append(deepcopy(cost))
    if damage in {"missing_forward", "missing_warmup"}:
        # Other covered days agree exactly, so the missing day itself must fail.
        key, filename = (
            ("warmup", "warmup.json")
            if damage == "missing_forward"
            else ("daily_context", "context.json")
        )
        data = json.loads((tmp_path / filename).read_bytes())
        for frame in data:
            for rule in frame["trading_rules"]:
                rule["cost_schedule"] = cost
        contract[key] = case.write(filename, data)
    case.write("admission.json", contract)
    case.registry.expected_sha256 = sha256_file(tmp_path / "admission.json")
    with pytest.raises(
        ValueError,
        match=(
            "FORWARD_SOURCE_CONTRACT_INVALID"
            if damage == "overlap"
            else "FORWARD_TRANSACTION_COST_SOURCE_MISMATCH"
        ),
    ):
        case.registry.load(case.command.dataset_id)


async def test_effective_cost_transition_keeps_existing_user_commission_overrides(
    tmp_path, monkeypatch
):
    case = fixture(tmp_path, monkeypatch)
    contract = deepcopy(case.contract)
    before = {
        **contract["transaction_costs"][0],
        "valid_to": (case.first - timedelta(days=1)).isoformat(),
    }
    after = {
        **contract["transaction_costs"][0],
        "valid_from": case.first.isoformat(),
        "commission_rate": "0.001",
        "minimum_commission": "5",
        "source_version": "SYNTHETIC_TEST_SECOND_COST_VERSION",
    }
    contract["transaction_costs"] = [after, before]  # Input order is immaterial.
    for key, filename, cost in (
        ("warmup", "warmup.json", before),
        ("daily_context", "context.json", after),
    ):
        data = json.loads((tmp_path / filename).read_bytes())
        for frame in data:
            for rule in frame["trading_rules"]:
                rule["cost_schedule"] = cost
        contract[key] = case.write(filename, data)
    case.write("admission.json", contract)
    case.registry.expected_sha256 = sha256_file(tmp_path / "admission.json")
    admitted = case.registry.load(case.command.dataset_id)
    assert admitted.frames[0].trading_rules[0].cost_schedule.commission_rate == Decimal("0.001")
    account = await run(case)
    assert account.status is PaperSessionStatus.STOPPED, account.error_message
    fills = [event for event in case.journal if event.event_type == "fill.created"]
    assert fills
    assert all(Decimal(event.payload["commission"]) == 0 for event in fills)


async def test_after_start_redownload_cannot_wash_original_preclose_receipt(tmp_path, monkeypatch):
    case = fixture(tmp_path, monkeypatch)
    original = case.receipts[0]
    case.receipts.append(republish(case, original))
    case.receipts[0] = republish(case, original, hour=6, same_id=True)
    account = await run(case)
    assert account.status is PaperSessionStatus.FAILED
    assert not any(item.event_type == "market.session" for item in case.journal)


async def test_late_start_cannot_turn_downloaded_history_into_forward(tmp_path, monkeypatch):
    case = fixture(tmp_path, monkeypatch)
    case.clock[0] = datetime.combine(case.first, time(11), UTC)
    account = await run(case)
    assert account.status is PaperSessionStatus.FAILED
    assert not any(item.event_type == "market.session" for item in case.journal)


@pytest.mark.parametrize(
    "damage",
    [
        "unknown_status",
        "nontradeable_executable",
        "warmup_factor",
        "warmup_future",
        "calendar_next",
        "authority_future",
        "missing_authority",
    ],
)
def test_even_repinned_contract_rejects_structural_lookahead_and_unknowns(
    tmp_path, monkeypatch, damage
):
    case = fixture(tmp_path, monkeypatch)
    contract = deepcopy(case.contract)
    if damage in {"unknown_status", "nontradeable_executable"}:
        data = json.loads((tmp_path / "context.json").read_bytes())
        data[0]["statuses"][0]["status"]["is_tradeable"] = (
            None if damage == "unknown_status" else False
        )
        contract["daily_context"] = case.write("context.json", data)
    elif damage.startswith("warmup"):
        data = json.loads((tmp_path / "warmup.json").read_bytes())
        if damage == "warmup_factor":
            data[0]["bars"][0]["adjusted_close"] = "1"
        else:
            data[-1]["trading_date"] = case.first.isoformat()
        contract["warmup"] = case.write("warmup.json", data)
    elif damage == "calendar_next":
        data = json.loads((tmp_path / "schedule.json").read_bytes())[:-1]
        contract["schedule"] = case.write("schedule.json", data)
    elif damage == "authority_future":
        contract["authorities"]["CALENDAR"]["known_at"] = "2099-01-01T00:00:00Z"
    else:
        del contract["authorities"]["SSE_ST"]
    case.write("admission.json", contract)
    case.registry.expected_sha256 = sha256_file(tmp_path / "admission.json")
    with pytest.raises(ValueError):
        case.registry.load(case.command.dataset_id)


async def test_pause_resume_reuses_factory_original_receipts_and_durable_commit_times(
    tmp_path, monkeypatch
):
    case = fixture(tmp_path, monkeypatch)
    tasks = []

    def publish(sid, event):
        if event["type"] == "input.committed" and not tasks:
            tasks.append(asyncio.create_task(case.manager.pause(sid)))

    case.manager.hub.publish = MagicMock(side_effect=publish)
    account = await run(case)
    assert account.status is PaperSessionStatus.PAUSED
    await asyncio.gather(*tasks)
    prefix = tuple(case.journal)
    case.manager.hub.publish = MagicMock()
    await case.manager.start(account.id)
    await asyncio.wait_for(case.manager._tasks[account.id], 20)
    after = await case.manager.get(account.id)
    assert after.status is PaperSessionStatus.STOPPED, after.error_message
    assert tuple(case.journal[: len(prefix)]) == prefix
    assert sum(item.event_type == "market.session" for item in case.journal) == 2
    assert sum(item.event_type == "input.committed" for item in case.journal) == 2
    assert any(item.event_type == "fill.created" for item in case.journal)


async def test_actual_forward_events_validate_typed_api_schema(tmp_path, monkeypatch):
    from app.api.schemas.paper import PaperEventResponse

    case = fixture(tmp_path, monkeypatch)
    await run(case)
    for item in case.journal:
        PaperEventResponse.model_validate(
            {
                "sequence": item.sequence,
                "type": item.event_type,
                "occurred_at": item.occurred_at,
                "payload": item.payload,
            }
        )


def test_contract_validation_errors_do_not_disclose_private_values(tmp_path):
    secret = "private-path-or-contract-material"
    path = tmp_path / (secret + ".json")
    path.write_text('{"unknown":"' + secret + '"}')
    with pytest.raises(ValueError) as caught:
        ForwardAdmissionRegistry(path, sha256_file(path)).load("missing-contract")
    assert str(caught.value) == "FORWARD_SOURCE_CONTRACT_INVALID"
    assert secret not in str(caught.value)


@pytest.mark.parametrize("cross_open", [False, True])
async def test_receipt_arrival_during_read_uses_fresh_clock_and_deadline(
    tmp_path, monkeypatch, cross_open
):
    case = fixture(tmp_path, monkeypatch)
    reader = case.manager._forward_factory.reader
    original = reader.read
    first_read = True

    async def read(frame):
        nonlocal first_read
        rows = await original(frame)
        if first_read:
            first_read = False
            case.clock[0] = (
                datetime.combine(case.second, time(1, 30), UTC)
                if cross_open
                else datetime.combine(case.first, time(10), UTC)
            )
        return rows

    reader.read = read

    def publish(sid, event):
        if event["type"] == "calendar.observed":
            case.clock[0] = datetime.combine(case.first, time(9, 59, 59), UTC)

    case.manager.hub.publish = MagicMock(side_effect=publish)
    account = await run(case)
    if cross_open:
        assert account.status is PaperSessionStatus.FAILED
        assert not any(event.event_type == "market.session" for event in case.journal)
    else:
        assert account.status is PaperSessionStatus.STOPPED, account.error_message
        assert any(event.event_type == "fill.created" for event in case.journal)


@pytest.mark.parametrize("dynamic", [False, True])
async def test_disposable_postgres_receipt_bridge_rest_ws_and_new_manager_resume(
    tmp_path, monkeypatch, dynamic
):
    """Real quant_test PostgreSQL/JSONB only; inputs remain explicitly synthetic."""
    from fastapi import FastAPI
    from httpx import ASGITransport, AsyncClient
    from sqlalchemy import delete, text

    from app.api.routes import paper as routes
    from app.api.schemas.paper import PaperEventResponse
    from app.core.config import get_settings
    from app.db.models.market_updates import MarketUpdateJobModel
    from app.db.models.paper import PaperTradingEventModel, PaperTradingSessionModel
    from app.db.session import SessionFactory, engine
    from tests.conftest import require_disposable_database

    settings = get_settings()
    require_disposable_database(settings.app_env, settings.database_url)
    if dynamic:
        # Context oracle/clock synthetic; receipt, account and journal rows use real quant_test.
        from tests.test_paper_daily_context import connect_contexts, dynamic_case

        case = connect_contexts(dynamic_case(tmp_path, monkeypatch, patch_repository=False))
    else:
        case = fixture(tmp_path, monkeypatch, patch_repository=False)
    job_id = case.receipts[0].job_id
    account_id = None
    managers = []
    websocket_task = None
    drain_task = None
    incoming = asyncio.Queue(maxsize=2)
    outgoing = asyncio.Queue(maxsize=4)
    frames = []
    try:
        async with SessionFactory() as db, db.begin():
            await db.execute(
                text(
                    "TRUNCATE product_market_observations, product_market_receipts, "
                    "product_market_update_jobs"
                )
            )
            db.add(
                MarketUpdateJobModel(
                    id=job_id,
                    request_key="synthetic-forward-bridge-pg",
                    configuration={},
                    configuration_sha256=canonical_sha256({}),
                    master_snapshot={},
                    status="SUCCEEDED",
                    phase="RAW_CANDIDATE",
                    created_at=case.clock[0],
                    completed_requests=20,
                    total_requests=20,
                    attempt=1,
                )
            )
            await db.flush()
            db.add_all(case.receipts)
            await db.flush()
            db.add_all(case.observations)

        updates = MarketUpdateManager(
            SessionFactory,
            engine,
            SimpleNamespace(registry=SimpleNamespace(root=tmp_path / "archive")),
            tmp_path / "cache",
        )

        def new_manager():
            factory = ReceiptSessionFactory(
                ForwardAdmissionRegistry(
                    tmp_path / "admission.json", case.registry.expected_sha256
                ),
                CanonicalReceiptReader(SessionFactory, updates),
                case.contexts if dynamic else None,
            )
            manager = service.PaperTradingManager(
                SessionFactory,
                MagicMock(),
                MagicMock(),
                forward_sources=factory,
                replay_interval_seconds=0,
                clock=lambda: case.clock[0],
            )
            managers.append(manager)
            monkeypatch.setattr(routes, "paper_manager", manager)
            return manager

        manager = new_manager()
        pause_tasks = []
        original_publish = manager.hub.publish

        def publish(sid, event):
            original_publish(sid, event)
            if event["type"] == "session.status" and event["payload"]["status"] == "RUNNING":
                case.clock[0] = datetime.combine(case.first, time(10), UTC)
            if event["type"] == "input.committed" and not pause_tasks:
                case.clock[0] = datetime.combine(case.second, time(10), UTC)
                pause_tasks.append(asyncio.create_task(manager.pause(sid)))

        manager.hub.publish = publish
        app = FastAPI()
        app.include_router(routes.router, prefix="/api")
        body = {
            "provider_type": "forward_a_share",
            "dataset_id": case.command.dataset_id,
            "symbol": "CN-A",
            "strategy": {
                "type": case.command.strategy_type,
                "parameters": manager._json_decimals(case.command.strategy_parameters),
            },
            "initial_cash": "1000000",
            "default_order_quantity": "1",
            "risk": case.command.risk.model_dump(mode="json"),
        }
        body["risk"].pop("allow_limit_orders")  # Domain-only field is not a public API input.
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            created = await client.post(
                "/api/paper-trading/sessions",
                json=body,
                headers={"Idempotency-Key": "synthetic-receipt-pg"},
            )
            assert created.status_code == 201, created.text
            account_id = UUID(created.json()["session_id"])
            same = await client.post(
                "/api/paper-trading/sessions",
                json=body,
                headers={"Idempotency-Key": "synthetic-receipt-pg"},
            )
            assert same.json()["session_id"] == str(account_id)
            path = f"/api/paper-trading/sessions/ws/{account_id}"
            scope = {
                "type": "websocket",
                "asgi": {"version": "3.0", "spec_version": "2.4"},
                "http_version": "1.1",
                "scheme": "ws",
                "path": path,
                "raw_path": path.encode(),
                "root_path": "",
                "query_string": b"",
                "headers": [(b"host", b"test"), (b"origin", settings.frontend_origin.encode())],
                "client": ("127.0.0.1", 12345),
                "server": ("test", 80),
                "subprotocols": [],
                "state": {},
            }
            incoming.put_nowait({"type": "websocket.connect"})
            websocket_task = asyncio.create_task(app(scope, incoming.get, outgoing.put))
            accepted = await asyncio.wait_for(outgoing.get(), 5)
            assert accepted["type"] == "websocket.accept"

            async def drain():
                while True:
                    frame = await outgoing.get()
                    if frame["type"] == "websocket.close":
                        return
                    assert frame["type"] == "websocket.send" and isinstance(frame["text"], str)
                    frames.append(json.loads(frame["text"]))

            drain_task = asyncio.create_task(drain())
            for _ in range(100):
                if manager.hub.subscriber_count(account_id):
                    break
                await asyncio.sleep(0.001)
            assert manager.hub.subscriber_count(account_id) == 1
            started = await client.post(f"/api/paper-trading/sessions/{account_id}/start")
            assert started.status_code == 200, started.text
            await asyncio.wait_for(manager._tasks[account_id], 20)
            await asyncio.gather(*pause_tasks)
            assert (await manager.get(account_id)).status is PaperSessionStatus.PAUSED
            before = await manager.events(account_id)
            original_started_at = (await manager.get(account_id)).started_at
            assert original_started_at == datetime.combine(case.first, time(6), UTC)
            assert len([item for item in before if item.event_type == "input.committed"]) == 1
            for _ in range(100):
                if any(item["type"] == "input.committed" for item in frames):
                    break
                await asyncio.sleep(0.001)
            assert frames[0]["type"] == "stream.connected"
            assert any(item["type"] == "input.committed" for item in frames)
            for item in frames:
                if item["type"] != "stream.connected":
                    PaperEventResponse.model_validate(item)
            incoming.put_nowait({"type": "websocket.disconnect", "code": 1000})
            await asyncio.wait_for(websocket_task, 2)
            websocket_task = None
            drain_task.cancel()
            with suppress(asyncio.CancelledError):
                await drain_task
            drain_task = None
            await manager.shutdown()

            restarted = new_manager()
            resumed = await client.post(f"/api/paper-trading/sessions/{account_id}/start")
            assert resumed.status_code == 200, resumed.text
            await asyncio.wait_for(restarted._tasks[account_id], 20)
            after = await restarted.events(account_id)
            assert after[: len(before)] == before
            assert (await restarted.get(account_id)).status is PaperSessionStatus.STOPPED
            assert (await restarted.get(account_id)).started_at == original_started_at
            assert len([item for item in after if item.event_type == "market.session"]) == 2
            assert len([item for item in after if item.event_type == "input.committed"]) == 2
            assert any(item.event_type == "fill.created" for item in after)
            validate_commit_history(after, await restarted.get(account_id))
            snapshot = await client.get(f"/api/paper-trading/sessions/{account_id}/snapshot")
            assert snapshot.status_code == 200, snapshot.text
            state = snapshot.json()
            assert state["session"]["provider_type"] == "forward_a_share"
            assert (
                state["latest_session"]["input_provenance"]
                == state["latest_portfolio"]["input_provenance"]
            )
            assert state["latest_portfolio"]["plan"]["mode"] == "forward_paper"
            assert state["fills"]
            event_response = await client.get(f"/api/paper-trading/sessions/{account_id}/events")
            assert event_response.status_code == 200
            for item in event_response.json():
                PaperEventResponse.model_validate(item)
    finally:
        if websocket_task is not None:
            incoming.put_nowait({"type": "websocket.disconnect", "code": 1000})
            await asyncio.wait_for(websocket_task, 2)
        if drain_task is not None:
            drain_task.cancel()
            with suppress(asyncio.CancelledError):
                await drain_task
        for manager in managers:
            await manager.shutdown()
        require_disposable_database(settings.app_env, settings.database_url)
        async with SessionFactory() as db, db.begin():
            if account_id is not None:
                await db.execute(
                    delete(PaperTradingEventModel).where(
                        PaperTradingEventModel.session_id == account_id
                    )
                )
                await db.execute(
                    delete(PaperTradingSessionModel).where(
                        PaperTradingSessionModel.id == account_id
                    )
                )
            await db.execute(
                text(
                    "TRUNCATE product_market_observations, product_market_receipts, "
                    "product_market_update_jobs"
                )
            )
