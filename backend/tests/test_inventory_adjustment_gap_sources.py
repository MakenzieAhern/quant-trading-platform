import json
from pathlib import Path

from app.data.catalog.checksums import sha256_file
from scripts.inventory_adjustment_gap_sources import inventory


def test_inventory_reuses_exact_bytes_and_preserves_missing(tmp_path: Path) -> None:
    pdf = tmp_path / "cached" / "one.pdf"
    pdf.parent.mkdir()
    pdf.write_bytes(b"official")
    metadata = {
        "url": "https://static.cninfo.com.cn/finalpage/one.PDF",
        "sha256": sha256_file(pdf),
        "http_status": 200,
        "retrieved_at_utc": "2026-09-19T00:00:00+00:00",
    }
    pdf.with_suffix(".pdf.meta.json").write_text(json.dumps(metadata))
    queue = [
        {
            "url": metadata["url"],
            "issuer": "000001",
            "affected_factor_changes": ["FACTOR:CN-A:SZSE:000001:2014-06-12"],
        },
        {
            "url": "https://static.cninfo.com.cn/finalpage/missing.PDF",
            "issuer": "000002",
            "affected_factor_changes": ["FACTOR:CN-A:SZSE:000002:2014-06-12"],
        },
    ]
    retained, missing = inventory(tmp_path, queue)
    assert retained[0]["source_sha256"] == sha256_file(pdf)
    assert retained[0]["source_path"] == "cached/one.pdf"
    assert missing == [queue[1]]
    assert (retained, missing) == inventory(tmp_path, list(reversed(queue)))
