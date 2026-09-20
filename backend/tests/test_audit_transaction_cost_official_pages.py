from hashlib import sha256

import pytest

from scripts.audit_transaction_cost_official_pages import SOURCES, validate_source, validate_tokens


def test_validate_tokens_fails_closed() -> None:
    validate_tokens("2012年1月1日起0.04‰调整为0.02‰", ("2012年1月1日起", "0.02‰"))

    with pytest.raises(ValueError, match="OFFICIAL_SOURCE_TOKENS_MISSING"):
        validate_tokens("2012年1月2日起0.02‰", ("2012年1月1日起",))


def test_validate_source_accepts_checksum_bound_visual_pdf(tmp_path) -> None:
    payload = b"%PDF-visual-review-fixture"
    (tmp_path / "notice.pdf").write_bytes(payload)

    validate_source(
        tmp_path,
        {"file": "notice.pdf", "sha256": sha256(payload).hexdigest()},
    )


def test_commission_scope_is_routed_to_account_evidence() -> None:
    source = next(item for item in SOURCES if item["file"].startswith("csrc-guangdong"))
    assert "净佣金" in "".join(source["tokens"])
    assert "全佣金" in "".join(source["tokens"])
