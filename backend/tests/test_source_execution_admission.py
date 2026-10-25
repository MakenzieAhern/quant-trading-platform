"""Known-invalid sources cannot become new finance; old cache/receipts stay readable."""

from dataclasses import replace
from datetime import UTC, date, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.api.routes import paper
from app.application.experiments import data
from app.application.experiments.models import CreateExperimentRequest
from app.application.experiments.runner import json_value
from app.application.experiments.service import ExperimentManager
from app.application.market_updates.contracts import CreateUpdateRequest
from app.application.market_updates.service import MarketUpdateManager
from app.application.paper_trading.service import PaperTradingManager
from app.data.catalog.checksums import canonical_sha256
from app.paper.models import PaperSessionStatus
from tests.test_paper_plan_checkpoint import account


def registry(monkeypatch, tmp_path, sha=data.HISTORICAL_ECONOMIC_GAP_SHA):
    result = data.ExperimentDatasetRegistry(tmp_path)
    manifest = SimpleNamespace(
        coverage_start=date(2010, 1, 1),
        coverage_end=date(2025, 12, 31),
        canonical_sha256=sha,
        security_count=5431,
    )
    monkeypatch.setattr(result, "manifest", lambda dataset_id: manifest)
    return result


@pytest.mark.parametrize(
    ("sha", "reason"),
    [
        (data.HISTORICAL_ECONOMIC_GAP_SHA, "SOURCE_CONTRACT_INTEGRITY_FAILED"),
        ("a" * 64, "SOURCE_CONTRACT_INTEGRITY_UNVERIFIED"),
    ],
)
def test_shared_execution_admission_rejects_failed_and_unverified_versions(
    monkeypatch, tmp_path, sha, reason
):
    source = registry(monkeypatch, tmp_path, sha)
    before = source.datasets()
    with pytest.raises(data.ExperimentInputError, match=f"^{reason}$"):
        source.resolve(data.HISTORICAL_ID)
    assert source.datasets() == before
    historical = source.resolve(data.HISTORICAL_ID, for_execution=False)
    assert historical["available"] is True
    assert historical["execution_available"] is False
    assert historical["execution_reason_code"] == reason
    assert historical["sha256"] == sha
    assert historical["current_dataset_quality"] == data.current_dataset_quality(
        data.HISTORICAL_ID, sha
    )
    assert source.resolve(data.DEMO_ID)["execution_available"] is True


def test_failed_source_is_stopped_before_full_dataset_loader(monkeypatch, tmp_path):
    source = registry(monkeypatch, tmp_path)
    monkeypatch.setattr(source, "dataset_root", lambda dataset_id: tmp_path)
    loader = MagicMock(side_effect=RuntimeError("FULL_DATASET_LOADER_REACHED"))
    monkeypatch.setattr(data, "FullDataset", loader)
    with pytest.raises(data.ExperimentInputError, match=r"^SOURCE_CONTRACT_INTEGRITY_FAILED$"):
        data.load_experiment_dataset(source, data.HISTORICAL_ID, date(2024, 1, 2), date(2024, 1, 4))
    loader.assert_not_called()


@pytest.mark.parametrize("status", [PaperSessionStatus.CREATED, PaperSessionStatus.PAUSED])
async def test_paper_start_rejects_source_before_transition_or_background_task(
    monkeypatch, tmp_path, status
):
    source = registry(monkeypatch, tmp_path)
    saved = replace(
        account(),
        status=status,
        strategy_parameters={
            **account().strategy_parameters,
            "dataset_sha256": data.HISTORICAL_ECONOMIC_GAP_SHA,
        },
    )
    before = repr(saved)
    database = MagicMock(side_effect=RuntimeError("DATABASE_WRITE_REACHED"))
    manager = PaperTradingManager(database, MagicMock(), MagicMock(), historical_datasets=source)
    monkeypatch.setattr(manager, "get", AsyncMock(return_value=saved))
    transition = AsyncMock(side_effect=RuntimeError("TRANSITION_REACHED"))
    monkeypatch.setattr(manager, "_transition", transition)
    with pytest.raises(data.ExperimentInputError, match=r"^SOURCE_CONTRACT_INTEGRITY_FAILED$"):
        await manager.start(saved.id)
    assert repr(saved) == before
    assert manager._tasks == {} and manager._providers == {}
    transition.assert_not_awaited()
    database.assert_not_called()


@pytest.mark.parametrize("pinned", [None, "", "b" * 64])
async def test_paper_start_cannot_borrow_current_admission_for_another_saved_version(
    monkeypatch, tmp_path, pinned
):
    source = registry(monkeypatch, tmp_path)
    saved = replace(
        account(),
        status=PaperSessionStatus.PAUSED,
        strategy_parameters={**account().strategy_parameters, "dataset_sha256": pinned},
    )
    manager = PaperTradingManager(MagicMock(), MagicMock(), MagicMock(), historical_datasets=source)
    monkeypatch.setattr(manager, "get", AsyncMock(return_value=saved))
    transition = AsyncMock(side_effect=RuntimeError("TRANSITION_REACHED"))
    monkeypatch.setattr(manager, "_transition", transition)
    with pytest.raises(data.ExperimentInputError, match=r"^DATASET_CHANGED_SINCE_SUBMISSION$"):
        await manager.start(saved.id)
    assert saved.strategy_parameters["dataset_sha256"] == pinned
    transition.assert_not_awaited()
    assert manager._tasks == {}


@pytest.mark.parametrize("status", [PaperSessionStatus.STARTING, PaperSessionStatus.RUNNING])
async def test_duplicate_active_start_is_still_an_idempotent_read(monkeypatch, status):
    source = MagicMock()
    source.resolve.side_effect = RuntimeError("NEW_ADMISSION_CHECK_REACHED")
    saved = replace(account(), status=status)
    manager = PaperTradingManager(MagicMock(), MagicMock(), MagicMock(), historical_datasets=source)
    monkeypatch.setattr(manager, "get", AsyncMock(return_value=saved))
    transition = AsyncMock(side_effect=RuntimeError("TRANSITION_REACHED"))
    monkeypatch.setattr(manager, "_transition", transition)
    assert await manager.start(saved.id) is saved
    source.resolve.assert_not_called()
    transition.assert_not_awaited()
    assert manager._tasks == {}


async def test_paper_start_route_translates_source_rejection_to_422_not_500(monkeypatch):
    manager = MagicMock()
    manager.start = AsyncMock(
        side_effect=data.ExperimentInputError("SOURCE_CONTRACT_INTEGRITY_FAILED")
    )
    monkeypatch.setattr(paper, "paper_manager", manager)
    with pytest.raises(HTTPException) as rejected:
        await paper.start_paper_session(account().id)
    assert rejected.value.status_code == 422
    assert "SOURCE_CONTRACT_INTEGRITY_FAILED" in str(rejected.value.detail)


async def test_raw_candidate_planning_uses_readable_archive_without_financial_admission(
    monkeypatch, tmp_path
):
    source = registry(monkeypatch, tmp_path / "archive")
    db = MagicMock()
    db.scalar = AsyncMock(return_value=None)
    db.commit = AsyncMock()
    factory = MagicMock()
    factory.return_value.__aenter__ = AsyncMock(return_value=db)
    reader = SimpleNamespace(
        registry=source,
        security=lambda dataset_id, sid: {
            "security_id": sid,
            "listed_from": "2000-01-01",
            "listed_to": None,
        },
    )
    provider = AsyncMock(side_effect=RuntimeError("PROVIDER_REACHED"))
    manager = MarketUpdateManager(
        factory,
        MagicMock(),
        reader,
        tmp_path / "candidate-cache",
        transport=provider,
        now=lambda: datetime(2026, 10, 8, tzinfo=UTC),
    )
    monkeypatch.setattr(manager, "_denied", AsyncMock(return_value=False))
    monkeypatch.setattr(manager, "_receipt_blocked", AsyncMock(return_value=False))
    job = await manager.create(
        CreateUpdateRequest(
            security_ids=["CN-A:SSE:600000"], start_date="2026-09-21", end_date="2026-09-22"
        ),
        "offline-candidate-planning",
    )
    assert job.status == "QUEUED"
    assert job.master_snapshot["current_authority"] == "UNVERIFIED"
    assert job.master_snapshot["sha256"] == data.HISTORICAL_SOURCE_CONTRACT_FAILURE_SHA
    assert source.resolve(data.HISTORICAL_ID, for_execution=False)["execution_available"] is False
    provider.assert_not_awaited()


@pytest.mark.parametrize("retry", [False, True])
@pytest.mark.parametrize("existing", [False, True])
async def test_experiment_new_execution_rejects_but_old_receipt_survives(
    monkeypatch, tmp_path, retry, existing
):
    source = registry(monkeypatch, tmp_path)
    request = CreateExperimentRequest(
        name="Historical admission check",
        dataset_id=data.HISTORICAL_ID,
        start_date=date(2024, 1, 2),
        end_date=date(2024, 1, 4),
    )
    configuration = json_value(request.model_dump())
    parent_id = uuid4() if retry else None
    receipt = SimpleNamespace(
        configuration_sha256=canonical_sha256(configuration), retry_of=parent_id
    )
    db = MagicMock()
    db.scalar = AsyncMock(side_effect=[None, receipt] if retry and existing else None)
    if not (retry and existing):
        db.scalar.return_value = receipt if existing else None
    factory = MagicMock()
    factory.return_value.__aenter__ = AsyncMock(return_value=db)
    manager = ExperimentManager(factory, source, MagicMock())
    if retry:
        monkeypatch.setattr(
            manager,
            "get",
            AsyncMock(
                return_value=SimpleNamespace(
                    id=parent_id, status="FAILED", configuration=configuration, attempt=1
                )
            ),
        )
        operation = manager.retry(parent_id, "new-request")
    else:
        operation = manager.create(request, "same-request")
    if existing:
        assert await operation is receipt
    else:
        with pytest.raises(data.ExperimentInputError, match=r"^SOURCE_CONTRACT_INTEGRITY_FAILED$"):
            await operation
    db.add.assert_not_called()
    assert not manager._wake.is_set()
