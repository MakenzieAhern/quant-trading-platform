import json
from datetime import UTC, date, datetime

import pytest
from httpx import ASGITransport, AsyncClient

from app.api.routes import markets
from app.application.experiments.data import (
    DEMO_ID,
    HISTORICAL_ID,
    ExperimentDatasetRegistry,
    ExperimentInputError,
)
from app.application.markets import MarketReader
from app.data.catalog import write_manifest
from app.data.catalog.checksums import canonical_sha256
from app.data.catalog.manifest import finalize_manifest
from app.data.catalog.normalized import write_canonical_parquet
from app.main import app

SID = "CN-A:SSE:600000"


@pytest.fixture
def archive(tmp_path):
    root = tmp_path / HISTORICAL_ID
    master = {
        "security_id": SID,
        "symbol": "600000",
        "exchange": "SSE",
        "board": "SSE_MAIN",
        "name": None,
        "source_observed_name": "测试银行",
        "name_temporal_authority": "SOURCE_OBSERVED_NOT_BACKDATED",
        "instrument_type": "COMMON_A_SHARE",
        "effective_from": "2029-01-01",
        "effective_to": "2030-01-08",
    }
    raw = {
        "security_id": SID,
        "trading_date": "2030-01-02",
        "raw_open": "10.123456789123456789",
        "raw_high": "11",
        "raw_low": "9",
        "raw_close": "10.5",
        "volume": "123456789123456789",
        "amount": "987654321.123456789",
        "risk_status": "NORMAL",
        "source_lineage": "TEST_ONLY_OFFICIAL_STYLE",
    }
    factor = {
        "security_id": SID,
        "effective_date": "2029-12-31",
        "hfq_factor": "1.5",
        "interval_from": "2030-01-01",
        "interval_to": "2030-12-31",
        "lineage": "TEST_EFFECTIVE_FACTOR",
    }
    tables = {
        "securities.parquet": [
            master,
            {
                **master,
                "security_id": "CN-A:SSE:600001",
                "symbol": "600001",
                "effective_from": "2030-02-01",
                "effective_to": None,
            },
        ],
        "calendar.parquet": [
            {"session_date": day, "is_open": day != "2030-01-04"}
            for day in (
                "2030-01-02",
                "2030-01-03",
                "2030-01-04",
                "2030-01-06",
                "2030-01-07",
                "2030-01-08",
                "2030-01-09",
            )
        ],
        "raw/SSE/2030-01.parquet": [
            raw,
            {**raw, "trading_date": "2030-01-06", "risk_status": "ST"},
            {**raw, "security_id": "CN-A:SSE:600001"},
        ],
        "raw/SSE/2010-01.parquet": [{**raw, "trading_date": "2010-01-02"}],
        "raw/SZSE/2030-01.parquet": [{**raw, "security_id": "CN-A:SZSE:000001"}],
        "adjustment-factors.parquet": [
            factor,
            {**factor, "effective_date": "2030-01-06", "hfq_factor": "2"},
            {**factor, "effective_date": "2030-02-01", "hfq_factor": "99"},
        ],
        "feature-only-observations.parquet": [
            {
                "security_id": SID,
                "trading_date": "2030-01-07",
                "raw_close": "10.6",
                "risk_status": "ST",
                "lineage": "PARTIAL_NON_TRADABLE",
            }
        ],
        "suspension-events.parquet": [
            {
                "security_id": SID,
                "suspended_at": "2030-01-03",
                "resumed_or_ended_at": "2030-01-06",
                "execution_open_blocked": "1",
            }
        ],
    }
    parts = []
    for name, rows in sorted(tables.items()):
        part = write_canonical_parquet(
            root / name, fieldnames=tuple(rows[0]), rows=rows, sort_keys=tuple(rows[0])[:1]
        )
        parts.append(part.model_copy(update={"relative_path": name}))
    manifest = finalize_manifest(
        {
            "dataset_id": HISTORICAL_ID,
            "provider": "TEST_FIXTURE",
            "provider_version": "test-v1",
            "retrieval_timestamp": datetime(2031, 1, 1, tzinfo=UTC),
            "coverage_start": "2030-01-01",
            "coverage_end": "2030-12-31",
            "security_count": 2,
            "symbols": ["600000", "600001"],
            "exchanges": ["SSE"],
            "fields": [],
            "adjustment_method": "TEST_HFQ",
            "rule_version": "TEST_RULES",
            "source_lineage": ["TEST_ONLY"],
            "partitions": parts,
        }
    )
    write_manifest(root / "manifest.json", manifest)
    freeze = {"dataset_manifest_sha256": manifest.canonical_sha256}
    freeze["freeze_record_sha256"] = canonical_sha256(freeze)
    (root / ".freeze.json").write_text(json.dumps(freeze))
    return MarketReader(ExperimentDatasetRegistry(tmp_path))


def test_archive_bounded_partition_reads_factors_dates_gaps_and_provenance(archive, monkeypatch):
    read = markets.market_reader  # The real configured reader is never used by this fixture.
    assert archive is not read
    from app.application import markets as module

    actual = module.pq.read_table
    reads = []

    def tracked(path, **kwargs):
        reads.append((str(path), kwargs))
        return actual(path, **kwargs)

    monkeypatch.setattr(module.pq, "read_table", tracked)
    result = archive.bars(HISTORICAL_ID, SID, date(2030, 1, 2), date(2030, 1, 9))
    assert [r["status"] for r in result["items"]] == [
        "OBSERVED",
        "SUSPENDED",
        "OBSERVED",
        "FEATURE_ONLY",
        "MISSING_OBSERVATION",
        "OUTSIDE_LISTING",
    ]
    first, suspended, resumed, feature, missing, outside = result["items"]
    assert first["raw"]["open"] == "10.123456789123456789"
    assert first["adjusted"]["open"] == "15.1851851836851851835"
    assert first["adjustment_effective_date"] == "2029-12-31"
    assert resumed["adjustment_factor"] == "2" and resumed["adjusted"]["close"] == "21"
    assert resumed["risk_status"] == "ST" and not resumed["execution_open_blocked"]
    assert suspended["raw"]["close"] is None and suspended["execution_open_blocked"]
    assert feature["raw"]["open"] is None and feature["adjusted"]["close"] == "21.2"
    assert missing["raw"]["close"] is None and missing["risk_status"] is None
    assert outside["raw"]["close"] is None
    assert result["metadata"]["is_live"] is False
    assert result["metadata"]["provider"] == "TEST_FIXTURE"
    assert result["metadata"]["retrieved_at_utc"] == "2031-01-01T00:00:00+00:00"
    assert result["metadata"]["status_counts"]["MISSING_OBSERVATION"] == 1
    assert all("2010-01" not in path and "/SZSE/" not in path for path, _ in reads)
    for path, kwargs in reads:
        if "/raw/" in path:
            assert ("security_id", "=", SID) in kwargs["filters"]
            assert ("trading_date", ">=", "2030-01-02") in kwargs["filters"]
    assert all(len(p["sha256"]) == 64 for p in result["metadata"]["partitions"])


def test_security_search_observed_names_delisted_retained_and_cache_validation(archive):
    found = archive.search(HISTORICAL_ID, "测试", "SSE", 1, 0)
    assert found["total"] == 2 and len(found["items"]) == 1
    assert found["items"][0]["security_id"] == SID
    assert found["items"][0]["name"] is None
    assert found["items"][0]["listed_to"] == "2030-01-08"
    assert archive.search(HISTORICAL_ID, "600001", "ALL", 20, 0)["total"] == 1
    assert archive.search(HISTORICAL_ID, "", "SZSE", 20, 0)["total"] == 0
    assert archive.search(HISTORICAL_ID, "", "SSE", 1, 1)["items"][0]["symbol"] == "600001"
    # Tampering only with a disposable test fixture invalidates the cached verified file.
    path = archive.registry.root / HISTORICAL_ID / "securities.parquet"
    path.write_bytes(path.read_bytes() + b"changed")
    with pytest.raises(ExperimentInputError, match="DATASET_INTEGRITY_FAILED"):
        archive.search(HISTORICAL_ID, "", "ALL", 20, 0)


def test_touched_partition_integrity_and_untouched_partition_not_loaded(archive):
    root = archive.registry.root / HISTORICAL_ID
    (root / "raw/SSE/2010-01.parquet").write_bytes(b"unrelated fixture deliberately unreadable")
    assert archive.bars(HISTORICAL_ID, SID, date(2030, 1, 2), date(2030, 1, 2))["total"] == 1
    touched = root / "raw/SSE/2030-01.parquet"
    touched.write_bytes(touched.read_bytes() + b"bad")
    with pytest.raises(ExperimentInputError, match="DATASET_INTEGRITY_FAILED"):
        archive.bars(HISTORICAL_ID, SID, date(2030, 1, 2), date(2030, 1, 2))


def test_clean_install_demo_is_real_bounded_synthetic_data(tmp_path):
    reader = MarketReader(ExperimentDatasetRegistry(tmp_path))
    assert reader.registry.datasets()[0]["available"] is False
    with pytest.raises(ExperimentInputError, match="DATASET_NOT_MOUNTED"):
        reader.search(HISTORICAL_ID, "", "ALL", 20, 0)
    result = reader.bars(DEMO_ID, SID, date(2030, 1, 2), date(2030, 1, 10))
    assert result["items"] and result["metadata"]["mode"] == "synthetic_demo"
    assert "SYNTHETIC_DEMO_NOT_MARKET_OR_RESEARCH_EVIDENCE" in result["metadata"]["limitations"]
    assert result["items"][0]["raw"]["close"] == result["items"][0]["adjusted"]["close"]
    assert reader.bars(DEMO_ID, SID, date(2030, 1, 5), date(2030, 1, 6))["items"] == []


async def test_market_api_rejects_unbounded_unknown_and_malformed_inputs(tmp_path, monkeypatch):
    monkeypatch.setattr(markets, "market_reader", MarketReader(ExperimentDatasetRegistry(tmp_path)))
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/markets/datasets")
        assert response.status_code == 200 and response.json()[0]["available"] is False
        query = {"dataset_id": DEMO_ID}
        for extra in (
            {"limit": 51},
            {"offset": -1},
            {"q": "x" * 81},
            {"exchange": "NYSE"},
            {"dataset_id": "../../data"},
        ):
            assert (
                await client.get("/api/markets/securities", params={**query, **extra})
            ).status_code == 422
        assert (
            await client.get("/api/markets/securities", params={"dataset_id": HISTORICAL_ID})
        ).json()["code"] == "DATASET_NOT_MOUNTED"
        path = f"/api/markets/securities/{SID}/bars"
        for start, end in (
            ("2030-01-02", "2031-01-04"),
            ("2030-02-02", "2030-01-02"),
            ("2029-01-02", "2029-01-03"),
        ):
            assert (
                await client.get(path, params={**query, "start_date": start, "end_date": end})
            ).status_code == 422
        assert (await client.get(path, params=query)).status_code == 422
        assert (
            await client.get(
                path.replace("600000", "600999"),
                params={**query, "start_date": "2030-01-02", "end_date": "2030-01-02"},
            )
        ).status_code == 404


def test_missing_adjustment_is_unknown_and_not_a_fabricated_identity_factor(archive, monkeypatch):
    read = archive._read

    def missing_factor(manifest, relative, **kwargs):
        return (
            [] if relative == "adjustment-factors.parquet" else read(manifest, relative, **kwargs)
        )

    monkeypatch.setattr(archive, "_read", missing_factor)
    result = archive.bars(HISTORICAL_ID, SID, date(2030, 1, 2), date(2030, 1, 2))
    item = result["items"][0]
    assert item["raw"]["close"] == "10.5"
    assert item["adjusted"]["close"] is item["adjustment_factor"] is None
    assert result["metadata"]["adjustment_missing_observations"] == 1


@pytest.mark.parametrize(
    "start,end,exchange,recorded,day,blocked,active",
    [
        ("2010/03/01 09:30", "2010-03-02", "SZSE", "1", "2010-03-01", True, True),
        ("2010/03/01 09:30", "2010-03-02", "SZSE", "1", "2010-03-02", True, True),
        ("2010/06/17 09:30", "2010/06/18 09:30", "SZSE", None, "2010-06-18", False, False),
        ("2010/06/17 09:30", "2010/06/18 13:00", "SZSE", None, "2010-06-18", True, True),
        ("2010/06/17 09:30", "2010-06-18", "SZSE", None, "2010-06-18", None, False),
        ("2012/07/02 即时", "2012-07-03", "SZSE", "0", "2012-07-02", None, True),
        ("2015/07/06 盘中即时", None, "SZSE", "1", "2015-07-06", None, True),
        ("2010-03-30", "2010-03-30", "SSE", "1", "2010-03-30", True, True),
        ("2010-03-29", "2010-03-30", "SSE", "1", "2010-03-30", None, False),
    ],
)
def test_suspension_raw_boundary_formats_preserve_distinct_exchange_semantics(
    start,
    end,
    exchange,
    recorded,
    day,
    blocked,
    active,
):
    from app.application.markets import _suspension_evidence

    source = {
        "security_id": f"CN-A:{exchange}:000001",
        "exchange": exchange,
        "suspended_at": start,
        "resumed_or_ended_at": end,
        "execution_open_blocked": recorded,
        "closure": "OFFICIAL_RESUMPTION" if exchange == "SZSE" else None,
        "source_files_json": '["test-source"]',
        "source_sha256_json": '["test-sha"]',
    }
    result = _suspension_evidence(source, day)
    assert result["day_open_blocked"] is blocked
    assert result["suspension_confirmed_on_day"] is active
    assert result["suspended_at"] == start and result["resumed_or_ended_at"] == end
    assert result["source_sha256_json"] == source["source_sha256_json"]


def test_same_day_sse_halt_is_not_a_missing_observation(archive, monkeypatch):
    read = archive._read

    def same_day(manifest, relative, **kwargs):
        rows = read(manifest, relative, **kwargs)
        return (
            [{**r, "resumed_or_ended_at": r["suspended_at"]} for r in rows]
            if relative == "suspension-events.parquet"
            else rows
        )

    monkeypatch.setattr(archive, "_read", same_day)
    item = archive.bars(HISTORICAL_ID, SID, date(2030, 1, 3), date(2030, 1, 3))["items"][0]
    assert item["status"] == "SUSPENDED"
    assert item["execution_open_blocked"] is True
    assert item["source_lineage"] == "OFFICIAL_SUSPENSION_EVIDENCE"
    assert item["suspension_evidence"][0]["boundary_semantics"] == "SUSPENSION_START_DAY"


def test_szse_zero_volume_carry_has_suspension_status_without_losing_raw_data(archive, monkeypatch):
    read = archive._read
    master = archive._master
    sid = "CN-A:SZSE:000001"

    def master_szse(manifest):
        return [{**master(manifest)[0], "security_id": sid, "exchange": "SZSE", "symbol": "000001"}]

    def zero_carry(manifest, relative, **kwargs):
        if relative == "suspension-events.parquet":
            assert kwargs["filters"] == [("security_id", "=", sid)]
            return [
                {
                    "security_id": sid,
                    "exchange": "SZSE",
                    "suspended_at": "2030/01/02 09:30",
                    "resumed_or_ended_at": "2030-01-03",
                    "execution_open_blocked": "1",
                    "closure": "OFFICIAL_DAILY_TRADE_OBSERVATION_CONSERVATIVE_BOUNDARY",
                }
            ]
        rows = read(manifest, relative, **kwargs)
        return (
            [{**r, "volume": "0", "amount": "0"} for r in rows]
            if relative.startswith("raw/")
            else rows
        )

    monkeypatch.setattr(archive, "_master", master_szse)
    monkeypatch.setattr(archive, "_read", zero_carry)
    item = archive.bars(HISTORICAL_ID, sid, date(2030, 1, 2), date(2030, 1, 2))["items"][0]
    assert item["status"] == "SUSPENDED" and item["execution_open_blocked"] is True
    assert item["raw"]["close"] == "10.5" and item["raw"]["volume"] == "0"
