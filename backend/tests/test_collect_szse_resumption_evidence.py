import json
from datetime import date

from app.data.catalog.checksums import canonical_json_bytes, canonical_sha256, sha256_file
from scripts.collect_szse_resumption_evidence import load_checkpoint, queue_rows


def test_resumption_queue_is_targeted_and_deduplicated():
    unresolved = [
        {"symbol": "000001", "suspended_at": "2015/01/01 09:30"},
        {"symbol": "000002", "suspended_at": "2016/01/01 09:30"},
    ]
    item = {
        "announcementId": "1",
        "announcementTime": 1422748800000,
        "secCode": "000001",
        "announcementTitle": "复牌公告",
        "adjunctUrl": "finalpage/2015-02-01/1.PDF",
    }
    rows = queue_rows([{"records": [item, item]}], unresolved)
    assert len(rows) == 1
    assert rows[0]["issuer"] == "000001"
    assert rows[0]["queue_type"] == "SZSE_OFFICIAL_RESUMPTION_EVIDENCE_PDF"


def test_load_checkpoint_reuses_only_verified_source(tmp_path):
    start, end = date(2010, 1, 1), date(2010, 1, 31)
    folder = tmp_path / "metadata-v1"
    folder.mkdir()
    source = folder / f"{start}-{end}-p001.json"
    source.write_bytes(b"{}\n")
    value = {
        "start": str(start),
        "end": str(end),
        "status": "COMPLETE_FOR_OFFICIAL_QUERY",
        "records": [],
        "sources": [{"params": {"pageNum": 1}, "sha256": sha256_file(source)}],
    }
    value["manifest_sha256"] = canonical_sha256(value)
    (folder / f"{start}-{end}-checkpoint.json").write_bytes(canonical_json_bytes(value) + b"\n")
    assert load_checkpoint(tmp_path, start, end) == json.loads(canonical_json_bytes(value))
