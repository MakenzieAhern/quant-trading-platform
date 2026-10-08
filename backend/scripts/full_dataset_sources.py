"""Fail closed on source references before new full-dataset publication or acceptance."""

import json
import re
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from app.data.catalog.checksums import canonical_sha256, sha256_file

SOURCE_NAMES = frozenset(
    {
        "SOURCE_PREFLIGHT",
        "SECURITY_MASTER",
        "SSE_ST",
        "SZSE_ST",
        "SUSPENSIONS",
        "ADJUSTMENTS",
        "CASH_ACTIONS",
        "BONUS_ACTIONS",
        "GAP_DISTRIBUTION_ACTIONS",
        "RIGHTS_ACTIONS",
        "MERGER_ACTIONS",
        "STRUCTURAL_ACTIONS",
        "CALENDAR",
        "BENCHMARK",
        "MARKET_RULES_AND_COSTS",
    }
)


def source_path(repository: Path, value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else (repository / "backend" / path).resolve()


def verify_source_manifest(
    path: Path, expected: str, *, master_authority_path: Path | None = None
) -> Any:
    if not isinstance(expected, str) or re.fullmatch(r"[0-9a-f]{64}", expected) is None:
        raise ValueError(f"SOURCE_MANIFEST_INVALID:{path}")
    content = json.loads(path.read_bytes())
    if master_authority_path is not None:
        # The master is an array; its manifest belongs to the P0 authority, not the array.
        authority = verify_source_manifest(master_authority_path, expected)
        if not isinstance(content, list) or canonical_sha256(content) != authority.get(
            "reconstructed_master_sha256"
        ):
            raise ValueError(f"SOURCE_MASTER_AUTHORITY_MISMATCH:{path}")
    elif (
        not isinstance(content, dict)
        or content.get("manifest_sha256") != expected
        or canonical_sha256({k: v for k, v in content.items() if k != "manifest_sha256"})
        != expected
    ):
        raise ValueError(f"SOURCE_MANIFEST_MISMATCH:{path}")
    return content


def verify_source_contracts(
    rows: Sequence[dict[str, Any]], repository: Path, state: dict[str, Any]
) -> dict[str, dict[str, Any]]:
    names = [row["name"] for row in rows]
    if len(names) != len(set(names)) or set(names) != SOURCE_NAMES:
        raise ValueError("SOURCE_CONTRACT_SET_CHANGED")
    contracts = {row["name"]: row for row in sorted(rows, key=lambda row: row["name"])}
    master_authority_path = repository / state["p0_public_report_path"]
    verify_source_manifest(master_authority_path, state["p0_public_report_manifest_sha256"])
    if sha256_file(master_authority_path) != state["p0_public_report_file_sha256"]:
        raise ValueError("SOURCE_MASTER_AUTHORITY_BYTES_CHANGED")
    if (
        contracts["SECURITY_MASTER"]["source_manifest_sha256"]
        != state["p0_public_report_manifest_sha256"]
    ):
        raise ValueError("SOURCE_MASTER_STATE_REFERENCE_MISMATCH")
    if (
        contracts["SOURCE_PREFLIGHT"]["source_manifest_sha256"]
        != state["full_source_preflight_manifest_sha256"]
        or contracts["SOURCE_PREFLIGHT"]["source_file_sha256"]
        != state["full_source_preflight_file_sha256"]
    ):
        raise ValueError("SOURCE_PREFLIGHT_STATE_REFERENCE_MISMATCH")
    contents = {}
    for name, row in contracts.items():
        path = source_path(repository, row["source_path"])
        if sha256_file(path) != row["source_file_sha256"]:
            raise ValueError(f"SOURCE_CONTRACT_BYTES_CHANGED:{name}")
        contents[name] = verify_source_manifest(
            path,
            row["source_manifest_sha256"],
            master_authority_path=master_authority_path if name == "SECURITY_MASTER" else None,
        )
    if (
        contents["SOURCE_PREFLIGHT"]
        .get("components", {})
        .get("security_master", {})
        .get("manifest_sha256")
        != contracts["SECURITY_MASTER"]["source_manifest_sha256"]
    ):
        raise ValueError("SOURCE_PREFLIGHT_MASTER_REFERENCE_MISMATCH")
    components = contents["SOURCE_PREFLIGHT"].get("components", {})
    # Only explicit 1:1 references: corporate_actions is an aggregate, not a ledger.
    for name, component, manifest_key, file_key in (
        ("SSE_ST", "st_history", "sse_manifest_sha256", None),
        ("SZSE_ST", "st_history", "szse_probe_sha256", None),
        ("SUSPENSIONS", "suspension_history", "authority_manifest_sha256", None),
        (
            "ADJUSTMENTS",
            "adjustment_factors",
            "authority_report_manifest_sha256",
            "authority_report_file_sha256",
        ),
        ("CALENDAR", "trading_calendar", "manifest_sha256", None),
        ("BENCHMARK", "csi300_benchmark", "manifest_sha256", None),
        (
            "MARKET_RULES_AND_COSTS",
            "market_rules_and_transaction_costs",
            "report_manifest_sha256",
            "report_file_sha256",
        ),
    ):
        reference = components.get(component, {})
        if reference.get(manifest_key) != contracts[name]["source_manifest_sha256"]:
            raise ValueError(f"SOURCE_PREFLIGHT_COMPONENT_REFERENCE_MISMATCH:{name}")
        if (
            file_key is not None
            and reference.get(file_key) != contracts[name]["source_file_sha256"]
        ):
            raise ValueError(f"SOURCE_PREFLIGHT_COMPONENT_BYTES_MISMATCH:{name}")
    return contracts


def verify_source_lineage(contracts: Sequence[dict[str, Any]], lineage: Sequence[str]) -> None:
    expected = tuple(sorted(f"{row['name']}:{row['source_manifest_sha256']}" for row in contracts))
    if tuple(lineage) != expected:
        raise ValueError("SOURCE_CONTRACT_LINEAGE_MISMATCH")
