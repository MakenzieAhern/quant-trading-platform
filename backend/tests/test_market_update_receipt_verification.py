"""Pure temporary-cache tests: no provider, application database, or source acquisition."""

from contextlib import asynccontextmanager
from copy import deepcopy
from datetime import UTC, date, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import UUID

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.api.routes import market_updates as routes
from app.application.market_updates import cache as cache_module
from app.application.market_updates.contracts import (
    AUTHORITY,
    FIELDS,
    PARSER_VERSION,
    PROVIDER,
    SDK_VERSION,
    SDK_WHEEL_SHA256,
    TERMS,
    UpdateError,
    parse_response,
    request_parameters,
)
from app.application.market_updates.service import MarketUpdateManager
from app.data.catalog.checksums import canonical_json_bytes, canonical_sha256
from app.db.models.market_updates import MarketObservationModel, MarketReceiptModel

SID = "CN-A:SSE:600000"
DAY = date(2026, 9, 18)
RECEIVED = datetime(2026, 9, 18, 10, tzinfo=UTC)


def receipt_payload():
    raw = {
        "fields": FIELDS.split(","),
        "rows": [
            ["2026-09-18", "sh.600000", "10", "11", "9", "10.5", "10", "100", "1020", "3", "1", "0"]
        ],
    }
    rows = parse_response(raw, SID, DAY, DAY)
    evidence = {
        "job_id": "a82c97a1-08b4-42f8-a14f-88ea9ee48e5c",
        "receipt_id": "1a94f829-985c-44b7-acaa-7f533b51f740",
        "provider": PROVIDER,
        "sdk_version": SDK_VERSION,
        "parser_version": PARSER_VERSION,
        "sdk_release_wheel_sha256": SDK_WHEEL_SHA256,
        "source_endpoint": "public-api.baostock.com:10030",
        "security_id": SID,
        "parameters": request_parameters(SID, DAY, DAY),
        "requested_at_utc": "2026-09-18T09:59:58+00:00",
        "response_completed_at_utc": "2026-09-18T09:59:59+00:00",
        "received_at_utc": RECEIVED.isoformat(),
        "first_received_at_utc": RECEIVED.isoformat(),
        "attempt": 1,
        "raw_response_representation": "SDK_DECODED_FIELDS_AND_ROWS_NOT_WIRE_BYTES",
        "raw_response_sha256": canonical_sha256(raw),
        "logical_rows_sha256": canonical_sha256({"rows": rows}),
        "row_count": len(rows),
        "terms": deepcopy(TERMS),
        "authority": deepcopy(AUTHORITY),
    }
    return raw, rows, evidence


def cache_and_manager(tmp_path):
    def no_database():
        raise AssertionError("NO_DATABASE_ALLOWED")

    manager = MarketUpdateManager(
        no_database,
        None,
        SimpleNamespace(registry=SimpleNamespace(root=tmp_path / "archive")),
        tmp_path / "cache",
    )
    return manager.cache, manager


def receipt_model(digest, evidence):
    return MarketReceiptModel(
        id=UUID(evidence["receipt_id"]),
        job_id=UUID(evidence["job_id"]),
        security_id=SID,
        received_at=RECEIVED,
        manifest_sha256=digest,
        evidence=evidence,
    )


@pytest.mark.parametrize("damage", ["price", "flag_type", "authority"])
async def test_rehashed_semantically_different_rows_fail_existing_readers(tmp_path, damage):
    cache, manager = cache_and_manager(tmp_path)
    raw, rows, evidence = receipt_payload()
    if damage == "price":
        rows[0]["raw"]["close"] = "10.6"
    elif damage == "flag_type":
        rows[0]["execution_eligible"] = 0
    else:
        rows[0]["execution_eligible"] = True
    evidence["logical_rows_sha256"] = canonical_sha256({"rows": rows})
    digest = cache.publish(raw, rows, evidence)
    # Every stored hash is self-consistent, including the DB receipt's evidence.
    with pytest.raises(UpdateError, match="PRODUCT_CACHE_INTEGRITY_FAILED"):
        cache.read(digest)
    with pytest.raises(UpdateError, match="PRODUCT_CACHE_INTEGRITY_FAILED"):
        await manager.verify_receipt(receipt_model(digest, evidence))


@pytest.mark.parametrize("version", ["product-baostock-raw-v1", "product-baostock-raw-v2"])
async def test_saved_supported_parser_versions_remain_readable_without_rewrite(tmp_path, version):
    cache, manager = cache_and_manager(tmp_path)
    raw, rows, evidence = receipt_payload()
    evidence["parser_version"] = version
    digest = cache.publish(raw, rows, evidence)
    before = {path.name: path.read_bytes() for path in cache.root.iterdir()}
    assert cache.read(digest)[1] == rows
    assert await manager.verify_receipt(receipt_model(digest, evidence)) == rows
    assert {path.name: path.read_bytes() for path in cache.root.iterdir()} == before


@pytest.mark.parametrize(
    "field,value",
    [
        ("parser_version", "caller-accepted-v3"),
        ("sdk_version", "0.9.3"),
        ("sdk_release_wheel_sha256", "0" * 64),
        ("provider", "CALLER_APPROVED"),
        ("source_endpoint", "different-source"),
        ("raw_response_representation", "WIRE_BYTES"),
        ("requested_at_utc", "2026-09-18T10:00:01+00:00"),
        ("response_completed_at_utc", "2026-09-18T10:00:01+00:00"),
        ("response_completed_at_utc", "2026-09-18T09:59:59"),
        ("received_at_utc", "2026-09-18T10:00:00"),
        ("received_at_utc", "2026-09-18T18:00:00+08:00"),
        ("first_received_at_utc", "2026-09-19T10:00:00+00:00"),
        ("row_count", True),
        ("row_count", 2),
        ("attempt", True),
        ("attempt", 4),
    ],
)
def test_rehashed_unsupported_receipt_metadata_is_not_authority(tmp_path, field, value):
    cache, _ = cache_and_manager(tmp_path)
    raw, rows, evidence = receipt_payload()
    evidence[field] = value
    digest = cache.publish(raw, rows, evidence)
    with pytest.raises(UpdateError, match="PRODUCT_CACHE_INTEGRITY_FAILED"):
        cache.read(digest)


@pytest.mark.parametrize(
    "field,value",
    [
        ("code", "sz.000001"),
        ("frequency", "5"),
        ("adjustflag", "2"),
        ("start_date", "2026-09-19"),
        ("end_date", "2026-10-20"),
        ("fields", "date,close"),
    ],
)
def test_rehashed_request_parameters_cannot_change_source_interpretation(tmp_path, field, value):
    cache, _ = cache_and_manager(tmp_path)
    raw, rows, evidence = receipt_payload()
    evidence["parameters"][field] = value
    digest = cache.publish(raw, rows, evidence)
    with pytest.raises(UpdateError, match="PRODUCT_CACHE_INTEGRITY_FAILED"):
        cache.read(digest)


@pytest.mark.parametrize("version", [2, True])
def test_unknown_or_boolean_manifest_version_is_not_supported(tmp_path, version):
    cache, _ = cache_and_manager(tmp_path)
    raw, rows, evidence = receipt_payload()
    digest = cache.publish(raw, rows, evidence)
    manifest = cache.read(digest)[0]
    manifest["version"] = version
    changed = cache._publish(canonical_json_bytes(manifest), "json")["sha256"]
    with pytest.raises(UpdateError, match="PRODUCT_CACHE_INTEGRITY_FAILED"):
        cache.read(changed)


@pytest.mark.parametrize("version", ["product-baostock-raw-v1", "product-baostock-raw-v2"])
def test_empty_suspended_turnover_respects_saved_parser_version(tmp_path, version):
    cache, _ = cache_and_manager(tmp_path)
    raw, _, evidence = receipt_payload()
    raw["rows"][0][7:9] = ["", ""]
    raw["rows"][0][10] = "0"
    rows = parse_response(raw, SID, DAY, DAY)
    evidence.update(
        parser_version=version,
        raw_response_sha256=canonical_sha256(raw),
        logical_rows_sha256=canonical_sha256({"rows": rows}),
    )
    digest = cache.publish(raw, rows, evidence)
    if version.endswith("v1"):
        with pytest.raises(UpdateError, match="PRODUCT_CACHE_INTEGRITY_FAILED"):
            cache.read(digest)
    else:
        assert cache.read(digest)[1][0]["raw"]["volume"] == "0"
        assert cache.read(digest)[1][0]["status"] == "VENDOR_SUSPENDED"


@pytest.mark.parametrize("blank", [False, True])
async def test_pinned_legacy_label_is_readable_with_diagnostic_but_not_executable(
    tmp_path, monkeypatch, blank
):
    cache, manager = cache_and_manager(tmp_path)
    raw, _, evidence = receipt_payload()
    if blank:
        raw["rows"][0][7:9] = ["", ""]
        raw["rows"][0][10] = "0"
    rows = parse_response(raw, SID, DAY, DAY)
    evidence.update(
        parser_version="product-baostock-raw-v1",
        raw_response_sha256=canonical_sha256(raw),
        logical_rows_sha256=canonical_sha256({"rows": rows}),
    )
    digest = cache.publish(raw, rows, evidence)
    # Synthetic binding exercises the branch, not the real retained receipt pins.
    monkeypatch.setattr(
        cache_module, "LEGACY_PARSER_LABEL_RECEIPTS", {digest: evidence["job_id"]}, raising=False
    )
    before = {path.name: path.read_bytes() for path in cache.root.iterdir()}
    manifest, loaded = cache.read(digest)
    assert loaded == rows
    assert manifest["evidence"] == evidence
    assert "reader_diagnostics" not in manifest
    receipt = receipt_model(digest, evidence)
    assert await manager.verify_receipt(receipt, for_execution=False) == rows
    with pytest.raises(UpdateError, match="PRODUCT_RECEIPT_PARSER_LABEL_MISMATCH"):
        await manager.verify_receipt(receipt)
    assert {path.name: path.read_bytes() for path in cache.root.iterdir()} == before


def test_legacy_exception_requires_the_two_documented_manifest_and_job_pins():
    expected = {
        "e117d2f313ea1579351c235e44af81c99bb5ef46a3a627a0329505c4c4d1a893",
        "c12aa42bb94898921f64f4eba687687f17dc374cc06299c13965da2ad1cd82b4",
    }
    job = "ed796871-4ce4-4cf3-b7f0-2223e636bb75"
    bindings = cache_module.LEGACY_PARSER_LABEL_RECEIPTS
    assert bindings == dict.fromkeys(expected, job)
    evidence = {"parser_version": "product-baostock-raw-v1", "job_id": job}
    for digest in expected:
        assert cache_module.receipt_reader_diagnostics(digest, evidence) == [
            "PARSER_LABEL_MISMATCH_READ_ONLY"
        ]
        assert (
            cache_module.receipt_reader_diagnostics(digest, {**evidence, "job_id": "other"}) == []
        )
        assert (
            cache_module.receipt_reader_diagnostics(
                digest, {**evidence, "parser_version": PARSER_VERSION}
            )
            == []
        )
    assert cache_module.receipt_reader_diagnostics("0" * 64, evidence) == []


@pytest.mark.parametrize("change", ["receipt_id", "job_id", "requested_at_utc", "raw", "rows"])
def test_rehashed_or_repackaged_receipts_cannot_inherit_legacy_exception(
    tmp_path, monkeypatch, change
):
    cache, _ = cache_and_manager(tmp_path)
    raw, _, evidence = receipt_payload()
    raw["rows"][0][7:9] = ["", ""]
    raw["rows"][0][10] = "0"
    rows = parse_response(raw, SID, DAY, DAY)
    evidence.update(
        parser_version="product-baostock-raw-v1",
        raw_response_sha256=canonical_sha256(raw),
        logical_rows_sha256=canonical_sha256({"rows": rows}),
    )
    original = cache.publish(raw, rows, evidence)
    monkeypatch.setattr(
        cache_module, "LEGACY_PARSER_LABEL_RECEIPTS", {original: evidence["job_id"]}
    )
    assert cache.read(original)[1] == rows
    if change == "raw":
        raw["rows"][0][5] = "10.6"
        rows = parse_response(raw, SID, DAY, DAY)
    elif change == "rows":
        rows[0]["raw"]["close"] = "10.6"
    elif change == "requested_at_utc":
        evidence[change] = "2026-09-18T09:59:57+00:00"
    else:
        evidence[change] = "f67cdfa5-8e10-43c4-885e-8c2b7525ba0b"
    evidence.update(
        raw_response_sha256=canonical_sha256(raw),
        logical_rows_sha256=canonical_sha256({"rows": rows}),
    )
    changed = cache.publish(raw, rows, evidence)
    assert changed != original
    with pytest.raises(UpdateError, match="PRODUCT_CACHE_INTEGRITY_FAILED"):
        cache.read(changed)
    # Merely naming a modified manifest after the approved digest also fails.
    (cache.root / f"{original}.json").write_bytes((cache.root / f"{changed}.json").read_bytes())
    with pytest.raises(UpdateError, match="PRODUCT_CACHE_INTEGRITY_FAILED"):
        cache.read(original)


async def test_actual_read_routes_expose_legacy_diagnostic_without_mutating_evidence(
    tmp_path, monkeypatch
):
    cache, manager = cache_and_manager(tmp_path)
    raw, rows, evidence = receipt_payload()
    evidence["parser_version"] = "product-baostock-raw-v1"
    digest = cache.publish(raw, rows, evidence)
    monkeypatch.setattr(cache_module, "LEGACY_PARSER_LABEL_RECEIPTS", {digest: evidence["job_id"]})
    receipt = receipt_model(digest, evidence)
    observation = MarketObservationModel(
        provider=PROVIDER,
        security_id=SID,
        trading_date=DAY,
        receipt_id=receipt.id,
        payload=deepcopy(rows[0]),
    )
    before = {path.name: path.read_bytes() for path in cache.root.iterdir()}
    original_evidence, original_payload = deepcopy(receipt.evidence), deepcopy(observation.payload)
    database = SimpleNamespace(
        get=AsyncMock(return_value=SimpleNamespace(id=receipt.job_id)),
        scalar=AsyncMock(return_value=1),
        scalars=AsyncMock(side_effect=[[receipt], [observation], [receipt]]),
    )

    @asynccontextmanager
    async def factory():
        yield database

    manager.factory = factory
    monkeypatch.setattr(routes, "market_update_manager", manager)
    app = FastAPI()
    app.include_router(routes.router, prefix="/api")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        receipt_response = await client.get(f"/api/market-updates/{receipt.job_id}/receipts")
        observation_response = await client.get(
            "/api/market-updates/observations",
            params={"security_id": SID, "start_date": DAY.isoformat(), "end_date": DAY.isoformat()},
        )
    for response in (receipt_response, observation_response):
        assert response.status_code == 200
        assert response.json()["items"][0]["reader_diagnostics"] == [
            "PARSER_LABEL_MISMATCH_READ_ONLY"
        ]
    assert receipt_response.json()["items"][0]["parser_version"] == "product-baostock-raw-v1"
    assert observation_response.json()["items"][0]["execution_eligible"] is False
    assert receipt.evidence == original_evidence
    assert observation.payload == original_payload
    assert {path.name: path.read_bytes() for path in cache.root.iterdir()} == before


def test_pending_recovery_rejects_rehashed_misinterpretation_before_link(tmp_path):
    cache, _ = cache_and_manager(tmp_path)
    raw, rows, evidence = receipt_payload()
    rows[0]["raw"]["close"] = "10.6"
    evidence["logical_rows_sha256"] = canonical_sha256({"rows": rows})
    journal = cache.journal({"raw": raw, "rows": rows, "evidence": evidence})
    before = (cache.root / journal).read_bytes()
    with pytest.raises(UpdateError, match="PRODUCT_CACHE_INTEGRITY_FAILED"):
        cache.pending()
    assert (cache.root / journal).read_bytes() == before


@pytest.mark.parametrize("member", ["raw", "rows"])
def test_parsing_consumes_exact_verified_bytes_not_reopened_paths(tmp_path, monkeypatch, member):
    cache, _ = cache_and_manager(tmp_path)
    raw, rows, evidence = receipt_payload()
    digest = cache.publish(raw, rows, evidence)
    manifest = cache.read(digest)[0]
    target = cache.root / manifest[member]["path"]
    original = cache_module.verified_file_bytes
    reads = []

    def swap_after_read(path, expected):
        content = original(path, expected)
        reads.append(path)
        if path == target:
            path.write_bytes(b"changed after verified read in isolated test cache")
        return content

    monkeypatch.setattr(cache_module, "verified_file_bytes", swap_after_read)
    assert cache.read(digest)[1] == rows
    assert reads.count(target) == 1
    with pytest.raises(UpdateError, match="PRODUCT_CACHE_INTEGRITY_FAILED"):
        cache.read(digest)


@pytest.mark.parametrize("corruption", ["bundle_rows", "db_observation"])
async def test_actual_observation_route_rejects_unreproduced_rows_without_database(
    tmp_path, monkeypatch, corruption
):
    cache, manager = cache_and_manager(tmp_path)
    raw, rows, evidence = receipt_payload()
    database_row = deepcopy(rows[0])
    database_row["raw"]["close"] = "10.6"
    if corruption == "bundle_rows":
        rows = [database_row]
        evidence["logical_rows_sha256"] = canonical_sha256({"rows": rows})
    digest = cache.publish(raw, rows, evidence)
    receipt = receipt_model(digest, evidence)
    observation = MarketObservationModel(
        provider=PROVIDER,
        security_id=SID,
        trading_date=DAY,
        receipt_id=receipt.id,
        payload=database_row,
    )
    # Only persistence query results are substituted; actual route, manager,
    # immutable cache, raw parser and DB-payload comparison all execute.
    database = SimpleNamespace(scalars=AsyncMock(side_effect=[[observation], [receipt]]))

    @asynccontextmanager
    async def factory():
        yield database

    manager.factory = factory
    monkeypatch.setattr(routes, "market_update_manager", manager)
    app = FastAPI()
    app.include_router(routes.router, prefix="/api")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get(
            "/api/market-updates/observations",
            params={"security_id": SID, "start_date": DAY.isoformat(), "end_date": DAY.isoformat()},
        )
    assert response.status_code == 422
    assert response.json()["code"] == "PRODUCT_CACHE_INTEGRITY_FAILED"
    assert database.scalars.await_count == 2
