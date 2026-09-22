"""Read-only independent exchange-exit countercheck of a frozen candidate master."""

import argparse
import asyncio
import hashlib
import json
from pathlib import Path

import pyarrow.parquet as pq

from scripts.reconcile_sse_cninfo import save


async def invalidate_registration(dataset_id: str) -> None:
    from sqlalchemy import select

    from app.db.models.research import ResearchDatasetModel, ResearchRunModel
    from app.db.session import SessionFactory

    async with SessionFactory() as session:
        dataset = await session.get(ResearchDatasetModel, dataset_id)
        if dataset is None:
            raise ValueError("DATASET_REGISTRATION_NOT_FOUND")
        dataset.readiness_status = "FAILED"
        runs = await session.scalars(
            select(ResearchRunModel).where(ResearchRunModel.dataset_id == dataset_id)
        )
        for run in runs:
            run.diagnostics = {
                **run.diagnostics,
                "dataset_acceptance_warning": (
                    "INVALIDATED: frozen candidate master omits STAR exit securities "
                    "688086,688287,688555. Historical engineering output only; "
                    "corrected dataset needs new audit and freeze review."
                ),
            }
        await session.commit()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--invalidate-registration", action="store_true")
    args = parser.parse_args()
    master = args.dataset / "candidate-master.parquet"
    source = args.evidence / "raw" / "sse-star-terminated.json"
    source_hash = hashlib.sha256(source.read_bytes()).hexdigest()
    snapshots = json.loads((args.evidence / "source-snapshot-manifest.json").read_bytes())[
        "snapshots"
    ]
    provenance = next(s for s in snapshots if s["raw_snapshot_filename"] == source.name)
    if provenance["sha256"] != source_hash:
        raise ValueError("SOURCE_CHECKSUM_MISMATCH")
    frozen = json.loads((args.dataset / ".freeze.json").read_bytes())
    present = {r["security_id"] for r in pq.read_table(master).to_pylist()}
    missing = []
    for row in json.loads(source.read_bytes())["result"]:
        sid = "CN-A:SSE:" + row["A_STOCK_CODE"]
        if (
            row["LIST_DATE"] <= "20240731"
            and row["DELIST_DATE"] >= "20230101"
            and sid not in present
        ):
            missing.append(
                dict(
                    security_id=sid,
                    official_listing_date=row["LIST_DATE"],
                    official_delisting_date=row["DELIST_DATE"],
                    classification="MISSING_FROM_FROZEN_CANDIDATE_MASTER",
                )
            )
    report = dict(
        status="FAIL" if missing else "NO_COUNTEREXAMPLE_IN_THIS_SOURCE",
        dataset_id=args.dataset.name,
        missing=sorted(missing, key=lambda r: r["security_id"]),
        missing_count=len(missing),
        candidate_master_file_sha256=hashlib.sha256(master.read_bytes()).hexdigest(),
        frozen_manifest_file_sha256=hashlib.sha256(
            (args.dataset / "manifest.json").read_bytes()
        ).hexdigest(),
        freeze_record_present=bool(frozen),
        source={k: provenance[k] for k in ("source_url", "retrieved_at", "sha256")},
        affected_checks=["SURVIVORSHIP", "DELISTING_RETENTION", "SECURITY_MASTER_COMPLETENESS"],
        limitation=(
            "This countercheck is not a full corrected universe count or permission "
            "to change frozen bytes. v2 requires new source closure, materialization, "
            "audits and human freeze review."
        ),
    )
    save(args.output, report)
    print(json.dumps(report, ensure_ascii=True))
    if missing:
        if args.invalidate_registration:
            asyncio.run(invalidate_registration(args.dataset.name))
        raise SystemExit(2)


if __name__ == "__main__":
    main()
