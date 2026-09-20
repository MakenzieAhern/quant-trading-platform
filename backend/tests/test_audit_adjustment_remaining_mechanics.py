from decimal import Decimal

import pytest

from scripts.audit_adjustment_remaining_mechanics import (
    reference_price_parity,
    verify_visual_date_review,
)


def test_reference_price_parity_uses_exchange_display_tick() -> None:
    result = reference_price_parity(Decimal("8.67"), Decimal("1.476"), Decimal("5.87"))

    assert result["status"] == "OFFICIAL_DECLARED_REFERENCE_DISPLAY_TICK_PARITY_PASS"


def test_visual_date_review_is_required(tmp_path) -> None:
    review = tmp_path / "review.json"
    review.write_text('{"scope":"DATE_COVERAGE_ONLY_NOT_ECONOMIC_TERMS_OR_ACCOUNTING","rows":[]}')

    with pytest.raises(ValueError, match="REQUIRED_VISUAL_DATE_REVIEW_MISSING"):
        verify_visual_date_review(review)
