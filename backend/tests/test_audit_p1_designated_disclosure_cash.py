"""The newspaper page must never merge a neighboring issuer's terms."""

import pytest

from scripts.audit_p1_designated_disclosure_cash import issuer_block


def test_issuer_block_is_bounded_by_next_security():
    text = (
        "证券代码:600761每股现金红利0.30元"
        "证券代码:600337证券简称:美克股份编号:临2011-022"
        "美克国际家具股份有限公司2010年度利润分配实施公告"
        "2010年度不进行公积金转增股本"
        "美克国际家具股份有限公司董事会"
        "证券代码:002079每股现金红利9.99元"
    )
    assert "0.30" not in issuer_block(text)
    assert "9.99" not in issuer_block(text)
    with pytest.raises(ValueError, match="ISSUER_PAGE_BOUNDARY_NOT_UNIQUE"):
        issuer_block(text.replace("证券代码:002079", "证券代码:600337"))
