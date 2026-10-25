"""Unqualified daily-context arrival durability, using only disposable quant_test."""

import asyncio
import json
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from sqlalchemy import select, text
from sqlalchemy.exc import DBAPIError

from app.application.paper_trading.context_store import ContextCandidate, DailyContextStore
from app.core.config import get_settings
from app.data.catalog.checksums import canonical_sha256
from app.data.catalog.freeze import write_immutable
from app.db.models.paper_context import PaperContextCandidateModel
from app.db.session import SessionFactory
from tests.conftest import require_disposable_database
from tests.test_paper_receipt_bridge import fixture


@pytest.fixture
async def context_case(tmp_path, monkeypatch):
    settings = get_settings()
    require_disposable_database(settings.app_env, settings.database_url)
    bridge = fixture(tmp_path, monkeypatch)
    admitted = bridge.registry.load(bridge.command.dataset_id)
    clock = [datetime(2032, 1, 1, tzinfo=UTC)]
    source = tmp_path / "source.json"
    source.write_text('{"source":"synthetic-only"}')
    from app.data.catalog.checksums import sha256_file

    candidate = ContextCandidate(
        eligibility_sha256=canonical_sha256(str(uuid4())),
        source_id="SYNTHETIC_TEST_ONLY",
        parser_version="synthetic-test-v1",
        source_published_at=clock[0] - timedelta(days=1),
        frame=admitted.frames[0],
        evidence=({"path": source.name, "sha256": sha256_file(source)},),
    )
    store = DailyContextStore(
        SessionFactory, tmp_path / "contexts", tmp_path / "research", clock=lambda: clock[0]
    )
    yield store, candidate, tmp_path, clock


async def test_after_start_arrival_and_duplicate_keep_first_observation(context_case):
    store, candidate, root, clock = context_case
    started = clock[0] - timedelta(hours=1)
    first = await store.capture(candidate, root)
    clock[0] += timedelta(hours=2)
    duplicate = await store.capture(candidate, root)
    assert first == duplicate
    assert first.first_observed_at > started
    assert first.source_published_at < first.first_observed_at
    assert first.execution_admitted is False
    read = await store.read_day(candidate.eligibility_sha256, candidate.frame.trading_date)
    assert read == (first,)


async def test_real_clock_registration_survives_new_store_and_duplicate(context_case):
    _, candidate, root, _ = context_case
    store = DailyContextStore(SessionFactory, root / "real-clock", root / "research")
    async with SessionFactory() as db:
        before = await db.scalar(text("SELECT clock_timestamp()"))
    # Synthetic, unqualified evidence; neither the application nor SQL clock is replaced.
    candidate = candidate.model_copy(update={"source_published_at": before - timedelta(seconds=1)})
    first = await store.capture(candidate, root)
    async with SessionFactory() as db:
        after = await db.scalar(text("SELECT clock_timestamp()"))
        registered = await db.scalar(
            select(PaperContextCandidateModel.registered_at).where(
                PaperContextCandidateModel.id == first.id
            )
        )
    assert before <= first.first_observed_at <= first.registered_at <= after
    assert registered == first.registered_at
    assert first.source_published_at <= first.first_observed_at
    assert first.execution_admitted is False
    reopened = DailyContextStore(SessionFactory, store.root, root / "research")
    assert (
        await reopened.read_pinned(
            candidate.eligibility_sha256, candidate.frame.trading_date, first.candidate_sha256
        )
        == first
    )
    assert await reopened.capture(candidate, root) == first


async def test_repackaged_same_evidence_cannot_move_first_time(context_case):
    store, candidate, root, clock = context_case
    first = await store.capture(candidate, root)
    (root / "renamed.json").write_bytes((root / "source.json").read_bytes())
    payload = candidate.model_dump(mode="json")
    payload["evidence"][0]["path"] = "renamed.json"
    clock[0] += timedelta(days=1)
    assert await store.capture(ContextCandidate.model_validate(payload), root) == first


async def test_conflicting_versions_remain_visible_and_original_is_immutable(context_case):
    store, candidate, root, clock = context_case
    first = await store.capture(candidate, root)
    clock[0] += timedelta(minutes=1)
    changed = candidate.model_copy(update={"parser_version": "synthetic-test-v2"})
    second = await store.capture(changed, root)
    records = await store.read_day(candidate.eligibility_sha256, candidate.frame.trading_date)
    assert records == (first, second)
    assert first.candidate_sha256 != second.candidate_sha256
    assert all(not record.execution_admitted for record in records)


async def test_pinned_read_keeps_consumed_version_and_revalidates_original_bytes(context_case):
    store, candidate, root, clock = context_case
    first = await store.capture(candidate, root)
    clock[0] += timedelta(minutes=1)
    second = await store.capture(candidate.model_copy(update={"parser_version": "later"}), root)
    # Later bad version cannot invalidate the already consumed original on replay.
    later = store.root / f"{second.candidate_sha256}.candidate.json"
    later.chmod(0o600)  # Deliberate corruption of this test's private immutable fixture.
    later.write_bytes(b"bad later version")
    assert (
        await store.read_pinned(
            candidate.eligibility_sha256, candidate.frame.trading_date, first.candidate_sha256
        )
        == first
    )
    with pytest.raises(ValueError, match="CONTEXT_EVIDENCE_INVALID"):
        await store.read_day(candidate.eligibility_sha256, candidate.frame.trading_date)
    for digest, day in (
        ("0" * 64, candidate.frame.trading_date),
        (first.candidate_sha256, candidate.frame.trading_date + timedelta(days=1)),
    ):
        with pytest.raises(ValueError, match="FORWARD_REPLAY_CONTEXT_DISAPPEARED"):
            await store.read_pinned(candidate.eligibility_sha256, day, digest)
    original = store.root / first.candidate.evidence[0].path
    original.chmod(0o600)
    original.write_bytes(b"bad original source")
    with pytest.raises(ValueError, match="CONTEXT_EVIDENCE_INVALID"):
        await store.read_pinned(
            candidate.eligibility_sha256, candidate.frame.trading_date, first.candidate_sha256
        )


async def test_concurrent_same_capture_converges(context_case):
    store, candidate, root, _ = context_case
    results = await asyncio.gather(*(store.capture(candidate, root) for _ in range(4)))
    assert all(item == results[0] for item in results)
    assert (
        len(await store.read_day(candidate.eligibility_sha256, candidate.frame.trading_date)) == 1
    )


async def test_later_concurrent_winner_does_not_use_earlier_request_clock(
    context_case, monkeypatch
):
    store, candidate, root, clock = context_case
    later = clock[0] + timedelta(seconds=1)

    def interleaved_write(path, content):
        if path.name.endswith(".observed.json"):
            payload = json.loads(content)
            payload["first_observed_at"] = later.isoformat()
            write_immutable(path, json.dumps(payload).encode())
            clock[0] = later + timedelta(seconds=1)
        write_immutable(path, content)

    monkeypatch.setattr(
        "app.application.paper_trading.context_store.write_immutable", interleaved_write
    )
    result = await store.capture(candidate, root)
    assert result.first_observed_at == later


async def test_database_failure_keeps_durable_first_time_and_evidence(context_case):
    store, candidate, root, clock = context_case
    original_factory = store.factory

    def fail():
        raise RuntimeError("synthetic database unavailable")

    store.factory = fail
    observed = clock[0]
    with pytest.raises(RuntimeError, match="database unavailable"):
        await store.capture(candidate, root)
    assert list(store.root.glob("*.observed.json"))
    retained = ContextCandidate.model_validate_json(
        next(store.root.glob("*.candidate.json")).read_bytes()
    )
    (root / "source.json").unlink()
    recovered = DailyContextStore(
        original_factory, store.root, root / "research", clock=lambda: clock[0]
    )
    clock[0] += timedelta(hours=5)
    result = await recovered.capture(retained, store.root)
    assert result.first_observed_at == observed
    assert result.first_observed_at < clock[0]


@pytest.mark.parametrize("operation", ["UPDATE", "DELETE"])
async def test_database_rejects_mutation(context_case, operation):
    store, candidate, root, _ = context_case
    record = await store.capture(candidate, root)
    query = (
        "UPDATE product_paper_context_candidates SET source_id = 'changed' WHERE id = :id"
        if operation == "UPDATE"
        else "DELETE FROM product_paper_context_candidates WHERE id = :id"
    )
    with pytest.raises(DBAPIError, match="append only"):
        async with SessionFactory() as db, db.begin():
            await db.execute(text(query), {"id": record.id})
    assert await store.read_day(candidate.eligibility_sha256, candidate.frame.trading_date) == (
        record,
    )


async def test_source_mutation_fails_before_registration(context_case):
    store, candidate, root, _ = context_case
    (root / "source.json").write_text("changed")
    with pytest.raises(ValueError, match="CONTEXT_EVIDENCE_INVALID"):
        await store.capture(candidate, root)
    assert await store.read_day(candidate.eligibility_sha256, candidate.frame.trading_date) == ()


async def test_read_revalidates_archived_bytes_not_original_path(context_case):
    store, candidate, root, _ = context_case
    record = await store.capture(candidate, root)
    (root / "source.json").unlink()
    assert await store.read_day(candidate.eligibility_sha256, candidate.frame.trading_date) == (
        record,
    )
    archive = store.root / f"{candidate.evidence[0].sha256}.source"
    archive.chmod(0o600)
    archive.write_bytes(b"corrupt")
    with pytest.raises(ValueError, match="CONTEXT_EVIDENCE_INVALID"):
        await store.read_day(candidate.eligibility_sha256, candidate.frame.trading_date)


async def test_future_publication_and_unknown_extra_approval_are_rejected(context_case):
    store, candidate, root, clock = context_case
    future = candidate.model_copy(update={"source_published_at": clock[0] + timedelta(seconds=1)})
    with pytest.raises(ValueError, match="CONTEXT_PUBLICATION_IN_FUTURE"):
        await store.capture(future, root)
    with pytest.raises(ValueError):
        ContextCandidate.model_validate({**candidate.model_dump(), "approved": True})


async def test_version_budget_fails_instead_of_truncating(context_case, monkeypatch):
    store, candidate, root, _ = context_case
    await store.capture(candidate, root)
    await store.capture(candidate.model_copy(update={"parser_version": "v2"}), root)
    monkeypatch.setattr("app.application.paper_trading.context_store.MAX_VERSIONS", 1)
    with pytest.raises(ValueError, match="CONTEXT_VERSION_BUDGET_EXCEEDED"):
        await store.read_day(candidate.eligibility_sha256, candidate.frame.trading_date)


async def test_file_publication_failure_never_creates_database_row(context_case, monkeypatch):
    store, candidate, root, _ = context_case

    def fail(*args):
        raise OSError("synthetic disk full")

    monkeypatch.setattr("app.application.paper_trading.context_store.write_immutable", fail)
    with pytest.raises(OSError, match="disk full"):
        await store.capture(candidate, root)
    async with SessionFactory() as db:
        assert not tuple(
            await db.scalars(
                select(PaperContextCandidateModel).where(
                    PaperContextCandidateModel.eligibility_sha256 == candidate.eligibility_sha256
                )
            )
        )


@pytest.mark.parametrize("path", ["../source.json", "/etc/passwd"])
async def test_evidence_path_escape_is_rejected(context_case, path):
    store, candidate, root, _ = context_case
    payload = candidate.model_dump(mode="json")
    payload["evidence"][0]["path"] = path
    with pytest.raises(ValueError, match="CONTEXT_EVIDENCE_PATH_ESCAPE"):
        await store.capture(ContextCandidate.model_validate(payload), root)


@pytest.mark.parametrize(
    ("setting", "message"),
    [
        ("MAX_EVIDENCE_BYTES", "CONTEXT_EVIDENCE_INVALID"),
        ("MAX_CONTEXT_BYTES", "CONTEXT_DOCUMENT_BUDGET_EXCEEDED"),
    ],
)
async def test_capture_resource_budget_before_database(context_case, monkeypatch, setting, message):
    store, candidate, root, _ = context_case
    monkeypatch.setattr(f"app.application.paper_trading.context_store.{setting}", 1)
    with pytest.raises(ValueError, match=message):
        await store.capture(candidate, root)
    assert await store.read_day(candidate.eligibility_sha256, candidate.frame.trading_date) == ()


async def test_missing_observation_fails_and_no_new_first_time_is_returned(context_case):
    store, candidate, root, clock = context_case
    record = await store.capture(candidate, root)
    (store.root / f"{record.candidate_sha256}.observed.json").unlink()
    with pytest.raises(ValueError, match="CONTEXT_EVIDENCE_INVALID"):
        await store.read_day(candidate.eligibility_sha256, candidate.frame.trading_date)
    clock[0] += timedelta(minutes=1)
    with pytest.raises(ValueError, match="CONTEXT_EVIDENCE_INVALID"):
        await store.capture(candidate, root)


def test_store_cannot_overlap_frozen_research(tmp_path):
    with pytest.raises(ValueError, match="CONTEXT_STORE_MUST_BE_SEPARATE_FROM_RESEARCH"):
        DailyContextStore(
            SessionFactory, tmp_path / "research" / "candidate", tmp_path / "research"
        )
