import json
import sys

from app.data.catalog.checksums import canonical_sha256
from scripts.reconcile_full_st_metadata import main


def test_failed_receipt_is_retained_without_becoming_a_cached_response(tmp_path, monkeypatch):
    metadata = {"results": []}
    metadata["manifest_sha256"] = canonical_sha256(metadata)
    source = tmp_path / "metadata.json"
    source.write_text(json.dumps(metadata))
    queue = tmp_path / "queue.json"
    queue.write_text("[]")
    failed = tmp_path / "failed.meta.json"
    failed.write_text(
        json.dumps(
            {
                "url": "https://query.sse.com.cn/security/stock/queryCompanyBulletinNew.do",
                "error": "URLError",
            }
        )
    )
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "reconcile",
            "--root",
            str(tmp_path),
            "--prior",
            str(tmp_path),
            "--metadata",
            str(source),
            "--queue",
            str(queue),
            "--batch",
            "recovery",
        ],
    )
    main()
    report = json.loads((tmp_path / "recovery/manifest.json").read_bytes())
    assert report["results"] == [] and report["accepted_events"] == 0
    assert report["cached_source_gaps"] == [
        {
            "path": str(failed),
            "reason": "RETAINED_FAILED_RETRIEVAL",
            "error": "URLError",
        }
    ]
