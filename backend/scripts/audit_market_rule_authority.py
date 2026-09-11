"""Verify an offline, reviewed rule-claim ledger; never infer semantics from HTTP 200."""

import argparse
import json
from datetime import date, datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

from scripts.reconcile_sse_cninfo import canonical, save, sha

CHECKS = (
    "RULE_SOURCE_PROVENANCE",
    "RULE_VERSION_BOUNDARY",
    "BOARD_PRECEDENCE",
    "MAIN_BOARD_PRICE_LIMIT",
    "CHINEXT_PRICE_LIMIT",
    "NEW_LISTING_EXCEPTION",
    "PRICE_CAGE",
    "INTRADAY_SUSPENSION",
    "ST_RULE_INTEGRATION",
    "LISTING_AGE_RULES",
    "LOT_SIZE_RULES",
    "TICK_SIZE_RULES",
    "SUSPENSION_RULES",
    "ORDER_REJECTION_RULES",
    "TRANSACTION_COST_EFFECTIVE_DATES",
)
SOURCE_TYPES = {
    "PRIMARY_RULE_NOTICE",
    "OFFICIAL_RULE_DOCUMENT",
    "OFFICIAL_IMPLEMENTATION_GUIDANCE",
    "OFFICIAL_INVESTOR_GUIDANCE",
    "OFFICIAL_TECHNICAL_CONFIRMATION",
    "LATER_OFFICIAL_VERSION_REFERENCE",
}
STATUSES = {"PASS", "PARTIAL", "FAIL", "NOT_MATERIAL_TO_PILOT"}


def _inside(root: Path, relative: str) -> Path:
    path = (root / relative).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError("PATH_OUTSIDE_EVIDENCE_ROOT")
    return path


def normalized(ledger: dict[str, Any]) -> dict[str, Any]:
    """Only unordered inventories are sorted; semantic evidence text is unchanged."""
    result = json.loads(canonical(ledger))
    for source in result["sources"]:
        source["rule_ids_supported"] = sorted(source["rule_ids_supported"])
    for claim in result["claims"]:
        claim["supporting_source_urls"] = sorted(claim["supporting_source_urls"])
        claim["checks"] = sorted(claim["checks"])
    result["sources"].sort(key=lambda row: row["source_url"])
    result["claims"].sort(key=lambda row: row["rule_id"])
    result["retired_locations"].sort(key=lambda row: row["url"])
    return result


def audit(ledger: dict[str, Any], staging: Path, repository: Path) -> dict[str, Any]:
    """Bind explicit semantic reviews to exact source AND implementation bytes."""
    ledger = normalized(ledger)
    sources = {row["source_url"]: row for row in ledger["sources"]}
    claims = {row["rule_id"]: row for row in ledger["claims"]}
    if len(sources) != len(ledger["sources"]) or len(claims) != len(ledger["claims"]):
        raise ValueError("DUPLICATE_SOURCE_OR_CLAIM")
    if not claims or not ledger["implementation_sha256"]:
        raise ValueError("EMPTY_AUTHORITY_REVIEW")
    for source in sources.values():
        url = urlsplit(source["source_url"])
        if url.scheme != "https" or not (
            url.hostname == "szse.cn" or (url.hostname or "").endswith(".szse.cn")
        ):
            raise ValueError("NON_OFFICIAL_SOURCE")
        if source["source_type"] not in SOURCE_TYPES:
            raise ValueError("INVALID_SOURCE_TYPE")
        offset = datetime.fromisoformat(source["retrieved_at_utc"]).utcoffset()
        if offset is None or offset.total_seconds() != 0:
            raise ValueError("NAIVE_RETRIEVAL_TIMESTAMP")
        raw = _inside(staging, source["raw_snapshot_path"]).read_bytes()
        if sha(raw) != source["sha256"]:
            raise ValueError("SOURCE_CHECKSUM_MISMATCH")
        if source["raw_snapshot_path"].endswith(".pdf") and not raw.startswith(b"%PDF-"):
            raise ValueError("NOT_PDF_BYTES")
        if not set(source["rule_ids_supported"]) <= claims.keys():
            raise ValueError("UNKNOWN_SUPPORTED_CLAIM")
    for path, expected in ledger["implementation_sha256"].items():
        if sha(_inside(repository, path).read_bytes()) != expected:
            raise ValueError("IMPLEMENTATION_CHANGED_REVIEW_REQUIRED")
    for claim in claims.values():
        if claim["pilot_materiality"] not in {"MATERIAL", "NOT_MATERIAL_TO_PILOT"}:
            raise ValueError("INVALID_MATERIALITY")
        if claim["confidence"] not in {"VERIFIED", "PARTIAL", "UNRESOLVED"}:
            raise ValueError("INVALID_CONFIDENCE")
        if claim["implementation_status"] not in STATUSES:
            raise ValueError("INVALID_IMPLEMENTATION_STATUS")
        if not claim["checks"] or not set(claim["checks"]) <= set(CHECKS):
            raise ValueError("INVALID_CLAIM_CHECK")
        start, end = date.fromisoformat(claim["effective_from"]), claim["effective_to"]
        if end is not None and start > date.fromisoformat(end):
            raise ValueError("INVALID_EFFECTIVE_RANGE")
        if not claim["rule_semantics"] or not claim["implementation_review"]:
            raise ValueError("MISSING_SEMANTIC_REVIEW")
        primary = sources.get(claim["primary_source_url"])
        if primary is None:
            if claim["confidence"] == "VERIFIED":
                raise ValueError("VERIFIED_WITHOUT_SOURCE")
        else:
            if primary["sha256"] != claim["primary_source_sha256"]:
                raise ValueError("CLAIM_SOURCE_CHECKSUM_MISMATCH")
            if claim["rule_id"] not in primary["rule_ids_supported"]:
                raise ValueError("SOURCE_CLAIM_MAPPING_MISMATCH")
            if not claim["source_locator"]:
                raise ValueError("MISSING_SOURCE_LOCATOR")
            if primary["source_type"] == "LATER_OFFICIAL_VERSION_REFERENCE" and claim["checks"] != [
                "RULE_VERSION_BOUNDARY"
            ]:
                raise ValueError("LATER_RULE_BEHAVIOR_LEAKAGE")
        if not set(claim["supporting_source_urls"]) <= sources.keys():
            raise ValueError("UNKNOWN_SUPPORTING_SOURCE")
    results = {}
    for check in CHECKS:
        relevant = [c for c in claims.values() if check in c["checks"]]
        states = {c["implementation_status"] for c in relevant}
        results[check] = (
            "FAIL"
            if "FAIL" in states
            else "PARTIAL"
            if not relevant
            or "PARTIAL" in states
            or any(c["confidence"] != "VERIFIED" for c in relevant)
            else "PASS"
            if "PASS" in states
            else "NOT_MATERIAL_TO_PILOT"
        )
    material = [c for c in claims.values() if c["pilot_materiality"] == "MATERIAL"]
    evidence_pass = bool(material) and all(c["confidence"] == "VERIFIED" for c in material)
    implementation_pass = all(c["implementation_status"] == "PASS" for c in material)
    return {
        "parser_version": "reviewed-rule-claims-v1",
        "source_manifest_sha256": sha(canonical(ledger)),
        "official_rule_sources_accepted": len(sources),
        "claim_count": len(claims),
        "full_history_rule_authority": "PARTIAL",
        "pilot_rule_authority": "PASS" if evidence_pass and implementation_pass else "PARTIAL",
        "market_rule_authority": "PASS_FOR_PILOT"
        if evidence_pass and implementation_pass and all(v == "PASS" for v in results.values())
        else "PARTIAL",
        "validation": results,
        "unclosed_claims": sorted(
            c["rule_id"]
            for c in material
            if c["confidence"] != "VERIFIED" or c["implementation_status"] != "PASS"
        ),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ledger", type=Path, required=True)
    parser.add_argument("--staging", type=Path, required=True)
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    ledger = json.loads(args.ledger.read_bytes())
    report = audit(ledger, args.staging, args.repository)
    reversed_ledger = dict(
        ledger, sources=list(reversed(ledger["sources"])), claims=list(reversed(ledger["claims"]))
    )
    assert report == audit(reversed_ledger, args.staging, args.repository)
    assert report == audit(ledger, args.staging, args.repository)
    report["validation"].update(INPUT_ORDER_REPRODUCIBILITY="PASS", CHECKSUM_REPEATABILITY="PASS")
    save(args.output, report)
    print(canonical(report).decode())
