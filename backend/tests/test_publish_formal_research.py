import pytest

from scripts.publish_formal_research import security_id


def test_trade_symbols_map_to_stable_security_ids() -> None:
    assert security_id("600000.SSE") == "CN-A:SSE:600000"
    assert security_id("000001.SZSE") == "CN-A:SZSE:000001"
    with pytest.raises(ValueError, match="INVALID_TRADE_SYMBOL"):
        security_id("BAD")
