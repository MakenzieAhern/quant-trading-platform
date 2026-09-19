import pytest

from scripts.audit_szse_fee_yearbooks import validate_page_text


def test_validate_page_text_binds_effective_boundary() -> None:
    text = "A股 按成交额双边收取0.0341‰ 自2023年8月28日起 由0.0487‰下调 监管费0.02‰"

    assert len(validate_page_text(2025, text)) == 64

    with pytest.raises(ValueError, match="FEE_TABLE_TOKENS_MISSING"):
        validate_page_text(2025, text.replace("2023年8月28日", "2023年8月29日"))
