import json
from datetime import date
from types import SimpleNamespace

import pytest

from app.data.catalog.checksums import canonical_sha256
from scripts.run_research import _raw_paths, load_candidate_freeze, stable_result


def test_development_partition_lock_never_selects_validation_or_oos() -> None:
    manifest = SimpleNamespace(
        partitions=tuple(
            SimpleNamespace(relative_path=f"raw/SSE/{year}-01.parquet")
            for year in range(2010, 2026)
        )
    )
    paths = _raw_paths(manifest, date(2017, 12, 31))
    assert paths[-1] == "raw/SSE/2017-01.parquet"
    assert all("/2018-" not in path and "/2022-" not in path for path in paths)


def test_stable_result_removes_random_order_identity() -> None:
    result = {"trades": [{"order_id": "random-a"}, {"order_id": "random-b"}]}
    assert stable_result(result) == {"trades": [{"sequence": 0}, {"sequence": 1}]}


def test_validation_rejects_changed_candidate_freeze(tmp_path) -> None:
    record = {
        "status": "FROZEN",
        "dataset_id": "cn-a-research-20100101-20251231-v1",
        "dataset_sha256": "dataset",
        "validation_period": {"start": "2018-01-01", "end": "2021-12-31"},
        "candidate_order": ["S0", "S1", "S2", "S3", "S4"],
        "selection_pool": ["S2", "S3", "S4"],
        "candidates": {
            "S2": {"strategy_id": "changed", "config": {"factor_names": ["MOM_12_1"]}},
            "S3": {
                "strategy_id": "cn_a_trend_low_vol_v1",
                "config": {"factor_names": ["TREND_120", "LOW_VOL"]},
            },
            "S4": {
                "strategy_id": "cn_a_cross_sectional_momentum_low_vol_v1",
                "config": {"factor_names": ["MOM_12_1", "TREND_120", "LOW_VOL"]},
            },
        },
    }
    record["freeze_record_sha256"] = canonical_sha256(record)
    path = tmp_path / "freeze.json"
    path.write_text(json.dumps(record))
    with pytest.raises(ValueError, match="CANDIDATE_FREEZE_CHANGED"):
        load_candidate_freeze(path, "dataset")
