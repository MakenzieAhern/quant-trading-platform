import pytest

from scripts.audit_transaction_cost_official_pages import validate_tokens


def test_validate_tokens_fails_closed() -> None:
    validate_tokens("2012年1月1日起0.04‰调整为0.02‰", ("2012年1月1日起", "0.02‰"))

    with pytest.raises(ValueError, match="OFFICIAL_SOURCE_TOKENS_MISSING"):
        validate_tokens("2012年1月2日起0.02‰", ("2012年1月1日起",))
