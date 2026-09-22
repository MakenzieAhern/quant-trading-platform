import pytest

from scripts.close_p1_bonus_policy_facts import close, close_differentiated


def row():
    return {
        "document_id": "OFFICIAL_DOCUMENT:abc",
        "affected_events": ["CNINFO:1"],
        "security_id": "CN-A:SSE:688339",
        "record_date": "2024-07-19",
        "ex_date": "2024-07-22",
        "bonus_ratio": "0.4",
        "source_sha256": "a" * 64,
        "exchange_evidence_sha256": "b" * 64,
        "candidate_class": "BONUS_ONLY",
        "classification": "EXACT_OFFICIAL_BONUS_SOURCE_TERMS_ACCOUNTING_PENDING",
    }


def test_close_requires_exact_bonus_only_source_fact():
    result = close([row()])
    assert result[0]["classification"] == "EXACT_OFFICIAL_BONUS_SOURCE_FACT_POLICY_CLOSED"
    assert result[0]["tradability_authority_scope"] == "SEPARATE_FULL_DATASET_GATE"
    with pytest.raises(ValueError, match="P1_BONUS_FACT_NOT_CLOSABLE"):
        close([{**row(), "candidate_class": "BOTH"}])


def test_differentiated_bonus_accepts_direct_or_corroborated_zero_cash():
    direct = {
        **row(),
        "status": "EXPLICIT_ZERO_CASH_BONUS_SOURCE_TERMS_ACCOUNTING_PENDING",
        "cash_explicitly_zero": True,
        "action_type": "CAPITAL_RESERVE_CONVERSION",
    }
    direct.pop("affected_events")
    direct.pop("candidate_class")
    direct.pop("classification")
    requirement = {"document_id": "OFFICIAL_DOCUMENT:abc", "affected_events": ["CNINFO:1"]}
    assert close_differentiated([direct], [], [requirement])[0]["affected_events"] == ["CNINFO:1"]
    indirect = {
        **direct,
        "status": "CASH_OR_IDENTITY_NOT_CLOSED",
        "cash_explicitly_zero": False,
    }
    corroboration = {
        **{
            key: indirect[key]
            for key in ("document_id", "security_id", "record_date", "ex_date", "bonus_ratio")
        },
        "classification": "OFFICIAL_ZERO_CASH_CORROBORATED_ACCOUNTING_PENDING",
    }
    assert close_differentiated([indirect], [corroboration], [requirement])
