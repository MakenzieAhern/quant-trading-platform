"""Synthetic qualification only; never registers a production authority parser."""

import asyncio
import json
from copy import deepcopy
from datetime import UTC, datetime, time, timedelta
from unittest.mock import MagicMock
from uuid import NAMESPACE_URL, uuid5

import pytest

from app.application.paper_trading.context_store import ContextCandidate, ContextRecord
from app.application.paper_trading.qualified_context import QualifiedContextReader, VerifiedContext
from app.application.paper_trading.receipt_source import ReceiptSessionFactory
from app.application.paper_trading.source_admission import (
    AUTHORITY_NAMES,
    DAILY_INPUT,
    AuthorityFrame,
    ContextSourceObservation,
    ForwardAdmissionRegistry,
)
from app.data.catalog.checksums import canonical_json_bytes, canonical_sha256, sha256_file
from app.paper.models import PaperSessionStatus
from tests.test_paper_receipt_bridge import fixture, run


def dynamic_case(tmp_path, monkeypatch, *, patch_repository=True):
    case = fixture(tmp_path, monkeypatch, patch_repository=patch_repository)
    admitted = case.registry.load(case.command.dataset_id)
    contract = deepcopy(case.contract)
    contract["schema_version"] = "PAPER_FORWARD_ADMISSION_V2"
    del contract["daily_context"]
    contract["context_verifier"] = "SYNTHETIC_INDEPENDENT_ORACLE_V1"
    contract["security_ids"] = [
        str(item.status.security_id) for item in admitted.frames[0].statuses
    ]
    case.write("admission.json", contract)
    case.registry = ForwardAdmissionRegistry(
        tmp_path / "admission.json", sha256_file(tmp_path / "admission.json")
    )
    case.frames = admitted.frames
    case.contract = contract
    return case


def test_v2_root_does_not_require_future_daily_facts(tmp_path, monkeypatch):
    case = dynamic_case(tmp_path, monkeypatch)
    (tmp_path / "context.json").unlink()
    admitted = case.registry.load(case.command.dataset_id)
    assert admitted.frames == ()
    assert admitted.forward_dates == (case.first, case.second)
    assert len(admitted.warmup) == 253


async def test_v2_creation_requires_registered_independent_verifier(tmp_path, monkeypatch):
    case = dynamic_case(tmp_path, monkeypatch)
    old = case.manager._forward_factory
    case.manager._forward_factory = ReceiptSessionFactory(case.registry, old.reader)
    with pytest.raises(ValueError, match="FORWARD_CONTEXT_VERIFIER_NOT_REGISTERED"):
        await case.manager.create(case.command)
    assert case.current[0] is None
    assert not case.journal


@pytest.mark.parametrize("gap", ["authority_expired", "cost_hole"])
async def test_dynamic_root_rejects_known_future_coverage_gap_before_creation(
    tmp_path, monkeypatch, gap
):
    case = connect_contexts(dynamic_case(tmp_path, monkeypatch))
    contract = deepcopy(case.contract)
    warmup = json.loads((tmp_path / "warmup.json").read_bytes())
    previous = (case.first - timedelta(days=1)).isoformat()
    if gap == "authority_expired":
        for authority in contract["authorities"].values():
            authority["valid_to"] = previous
        digest = canonical_sha256(contract["authorities"])
        for frame in warmup:
            frame["authorities_sha256"] = digest
    else:
        for cost in contract["transaction_costs"]:
            cost["valid_to"] = previous
        for frame in warmup:
            for rule in frame["trading_rules"]:
                rule["cost_schedule"]["valid_to"] = previous
    contract["warmup"] = case.write("warmup.json", warmup)
    case.write("admission.json", contract)
    case.registry.expected_sha256 = sha256_file(tmp_path / "admission.json")
    with pytest.raises(ValueError, match=r"FORWARD_(AUTHORITY|TRANSACTION_COST)"):
        await case.manager.create(case.command)
    assert case.current[0] is None


def connect_contexts(case):
    """Separate fixture source oracle from untrusted candidate payloads and timestamps."""
    originals, sources, candidates = {}, {}, {}
    for frame in case.frames:
        body = canonical_json_bytes(frame.model_dump(mode="json"))
        digest = canonical_sha256(frame.model_dump(mode="json"))
        originals[digest] = body
        captured = datetime.combine(frame.trading_date, time(8), UTC)
        sources[digest] = ContextSourceObservation(
            authority_names=tuple(sorted(AUTHORITY_NAMES - {"RAW_OHLCV"})),
            evidence_sha256=digest,
            receipt_sha256=canonical_sha256({"original_source": digest}),
            published_at=captured - timedelta(minutes=3),
            completed_at=captured - timedelta(minutes=2),
            first_observed_at=captured - timedelta(minutes=1),
        )
        candidate = ContextCandidate(
            eligibility_sha256=case.registry.expected_sha256,
            source_id="SYNTHETIC_TEST_ONLY",
            parser_version="independent-synthetic-oracle-v1",
            source_published_at=sources[digest].published_at,
            frame=frame,
            evidence=({"path": digest + ".source", "sha256": digest},),
        )
        identity = canonical_sha256(candidate.model_dump(mode="json"))
        candidates[frame.trading_date] = ContextRecord(
            id=uuid5(NAMESPACE_URL, "paper-context-candidate:" + identity),
            candidate_sha256=identity,
            observation_sha256=canonical_sha256({"candidate": identity, "time": str(captured)}),
            first_observed_at=captured,
            registered_at=captured + timedelta(seconds=1),
            source_published_at=candidate.source_published_at,
            candidate=candidate,
        )

    class Store:
        def __init__(self):
            self.rows = {day: [record] for day, record in candidates.items()}
            self.requested = asyncio.Event()
            self.arrived = asyncio.Event()
            self.arrived.set()

        async def read_day(self, root, day):
            self.requested.set()
            await self.arrived.wait()
            return tuple(self.rows.get(day, ()))

        async def read_pinned(self, root, day, digest):
            return next(row for row in self.rows[day] if row.candidate_sha256 == digest)

        def evidence(self, record):
            return {pin.sha256: originals[pin.sha256] for pin in record.candidate.evidence}

    class Oracle:
        def verify(self, admitted, record, evidence):
            assert len(evidence) == 1
            digest, body = next(iter(evidence.items()))
            if canonical_sha256(json.loads(body)) != digest:
                raise ValueError("SYNTHETIC_ORACLE_CHANGED_SOURCE_BYTES")
            observation = sources[digest]
            if (
                record.candidate.source_id != "SYNTHETIC_TEST_ONLY"
                or record.candidate.parser_version != "independent-synthetic-oracle-v1"
                or record.source_published_at != observation.published_at
            ):
                raise ValueError("SYNTHETIC_ORACLE_SOURCE_IDENTITY_MISMATCH")
            return VerifiedContext(AuthorityFrame.model_validate_json(body), (observation,))

    store = Store()
    contexts = QualifiedContextReader(store, {case.contract["context_verifier"]: Oracle()})
    previous = case.manager._forward_factory
    case.manager._forward_factory = ReceiptSessionFactory(case.registry, previous.reader, contexts)
    case.contexts, case.context_store = contexts, store
    case.originals, case.source_observations, case.candidates = originals, sources, candidates
    return case


async def test_after_start_arrival_reaches_real_manager_plan_ledger_and_api(tmp_path, monkeypatch):
    from app.api.schemas.paper import PaperEventResponse

    case = connect_contexts(dynamic_case(tmp_path, monkeypatch))
    case.context_store.arrived.clear()
    account = await case.manager.create(case.command)
    await case.manager.start(account.id)
    await asyncio.wait_for(case.context_store.requested.wait(), 10)
    assert case.current[0].status is PaperSessionStatus.RUNNING
    assert not any(event.event_type == "market.session" for event in case.journal)
    case.context_store.arrived.set()
    await asyncio.wait_for(case.manager._tasks[account.id], 20)
    assert case.current[0].status is PaperSessionStatus.STOPPED, case.current[0].error_message
    batches = [batch for batch in case.batches if batch[0].event_type == "market.session"]
    assert len(batches) == 2
    for batch in batches:
        pin = batch[0].payload["input_provenance"]
        assert pin["schema_version"] == "PAPER_DAILY_INPUT_V2"
        assert pin == batch[-1].payload["input_provenance"]
        assert pin == batch[-1].payload["plan"]["input_provenance"]
        parsed = DAILY_INPUT.validate_python(pin)
        assert parsed.context.first_captured_at > case.current[0].started_at
        assert (
            parsed.context.candidate_sha256 == case.candidates[parsed.trading_date].candidate_sha256
        )
    assert not any(event.event_type == "fill.created" for event in batches[0])
    assert any(event.event_type == "fill.created" for event in batches[1])
    for event in case.journal:
        PaperEventResponse.model_validate(
            {
                "sequence": event.sequence,
                "type": event.event_type,
                "occurred_at": event.occurred_at,
                "payload": event.payload,
            }
        )


@pytest.mark.parametrize(
    "fault",
    [
        "candidate_fact",
        "source_bytes",
        "version_conflict",
        "late",
        "future",
        "universe",
        "missing_coverage",
        "source_time",
        "parser",
    ],
)
async def test_unqualified_or_conflicting_context_never_reaches_financial_batch(
    tmp_path, monkeypatch, fault
):
    case = connect_contexts(dynamic_case(tmp_path, monkeypatch))
    record = case.candidates[case.first]
    digest = record.candidate.evidence[0].sha256
    if fault == "source_bytes":
        case.originals[digest] = b"{}"
    elif fault == "version_conflict":
        case.context_store.rows[case.first].append(record)
    elif fault in {"missing_coverage", "source_time"}:
        source = case.source_observations[digest]
        case.source_observations[digest] = source.model_copy(
            update=(
                {"authority_names": ("SSE_ST",)}
                if fault == "missing_coverage"
                else {"first_observed_at": record.first_observed_at + timedelta(seconds=1)}
            )
        )
    else:
        candidate = record.candidate
        if fault == "parser":
            record = record.model_copy(
                update={"candidate": candidate.model_copy(update={"parser_version": "other"})}
            )
        elif fault in {"candidate_fact", "universe"}:
            factors = dict(candidate.frame.adjustment_factors)
            factors[next(iter(factors))] = "2"
            frame = candidate.frame.model_copy(update={"adjustment_factors": factors})
            if fault == "universe":
                frame = candidate.frame.model_copy(
                    update={"statuses": candidate.frame.statuses[:-1]}
                )
            record = record.model_copy(
                update={"candidate": candidate.model_copy(update={"frame": frame})}
            )
        else:
            timestamp = (
                datetime.combine(case.second, time(1, 30), UTC)
                if fault == "late"
                else datetime.combine(case.first, time(11), UTC)
            )
            record = record.model_copy(update={"registered_at": timestamp})
        case.context_store.rows[case.first] = [record]
    account = await run(case)
    assert account.status is PaperSessionStatus.FAILED
    assert not any(item.event_type == "market.session" for item in case.journal)


async def test_new_manager_resume_uses_consumed_pin_not_later_conflicting_version(
    tmp_path, monkeypatch
):
    from app.application.paper_trading.service import PaperTradingManager

    case = connect_contexts(dynamic_case(tmp_path, monkeypatch))
    tasks = []

    def publish(sid, event):
        if event["type"] == "input.committed" and not tasks:
            tasks.append(asyncio.create_task(case.manager.pause(sid)))

    case.manager.hub.publish = MagicMock(side_effect=publish)
    account = await run(case)
    await asyncio.gather(*tasks)
    assert account.status is PaperSessionStatus.PAUSED
    original_start = account.started_at
    prefix = tuple(case.journal)
    original = case.candidates[case.first]
    case.context_store.rows[case.first].append(
        original.model_copy(update={"candidate_sha256": "f" * 64})
    )
    old = case.manager
    case.manager = PaperTradingManager(
        old._session_factory,
        MagicMock(),
        MagicMock(),
        forward_sources=old._forward_factory,
        replay_interval_seconds=0,
        clock=lambda: case.clock[0],
    )
    await case.manager.start(account.id)
    await asyncio.wait_for(case.manager._tasks[account.id], 20)
    after = await case.manager.get(account.id)
    assert after.status is PaperSessionStatus.STOPPED, after.error_message
    assert after.started_at == original_start
    assert tuple(case.journal[: len(prefix)]) == prefix
    assert sum(event.event_type == "market.session" for event in case.journal) == 2
    assert sum(event.event_type == "input.committed" for event in case.journal) == 2
    assert any(event.event_type == "fill.created" for event in case.journal)


@pytest.mark.parametrize("dynamic", [False, True])
@pytest.mark.parametrize("boundary", ["receipt", "context"])
async def test_clock_rollback_cannot_acknowledge_future_evidence_or_advance(
    tmp_path, monkeypatch, dynamic, boundary
):
    case = (
        connect_contexts(dynamic_case(tmp_path, monkeypatch))
        if dynamic
        else fixture(tmp_path, monkeypatch)
    )
    if dynamic and boundary == "context":
        record = case.candidates[case.first]
        case.context_store.rows[case.first] = [
            record.model_copy(
                update={
                    "registered_at": datetime.combine(case.first, time(10), UTC)
                    + timedelta(seconds=1)
                }
            )
        ]
        reader = case.manager._forward_factory.reader
        original = reader.read

        async def read(frame):
            result = await original(frame)
            case.clock[0] += timedelta(seconds=2)
            return result

        monkeypatch.setattr(reader, "read", read)

    def publish(sid, event):
        if event["type"] == "portfolio.snapshot":
            case.clock[0] = datetime.combine(case.first, time(10), UTC) - timedelta(seconds=1)
            if dynamic and boundary == "context":
                case.clock[0] += timedelta(seconds=1)

    case.manager.hub.publish = MagicMock(side_effect=publish)
    account = await run(case)
    assert account.status is PaperSessionStatus.FAILED
    assert sum(item.event_type == "market.session" for item in case.journal) == 1
    assert not any(item.event_type == "input.committed" for item in case.journal)
    assert not any(item.event_type == "fill.created" for item in case.journal)


async def test_stop_while_waiting_for_context_never_consumes_unread_day(tmp_path, monkeypatch):
    case = connect_contexts(dynamic_case(tmp_path, monkeypatch))
    case.context_store.arrived.clear()
    account = await case.manager.create(case.command)
    await case.manager.start(account.id)
    await asyncio.wait_for(case.context_store.requested.wait(), 10)
    await case.manager.stop(account.id)
    await asyncio.wait_for(case.manager._tasks[account.id], 10)
    assert case.current[0].status is PaperSessionStatus.STOPPED
    assert not any(item.event_type == "market.session" for item in case.journal)


@pytest.mark.parametrize("missing", ["context", "raw"])
async def test_missing_first_day_cannot_skip_to_ready_second_day(tmp_path, monkeypatch, missing):
    case = connect_contexts(dynamic_case(tmp_path, monkeypatch))

    async def unavailable(*args):
        case.clock[0] = datetime.combine(case.second, time(1, 30), UTC)
        return () if missing == "context" else None

    if missing == "context":
        monkeypatch.setattr(case.context_store, "read_day", unavailable)
    else:
        monkeypatch.setattr(case.manager._forward_factory.reader, "read", unavailable)
    account = await run(case)
    assert account.status is PaperSessionStatus.FAILED
    assert not any(item.event_type == "market.session" for item in case.journal)
