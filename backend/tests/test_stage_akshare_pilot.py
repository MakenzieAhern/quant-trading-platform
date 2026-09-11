import json

import pytest

from scripts.reconcile_sse_cninfo import sha
from scripts.stage_akshare_pilot import pilot_members, raw_url


def test_pilot_inventory_retains_delisted_and_rejects_future_ipo_and_mutation(tmp_path):
    root = tmp_path / "security-master-pilot"
    root.mkdir()
    raw = (
        b"security_id,listing_date,delisting_date\n"
        b"CN-A:SSE:600000,1999-01-01,\n"
        b"CN-A:SSE:600070,1997-01-01,2025-01-01\n"
        b"CN-A:SSE:688999,2024-08-01,\n"
        b"CN-A:SSE:600999,1990-01-01,2022-12-01\n"
    )
    path = root / "master.csv"
    path.write_bytes(raw)
    (root / "security-master-input.json").write_text(
        json.dumps(
            dict(
                complete=True,
                coverage_start="2023-01-01",
                coverage_end="2024-07-31",
                sources=[dict(filename="master.csv", sha256=sha(raw))],
            )
        )
    )
    assert [row["security_id"] for row in pilot_members(tmp_path)] == [
        "CN-A:SSE:600070",
        "CN-A:SSE:600000",
    ]
    path.write_bytes(raw + b"changed")
    with pytest.raises(ValueError, match="CHECKSUM_CHANGED"):
        pilot_members(tmp_path)
    assert "fqt=0&secid=1.600070" in raw_url("SSE", "600070")
    with pytest.raises(ValueError, match="INVALID_REQUEST_IDENTITY"):
        raw_url("OTHER", "600070")
