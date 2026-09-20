from datetime import date
from types import SimpleNamespace

from scripts.run_research import _raw_paths, stable_result


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
