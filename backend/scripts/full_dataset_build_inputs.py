"""Explicit successor inputs; source inspection is not materialization authority."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from app.data.catalog.checksums import canonical_json_bytes, canonical_sha256, sha256_file
from app.data.catalog.freeze import require_unfrozen, write_immutable
from scripts.full_dataset_sources import source_path, verify_source_contracts

REFERENCE_PINS = {
    "p0_public_report_path",
    "p0_public_report_manifest_sha256",
    "p0_public_report_file_sha256",
    "full_source_preflight_manifest_sha256",
    "full_source_preflight_file_sha256",
}
AUXILIARY_INPUTS = {
    "adjustment_inventory",
    "rights_inventory",
    "suspension_events",
    "feature_only_observations",
    "benchmark_parquet",
}
PREFLIGHT_COMPONENTS = {
    "security_master",
    "st_history",
    "suspension_history",
    "corporate_actions",
    "adjustment_factors",
    "raw_ohlcv",
    "market_rules_and_transaction_costs",
    "trading_calendar",
    "csi300_benchmark",
}


class FilePin(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    path: Path
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")


class RawFilePin(FilePin):
    metadata_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")


class CandidateBuildInputs(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    operation: Literal["ISOLATED_SUCCESSOR_MATERIALIZATION"]
    authorization_source: Literal["ACCEPTED_V1_2_PRODUCT_GOAL"]
    dataset_id: str = Field(pattern=r"^[a-z0-9][a-z0-9._-]{2,127}$")
    coverage: tuple[str, str]
    recorded_at_utc: datetime
    work_root: Path
    final_root: Path
    reference_pins: dict[str, str]
    source_contracts: tuple[dict[str, str], ...]
    auxiliary_inputs: dict[str, FilePin]
    raw_sources: dict[str, tuple[RawFilePin, ...]]
    market_rule_manifest_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")

    def source(self, repository: Path, name: str) -> Path:
        return source_path(
            repository,
            next(row["source_path"] for row in self.source_contracts if row["name"] == name),
        )

    def read_bytes(self, repository: Path, path: Path) -> bytes:
        pins = {
            source_path(repository, row["source_path"]).resolve(): row["source_file_sha256"]
            for row in self.source_contracts
        }
        pins.update({pin.path: pin.sha256 for pin in self.auxiliary_inputs.values()})
        pins[(repository / self.reference_pins["p0_public_report_path"]).resolve()] = (
            self.reference_pins["p0_public_report_file_sha256"]
        )
        content = path.read_bytes()
        if hashlib.sha256(content).hexdigest() != pins[path.resolve()]:
            raise ValueError(f"CANDIDATE_CONSUMED_BYTES_CHANGED:{path.name}")
        return content

    def read_json(self, repository: Path, path: Path) -> Any:
        return json.loads(self.read_bytes(repository, path))

    def date_source_pins(self, repository: Path) -> dict[Path, str]:
        # The optional manifest selects parser inputs, not approval or new entitlements.
        from scripts.ordinary_distribution_dates import date_source_pins

        pin = self.auxiliary_inputs.get("ordinary_dates")
        return date_source_pins(self.read_json(repository, pin.path), pin.path) if pin else {}

    def recheck(self, repository: Path) -> None:
        verify_source_contracts(self.source_contracts, repository, self.reference_pins)
        for pin in self.auxiliary_inputs.values():
            if sha256_file(pin.path) != pin.sha256:
                raise ValueError(f"CANDIDATE_AUXILIARY_CHANGED:{pin.path.name}")
        for path, digest in self.date_source_pins(repository).items():
            if sha256_file(path) != digest:
                raise ValueError(f"ORDINARY_DATES_SOURCE_CHANGED:{path.name}")
        for pins in self.raw_sources.values():
            for pin in pins:
                require_unaliased_raw(pin.path)
                metadata = pin.path.with_suffix(pin.path.suffix + ".meta.json")
                if (
                    sha256_file(pin.path) != pin.sha256
                    or sha256_file(metadata) != pin.metadata_sha256
                ):
                    raise ValueError(f"CANDIDATE_RAW_INPUT_CHANGED:{pin.path.name}")
                if json.loads(metadata.read_bytes()).get("sha256") != pin.sha256:
                    raise ValueError(f"CANDIDATE_RAW_METADATA_MISMATCH:{pin.path.name}")

    def input_selection_sha256(self, repository: Path) -> str:
        # Exclude the preflight's own hash to avoid a circular digest; outputs are not inputs.
        selected = self.model_dump(
            mode="json", exclude={"work_root", "final_root", "source_contracts", "reference_pins"}
        )
        selected["source_contracts"] = [
            {**row, "source_path": str(source_path(repository, row["source_path"]).resolve())}
            for row in sorted(self.source_contracts, key=lambda row: row["name"])
            if row["name"] != "SOURCE_PREFLIGHT"
        ]
        selected["reference_pins"] = {
            key: value for key, value in self.reference_pins.items() if key.startswith("p0_")
        }
        selected["reference_pins"]["p0_public_report_path"] = str(
            (repository / self.reference_pins["p0_public_report_path"]).resolve()
        )
        selected["raw_sources"] = {
            exchange: sorted(pins, key=lambda pin: pin["path"])
            for exchange, pins in selected["raw_sources"].items()
        }
        return canonical_sha256(selected)

    def ownership(self) -> dict[str, Any]:
        # Bind executable interpretation as well as data; unrelated application edits do not matter.
        return {
            "operation": self.operation,
            "dataset_id": self.dataset_id,
            "inputs_sha256": canonical_sha256(self.model_dump(mode="json")),
            "producer_sha256": producer_sha256(),
        }

    def claim_work_root(self, ownership: dict[str, Any]) -> None:
        path = self.work_root / "build-inputs.json"
        if self.final_root.exists() and not path.exists():
            raise ValueError("CANDIDATE_WORK_ROOT_NOT_OWNED")
        if self.work_root.exists() and any(self.work_root.iterdir()) and not path.exists():
            raise ValueError("CANDIDATE_WORK_ROOT_NOT_OWNED")
        for existing in (
            self.work_root,
            *self.work_root.rglob("*"),
            self.final_root,
            *self.final_root.rglob("*"),
        ):
            if existing.is_symlink() or (existing.is_file() and existing.stat().st_nlink > 1):
                raise ValueError("CANDIDATE_OUTPUT_NOT_ISOLATED")
            require_unfrozen(existing / ".candidate-write-check" if existing.is_dir() else existing)
        write_immutable(path, canonical_json_bytes(ownership) + b"\n")
        self.final_root.parent.mkdir(parents=True, exist_ok=True)
        if self.work_root.stat().st_dev != self.final_root.parent.stat().st_dev:
            raise ValueError("CANDIDATE_ATOMIC_PUBLICATION_REQUIRES_SAME_FILESYSTEM")


def producer_sha256() -> dict[str, str]:
    code = (
        Path(__file__),
        Path(__file__).with_name("materialize_full_dataset.py"),
        Path(__file__).with_name("ordinary_distribution_dates.py"),
        Path(__file__).with_name("distribution_payment_terms.py"),
        Path(__file__).with_name("retained_bonus_terms.py"),
        Path(__file__).with_name("audit_p1_retained_cash_sources.py"),
        Path(__file__).with_name("audit_p1_orphan_cash_facts.py"),
        Path(__file__).with_name("reconcile_distribution_cash.py"),
        Path(__file__).with_name("link_distribution_notices.py"),
        Path(__file__).parents[1] / "app/domain/markets/corporate_actions.py",
        Path(__file__).parents[1] / "app/data/full_dataset.py",
        Path(__file__).parents[1] / "app/data/catalog/checksums.py",
    )
    return {path.name: sha256_file(path) for path in code}


def require_unaliased_raw(path: Path) -> None:
    # SSE's filename stem and its adjacent metadata are part of the parsed security identity.
    if any(
        item.is_symlink()
        for item in (path, path.with_suffix(path.suffix + ".meta.json"), *path.parents)
    ):
        raise ValueError("CANDIDATE_RAW_PATH_ALIASED")


def load_candidate_build_inputs(
    path: Path,
    expected_sha256: str,
    repository: Path,
    *,
    legacy_dataset_id: str,
    coverage: tuple[str, str],
) -> CandidateBuildInputs:
    path, repository = path.resolve(), repository.resolve()
    content = path.read_bytes()
    if hashlib.sha256(content).hexdigest() != expected_sha256:
        raise ValueError("CANDIDATE_BUILD_SPEC_CHANGED")
    spec = CandidateBuildInputs.model_validate_json(content)
    if spec.dataset_id == legacy_dataset_id or spec.coverage != coverage:
        raise ValueError("CANDIDATE_DATASET_IDENTITY_INVALID")
    if spec.recorded_at_utc.tzinfo is None or spec.recorded_at_utc.utcoffset() != UTC.utcoffset(
        None
    ):
        raise ValueError("CANDIDATE_TIMESTAMP_MUST_BE_UTC")
    if (
        set(spec.reference_pins) != REFERENCE_PINS
        or not AUXILIARY_INPUTS
        <= set(spec.auxiliary_inputs)
        <= AUXILIARY_INPUTS | {"ordinary_references", "ordinary_dates"}
        or set(spec.raw_sources) != {"SSE", "SZSE"}
        or any(not pins for pins in spec.raw_sources.values())
    ):
        raise ValueError("CANDIDATE_INPUT_SET_INVALID")

    def absolute(value: Path) -> Path:
        return value if value.is_absolute() else path.parent / value

    outputs = [absolute(spec.work_root), absolute(spec.final_root)]
    for output in outputs:
        if any(parent.is_symlink() for parent in (output, *output.parents)):
            raise ValueError("CANDIDATE_OUTPUT_NOT_ISOLATED")
        require_unfrozen(output / "build-inputs.json")
        if output.resolve().is_relative_to(repository):
            raise ValueError("CANDIDATE_OUTPUT_NOT_ISOLATED")
    work, final = (output.resolve() for output in outputs)
    if work.is_relative_to(final) or final.is_relative_to(work) or final.name != spec.dataset_id:
        raise ValueError("CANDIDATE_OUTPUT_NOT_ISOLATED")
    auxiliary = {
        name: pin.model_copy(update={"path": absolute(pin.path).resolve()})
        for name, pin in spec.auxiliary_inputs.items()
    }
    for pins in spec.raw_sources.values():
        for pin in pins:
            require_unaliased_raw(absolute(pin.path))
    raw = {
        exchange: tuple(
            sorted(
                (pin.model_copy(update={"path": absolute(pin.path).resolve()}) for pin in pins),
                key=lambda pin: str(pin.path),
            )
        )
        for exchange, pins in spec.raw_sources.items()
    }
    raw_paths = [pin.path for pins in raw.values() for pin in pins]
    if len(set(raw_paths)) != len(raw_paths):
        raise ValueError("CANDIDATE_DUPLICATE_RAW_INPUT")
    spec = spec.model_copy(
        update={
            "work_root": work,
            "final_root": final,
            "auxiliary_inputs": auxiliary,
            "raw_sources": raw,
            "source_contracts": tuple(sorted(spec.source_contracts, key=lambda row: row["name"])),
        }
    )
    inputs = [path, repository / spec.reference_pins["p0_public_report_path"]]
    inputs.extend(source_path(repository, row["source_path"]) for row in spec.source_contracts)
    inputs.extend(pin.path for pin in auxiliary.values())
    inputs.extend(spec.date_source_pins(repository))
    inputs.extend(raw_paths)
    inputs.extend(raw_path.with_suffix(raw_path.suffix + ".meta.json") for raw_path in raw_paths)
    if any(
        input_path.resolve().is_relative_to(output)
        for input_path in inputs
        for output in (work, final)
    ):
        raise ValueError("CANDIDATE_INPUT_OUTPUT_OVERLAP")
    # Authenticate cheap source/preflight references before reading the large raw archive.
    verify_source_contracts(spec.source_contracts, repository, spec.reference_pins)
    preflight = spec.read_json(repository, spec.source(repository, "SOURCE_PREFLIGHT"))
    components = preflight.get("components", {})
    if (
        preflight.get("status") != "PASS"
        or preflight.get("dataset_id") != spec.dataset_id
        or preflight.get("coverage") != list(coverage)
        or preflight.get("mandatory_incomplete_components") != []
        or set(components) != PREFLIGHT_COMPONENTS
        or any(
            not str(component.get("status", "")).startswith("PASS")
            for component in components.values()
        )
        or "approval" in preflight
        or preflight.get("operation") != spec.operation
        or preflight.get("financial_coverage") == "PARTIAL"
        or any(not row["status"].startswith("PASS") for row in spec.source_contracts)
    ):
        raise ValueError("CANDIDATE_SOURCE_PREFLIGHT_NOT_AUTHORIZED")
    if preflight.get("input_selection_sha256") != spec.input_selection_sha256(repository):
        raise ValueError("CANDIDATE_PREFLIGHT_INPUT_SELECTION_MISMATCH")
    spec.recheck(repository)
    adjustment = spec.read_json(repository, spec.source(repository, "ADJUSTMENTS"))
    inventory = auxiliary["adjustment_inventory"]
    if [
        row.get("sha256")
        for row in adjustment.get("inputs", [])
        if Path(row.get("path", "")).resolve() == inventory.path
    ] != [inventory.sha256]:
        raise ValueError("CANDIDATE_ADJUSTMENT_INVENTORY_REFERENCE_MISMATCH")
    rights = spec.read_json(repository, spec.source(repository, "RIGHTS_ACTIONS"))
    rights_inventory = auxiliary["rights_inventory"]
    if (
        Path(rights.get("inventory_path", "")).resolve() != rights_inventory.path
        or rights.get("inventory_sha256") != rights_inventory.sha256
    ):
        raise ValueError("CANDIDATE_RIGHTS_INVENTORY_REFERENCE_MISMATCH")
    feature = auxiliary["feature_only_observations"]
    raw_component = components["raw_ohlcv"]
    if (
        Path(raw_component.get("report_path", "")).resolve() != feature.path
        or raw_component.get("report_file_sha256") != feature.sha256
        or raw_component.get("report_manifest_sha256")
        != canonical_sha256(
            {
                key: value
                for key, value in spec.read_json(repository, feature.path).items()
                if key != "manifest_sha256"
            }
        )
    ):
        raise ValueError("CANDIDATE_FEATURE_INPUT_REFERENCE_MISMATCH")
    benchmark = spec.read_json(repository, spec.source(repository, "BENCHMARK"))
    if benchmark.get("partition", {}).get("sha256") != auxiliary["benchmark_parquet"].sha256:
        raise ValueError("CANDIDATE_BENCHMARK_INPUT_REFERENCE_MISMATCH")
    # Suspension normalization has no existing direct parent output pin; keep its explicit byte pin.
    if sha256_file(path) != expected_sha256:
        raise ValueError("CANDIDATE_BUILD_SPEC_CHANGED")
    return spec
