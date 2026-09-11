import json
from decimal import Decimal

import pytest

from scripts.materialize_akshare_partitions import materialize, normalized_bars
from scripts.reconcile_sse_cninfo import save, sha
from scripts.stage_akshare_pilot import pilot_members, raw_url, snapshot, stage_one


def test_raw_partition_is_unadjusted_decimal_order_independent_and_not_synthetic():
    member = dict(
        security_id="CN-A:SSE:600004", symbol="600004", listing_date="2000-01-01", delisting_date=""
    )
    lines = [
        "2023-01-03,10,10.5,11,9,123,12300,0,0,0,0",
        "2023-01-04,11,11,12,10,124,12400,0,0,0,0",
    ]

    def payload(rows):
        return json.dumps(dict(data=dict(code="600004", klines=rows))).encode()

    sessions = {"2023-01-03", "2023-01-04", "2023-01-05"}
    result = normalized_bars(payload(lines), member, sessions)
    assert result == normalized_bars(payload(list(reversed(lines))), member, sessions)
    assert result[0]["volume"] == Decimal(12300)
    assert result[0]["raw_close"] == Decimal("10.5")
    assert result[0]["adjusted_close"] is None
    assert len(result) == 2  # Missing Jan 5 is not synthesized or called suspended.
    with pytest.raises(ValueError, match="DUPLICATE"):
        normalized_bars(payload(lines + lines), member, sessions)
    member["delisting_date"] = "2023-01-04"
    with pytest.raises(ValueError, match="LIFECYCLE"):
        normalized_bars(payload(lines), member, sessions)


def test_failed_symbol_does_not_prevent_an_independent_symbol(tmp_path, monkeypatch):
    def response(root, name, url, round_no):
        if name == "600070.json":
            raise ConnectionError("closed before HTTP")
        if name.endswith(".json"):
            return root / name, b'{"data":{"code":"600004","klines":["2023-01-03,10,10,11,9,100"]}}'
        return root / name, b'var sh600004hfq={"total":1,"data":[{"d":"1900-01-01","f":"1"}]};'

    monkeypatch.setattr("scripts.stage_akshare_pilot.snapshot", response)
    row = dict(
        security_id="CN-A:SSE:600070",
        symbol="600070",
        exchange="SSE",
        listing_date="1997-06-04",
        delisting_date="2025-04-30",
    )
    assert stage_one(tmp_path, row, 0)["status"] == "PENDING_RETRY"
    assert stage_one(tmp_path, row, 2)["status"] == "UNRESOLVED_REQUIRED_DATA"
    row.update(security_id="CN-A:SSE:600004", symbol="600004")
    assert stage_one(tmp_path, row, 0)["status"] == "RECOVERED_PRIMARY"


def test_snapshot_preserves_failure_and_never_repeats_same_attempt(tmp_path, monkeypatch):
    calls = []

    def failed_fetch(root, name, url):
        root.mkdir(parents=True, exist_ok=True)
        (root / (name + ".meta.json")).write_text(
            json.dumps(dict(url=url, error="ConnectionError"))
        )
        calls.append(url)
        raise ConnectionError("closed")

    monkeypatch.setattr("scripts.stage_akshare_pilot.fetch", failed_fetch)
    url = raw_url("SSE", "600070")
    with pytest.raises(ConnectionError):
        snapshot(tmp_path, "600070.json", url, 0)
    with pytest.raises(RuntimeError, match="PERSISTED_ATTEMPT"):
        snapshot(tmp_path, "600070.json", url, 0)
    with pytest.raises(ConnectionError):
        snapshot(tmp_path, "600070.json", url, 1)
    assert calls == [url, url]
    assert (tmp_path / "recovery-attempts/0/600070.json.meta.json").exists()


def test_pilot_inventory_retains_delisted_and_rejects_future_ipo_and_mutation(tmp_path):
    root = tmp_path / "security-master-pilot"
    root.mkdir()
    raw = (
        b"security_id,listing_date,delisting_date\n"
        b"CN-A:SSE:600000,1999-01-01,\n"
        b"CN-A:SSE:600070,1997-01-01,2025-01-01\n"
        b"CN-A:SSE:688999,2024-08-01,\n"
        b"CN-A:SSE:600999,1990-01-01,2022-12-01\n"
    )
    path = root / "master.csv"
    path.write_bytes(raw)
    (root / "security-master-input.json").write_text(
        json.dumps(
            dict(
                complete=True,
                coverage_start="2023-01-01",
                coverage_end="2024-07-31",
                sources=[dict(filename="master.csv", sha256=sha(raw))],
            )
        )
    )
    assert [row["security_id"] for row in pilot_members(tmp_path)] == [
        "CN-A:SSE:600070",
        "CN-A:SSE:600000",
    ]
    path.write_bytes(raw + b"changed")
    with pytest.raises(ValueError, match="CHECKSUM_CHANGED"):
        pilot_members(tmp_path)
    assert "fqt=0&secid=1.600070" in raw_url("SSE", "600070")
    with pytest.raises(ValueError, match="INVALID_REQUEST_IDENTITY"):
        raw_url("OTHER", "600070")


def test_partial_partitions_resume_repeatably_and_reject_changed_bytes(tmp_path, monkeypatch):
    import pyarrow.parquet as parquet

    sid = "CN-A:SSE:600004"
    member = dict(
        security_id=sid,
        symbol="600004",
        exchange="SSE",
        listing_date="2000-01-01",
        delisting_date="",
    )
    monkeypatch.setattr("scripts.materialize_akshare_partitions.pilot_members", lambda _: [member])
    save(
        tmp_path / "sse-st-pilot/completeness-20260910/calendar/pilot-sessions.json", ["2023-01-03"]
    )
    raw = tmp_path / "raw.json"
    save(raw, dict(data=dict(code="600004", klines=["2023-01-03,10,10.5,11,9,123,12300,0,0,0,0"])))
    factor = tmp_path / "factor.js"
    factor.write_bytes(
        b'var sh600004hfq={"total":2,"data":'
        b'[{"d":"2000-01-01","f":"2"},{"d":"2025-01-01","f":"4"}]};'
    )
    root = tmp_path / "pilot-akshare-20260911"
    save(
        root / "recovery-checkpoint.json",
        dict(
            completed={
                sid: dict(
                    raw_path=raw.name,
                    raw_sha256=sha(raw.read_bytes()),
                    factor_path=factor.name,
                    factor_sha256=sha(factor.read_bytes()),
                )
            }
        ),
    )
    first = materialize(tmp_path)
    receipt = (root / "partition-checkpoint.json").read_bytes()
    assert first["securities_partitioned"] == 1 and not first["published"]
    assert materialize(tmp_path) == first
    assert (root / "partition-checkpoint.json").read_bytes() == receipt
    factors = root / "dataset-staging/SSE/600004/factors.parquet"
    rows = parquet.read_table(factors).to_pylist()
    assert [row["effective_from"] for row in rows] == ["2000-01-01"]
    # A lost receipt can be rebuilt without changing the physical partition hashes.
    (root / "partition-checkpoint.json").unlink()
    assert materialize(tmp_path) == first
    assert (root / "partition-checkpoint.json").read_bytes() == receipt
    factors.write_bytes(b"changed")
    with pytest.raises(ValueError, match="PARTITION_BYTES_CHANGED"):
        materialize(tmp_path)
