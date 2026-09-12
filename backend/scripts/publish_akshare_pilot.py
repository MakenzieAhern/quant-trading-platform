"""Compose accepted Pilot inputs into an atomic, unfrozen catalog publication."""

import argparse
import ast
import base64
import csv
import json
import shutil
from collections import Counter
from datetime import UTC, datetime
from decimal import Decimal
from importlib import import_module
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

import pyarrow.parquet as parquet

from app.data.catalog import (
    DatasetPartition,
    finalize_manifest,
    load_manifest,
    verify_dataset,
    write_canonical_parquet,
    write_manifest,
)
from scripts.audit_amount_impact import status_lookup
from scripts.audit_pilot_observations import missing_intervals
from scripts.reconcile_sse_cninfo import canonical, save, sha
from scripts.stage_akshare_pilot import DATASET_ID, END, START, candidate_members, pilot_members

# Existing accepted Pilot inputs; composition pins their bytes, not a fresh authority review.
ACCEPTED_INPUTS = {
    "benchmark-route-20260910/CSI300-1.json": (
        "7290b8616bbd2673ed70c768622d14c50016274cf55c7d947ce2e555c48d9d91"
    ),
    "security-master-pilot/sse-security-master.csv": (
        "b4d930c0e3368f67237076588dd65088de4e77ebcd8187d3bc271d761d7c9972"
    ),
    "security-master-pilot/szse-security-master.csv": (
        "f5aeca86c3c3df35d61f049e1a33eab96b0c18d833143339d685b62da6e07242"
    ),
    "sse-st-pilot/pilot-scope-20260910/coverage-intervals.json": (
        "f6d951ad2524f2a49cbbcbcfe3b76e4ca630a02d3036903d19a2a1597764e68d"
    ),
    "szse-st-recovery-20260910/audit/security-timelines.json": (
        "127f4cec8c32277057f6cf35f502a6efd2d54051607d5df32241d99859bed6f1"
    ),
    "sse-st-pilot/completeness-20260910/calendar/pilot-sessions.json": (
        "314ec2633400880b1573a59508ac71930c834ec3f25ed59d6b55e70c0a917dd6"
    ),
}


def prepare_calendar_history(staging: Path, sdk_root: Path) -> dict:
    """Decode the accepted snapshot offline; retain pre-Pilot IPO sessions."""
    source = staging / "sse-st-pilot/completeness-20260910/calendar/sina-trading-calendar.txt"
    metadata = json.loads(source.with_suffix(".txt.meta.json").read_bytes())
    if sha(source.read_bytes()) != metadata["sha256"]:
        raise ValueError("ACCEPTED_CALENDAR_SNAPSHOT_CHANGED")
    decoder = sdk_root / "akshare/stock/cons.py"
    record = sdk_root / "akshare-1.18.94.dist-info/RECORD"
    expected = next(
        row[1]
        for row in csv.reader(record.read_text().splitlines())
        if row[0] == "akshare/stock/cons.py"
    )
    if expected != "sha256=" + base64.urlsafe_b64encode(
        bytes.fromhex(sha(decoder.read_bytes()))
    ).decode().rstrip("="):
        raise ValueError("PINNED_CALENDAR_DECODER_CHANGED")
    tree = ast.parse(decoder.read_text())
    code = next(
        ast.literal_eval(n.value)
        for n in tree.body
        if isinstance(n, ast.Assign)
        and any(isinstance(t, ast.Name) and t.id == "hk_js_decode" for t in n.targets)
    )
    runtime = import_module("py_mini_racer").MiniRacer()
    runtime.eval(code)
    decoded = runtime.call("d", source.read_text().split("=")[1].split(";")[0].replace('"', ""))
    history = sorted({d[:10] for d in decoded if "2022-12-01" <= d[:10] <= END})
    pilot = json.loads((source.parent / "pilot-sessions.json").read_bytes())
    if [d for d in history if START <= d <= END] != pilot:
        raise ValueError("ACCEPTED_PILOT_CALENDAR_CHANGED")
    output = staging / "pilot-akshare-20260911"
    save(output / "calendar-history.json", history)
    provenance = dict(
        source_snapshot_sha256=metadata["sha256"],
        source_metadata=metadata,
        decoder_sha256=sha(decoder.read_bytes()),
        sdk_version="1.18.94",
        history_sha256=sha(canonical(history)),
        sessions=len(history),
        use="Pre-Pilot listing-age evidence; no new calendar acquisition",
    )
    save(output / "calendar-history-provenance.json", provenance)
    return provenance


def write_table(
    root: Path, relative: str, rows: list[dict], keys: tuple[str, ...]
) -> DatasetPartition:
    fields = tuple(sorted(set(keys) | {key for row in rows for key in row}))
    target = root / relative
    temporary = target.with_suffix(".parquet.tmp")
    receipt = write_canonical_parquet(temporary, fieldnames=fields, rows=rows, sort_keys=keys)
    if target.exists() and sha(target.read_bytes()) != receipt.sha256:
        raise ValueError("IMMUTABLE_BUILD_PARTITION_CHANGED:" + relative)
    temporary.replace(target)
    return receipt.model_copy(update={"relative_path": relative})


def delisting_starts(staging: Path) -> dict[str, str]:
    entries = json.loads(
        (staging / "sse-st-pilot/pilot-scope-20260910/coverage-intervals.json").read_bytes()
    )
    for timeline in json.loads(
        (staging / "szse-st-recovery-20260910/audit/security-timelines.json").read_bytes()
    ):
        entries.extend([timeline["anchor"], *timeline["pilot_events"]])
    result = {}
    for entry in entries:
        if entry["status"] == "DELISTING_PERIOD":
            sid, start = entry["security_id"], entry["effective_from"]
            result[sid] = min(start, result.get(sid, start))
    return result


def source_metadata(staging: Path, inputs: dict) -> list[dict]:
    files = [dict(path=inputs["factor_path"], sha256=inputs["factor_sha256"], provider="Sina")]
    if inputs.get("provider") == "Tencent":
        files.extend(dict(**s, provider="Tencent") for s in inputs["sources"])
    else:
        files.append(
            dict(path=inputs["raw_path"], sha256=inputs["raw_sha256"], provider="Eastmoney")
        )
    result = []
    for item in files:
        path = staging / item["path"]
        metadata_path = path.with_suffix(path.suffix + ".meta.json")
        if metadata_path.exists():
            meta = json.loads(metadata_path.read_bytes())
        else:
            # The accepted native-Windows route stores metadata in one acceptance manifest.
            accepted = json.loads((path.parent / "acceptance-manifest.json").read_bytes())
            signature = accepted.pop("canonical_sha256")
            if sha(canonical(accepted)) != signature:
                raise ValueError("ACCEPTED_SOURCE_MANIFEST_CHANGED")
            meta = next(r for r in accepted["sources"] if r["file"] == path.name)
            meta = {**meta, "retrieved_at_utc": meta["retrieval_completed_utc"]}
        timestamp = datetime.fromisoformat(meta["retrieved_at_utc"])
        if (
            meta["sha256"] != item["sha256"]
            or sha(path.read_bytes()) != item["sha256"]
            or timestamp.utcoffset() != UTC.utcoffset(timestamp)
        ):
            raise ValueError("SOURCE_METADATA_PROVENANCE_CHANGED")
        result.append(
            dict(
                path=item["path"],
                provider=item["provider"],
                raw_content_sha256=item["sha256"],
                request_url=meta["url"],
                request_parameters=parse_qs(urlsplit(meta["url"]).query),
                retrieval_timestamp_utc=meta["retrieved_at_utc"],
            )
        )
    return sorted(result, key=lambda r: r["path"])


def publication_inputs(staging: Path, repository: Path) -> tuple[list[dict], dict, dict]:
    state = json.loads((repository / ".research/project_state.json").read_bytes())
    if state["current_stage"] != "R2" or state["status"] != "RUNNING" or state["dataset_frozen"]:
        raise ValueError("R2_PUBLICATION_NOT_AUTHORIZED")
    preflight = json.loads(
        (staging / "pilot-execution-20260911/source-authority-preflight.json").read_bytes()
    )
    signature = preflight.pop("canonical_sha256")
    if signature != state["source_manifest_sha256"] or sha(canonical(preflight)) != signature:
        raise ValueError("SOURCE_AUTHORITY_PREFLIGHT_CHANGED")
    preflight["canonical_sha256"] = signature
    if preflight["SOURCE_AUTHORITY_PREFLIGHT"] != "PASS":
        raise ValueError("SOURCE_AUTHORITY_PREFLIGHT_NOT_PASS")
    members = pilot_members(staging)
    root = staging / "pilot-akshare-20260911"
    primary = json.loads((root / "recovery-checkpoint.json").read_bytes())
    if sha((root / "recovery-checkpoint.json").read_bytes()) != state["r2_checkpoint_sha256"]:
        raise ValueError("ORIGINAL_PRIMARY_CHECKPOINT_CHANGED")
    secondary = json.loads((root / "secondary-checkpoint.json").read_bytes())
    policy = repository / "docs/research/CN_A_RAW_OHLCV_FAILOVER_V1.json"
    if (
        secondary["policy_sha256"] != state["raw_failover_policy_sha256"]
        or sha(policy.read_bytes()) != secondary["policy_sha256"]
    ):
        raise ValueError("FROZEN_RAW_FAILOVER_POLICY_CHANGED")
    if primary["completed"].keys() & secondary["completed"].keys():
        raise ValueError("SECONDARY_REPLACED_PRIMARY")
    required = {m["security_id"] for m in members}
    completed = {
        sid: record
        for sid, record in {**primary["completed"], **secondary["completed"]}.items()
        if sid in required
    }
    if completed.keys() != required or secondary["failures"].keys() & required:
        raise ValueError("UNRESOLVED_REQUIRED_DATA")
    partitions = json.loads((root / "partition-checkpoint.json").read_bytes())
    if partitions["failures"] or set(partitions["partitions"]) != required:
        raise ValueError("INCOMPLETE_OR_FAILED_PARTITIONS")
    return members, completed, preflight


def publish(staging: Path, repository: Path) -> dict:
    members, completed, preflight = publication_inputs(staging, repository)
    for relative, expected in ACCEPTED_INPUTS.items():
        if sha((staging / relative).read_bytes()) != expected:
            raise ValueError("ACCEPTED_PILOT_INPUT_CHANGED:" + relative)
    root = staging / "pilot-akshare-20260911"
    source_root = root / "dataset-staging"
    receipts = json.loads((root / "partition-checkpoint.json").read_bytes())["partitions"]
    amount = json.loads((staging / "raw-failover-v1/amount-impact-current-audit.json").read_bytes())
    if (
        amount["available_securities"] != len(members)
        or amount["available_rows"] != sum(r["raw_rows"] for r in receipts.values())
        or amount["amount_decisions_ambiguous"]
        or amount["outlier_count"]
        or amount["classification"] != "LIMITED_PRECISION_PARITY"
    ):
        raise ValueError("FULL_IN_SCOPE_AMOUNT_AUDIT_NOT_PASS")
    scope_root = staging / "instrument-scope-20260912"
    scope = json.loads((scope_root / "approved-scope-manifest.json").read_bytes())
    facts = json.loads((scope_root / "approved-classifications.json").read_bytes())
    by_id = {r["classification"]["security_id"]["value"]: r for r in facts}
    sessions = json.loads(
        (staging / "sse-st-pilot/completeness-20260910/calendar/pilot-sessions.json").read_bytes()
    )
    if (
        sessions != sorted(set(sessions))
        or not sessions
        or sessions[0] < START
        or sessions[-1] > END
    ):
        raise ValueError("INVALID_ACCEPTED_CALENDAR")
    get_status = status_lookup(staging)
    starts = delisting_starts(staging)
    calendar_history = json.loads((root / "calendar-history.json").read_bytes())
    calendar_provenance = json.loads((root / "calendar-history-provenance.json").read_bytes())
    if (
        sha(canonical(calendar_history)) != calendar_provenance["history_sha256"]
        or [d for d in calendar_history if START <= d <= END] != sessions
    ):
        raise ValueError("LISTING_AGE_CALENDAR_CHANGED")
    build = root / "catalog-build"
    final = staging.parent / DATASET_ID
    input_digest = sha(
        canonical(
            dict(
                completed=completed,
                scope=scope,
                preflight=preflight,
                receipts=receipts,
                amount=amount,
                calendar_provenance=calendar_provenance,
                accepted_input_hashes=ACCEPTED_INPUTS,
            )
        )
    )
    build_record = root / "catalog-build-checkpoint.json"
    checkpoint = (
        json.loads(build_record.read_bytes())
        if build_record.exists()
        else dict(
            input_sha256=input_digest,
            retrieval_timestamp=datetime.now(UTC).isoformat(),
            published=False,
        )
    )
    if checkpoint["input_sha256"] != input_digest:
        raise ValueError("CATALOG_BUILD_INPUTS_CHANGED")
    save(build_record, checkpoint)
    if final.exists():
        manifest = load_manifest(final / "manifest.json")
        verify_dataset(final, manifest)
        report = json.loads((root / "publication-report.json").read_bytes())
        if report["manifest_sha256"] != manifest.canonical_sha256:
            raise ValueError("EXISTING_PUBLICATION_MISMATCH")
        save(
            build_record,
            {**checkpoint, "published": True, "manifest_sha256": manifest.canonical_sha256},
        )
        save(
            root / "publication-resume-verification.json",
            dict(
                status="PASS",
                input_sha256=input_digest,
                manifest_sha256=manifest.canonical_sha256,
                verified_at_utc=datetime.now(UTC).isoformat(),
                source_refetched=False,
                partitions_rewritten=False,
            ),
        )
        return report
    partitions, missing, lineage = [], [], []
    counts = dict(
        total_bars=0,
        st_observations=0,
        star_st_observations=0,
        suspension_observations_confirmed=0,
        suspension_status_unknown=0,
        tradeability_status_unknown=0,
        missing_observations=0,
        adjustment_rows=0,
        primary_source_securities=0,
        secondary_source_securities=0,
    )
    for member in sorted(members, key=lambda m: m["security_id"]):
        sid = member["security_id"]
        receipt = receipts[sid]
        for kind in ("raw", "factor"):
            expected_source = completed[sid][kind + "_sha256"]
            if (
                receipt["source_hashes"][kind] != expected_source
                or sha((staging / completed[sid][kind + "_path"]).read_bytes()) != expected_source
            ):
                raise ValueError("PUBLICATION_SOURCE_LINEAGE_CHANGED")
        for item in receipt["files"]:
            source, target = source_root / item["relative_path"], build / item["relative_path"]
            if sha(source.read_bytes()) != item["sha256"]:
                raise ValueError("INPUT_PARTITION_CHANGED")
            target.parent.mkdir(parents=True, exist_ok=True)
            if not target.exists():
                temporary = target.with_suffix(".parquet.tmp")
                shutil.copyfile(source, temporary)
                temporary.replace(target)
            if sha(target.read_bytes()) != item["sha256"]:
                raise ValueError("COPIED_PARTITION_CHANGED")
            partitions.append(DatasetPartition.model_validate(item))
        relative = f"{member['exchange']}/{member['symbol']}"
        bars = parquet.read_table(source_root / relative / "raw.parquet").to_pylist()
        dates = [r["trading_date"] for r in bars]
        gaps = missing_intervals(member, sessions, dates)
        missing.extend(
            dict(security_id=sid, **gap, classification="MISSING_NOT_INFERRED_SUSPENSION")
            for gap in gaps
        )
        counts["missing_observations"] += sum(g["sessions"] for g in gaps)
        present = set(dates)
        states = []
        for day in sessions:
            if day < member["listing_date"] or (
                member["delisting_date"] and day >= member["delisting_date"]
            ):
                continue
            risk = get_status(sid, day)
            if risk not in {"NORMAL", "ST", "STAR_ST", "DELISTING_PERIOD"}:
                raise ValueError("UNKNOWN_ST_POINT_IN_TIME")
            states.append(
                dict(
                    security_id=sid,
                    trading_date=day,
                    risk_status=risk,
                    delisting_period_start=starts.get(sid) if risk == "DELISTING_PERIOD" else None,
                    is_st=risk in {"ST", "STAR_ST"},
                    is_star_st=risk == "STAR_ST",
                    bar_observed=day in present,
                    is_suspended=None,
                    is_tradeable=None,
                    execution_state="NO_FILL_UNLESS_SEPARATE_OFFICIAL_TRADEABILITY_EVIDENCE",
                    status_source="SSE_OFFICIAL_RECONCILED"
                    if member["exchange"] == "SSE"
                    else "SZSE_ACCEPTED_DATED",
                )
            )
            counts["st_observations"] += int(day in present and risk == "ST")
            counts["star_st_observations"] += int(day in present and risk == "STAR_ST")
        counts["suspension_status_unknown"] += len(states)
        counts["tradeability_status_unknown"] += len(states)
        partitions.append(
            write_table(
                build, relative + "/daily-state.parquet", states, ("security_id", "trading_date")
            )
        )
        counts["total_bars"] += len(bars)
        counts["adjustment_rows"] += receipt["factor_rows"]
        provider = "Tencent" if completed[sid].get("provider") == "Tencent" else "Eastmoney"
        counts[
            "secondary_source_securities" if provider == "Tencent" else "primary_source_securities"
        ] += 1
        lineage.append(
            dict(
                security_id=sid,
                provider=provider,
                underlying_source=provider,
                input_lineage_json=canonical(completed[sid]).decode(),
                source_metadata_json=canonical(source_metadata(staging, completed[sid])).decode(),
                provider_interface="AKShare 1.18.94 stock_zh_a_hist_tx"
                if provider == "Tencent"
                else "AKShare 1.18.94 stock_zh_a_hist(adjust=empty)",
                normalized_logical_sha256=next(
                    p["logical_sha256"]
                    for p in receipt["files"]
                    if p["relative_path"].endswith("/raw.parquet")
                ),
                date_coverage_json=canonical([dates[0], dates[-1]]).decode(),
                failover_reason=completed[sid].get("failover_reason", "PRIMARY_SUCCEEDED"),
                instrument_classification_json=canonical(by_id[sid]).decode(),
            )
        )
    benchmark_root = staging / "benchmark-route-20260910"
    benchmark_manifest = json.loads((benchmark_root / "acceptance-manifest.json").read_bytes())
    benchmark_path = benchmark_root / "CSI300-1.json"
    expected = next(
        r["sha256"] for r in benchmark_manifest["files"] if r["path"] == benchmark_path.name
    )
    if sha(benchmark_path.read_bytes()) != expected:
        raise ValueError("ACCEPTED_BENCHMARK_CHANGED")
    benchmark = []
    for line in json.loads(benchmark_path.read_bytes())["data"]["klines"]:
        fields = line.split(",")
        benchmark.append(
            dict(
                benchmark_id="CSI300_PRICE_INDEX", trading_date=fields[0], close=Decimal(fields[2])
            )
        )
    if [r["trading_date"] for r in benchmark] != sessions:
        raise ValueError("BENCHMARK_CALENDAR_MISMATCH")
    rule_bytes = (staging / "pilot-execution-20260911/normalized-rules.json").read_bytes()
    if sha(rule_bytes) != preflight["normalized_rule_sha256"]:
        raise ValueError("ACCEPTED_RULES_CHANGED")
    tables = (
        (
            "securities.parquet",
            [dict(**m, instrument_type="COMMON_A_SHARE") for m in members],
            ("security_id",),
        ),
        ("candidate-master.parquet", candidate_members(staging), ("security_id",)),
        (
            "out-of-scope.parquet",
            [
                dict(
                    security_id=r["security_id"],
                    instrument_type=r["instrument_type"],
                    status=r["status"],
                    evidence_json=canonical(r).decode(),
                )
                for r in json.loads((scope_root / "out-of-scope-instruments.json").read_bytes())
            ],
            ("security_id",),
        ),
        (
            "calendar.parquet",
            [dict(session_date=d, is_open=True) for d in sessions],
            ("session_date",),
        ),
        ("csi300-bars.parquet", benchmark, ("trading_date",)),
        (
            "calendar-history.parquet",
            [dict(session_date=d, is_open=True) for d in calendar_history],
            ("session_date",),
        ),
        ("missing-observations.parquet", missing, ("security_id", "effective_from")),
        ("lineage.parquet", lineage, ("security_id",)),
        (
            "contracts.parquet",
            [
                dict(name="SOURCE_AUTHORITY_PREFLIGHT", payload=canonical(preflight).decode()),
                dict(name="INSTRUMENT_SCOPE", payload=canonical(scope).decode()),
                dict(name="EFFECTIVE_MARKET_RULES", payload=rule_bytes.decode()),
                dict(name="AMOUNT_PRECISION_AUDIT", payload=canonical(amount).decode()),
                dict(name="ACCEPTED_INPUT_HASHES", payload=canonical(ACCEPTED_INPUTS).decode()),
                dict(
                    name="CALENDAR_HISTORY_PROVENANCE",
                    payload=canonical(calendar_provenance).decode(),
                ),
            ],
            ("name",),
        ),
    )
    for relative, rows, keys in tables:
        partitions.append(write_table(build, relative, rows, keys))
    manifest = finalize_manifest(
        dict(
            dataset_id=DATASET_ID,
            provider="AKShare:Eastmoney+Tencent;Sina;SSE;SZSE",
            provider_version="1.18.94",
            retrieval_timestamp=checkpoint["retrieval_timestamp"],
            coverage_start=START,
            coverage_end=END,
            security_count=len(members),
            symbols=tuple(sorted(m["symbol"] for m in members)),
            exchanges=("SSE", "SZSE"),
            fields=tuple(sorted(bars[0])),
            adjustment_method="Separate Sina HFQ factors; as-of features only; raw execution",
            rule_version=preflight["market_rule_manifest_sha256"],
            source_lineage=(
                "source-preflight:" + preflight["canonical_sha256"],
                "instrument-scope:" + sha(canonical(scope)),
                "frozen-raw-failover:"
                + sha((repository / "docs/research/CN_A_RAW_OHLCV_FAILOVER_V1.json").read_bytes()),
            ),
            partitions=tuple(sorted(partitions, key=lambda p: p.relative_path)),
            known_limitations=(
                "Pilot only, not frozen and not authorized for strategy studies",
                "Master names are display metadata, not historical name or ST eligibility inputs",
                "Tencent LIMITED_PRECISION_PARITY; "
                "amount decisions pass the accepted interval audit",
                "Missing bars are not synthetic observations or inferred suspensions",
                "Official daily suspension/tradeability is not certified by OHLCV; "
                "unknown remains null and no-fill",
                "Raw pre_close is not fabricated; missing execution reference causes no-fill",
                "Separate HFQ feature factors are not a complete corporate-action cash-flow ledger",
            ),
        )
    )
    write_manifest(build / "manifest.json", manifest)
    verify_dataset(build, manifest)
    report = dict(
        dataset_id=DATASET_ID,
        coverage=[START, END],
        securities=len(members),
        pre_scope_filter_candidates=scope["total_master_securities"],
        instrument_counts=scope["counts"],
        board_counts=dict(Counter(m["board"] for m in members)),
        exchange_counts=dict(Counter(m["exchange"] for m in members)),
        trading_sessions=len(sessions),
        benchmark_rows=len(benchmark),
        **counts,
        failed_securities=0,
        unresolved_required_data=0,
        rejected_observations=0,
        manifest_sha256=manifest.canonical_sha256,
        manifest_file_sha256=sha((build / "manifest.json").read_bytes()),
        dataset_audited=False,
        dataset_frozen=False,
        input_sha256=input_digest,
    )
    save(root / "publication-report.json", report)
    build.rename(final)
    save(
        build_record,
        {**checkpoint, "published": True, "manifest_sha256": manifest.canonical_sha256},
    )
    print(json.dumps(report), flush=True)
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--staging", required=True, type=Path)
    parser.add_argument("--repository", required=True, type=Path)
    parser.add_argument("--prepare-calendar-history", action="store_true")
    parser.add_argument("--sdk-root", type=Path)
    args = parser.parse_args()
    if args.prepare_calendar_history:
        if args.sdk_root is None:
            parser.error("--sdk-root is required for offline calendar decoding")
        print(json.dumps(prepare_calendar_history(args.staging, args.sdk_root)))
    else:
        publish(args.staging, args.repository)
