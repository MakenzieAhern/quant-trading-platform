import re
from pathlib import Path

from scripts.audit_public_security_master import (
    SZSE_CODE_PATTERN,
    active_codes,
    extract_yearbook_codes,
    normalized_rows,
)


def test_master_boundaries_and_order_are_deterministic() -> None:
    rows = [
        {
            "security_id": "b",
            "symbol": "600002",
            "exchange": "SSE",
            "effective_from": "2011-01-01",
            "effective_to": "",
        },
        {
            "security_id": "a",
            "symbol": "600001",
            "exchange": "SSE",
            "effective_from": "2010-01-01",
            "effective_to": "2010-12-31",
        },
    ]
    assert active_codes(rows, "SSE", "2010-12-31") == {"600001"}
    assert [row["security_id"] for row in normalized_rows(rows)] == ["a", "b"]
    assert [row["security_id"] for row in normalized_rows(list(reversed(rows)))] == ["a", "b"]


def test_szse_302_code_is_part_of_the_historical_code_domain() -> None:
    assert re.findall(SZSE_CODE_PATTERN, "302132 code-change row") == ["302132"]


def test_yearbook_parser_rejects_non_pdf(tmp_path: Path) -> None:
    path = tmp_path / "not.pdf"
    path.write_bytes(b"not a pdf")
    try:
        extract_yearbook_codes(path, "SSE")
    except Exception:
        pass
    else:
        raise AssertionError("invalid source accepted")
