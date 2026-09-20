import hashlib
import json
from pathlib import Path

from app.data.catalog.normalized import _logical_hash
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
