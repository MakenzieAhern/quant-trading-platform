import pytest

from scripts.audit_full_cash_ledger import merge_events, security_at


def row(amount, source="old", title="权益分派实施公告"):
    return {
        "event": {
            "security_id": {"value": "CN-A:SSE:600000"},
            "action_type": "CASH_DIVIDEND",
            "record_date": "2020-01-02",
            "ex_date": "2020-01-03",
            "cash_per_share": amount,
            "source_url": source,
            "source_document": title,
        }
    }


def test_merge_events_preserves_baseline_and_rejects_economic_conflict():
    baseline = row("0.10")
    same = row("0.100", "new")
    assert merge_events([baseline], [[same]]) == [baseline]
    assert merge_events([baseline], [[same]]) == merge_events([baseline], [[same], []])
    with pytest.raises(ValueError, match="CONFLICTING_ACCEPTED_CASH_EVENT"):
        merge_events([baseline], [[row("0.11", "conflict")]])


def test_merge_events_replaces_obsolete_price_adjustment_notice():
    obsolete = row("0.20", title="关于利润分配实施后调整可转债转股价格的公告")
    implementation = row("0.1999996")
    assert merge_events([obsolete], [[implementation]]) == [implementation]


def test_security_at_uses_stable_id_for_backfilled_current_symbol():
    master = [
        {
            "security_id": "CN-A:SSE:601360",
            "symbol": "601313",
            "instrument_type": "COMMON_A_SHARE",
            "effective_from": "2012-01-16",
            "effective_to": "2018-02-22",
        }
    ]
    assert (
        security_at(
            master,
            {"CN-A:SSE:601360": "COMMON_A_SHARE"},
            "SSE",
            "601360",
            "2012-04-23",
            "2012-04-24",
        )
        == "CN-A:SSE:601360"
    )
    assert (
        security_at([], {"CN-A:SSE:689009": "CDR"}, "SSE", "689009", "2024-05-23", "2024-05-24")
        is None
    )
