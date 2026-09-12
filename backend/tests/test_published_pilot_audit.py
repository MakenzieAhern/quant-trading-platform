from copy import deepcopy
from datetime import date

import pytest

from app.domain.markets.cn_a_rules import historical_cn_a_rules
from scripts.audit_published_pilot import audit_security, check_rule_resolution


def test_security_audit_rejects_future_bars_adjusted_execution_and_inferred_status():
    sid = "CN-A:SSE:123456"
    member = dict(security_id=sid, listing_date="2023-01-03", delisting_date="2023-01-05")
    sessions = ["2023-01-03", "2023-01-04", "2023-01-05"]
    bars = [
        dict(
            security_id=sid,
            trading_date="2023-01-03",
            raw_open="10",
            raw_high="11",
            raw_low="9",
            raw_close="10",
            volume="100",
            amount="1000",
            adjusted_close=None,
        )
    ]
    factors = [
        dict(security_id=sid, effective_from="2023-01-03", hfq_factor="2"),
        dict(security_id=sid, effective_from="2023-01-04", hfq_factor="3"),
    ]
    states = [
        dict(
            security_id=sid,
            trading_date=d,
            risk_status="ST",
            is_st="1",
            is_star_st="0",
            bar_observed=str(int(d == "2023-01-03")),
            is_suspended=None,
            is_tradeable=None,
            execution_state="NO_FILL_UNLESS_SEPARATE_OFFICIAL_TRADEABILITY_EVIDENCE",
        )
        for d in sessions[:2]
    ]
    result = audit_security(member, bars, factors, states, sessions, lambda *_: "ST")
    assert result["bars"] == 1 and result["lifecycle_sessions"] == 2
    assert result["gaps"] == [
        dict(effective_from="2023-01-04", effective_to="2023-01-04", sessions=1)
    ]
    for field, value, error in (
        ("is_suspended", "0", "INFERRED_TRADEABILITY"),
        ("risk_status", "NORMAL", "ST_IDENTITY_OR_REPLAY"),
    ):
        changed = deepcopy(states)
        changed[0][field] = value
        with pytest.raises(ValueError, match=error):
            audit_security(member, bars, factors, changed, sessions, lambda *_: "ST")
    with pytest.raises(ValueError, match="RAW_ADJUSTED_MIX"):
        audit_security(
            member,
            [{**bars[0], "adjusted_close": "20"}],
            factors,
            states,
            sessions,
            lambda *_: "ST",
        )
    with pytest.raises(ValueError, match="OUT_OF_LIFECYCLE"):
        audit_security(
            member,
            [{**bars[0], "trading_date": "2023-01-05"}],
            factors,
            states,
            sessions,
            lambda *_: "ST",
        )


def test_rule_audit_checks_publication_dates_and_original_listing_age():
    version = historical_cn_a_rules()
    member = dict(
        security_id="CN-A:SZSE:123456",
        exchange="SZSE",
        board="SZSE_MAIN",
        listing_date="2023-04-10",
        delisting_date="",
    )
    sessions = ["2023-04-10", "2023-04-11"]
    assert check_rule_resolution(version, [member], sessions, sessions, lambda *_: "ST") == 2
    future = version.model_copy(
        update={
            "rules": tuple(
                r.model_copy(update={"source_publication_date": date(2025, 1, 1)})
                for r in version.rules
            )
        }
    )
    with pytest.raises(ValueError, match="FUTURE_RULE_LEAKAGE"):
        check_rule_resolution(future, [member], sessions, sessions, lambda *_: "ST")
