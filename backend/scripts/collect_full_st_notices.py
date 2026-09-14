"""Collect only full-period risk-notice metadata outside accepted Pilot coverage."""

import argparse
import calendar
import json
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from pathlib import Path
from threading import Event

from app.data.catalog.checksums import canonical_json_bytes, canonical_sha256, sha256_file
from app.data.catalog.freeze import write_immutable
from scripts.recover_distribution_metadata import collect_window


def missing_windows():
    return [
        (date(y, m, 1), date(y, m, calendar.monthrange(y, m)[1]))
        for y in range(2010, 2026)
        for m in range(1, 13)
        if not (y >= 2023 and (y, m) <= (2024, 7))
    ]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args()
    parser_sha = sha256_file(Path(__file__))
    helper_sha = sha256_file(Path(__file__).with_name("recover_distribution_metadata.py"))
    denied = Event()
    jobs = [
        (key, term, start, end)
        for key, term in (("risk", "风险警示"), ("special", "特别处理"))
        for start, end in missing_windows()
    ]

    def collect(job):
        key, term, start, end = job
        if denied.is_set():
            return dict(
                keyword=term,
                start=str(start),
                end=str(end),
                sources=[],
                status="NOT_ATTEMPTED_AFTER_ACCESS_DENIAL",
            )
        checkpoint = args.root / "metadata-v1" / key / f"{start}-{end}-checkpoint.json"
        if checkpoint.exists():
            prior = json.loads(checkpoint.read_bytes())
            if prior["manifest_sha256"] != canonical_sha256(
                {k: v for k, v in prior.items() if k != "manifest_sha256"}
            ):
                raise ValueError("ST_METADATA_CHECKPOINT_CHANGED")
            if prior.get("access_denied"):
                denied.set()
            for receipt in prior["sources"]:
                params = receipt["params"]
                path = (
                    args.root / "metadata-v1" / key / f"{start}-{end}-p{params['pageNum']:03}.json"
                )
                if sha256_file(path) != receipt["sha256"]:
                    raise ValueError("ST_METADATA_SOURCE_CHANGED")
            return prior
        receipts = []
        try:
            rows = collect_window(
                args.root,
                start,
                end,
                receipts,
                keyword=term,
                category="",
                prefix=f"metadata-v1/{key}",
            )
            result = dict(
                keyword=term,
                start=str(start),
                end=str(end),
                records=rows,
                status="COMPLETE_FOR_QUERY_NOT_EVENT_CENSUS",
                sources=receipts,
            )
        except Exception as exc:
            access_denied = getattr(exc, "code", None) in {403, 429} or "ACCESS_DENIED" in str(exc)
            if access_denied:
                denied.set()
            result = dict(
                keyword=term,
                start=str(start),
                end=str(end),
                status="FAILED",
                sources=receipts,
                error=f"{type(exc).__name__}: {exc}",
                access_denied=access_denied,
            )
        result["manifest_sha256"] = canonical_sha256(result)
        write_immutable(checkpoint, canonical_json_bytes(result) + b"\n")
        print(key, start, result["status"], len(result.get("records", [])), flush=True)
        return result

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(collect, jobs))
    report = dict(
        parser_version="FULL_ST_MISSING_PERIOD_METADATA_V1",
        parser_sha256=parser_sha,
        helper_sha256=helper_sha,
        results=results,
        failures=sum(r["status"] != "COMPLETE_FOR_QUERY_NOT_EVENT_CENSUS" for r in results),
        accepted_pilot_coverage_not_requeried=["2023-01-01", "2024-07-31"],
        accepted_events=0,
        full_dataset_created=False,
        scope="METADATA_LEADS_REQUIRE_OFFICIAL_RECONCILIATION_AND_NAME_CROSSCHECK",
    )
    report["manifest_sha256"] = canonical_sha256(report)
    write_immutable(args.root / "metadata-manifest-v1.json", canonical_json_bytes(report) + b"\n")


if __name__ == "__main__":
    main()
