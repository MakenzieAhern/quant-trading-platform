from datetime import date

from scripts.fetch_a_share_security_master import (
    FIELDS,
    _chinese_date,
    _delisting_date_from_text,
    _factbook_b_share,
    _name_key,
    _row,
    _szse_a_symbol,
)


def test_official_source_normalization_is_strict_and_deterministic() -> None:
    assert _chinese_date("2024 年 7 月 12 日") == date(2024, 7, 12)
    assert _name_key("深圳市天地\uff08集团\uff09股份有限公司") == "深圳市天地集团"
    assert _szse_a_symbol("000038")
    assert _szse_a_symbol("300156")
    assert not _szse_a_symbol("200038")
    assert not _szse_a_symbol("123001")
    assert _factbook_b_share("000992", "中", "鲁\uff22 山东省中鲁远洋渔业股份有限公司")
    assert not _factbook_b_share("002601", "龙佰集团", "龙佰集团股份有限公司 LB Group")
    assert _delisting_date_from_text("将在 2026 年 1 月 22 日被摘牌") == date(2026, 1, 22)
    assert "source_url" in FIELDS
    assert (
        _row(
            "SZSE",
            "000038",
            "深大通",
            "SZSE_MAIN",
            date(1994, 8, 8),
            date(2023, 7, 12),
            "https://www.szse.cn/official-notice.html",
        )["source_url"]
        == "https://www.szse.cn/official-notice.html"
    )
