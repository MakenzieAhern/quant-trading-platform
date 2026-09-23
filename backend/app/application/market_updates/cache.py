"""Append-only content-addressed receipt bundles, published before DB references."""

import json
import os
import re
import tempfile
from importlib import import_module
from pathlib import Path
from typing import Any

from app.application.market_updates.contracts import UpdateError
from app.data.catalog.checksums import canonical_json_bytes, canonical_sha256, sha256_file

pa: Any = import_module("pyarrow")
pq: Any = import_module("pyarrow.parquet")


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
            if sha256_file(path) != path.name.removesuffix(".pending.json"):
                raise UpdateError("PRODUCT_CACHE_INTEGRITY_FAILED")
            payload = json.loads(path.read_bytes())
            if (
                canonical_sha256(payload["raw"]) != payload["evidence"]["raw_response_sha256"]
                or canonical_sha256({"rows": payload["rows"]})
                != payload["evidence"]["logical_rows_sha256"]
            ):
                raise UpdateError("PRODUCT_CACHE_INTEGRITY_FAILED")
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
        if re.fullmatch(r"[0-9a-f]{64}", digest) is None:
            raise UpdateError("PRODUCT_CACHE_INTEGRITY_FAILED")
        try:
            path = self.root / f"{digest}.json"
            if sha256_file(path) != digest:
                raise ValueError("manifest digest mismatch")
            manifest: dict[str, Any] = json.loads(path.read_bytes())
            for member in ("raw", "rows"):
                entry = manifest[member]
                file = (self.root / entry["path"]).resolve()
                if file.parent != self.root or sha256_file(file) != entry["sha256"]:
                    raise ValueError("partition digest mismatch")
            raw = json.loads((self.root / manifest["raw"]["path"]).read_bytes())
            if canonical_sha256(raw) != manifest["evidence"]["raw_response_sha256"]:
                raise ValueError("receipt raw checksum mismatch")
            rows = [
                json.loads(row["payload"])
                for row in pq.read_table(self.root / manifest["rows"]["path"]).to_pylist()
            ]
            expected = manifest["evidence"].get("logical_rows_sha256")
            if expected is not None and canonical_sha256({"rows": rows}) != expected:
                raise ValueError("normalized rows checksum mismatch")
            return manifest
        except (OSError, KeyError, ValueError, TypeError) as exc:
            raise UpdateError("PRODUCT_CACHE_INTEGRITY_FAILED") from exc
