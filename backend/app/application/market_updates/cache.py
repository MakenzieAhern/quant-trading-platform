"""Append-only content-addressed receipt bundles, published before DB references."""

import json
import os
import re
import tempfile
from datetime import date, datetime, timedelta
from importlib import import_module
from pathlib import Path
from typing import Any

from app.application.market_updates.contracts import (
    PROVIDER,
    SDK_VERSION,
    SDK_WHEEL_SHA256,
    UpdateError,
    parse_response,
    request_parameters,
)
from app.data.catalog.checksums import (
    canonical_json_bytes,
    canonical_sha256,
    sha256_file,
    verified_file_bytes,
)
from app.domain.markets import SecurityId

pa: Any = import_module("pyarrow")
pq: Any = import_module("pyarrow.parquet")

# SOURCE_READINESS at 5305096 records a live normalization fix before the v2 label.
_LEGACY_JOB = "ed796871-4ce4-4cf3-b7f0-2223e636bb75"
LEGACY_PARSER_LABEL_RECEIPTS = {
    "e117d2f313ea1579351c235e44af81c99bb5ef46a3a627a0329505c4c4d1a893": _LEGACY_JOB,
    "c12aa42bb94898921f64f4eba687687f17dc374cc06299c13965da2ad1cd82b4": _LEGACY_JOB,
}


def receipt_reader_diagnostics(manifest_sha256: str, evidence: dict[str, Any]) -> list[str]:
    """Derived read-only provenance; never alter the retained evidence or label."""
    if (
        manifest_sha256 in LEGACY_PARSER_LABEL_RECEIPTS
        and evidence.get("job_id") == LEGACY_PARSER_LABEL_RECEIPTS[manifest_sha256]
        and evidence.get("parser_version") == "product-baostock-raw-v1"
    ):
        return ["PARSER_LABEL_MISMATCH_READ_ONLY"]
    return []


def _verify_payload(
    raw: dict[str, Any],
    rows: list[dict[str, Any]],
    evidence: dict[str, Any],
    *,
    manifest_sha256: str = "",
) -> None:
    """Reproduce saved parser output; hashes prove bytes, never their interpretation."""
    sid = str(SecurityId(value=evidence["security_id"]))
    params = evidence["parameters"]
    start, end = (date.fromisoformat(params[key]) for key in ("start_date", "end_date"))
    version = evidence["parser_version"]
    timestamps = [
        datetime.fromisoformat(evidence[key])
        for key in (
            "requested_at_utc",
            "response_completed_at_utc",
            "received_at_utc",
            "first_received_at_utc",
        )
    ]
    requested, completed, received, first_received = timestamps
    if (
        evidence["provider"] != PROVIDER
        or evidence["sdk_version"] != SDK_VERSION
        or evidence["sdk_release_wheel_sha256"] != SDK_WHEEL_SHA256
        or version not in {"product-baostock-raw-v1", "product-baostock-raw-v2"}
        or evidence["source_endpoint"] != "public-api.baostock.com:10030"
        or evidence["raw_response_representation"] != "SDK_DECODED_FIELDS_AND_ROWS_NOT_WIRE_BYTES"
        or not 1 <= (end - start).days + 1 <= 31
        or params != request_parameters(sid, start, end)
        or any(value.utcoffset() != timedelta(0) for value in timestamps)
        or not requested <= completed <= received == first_received
        or type(evidence["attempt"]) is not int
        or not 1 <= evidence["attempt"] <= 3
        or type(evidence["row_count"]) is not int
        or evidence["row_count"] != len(rows)
        or canonical_sha256(raw) != evidence["raw_response_sha256"]
        or canonical_sha256({"rows": rows}) != evidence["logical_rows_sha256"]
    ):
        raise ValueError("receipt evidence does not describe supported source input")
    parsed = parse_response(raw, sid, start, end)
    # Only the two immutable, documented legacy receipts may use the mislabeled rule.
    if (
        version == "product-baostock-raw-v1"
        and any(row[7] == row[8] == "" and row[10] == "0" for row in raw["rows"])
        and not receipt_reader_diagnostics(manifest_sha256, evidence)
    ):
        raise ValueError("suspended blank turnover was not supported by parser v1")
    if canonical_json_bytes(parsed) != canonical_json_bytes(rows):
        raise ValueError("normalized receipt rows do not reproduce the original response")


class ReceiptCache:
    def __init__(self, root: Path, research_root: Path) -> None:
        self.root = root.resolve()
        protected = research_root.resolve()
        if (
            self.root.is_relative_to(protected)
            or protected.is_relative_to(self.root)
            or ".research" in self.root.parts
        ):
            raise UpdateError("PRODUCT_CACHE_MUST_BE_SEPARATE_FROM_RESEARCH")

    def _publish(self, content: bytes, suffix: str) -> dict[str, str]:
        import hashlib

        digest = hashlib.sha256(content).hexdigest()
        self.root.mkdir(parents=True, exist_ok=True)
        target = self.root / f"{digest}.{suffix}"
        # Hard-link is an atomic create-if-absent, unlike replace which overwrites evidence.
        fd, temporary = tempfile.mkstemp(prefix=".receipt-", dir=self.root)
        try:
            with os.fdopen(fd, "wb") as stream:
                stream.write(content)
                stream.flush()
                os.fsync(stream.fileno())
            try:
                os.link(temporary, target)
            except FileExistsError:
                if sha256_file(target) != digest:
                    raise UpdateError("PRODUCT_CACHE_INTEGRITY_FAILED") from None
            if os.name != "nt":
                directory_fd = os.open(self.root, os.O_RDONLY | os.O_DIRECTORY)
                try:
                    os.fsync(directory_fd)
                finally:
                    os.close(directory_fd)
        finally:
            Path(temporary).unlink(missing_ok=True)
        return {"path": target.name, "sha256": digest}

    def publish(
        self, raw: dict[str, Any], rows: list[dict[str, Any]], evidence: dict[str, Any]
    ) -> str:
        raw_file = self._publish(canonical_json_bytes(raw), "json")
        # Exact financial strings are stored inside canonical JSON, not Arrow doubles.
        table = pa.table(
            {"payload": [canonical_json_bytes(row).decode("utf-8") for row in rows]},
            schema=pa.schema([("payload", pa.string())]),
        )
        buffer = pa.BufferOutputStream()
        pq.write_table(table, buffer, compression="zstd")
        normalized = self._publish(buffer.getvalue().to_pybytes(), "parquet")
        manifest = {"version": 1, "evidence": evidence, "raw": raw_file, "rows": normalized}
        return self._publish(canonical_json_bytes(manifest), "json")["sha256"]

    def journal(self, payload: dict[str, Any]) -> str:
        """Receipt intent is durable before any DB write or cancellable publication."""
        return self._publish(canonical_json_bytes(payload), "pending.json")["path"]

    def pending(self) -> list[tuple[str, dict[str, Any]]]:
        records = []
        for path in self.root.glob("*.pending.json"):
            try:
                payload = json.loads(
                    verified_file_bytes(path, path.name.removesuffix(".pending.json"))
                )
                _verify_payload(payload["raw"], payload["rows"], payload["evidence"])
            except (OSError, KeyError, ValueError, TypeError) as exc:
                raise UpdateError("PRODUCT_CACHE_INTEGRITY_FAILED") from exc
            records.append((path.name, payload))
        return sorted(records, key=lambda item: (item[1]["evidence"]["received_at_utc"], item[0]))

    def acknowledge(self, journal: str) -> None:
        # Only remove this temporary index after immutable DB+bundle publication.
        if re.fullmatch(r"[0-9a-f]{64}\.pending\.json", journal) is None:
            raise UpdateError("PRODUCT_CACHE_INTEGRITY_FAILED")
        (self.root / journal).unlink(missing_ok=True)

    def record_denial(self, received_at: str) -> None:
        self._publish(
            canonical_json_bytes(
                {
                    "error_code": "SOURCE_ACCESS_DENIED",
                    "received_at_utc": received_at,
                    "scope": "BAOSTOCK_PUBLIC_SINGLE_SECURITY_EOD",
                    "version": 1,
                }
            ),
            "denial.json",
        )

    def denied(self) -> bool:
        # Even a corrupt denial record fails closed; it must never silently resume access.
        return next(self.root.glob("*.denial.json"), None) is not None

    def verify(self, digest: str) -> dict[str, Any]:
        return self.read(digest)[0]

    def read(self, digest: str) -> tuple[dict[str, Any], list[dict[str, Any]]]:
        """Read normalized rows only after verifying their immutable receipt bundle."""
        if re.fullmatch(r"[0-9a-f]{64}", digest) is None:
            raise UpdateError("PRODUCT_CACHE_INTEGRITY_FAILED")
        try:
            path = self.root / f"{digest}.json"
            manifest: dict[str, Any] = json.loads(verified_file_bytes(path, digest))
            if type(manifest["version"]) is not int or manifest["version"] != 1:
                raise ValueError("unsupported receipt manifest version")
            consumed = {}
            for member in ("raw", "rows"):
                entry = manifest[member]
                file = (self.root / entry["path"]).resolve()
                if file.parent != self.root:
                    raise ValueError("partition path escapes receipt cache")
                consumed[member] = verified_file_bytes(file, entry["sha256"])
            raw = json.loads(consumed["raw"])
            rows = [
                json.loads(row["payload"])
                for row in pq.read_table(pa.BufferReader(consumed["rows"])).to_pylist()
            ]
            _verify_payload(raw, rows, manifest["evidence"], manifest_sha256=digest)
            return manifest, rows
        except (OSError, KeyError, ValueError, TypeError) as exc:
            raise UpdateError("PRODUCT_CACHE_INTEGRITY_FAILED") from exc
