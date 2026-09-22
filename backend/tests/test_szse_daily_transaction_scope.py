import json
from decimal import Decimal

from scripts.audit_szse_daily_transaction_scope import classify, official_source, sha


def test_scope_classification_uses_official_post_close_signature():
    row = {"symbol": "000001", "volume_gap": "999900", "amount_gap": "12029952.38"}
    assert classify(row, (Decimal(1000000), Decimal(12030000)), Decimal("12.00")) == (
        "OFFICIAL_BLOCK_RECONCILED_WITHIN_DISPLAY_PRECISION"
    )
    row = {"symbol": "300001", "volume_gap": "1800", "amount_gap": "33700"}
    assert classify(row, (Decimal(0), Decimal(0)), Decimal("17.76")) == (
        "OFFICIAL_POST_CLOSE_FIXED_PRICE_SIGNATURE"
    )
    row["symbol"] = "000002"
    assert classify(row, (Decimal(0), Decimal(0)), Decimal("17.76")) == ("UNEXPLAINED_SCOPE_GAP")


def test_official_scope_source_is_checksum_bound(tmp_path):
    path = tmp_path / "source.html"
    raw = "<p>盘后定价成交量 计入当日总成交量</p>".encode()
    path.write_bytes(raw)
    path.with_suffix(".html.meta.json").write_text(
        json.dumps(
            {
                "url": "https://www.szse.cn/source",
                "sha256": sha(raw),
                "retrieved_at_utc": "2026-09-19T18:39:17Z",
            }
        )
    )
    assert official_source(path, "https://www.szse.cn/source", ("盘后定价成交量计入当日总成交量",))[
        "sha256"
    ] == sha(raw)
