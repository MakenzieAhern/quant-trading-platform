import json

import pytest

from app.data.catalog.checksums import canonical_sha256
from scripts.publish_formal_research import load_result, security_id


def test_trade_symbols_map_to_stable_security_ids() -> None:
    assert security_id("600000.SSE") == "CN-A:SSE:600000"
    assert security_id("000001.SZSE") == "CN-A:SZSE:000001"
    with pytest.raises(ValueError, match="INVALID_TRADE_SYMBOL"):
        security_id("BAD")


def test_legacy_formal_result_gets_explicit_null_freeze_lineage(tmp_path) -> None:
    result = {"period_kind": "DEVELOPMENT"}
    result["result_sha256"] = canonical_sha256(result)
    (tmp_path / "result.json").write_text(json.dumps(result))
    (tmp_path / "receipt.json").write_text(
        json.dumps({"status": "PASS", "result_sha256": result["result_sha256"]})
    )

    loaded = load_result(tmp_path)

    assert loaded["candidate_freeze_sha256"] is None
    assert loaded["methodology_freeze_sha256"] is None
