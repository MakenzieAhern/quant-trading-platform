"""Rebuild the approved Pilot revision using pinned parent sources, never parent verdicts."""

import argparse
import json
import shutil
from pathlib import Path

import pyarrow.parquet as pq

from app.data.catalog import load_manifest, verify_dataset
from app.data.providers.research import DailyBarRecord
from app.domain.markets.security import InstrumentClassification
from scripts.audit_amount_impact import QUANTUM, interval_decisions, status_lookup
from scripts.audit_raw_failover import normalized
from scripts.materialize_akshare_partitions import normalized_bars
from scripts.publish_akshare_pilot import ACCEPTED_INPUTS, delisting_starts, publish, write_table
from scripts.reconcile_sse_cninfo import canonical, save, sha
from scripts.sina_adjustment_audit import parse_factors
from scripts.stage_akshare_pilot import DATASET_ID, END, START, scope_members

V2 = "cn-a-pilot-akshare-20230101-20240731-v2"


def prepare(staging: Path, repository: Path) -> dict:
    parent = staging.parent / DATASET_ID
    manifest = load_manifest(parent / "manifest.json")
    verify_dataset(parent, manifest)
    state = json.loads((repository / ".research/project_state.json").read_bytes())
    if state.get("revised_pilot_rebuild_decision") != "APPROVED" or state.get(
        "revised_pilot_dataset_frozen"
    ):
        raise ValueError("REBUILD_NOT_AUTHORIZED")
    if manifest.canonical_sha256 != state.get(
        "pilot_v1_manifest_sha256", state["pilot_manifest_sha256"]
    ):
        raise ValueError("PARENT_MANIFEST_CHANGED")
    root = staging / "pilot-v2-build"
    master = staging / "pilot-v2-master"
    impact = json.loads((master / "master-impact.json").read_bytes())
    if (
        impact["removed"]
        or impact["conflicts"]
        or any(
            d["missing"] or d["extra"] for d in impact["independent_baseline_differences"].values()
        )
    ):
        raise ValueError("MASTER_NOT_RECONCILED")
    candidates = json.loads((master / "candidate-master.json").read_bytes())
    if sha(canonical(candidates)) != impact["candidate_master_sha256"]:
        raise ValueError("MASTER_DIGEST_CHANGED")
    evidence = json.loads((master / "new-member-evidence.json").read_bytes())
    raw_checkpoint = json.loads((staging / "pilot-v2-raw/checkpoint.json").read_bytes())
    changed = {r["security_id"] for r in impact["changed_lifecycles"]}
    added = set(impact["new_active_during_pilot"])
    if raw_checkpoint["failures"] or set(raw_checkpoint["completed"]) != changed | added:
        raise ValueError("REVISED_RAW_INPUTS_INCOMPLETE")
    facts = json.loads(
        (staging / "instrument-scope-20260912/approved-classifications.json").read_bytes()
    )
    for entry in evidence:
        fact = entry["classification"]
        facts.append(
            dict(classification=fact, sources=[], revised_evidence=entry["classification_evidence"])
        )
    # Rebuild changed typed-listing facts from the corrected official A-only register.
    source = next(
        r
        for r in impact["evidence"]
        if r["raw_snapshot_filename"] == "sse-a-boards-terminated.json"
    )
    for entry in facts:
        sid = entry["classification"]["security_id"]["value"]
        if sid in changed:
            member = next(m for m in candidates if m["security_id"] == sid)
            if member["exchange"] != "SSE" or member["board"] != "SSE_MAIN":
                raise ValueError("CHANGED_CLASSIFICATION_REQUIRES_DATED_REVIEW")
            entry["classification"] = InstrumentClassification(
                security_id={"value": sid},
                instrument_type="COMMON_A_SHARE",
                effective_from=member["listing_date"],
                source_publication_date=None,
                evidence_basis="ORIGINAL_TYPED_LISTING_REGISTER",
                source_listing_date=member["listing_date"],
                source_url=source["source_url"],
                source_document_sha256=source["sha256"],
                retrieval_timestamp=source["retrieved_at"],
            ).model_dump(mode="json")
            entry["sources"] = [source]
            entry.pop("original_typed_listing_fields", None)
    members = scope_members(
        candidates, [InstrumentClassification.model_validate(r["classification"]) for r in facts]
    )
    prior_members = {
        r["security_id"]: r for r in pq.read_table(parent / "securities.parquet").to_pylist()
    }
    original = staging / "pilot-akshare-20260911"
    primary = json.loads((original / "recovery-checkpoint.json").read_bytes())
    secondary = json.loads((original / "secondary-checkpoint.json").read_bytes())
    completed = {**primary["completed"], **secondary["completed"]}
    pending = dict(primary["pending"])
    old_receipts = json.loads((original / "partition-checkpoint.json").read_bytes())["partitions"]
    receipts, reuse, reused_daily = {}, [], {}
    parent_parts = {p.relative_path: p.model_dump(mode="json") for p in manifest.partitions}
    sessions = json.loads(
        (staging / "sse-st-pilot/completeness-20260910/calendar/pilot-sessions.json").read_bytes()
    )
    old_status = status_lookup(staging)
    new_status = {r["member"]["security_id"]: r for r in evidence}
    starts = delisting_starts(staging)
    for sid, entry in new_status.items():
        for event in entry["events"]:
            if event["status"] == "DELISTING_PERIOD":
                starts[sid] = event["effective_from"]

    def get_status(sid, day):
        if sid not in new_status:
            return old_status(sid, day)
        entry = new_status[sid]
        eligible = [e for e in entry["events"] if START <= e["effective_from"] <= day]
        return (
            max(eligible, key=lambda e: e["effective_from"])["status"]
            if eligible
            else entry["anchor"]["status"]
        )

    amount_decisions, ambiguous = 0, []
    policy_sha = state["raw_failover_policy_sha256"]
    for member in members:
        sid = member["security_id"]
        prefix = f"{member['exchange']}/{member['symbol']}/"
        if sid not in added | changed:
            before = prior_members[sid]
            keys = (
                "security_id",
                "symbol",
                "exchange",
                "board",
                "listing_date",
                "delisting_date",
                "effective_from",
                "effective_to",
            )
            if any(before[k] != member[k] for k in keys):
                raise ValueError("UNCLASSIFIED_PARTITION_INTERPRETATION_CHANGE")
            receipts[sid] = old_receipts[sid]
            daily = parent_parts[prefix + "daily-state.parquet"]
            reused_daily[sid] = daily
            reuse.append(
                dict(
                    path=daily["relative_path"],
                    disposition="REUSED_V1",
                    sha256=daily["sha256"],
                    logical_sha256=daily["logical_sha256"],
                )
            )
            for part in old_receipts[sid]["files"]:
                source_path = parent / part["relative_path"]
                if sha(source_path.read_bytes()) != part["sha256"]:
                    raise ValueError("PARENT_PARTITION_CHANGED")
                target = root / "dataset-staging" / part["relative_path"]
                target.parent.mkdir(parents=True, exist_ok=True)
                if not target.exists():
                    shutil.copyfile(source_path, target)
                if sha(target.read_bytes()) != part["sha256"]:
                    raise ValueError("REUSED_PARTITION_CHANGED")
                reuse.append(
                    dict(
                        path=part["relative_path"],
                        disposition="REUSED_V1",
                        **{k: part[k] for k in ("sha256", "logical_sha256")},
                    )
                )
            bars = pq.read_table(parent / prefix / "raw.parquet").to_pylist()
        else:
            checkpoint = raw_checkpoint["completed"][sid]
            inputs = checkpoint["inputs"]
            if sid in added:
                raw_path = staging / inputs["raw_path"]
                rows = normalized(raw_path.read_bytes(), member, set(sessions))
                raw_meta = json.loads(raw_path.with_suffix(".raw.meta.json").read_bytes())
                pending[sid] = dict(
                    error_type="RemoteDisconnected", round=2, attempts=inputs["primary_attempts"]
                )
                sources = [dict(path=inputs["raw_path"], sha256=inputs["raw_sha256"])]
                payload = dict(
                    format="TENCENT_RAW_V1",
                    rows=rows,
                    sources=sources,
                    policy_sha256=policy_sha,
                    primary_failure_sha256=sha(canonical(pending[sid])),
                    amount_decisions_sha256=sha(canonical(interval_decisions(rows, QUANTUM))),
                )
                normalized_path = root / "normalized" / f"{member['symbol']}.json"
                save(normalized_path, payload)
                inputs = dict(
                    provider="Tencent",
                    raw_path=str(normalized_path.relative_to(staging)),
                    raw_sha256=sha(canonical(payload)),
                    factor_path=inputs["factor_path"],
                    factor_sha256=inputs["factor_sha256"],
                    sources=sources,
                    policy_sha256=policy_sha,
                    failover_reason="CONNECTION_CLOSED_BEFORE_HTTP",
                    retrieval_timestamp_utc=raw_meta["retrieved_at_utc"],
                )
            else:
                inputs = completed[sid]
                if inputs.get("provider") == "Tencent":
                    rows = json.loads((staging / inputs["raw_path"]).read_bytes())["rows"]
                else:
                    rows = normalized_bars(
                        (staging / inputs["raw_path"]).read_bytes(), member, set(sessions)
                    )
            if inputs.get("provider") == "Tencent":
                bars = []
                for row in rows:
                    bar = DailyBarRecord.model_validate(row).model_dump(mode="python")
                    bar.update(security_id=sid, source="AKShare:stock_zh_a_hist_tx:Tencent:day:raw")
                    bars.append(bar)
            else:
                bars = rows
            code = ("sh" if member["exchange"] == "SSE" else "sz") + member["symbol"]
            curve = parse_factors((staging / inputs["factor_path"]).read_bytes(), code, "hfq")
            baseline = max((d for d, _ in curve if d <= START), default=None)
            factors = [
                dict(
                    security_id=sid,
                    effective_from=d,
                    hfq_factor=v,
                    source="AKShare:Sina:hfq-factor",
                    simulation_use="AS_OF_FEATURE_ONLY",
                )
                for d, v in curve
                if d <= END and (d >= START or d == baseline)
            ]
            parts = [
                write_table(
                    root / "dataset-staging",
                    prefix + "raw.parquet",
                    bars,
                    ("security_id", "trading_date"),
                ),
                write_table(
                    root / "dataset-staging",
                    prefix + "factors.parquet",
                    factors,
                    ("security_id", "effective_from"),
                ),
            ]
            receipts[sid] = dict(
                files=[p.model_dump(mode="json") for p in parts],
                raw_rows=len(bars),
                factor_rows=len(factors),
                source_hashes={k: inputs[k + "_sha256"] for k in ("raw", "factor")},
            )
            completed[sid] = inputs
            reuse.extend(
                dict(
                    path=p.relative_path,
                    disposition="NEW" if sid in added else "REBUILT_LIFECYCLE_CHANGED",
                    sha256=p.sha256,
                    logical_sha256=p.logical_sha256,
                )
                for p in parts
            )
        normalized_amount = [
            dict(trading_date=str(r["trading_date"]), amount=str(r["amount"])) for r in bars
        ]
        decisions = interval_decisions(
            normalized_amount,
            QUANTUM if completed[sid].get("provider") == "Tencent" else QUANTUM * 0,
        )
        schedule = set(sessions[252::20])
        checked = [
            r
            for r in decisions
            if r["day"] in schedule and get_status(sid, r["day"]) not in {"ST", "STAR_ST"}
        ]
        amount_decisions += len(checked)
        ambiguous.extend(dict(security_id=sid, **r) for r in checked if not r["stable"])
    if ambiguous:
        save(root / "ambiguous-amount.json", ambiguous)
        raise ValueError("AMBIGUOUS_AMOUNT_DECISION")
    completed = {m["security_id"]: completed[m["security_id"]] for m in members}
    save(root / "partition-checkpoint.json", dict(partitions=receipts, failures={}))
    save(
        root / "reuse-rebuild-manifest.json",
        dict(
            parent_dataset_id=DATASET_ID,
            parent_manifest_sha256=manifest.canonical_sha256,
            supersedes_reason="SECURITY_MASTER_COMPLETENESS_DEFECT",
            partitions=reuse,
        ),
    )
    for name in ("calendar-history.json", "calendar-history-provenance.json"):
        save(root / name, json.loads((original / name).read_bytes()))
    accepted = {
        k: v for k, v in ACCEPTED_INPUTS.items() if not k.startswith("security-master-pilot/")
    }
    for name in (
        "sse-security-master.csv",
        "szse-security-master.csv",
        "master-impact.json",
        "new-member-evidence.json",
    ):
        accepted["pilot-v2-master/" + name] = sha((master / name).read_bytes())
    preflight = json.loads(
        (staging / "pilot-execution-20260911/source-authority-preflight.json").read_bytes()
    )
    original_preflight_sha = preflight.pop("canonical_sha256")
    if (
        original_preflight_sha
        != state.get("preserved_v1_source_manifest_sha256", state["source_manifest_sha256"])
        or sha(canonical(preflight)) != original_preflight_sha
    ):
        raise ValueError("PRESERVED_PREFLIGHT_CHANGED")
    preflight.update(
        parent_dataset_id=DATASET_ID,
        supersedes_reason="SECURITY_MASTER_COMPLETENESS_DEFECT",
        revised_master_sha256=impact["candidate_master_sha256"],
    )
    preflight["canonical_sha256"] = sha(canonical(preflight))
    scope = json.loads(
        (staging / "instrument-scope-20260912/approved-scope-manifest.json").read_bytes()
    )
    scope.update(
        total_master_securities=len(candidates),
        post_scope_filter_securities=len(members),
        classifications_sha256=sha(canonical(facts)),
    )
    scope["counts"]["COMMON_A_SHARE"] = len(members)
    amount = json.loads((staging / "raw-failover-v1/amount-impact-current-audit.json").read_bytes())
    amount.update(
        available_securities=len(members),
        available_rows=sum(r["raw_rows"] for r in receipts.values()),
        amount_decisions_ambiguous=0,
        revised_full_universe_decisions_checked=amount_decisions,
    )
    context = dict(
        dataset_id=V2,
        root=root,
        members=members,
        candidates=candidates,
        completed=completed,
        preflight=preflight,
        accepted_inputs=accepted,
        amount=amount,
        scope=scope,
        facts=facts,
        get_status=get_status,
        starts=starts,
        receipts=receipts,
        reused_daily=reused_daily,
        primary_pending=pending,
    )
    save(
        root / "revision-context.json",
        {k: v for k, v in context.items() if k not in {"root", "get_status"}},
    )
    return context


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--staging", type=Path, required=True)
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--prepare-only", action="store_true")
    parser.add_argument("--audit", action="store_true")
    args = parser.parse_args()
    revision = prepare(args.staging, args.repository)
    if not args.prepare_only:
        publish(args.staging, args.repository, revision=revision)
        publish(args.staging, args.repository, revision=revision)
        if args.audit:
            from scripts.audit_published_pilot import audit

            print(json.dumps(audit(args.staging, args.staging.parent / V2, revision=revision)))
