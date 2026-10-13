"""Read-only HTTP capability checks use real local registries, never an application DB."""

import json
from unittest.mock import MagicMock

import pytest
from httpx import ASGITransport, AsyncClient

from app.api.routes import paper
from app.api.schemas.paper import PaperCapabilitiesResponse
from app.application.backtests.registry import DatasetRegistry, StrategyRegistry
from app.application.experiments import data
from app.application.experiments.data import ExperimentDatasetRegistry, ExperimentInputError
from app.application.paper_trading.service import PaperTradingManager
from app.data.catalog import finalize_manifest, load_manifest
from app.data.catalog.checksums import canonical_sha256
from app.data.catalog.freeze import MARKER
from app.main import app
from tests import test_product_markets

CSV = "timestamp,open,high,low,close,volume\n2024-01-02T15:00:00Z,10,11,9,10,100\n"
archive = test_product_markets.archive


@pytest.fixture
def manager(tmp_path, monkeypatch):
    fixtures = tmp_path / "fixtures"
    fixtures.mkdir()
    (fixtures / "AAPL.csv").write_text(CSV)
    value = PaperTradingManager(
        MagicMock(side_effect=AssertionError("capabilities must not access the database")),
        DatasetRegistry.phase7(fixtures),
        StrategyRegistry(),
        historical_datasets=ExperimentDatasetRegistry(tmp_path / "research"),
    )
    monkeypatch.setattr(paper, "paper_manager", value)
    return value


async def get_capabilities():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/paper-trading/sessions/capabilities")
    assert response.status_code == 200
    assert response.headers["cache-control"] == "no-store"
    return response.json()


async def test_capabilities_static_route_uses_actual_manager_registries_without_database(manager):
    payload = await get_capabilities()
    assert payload == {
        "providers": [
            {
                "provider_type": "replay",
                "dataset_id": "AAPL_fixture",
                "symbol": "AAPL",
                "available": True,
                "reason_code": None,
            },
            {
                "provider_type": "simulated_a_share",
                "dataset_id": "CN_A_SIMULATED_PAPER_FIXTURE_V1",
                "symbol": "CN-A",
                "available": True,
                "reason_code": None,
            },
            {
                "provider_type": "historical_a_share",
                "dataset_id": data.HISTORICAL_ID,
                "symbol": "CN-A",
                "available": False,
                "reason_code": "DATASET_NOT_MOUNTED",
            },
        ],
        "forward": {"available": False, "reason_code": "FORWARD_NOT_AVAILABLE"},
    }
    assert await get_capabilities() == payload
    manager._session_factory.assert_not_called()
    assert manager._tasks == {} and manager._providers == {}


@pytest.mark.parametrize(
    ("content", "reason"),
    [
        (None, "REPLAY_DATA_UNAVAILABLE"),
        (CSV.splitlines()[0] + "\n", "REPLAY_DATA_UNAVAILABLE"),
        (CSV.replace(",10,11,9,10,100", ",10,9,11,10,100"), "REPLAY_DATA_INVALID"),
    ],
)
async def test_replay_checks_actual_csv_and_keeps_other_modes_independent(
    manager, tmp_path, content, reason
):
    source = tmp_path / "fixtures/AAPL.csv"
    if content is None:
        source.unlink()
    else:
        source.write_text(content)
    providers = (await get_capabilities())["providers"]
    assert providers[0]["available"] is False and providers[0]["reason_code"] == reason
    assert providers[1]["available"] is True
    assert str(tmp_path) not in json.dumps(providers)
    source.write_text(CSV)
    assert (await get_capabilities())["providers"][0]["available"] is True


async def test_historical_readability_is_not_execution_and_changed_source_is_rechecked(
    manager, archive, monkeypatch
):
    manager._historical_datasets = archive.registry
    root = archive.registry.dataset_root(data.HISTORICAL_ID)
    original = load_manifest(root / "manifest.json")
    # Classify this isolated manifest as the known-bad version without touching retained data.
    monkeypatch.setattr(data, "HISTORICAL_SOURCE_CONTRACT_FAILURE_SHA", original.canonical_sha256)
    assert archive.registry.resolve(data.HISTORICAL_ID, for_execution=False)["available"]
    denied = (await get_capabilities())["providers"][2]
    assert denied["available"] is False
    assert denied["reason_code"] == "SOURCE_CONTRACT_INTEGRITY_FAILED"

    changed = finalize_manifest({**original.model_dump(), "provider_version": "fixture-v2"})
    (root / "manifest.json").write_text(changed.model_dump_json())
    freeze = {"dataset_manifest_sha256": changed.canonical_sha256}
    freeze["freeze_record_sha256"] = canonical_sha256(freeze)
    (root / MARKER).write_text(json.dumps(freeze))
    assert archive.registry.resolve(data.HISTORICAL_ID, for_execution=False)["available"]
    changed_capability = (await get_capabilities())["providers"][2]
    assert changed_capability["available"] is False
    assert changed_capability["reason_code"] == "SOURCE_CONTRACT_INTEGRITY_UNVERIFIED"


async def test_missing_historical_registry_is_explicit(manager):
    manager._historical_datasets = None
    row = (await get_capabilities())["providers"][2]
    assert not row["available"] and row["reason_code"] == "DATASET_NOT_REGISTERED"


@pytest.mark.parametrize("error", [RuntimeError("/private/secret"), ExperimentInputError("secret")])
async def test_unexpected_registry_failures_are_opaque_and_isolated(manager, monkeypatch, error):
    monkeypatch.setattr(manager._historical_datasets, "resolve", MagicMock(side_effect=error))
    payload = await get_capabilities()
    assert payload["providers"][0]["available"]
    assert payload["providers"][1]["available"]
    assert payload["providers"][2]["reason_code"] == "PAPER_CAPABILITY_CHECK_FAILED"
    assert "secret" not in json.dumps(payload)
    manager._session_factory.assert_not_called()


async def test_unregistered_replay_is_unavailable(manager):
    manager._datasets = DatasetRegistry(())
    row = (await get_capabilities())["providers"][0]
    assert not row["available"] and row["reason_code"] == "REPLAY_DATA_UNAVAILABLE"


async def test_unexpected_replay_failure_is_opaque_and_does_not_hide_synthetic(
    manager, monkeypatch
):
    monkeypatch.setattr(
        manager._datasets, "resolve", MagicMock(side_effect=RuntimeError("/private/secret"))
    )
    payload = await get_capabilities()
    assert payload["providers"][0]["reason_code"] == "PAPER_CAPABILITY_CHECK_FAILED"
    assert payload["providers"][1]["available"]
    assert "secret" not in json.dumps(payload)


@pytest.mark.parametrize(
    "damage", ["missing", "duplicate", "identity", "available", "reason", "forward"]
)
async def test_capability_response_contract_rejects_inconsistent_or_expanded_modes(manager, damage):
    payload = await get_capabilities()
    if damage == "missing":
        payload["providers"].pop()
    elif damage == "duplicate":
        payload["providers"][2] = payload["providers"][0]
    elif damage == "identity":
        payload["providers"][0]["dataset_id"] = "CN_A_SIMULATED_PAPER_FIXTURE_V1"
    elif damage == "available":
        payload["providers"][2]["available"] = True
    elif damage == "reason":
        payload["providers"][2]["reason_code"] = "unbounded provider exception"
    else:
        payload["forward"]["available"] = True
    with pytest.raises(ValueError):
        PaperCapabilitiesResponse.model_validate(payload)


async def test_forward_capability_does_not_add_a_create_provider(manager):
    assert (await get_capabilities())["forward"]["available"] is False
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/api/paper-trading/sessions",
            json={
                "provider_type": "forward",
                "dataset_id": "CN_A_SIMULATED_PAPER_FIXTURE_V1",
                "symbol": "CN-A",
                "strategy": {"type": "cn_a_cross_sectional_momentum_low_vol_v1", "parameters": {}},
            },
        )
    assert response.status_code == 422
    manager._session_factory.assert_not_called()
