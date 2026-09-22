"""Extend the accepted calendar snapshot offline; never republish or freeze the Pilot."""

import argparse
import json
import sys
from collections import Counter
from datetime import date
from pathlib import Path

from app.data.catalog.checksums import canonical_json_bytes, canonical_sha256, sha256_file
from app.data.catalog.freeze import write_immutable
from scripts.publish_akshare_pilot import decode_calendar_snapshot


def sessions(decoded):
    values = [value[:10] for value in decoded]
    if len(set(values)) != len(values):
        raise ValueError("DUPLICATE_CALENDAR_SESSION")
    if any(date.fromisoformat(value).weekday() > 4 for value in values):
        raise ValueError("WEEKEND_A_SHARE_SESSION")
    history = sorted(value for value in values if value <= "2025-12-31")
    return history, [value for value in history if value >= "2010-01-01"]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("staging", "sdk-root", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    sys.path.append(str(args.sdk_root))  # Reuse the pinned decoder runtime; install nothing.
    decoded, metadata, decoder_hash = decode_calendar_snapshot(args.staging, args.sdk_root)
    if metadata["sha256"] != "d5112e08726ecc435092fb63547a34fc514b071b1a4a84f9e2c29fb9023726a9":
        raise ValueError("ACCEPTED_CALENDAR_SOURCE_IDENTITY_CHANGED")
    history, selected = sessions(decoded)
    if not selected or selected[0] != "2010-01-04" or selected[-1] != "2025-12-31":
        raise ValueError("FULL_CALENDAR_ENDPOINT_COVERAGE_MISSING")
    if (history, selected) != sessions(list(reversed(decoded))):
        raise ValueError("CALENDAR_INPUT_ORDER_CHANGED")
    result = dict(
        parser_version="ACCEPTED_CALENDAR_FULL_RANGE_EXTENSION_V1",
        parser_sha256=sha256_file(Path(__file__)),
        decoder_wrapper_sha256=sha256_file(Path(__file__).with_name("publish_akshare_pilot.py")),
        decoder_sha256=decoder_hash,
        source=metadata,
        source_acquisition="REUSED_ACCEPTED_SNAPSHOT_OFFLINE",
        requested_coverage=["2010-01-01", "2025-12-31"],
        sessions=selected,
        listing_age_history=history,
        trading_sessions=len(selected),
        annual_sessions=dict(sorted(Counter(value[:4] for value in selected).items())),
        input_order_reproducibility="PASS",
        benchmark_alignment="PENDING_FULL_BENCHMARK",
        full_source_preflight="PARTIAL",
        dataset_created=False,
    )
    result["manifest_sha256"] = canonical_sha256(result)
    write_immutable(args.output, canonical_json_bytes(result) + b"\n")
    print(
        json.dumps(
            {
                k: v
                for k, v in result.items()
                if k not in {"sessions", "listing_age_history", "source"}
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
