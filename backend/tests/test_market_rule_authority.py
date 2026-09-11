from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest

from scripts.audit_market_rule_authority import CHECKS, audit
from scripts.reconcile_sse_cninfo import sha


def _ledger(tmp_path: Path) -> dict[str, Any]:
    raw = b"official small offline fixture, not a real authority source"
    (tmp_path / "source.html").write_bytes(raw)
    (tmp_path / "implementation.py").write_bytes(b"reviewed fixture\n")
    url = "https://investor.szse.cn/fixture.html"
    return {
        "sources": [
            {
                "source_url": url,
                "source_type": "OFFICIAL_INVESTOR_GUIDANCE",
                "retrieved_at_utc": "2026-09-11T00:00:00+00:00",
                "raw_snapshot_path": "source.html",
                "sha256": sha(raw),
                "rule_ids_supported": ["fixture"],
            }
        ],
        "claims": [
            {
                "rule_id": "fixture",
                "primary_source_url": url,
                "primary_source_sha256": sha(raw),
                "supporting_source_urls": [],
                "source_locator": "fixture only",
                "checks": list(CHECKS),
                "effective_from": "2023-01-01",
                "effective_to": "2024-07-31",
                "rule_semantics": "offline fixture",
                "implementation_review": "offline fixture",
                "confidence": "VERIFIED",
                "implementation_status": "PASS",
                "pilot_materiality": "MATERIAL",
            }
        ],
        "implementation_sha256": {"implementation.py": sha(b"reviewed fixture\n")},
        "retired_locations": [],
    }


def test_claim_audit_is_deterministic_and_cannot_promote_missing_or_failed_reviews(
    tmp_path: Path,
) -> None:
    ledger = _ledger(tmp_path)
    result = audit(ledger, tmp_path, tmp_path)
    assert result["market_rule_authority"] == "PASS_FOR_PILOT"
    reversed_checks = deepcopy(ledger)
    reversed_checks["claims"][0]["checks"].reverse()
    assert result == audit(reversed_checks, tmp_path, tmp_path)
    for status in ("PARTIAL", "FAIL", "NOT_MATERIAL_TO_PILOT"):
        failed = deepcopy(ledger)
        failed["claims"][0]["implementation_status"] = status
        assert audit(failed, tmp_path, tmp_path)["market_rule_authority"] == "PARTIAL"
    missing = deepcopy(ledger)
    missing["claims"][0]["checks"].pop()
    assert audit(missing, tmp_path, tmp_path)["market_rule_authority"] == "PARTIAL"
    unresolved = deepcopy(ledger)
    unresolved["claims"][0]["confidence"] = "UNRESOLVED"
    assert audit(unresolved, tmp_path, tmp_path)["pilot_rule_authority"] == "PARTIAL"


def test_claim_audit_rejects_changed_bytes_unofficial_sources_and_future_behavior(
    tmp_path: Path,
) -> None:
    ledger = _ledger(tmp_path)
    for field, value, error in (
        ("source_type", "LATER_OFFICIAL_VERSION_REFERENCE", "LATER_RULE_BEHAVIOR"),
        ("source_url", "https://szse.cn.example.org/fixture", "NON_OFFICIAL"),
        ("raw_snapshot_path", "../escape", "PATH_OUTSIDE"),
        ("retrieved_at_utc", "2026-09-11T00:00:00", "NAIVE_RETRIEVAL"),
    ):
        changed = deepcopy(ledger)
        changed["sources"][0][field] = value
        with pytest.raises(ValueError, match=error):
            audit(changed, tmp_path, tmp_path)
    (tmp_path / "source.html").write_bytes(b"changed source")
    with pytest.raises(ValueError, match="SOURCE_CHECKSUM"):
        audit(ledger, tmp_path, tmp_path)
    ledger = _ledger(tmp_path)
    (tmp_path / "implementation.py").write_bytes(b"changed implementation")
    with pytest.raises(ValueError, match="IMPLEMENTATION_CHANGED"):
        audit(ledger, tmp_path, tmp_path)
