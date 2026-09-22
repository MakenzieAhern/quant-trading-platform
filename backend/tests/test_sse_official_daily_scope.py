import pytest

from scripts.audit_sse_official_daily_scope import within_interval


def test_sse_source_bars_follow_accepted_symbol_interval():
    row = {"symbol": "600849", "effective_from": "1994-03-24", "effective_to": "2010-03-04"}
    sessions = {"2010-03-03", "2010-03-09"}
    bar = [20100309, 16.2, 16.2, 15.65, 16.2, 93775802, 1509577609]
    assert within_interval(bar, row, sessions) is False
    bar[0] = 20100303
    assert within_interval(bar, row, sessions) is True
    successor = {"symbol": "601607", "effective_from": "2010-03-05", "effective_to": None}
    assert within_interval(bar, successor, sessions) is False
    bar[0] = 20100309
    assert within_interval(bar, successor, sessions) is True
    bar[2] = 15.5
    with pytest.raises(ValueError, match="INVALID_OHLCV"):
        within_interval(bar, row, sessions)
