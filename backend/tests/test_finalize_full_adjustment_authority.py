from decimal import Decimal

import pytest

from scripts.finalize_full_adjustment_authority import partition_factor_changes


def test_factor_partition_rejects_overlap_and_omission() -> None:
    universe = {"a", "b"}

    assert partition_factor_changes(universe, {"one": {"a"}, "two": {"b"}}) == [
        {"factor_change": "a", "classification": "one"},
        {"factor_change": "b", "classification": "two"},
    ]
    with pytest.raises(ValueError, match="DUPLICATE_FACTOR_CLASSIFICATION"):
        partition_factor_changes(universe, {"one": {"a"}, "two": {"a", "b"}})
    with pytest.raises(ValueError, match="FACTOR_PARTITION_MISMATCH"):
        partition_factor_changes(universe, {"one": {"a"}})


def test_cash_overlay_formula() -> None:
    from scripts.finalize_full_adjustment_authority import official_cash_overlay

    event = {
        "event_checksum": "ignored",
        "event": {
            "security_id": {"value": "CN-A:SSE:600000"},
            "action_type": "CASH_DIVIDEND",
            "ex_date": "2020-01-02",
            "cash_per_share": "1",
            "source_document": "notice",
            "source_url": "https://example.test/notice.pdf",
            "source_document_sha256": "a" * 64,
            "source_provider": "OFFICIAL_TEST",
            "source_version": "V1",
            "source_record_hash": "b" * 64,
            "completeness": "COMPLETE",
        },
    }
    from app.domain.markets.corporate_actions import CorporateAction

    event["event_checksum"] = CorporateAction.model_validate(event["event"]).event_checksum

    step = Decimal(official_cash_overlay(event, Decimal("10"))["factor_step"])
    assert abs(step - Decimal(10) / Decimal(9)) < Decimal("1e-27")
