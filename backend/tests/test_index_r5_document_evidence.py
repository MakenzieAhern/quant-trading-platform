import json

import pytest

from scripts.index_r5_document_evidence import cached_extractions, documents


def test_cached_extractions_require_matching_source_identity(tmp_path):
    cache = tmp_path / "batch-v1/text"
    cache.mkdir(parents=True)
    path = cache / ("a" * 64 + ".json")
    raw = json.dumps({"source_sha256": "a" * 64, "pages": ["official"]}).encode()
    path.write_bytes(raw)
    assert cached_extractions([tmp_path]) == {"a" * 64: raw}

    duplicate = tmp_path / "copy/batch-v1/text" / path.name
    duplicate.parent.mkdir(parents=True)
    duplicate.write_text(
        json.dumps(
            {
                "source_sha256": "a" * 64,
                "parser_version": "newer-metadata",
                "pages": ["official"],
            }
        )
    )
    assert json.loads(cached_extractions([tmp_path])["a" * 64])["pages"] == ["official"]
    duplicate.write_text(json.dumps({"source_sha256": "a" * 64, "pages": ["changed"]}))
    with pytest.raises(ValueError, match="CONFLICTING_EXTRACTION_CACHES"):
        cached_extractions([tmp_path])


def test_documents_can_read_immutable_receipts_before_batch_manifest(tmp_path):
    receipts = tmp_path / "batch-v1/receipts"
    receipts.mkdir(parents=True)
    (receipts / "a.json").write_text(json.dumps({"retrieval_status": "PASS", "source_sha256": "a"}))
    assert documents(tmp_path, "batch-v1", True) == [
        {"retrieval_status": "PASS", "source_sha256": "a"}
    ]
