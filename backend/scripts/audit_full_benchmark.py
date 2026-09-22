"""Audit official CSI300 price-index history without changing the accepted Pilot benchmark."""

import argparse
import json
from datetime import datetime
from decimal import Decimal
from pathlib import Path

from app.data.catalog.checksums import canonical_json_bytes, canonical_sha256, sha256_file
from app.data.catalog.freeze import write_immutable
from scripts.publish_akshare_pilot import write_table


def normalize(payload, sessions):
    if payload["code"] != "200":
        raise ValueError("OFFICIAL_INDEX_REQUEST_FAILED")
    rows = []
    for source in payload["data"]:
        if source["indexCode"] != "000300":
            raise ValueError("WRONG_BENCHMARK_IDENTITY")
        day = datetime.strptime(source["tradeDate"], "%Y%m%d").date().isoformat()
        prices = {key: Decimal(str(source[key])) for key in ("open", "high", "low", "close")}
        if not all(p.is_finite() and p > 0 for p in prices.values()) or not (
            prices["low"]
            <= min(prices["open"], prices["close"])
            <= max(prices["open"], prices["close"])
            <= prices["high"]
        ):
            raise ValueError("INVALID_BENCHMARK_OHLC")
        rows.append(
            dict(benchmark_id="CSI300_PRICE_INDEX", trading_date=day, close=prices["close"])
        )
    rows.sort(key=lambda row: row["trading_date"])
    dates = [r["trading_date"] for r in rows]
    if dates != sorted(set(dates)) or dates != sorted(sessions):
        raise ValueError("BENCHMARK_CALENDAR_MISMATCH")
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--staging", type=Path, required=True)
    args = parser.parse_args()
    root = args.staging / "full-benchmark-v1"
    calendar_path = args.staging / "full-calendar-v1/calendar-manifest-v3.json"
    calendar = json.loads(calendar_path.read_bytes())
    sources, payloads = [], []
    for name in ("CSI300-official-candidate.json", "CSI300-official-session-boundary.json"):
        path = root / name
        metadata = json.loads(path.with_suffix(".json.meta.json").read_bytes())
        if (
            metadata["http_status"] != 200
            or not metadata["url"].startswith(
                "https://www.csindex.com.cn/csindex-home/perf/index-perf?"
            )
            or sha256_file(path) != metadata["sha256"]
        ):
            raise ValueError("OFFICIAL_INDEX_SOURCE_CHANGED")
        sources.append(metadata)
        payloads.append(json.loads(path.read_bytes(), parse_float=str))
    rows = normalize(payloads[1], calendar["sessions"])
    if rows != normalize(
        {**payloads[1], "data": list(reversed(payloads[1]["data"]))},
        list(reversed(calendar["sessions"])),
    ):
        raise ValueError("INDEX_INPUT_ORDER_CHANGED")
    rejected = [r for r in payloads[0]["data"] if r["tradeDate"] == "20100101"]
    retained = [r for r in payloads[0]["data"] if r["tradeDate"] != "20100101"]
    if (
        len(rejected) != 1
        or {k: v for k, v in rejected[0].items() if k != "tradeDate"}
        != {k: v for k, v in payloads[1]["data"][0].items() if k != "tradeDate"}
        or rows != normalize({**payloads[0], "data": retained}, calendar["sessions"])
    ):
        raise ValueError("QUERY_BOUNDARY_ARTIFACT_NOT_EXPLAINED")
    pilot = args.staging / "benchmark-route-20260910/CSI300-1.json"
    if sha256_file(pilot) != "7290b8616bbd2673ed70c768622d14c50016274cf55c7d947ce2e555c48d9d91":
        raise ValueError("ACCEPTED_PILOT_BENCHMARK_CHANGED")
    reference = {
        fields[0]: fields[2]
        for fields in (r.split(",") for r in json.loads(pilot.read_bytes())["data"]["klines"])
    }
    observed = {r["trading_date"]: r["close"] for r in rows}
    if any(observed.get(day) != Decimal(price) for day, price in reference.items()):
        raise ValueError("ACCEPTED_PILOT_CLOSE_PARITY_FAILED")
    partition = write_table(root, "benchmark.parquet", rows, ("trading_date",))
    repeated = write_table(
        root, "benchmark-replay.parquet", list(reversed(rows)), ("trading_date",)
    )
    if partition.sha256 != repeated.sha256:
        raise ValueError("BENCHMARK_PARTITION_CHECKSUM_CHANGED")
    report = dict(
        authority="CSI300_PRICE_INDEX",
        source_provider="OFFICIAL_CHINA_SECURITIES_INDEX",
        status="PASS_FOR_FULL_RANGE_CLOSE_SERIES",
        accepted_pilot_unchanged=True,
        parser_version="OFFICIAL_CSI300_FULL_CLOSE_V1",
        parser_sha256=sha256_file(Path(__file__)),
        calendar_manifest_sha256=calendar["manifest_sha256"],
        sources=sources,
        coverage=[rows[0]["trading_date"], rows[-1]["trading_date"]],
        trading_sessions=len(rows),
        pilot_close_parity_sessions=len(reference),
        pilot_close_parity="PASS",
        calendar_alignment="PASS",
        ohlc_validity="PASS",
        input_order_reproducibility="PASS",
        checksum_repeatability="PASS",
        partition=partition.model_dump(mode="json"),
        rejected_source_rows=rejected,
        rejection_reason="NONTRADING_QUERY_START_DUPLICATES_FIRST_SESSION; NO_DATE_REWRITE",
        volume_and_amount_used=False,
        dataset_created=False,
        dataset_frozen=False,
    )
    report["manifest_sha256"] = canonical_sha256(report)
    write_immutable(root / "acceptance-manifest-v2.json", canonical_json_bytes(report) + b"\n")
    print(
        json.dumps(
            {k: v for k, v in report.items() if k not in {"sources", "rejected_source_rows"}},
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
