import argparse
import json
import tempfile
from datetime import UTC, datetime, timedelta
from pathlib import Path

from app.data.catalog import write_canonical_parquet
from app.data.catalog.checksums import canonical_json_bytes, sha256_file
from app.data.security_master import (
    PointInTimeSecurityMaster,
    SecurityMasterError,
    load_security_master,
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Audit official point-in-time A-share universe files"
    )
    parser.add_argument(
        "--staging-root",
        type=Path,
        default=Path("/home/yuchen/data/research/staging/security-master"),
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("/home/yuchen/data/research/security-master-audit"),
    )
    args = parser.parse_args()
    args.output_root.mkdir(parents=True, exist_ok=True)
    try:
        master = load_security_master(args.staging_root)
        report = _audit(master)
        if report["status"] == "PASS":
            _write_dataset(args.output_root, master, report)
    except (OSError, ValueError) as exc:
        report = {
            "schema_version": "1.0",
            "status": "BLOCKED",
            "reason": str(exc),
            "retrieval_timestamp": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        }
    (args.output_root / "audit-report.json").write_bytes(canonical_json_bytes(report) + b"\n")
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    if report["status"] != "PASS":
        raise SystemExit(2)


def _audit(master: PointInTimeSecurityMaster) -> dict[str, object]:
    if not master.complete:
        return {"schema_version": "1.0", "status": "BLOCKED", "reason": "INCOMPLETE_SOURCE"}
    by_security = {}
    for record in master.records:
        by_security.setdefault(str(record.security_id), record)
    exited = tuple(record for record in by_security.values() if record.delisting_date is not None)
    if not exited:
        return {
            "schema_version": "1.0",
            "status": "BLOCKED",
            "reason": "NO_EXITED_SECURITY_EVIDENCE",
        }
    retained = 0
    retained_expected = 0
    excluded_after_exit = 0
    excluded_after_exit_expected = 0
    for record in exited:
        assert record.delisting_date is not None
        before = max(record.listing_date, record.delisting_date - timedelta(days=1))
        if master.coverage_start <= before <= master.coverage_end:
            retained_expected += 1
            retained += record.security_id in master.eligible_universe(before)
        after = record.delisting_date + timedelta(days=1)
        if master.coverage_start <= after <= master.coverage_end:
            excluded_after_exit_expected += 1
            excluded_after_exit += record.security_id not in master.eligible_universe(after)
    future_exclusions = 0
    future_exclusions_expected = 0
    for record in by_security.values():
        before = record.listing_date - timedelta(days=1)
        if master.coverage_start <= before <= master.coverage_end:
            future_exclusions_expected += 1
            future_exclusions += record.security_id not in master.eligible_universe(before)
    reversed_master = PointInTimeSecurityMaster.create(
        coverage_start=master.coverage_start,
        coverage_end=master.coverage_end,
        complete=master.complete,
        source_versions=reversed(master.source_versions),
        records=reversed(master.records),
    )
    passed = (
        reversed_master.checksum == master.checksum
        and retained == retained_expected
        and excluded_after_exit == excluded_after_exit_expected
        and future_exclusions == future_exclusions_expected
    )
    status = "PASS" if passed else "BLOCKED"
    return {
        "schema_version": "1.0",
        "status": status,
        "reason": None if status == "PASS" else "UNIVERSE_BOUNDARY_OR_CHECKSUM_CHECK_FAILED",
        "coverage_start": master.coverage_start.isoformat(),
        "coverage_end": master.coverage_end.isoformat(),
        "security_count": len({str(item.security_id) for item in master.records}),
        "record_count": len(master.records),
        "exited_security_count": len({str(item.security_id) for item in exited}),
        "exited_pre_delisting_checks": retained,
        "post_delisting_exclusion_checks": excluded_after_exit,
        "future_listing_exclusion_checks": future_exclusions,
        "security_master_checksum": master.checksum,
        "reversed_input_checksum": reversed_master.checksum,
    }


def _write_dataset(
    output_root: Path, master: PointInTimeSecurityMaster, report: dict[str, object]
) -> None:
    dataset_root = output_root / f"security-master-{master.checksum[:12]}"
    if dataset_root.exists():
        try:
            existing = json.loads((dataset_root / "manifest.json").read_text(encoding="utf-8"))
            partition = existing["partition"]
            unchanged = (
                existing["security_master_checksum"] == master.checksum
                and sha256_file(dataset_root / "securities.parquet") == partition["sha256"]
            )
        except (OSError, KeyError, TypeError, json.JSONDecodeError) as exc:
            raise SecurityMasterError("EXISTING_SECURITY_MASTER_INVALID") from exc
        if unchanged:
            return
        raise SecurityMasterError("IMMUTABLE_SECURITY_MASTER_CONFLICT")
    with tempfile.TemporaryDirectory(prefix="security-master-", dir=output_root) as temporary:
        staging = Path(temporary) / dataset_root.name
        rows = tuple(record.model_dump(mode="python") for record in master.records)
        fields = tuple(sorted({key for row in rows for key in row}))
        partition = write_canonical_parquet(
            staging / "securities.parquet",
            fieldnames=fields,
            rows=rows,
            sort_keys=("security_id", "effective_from", "symbol"),
        )
        manifest = {
            **report,
            "dataset_id": dataset_root.name,
            "source_versions": [item.model_dump(mode="json") for item in master.source_versions],
            "partition": partition.model_dump(mode="json"),
        }
        (staging / "manifest.json").write_bytes(canonical_json_bytes(manifest) + b"\n")
        staging.replace(dataset_root)


if __name__ == "__main__":
    main()
