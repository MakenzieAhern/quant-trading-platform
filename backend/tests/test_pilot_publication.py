import json
from decimal import Decimal
from pathlib import Path

import pyarrow.parquet as parquet
import pytest

from app.data.catalog import load_manifest, verify_dataset
from app.domain.markets.cn_a_rules import historical_cn_a_rules
from scripts.audit_published_pilot import audit as audit_catalog
from scripts.publish_akshare_pilot import publication_inputs, publish, source_metadata, write_table
from scripts.reconcile_sse_cninfo import canonical, save, sha
from scripts.stage_akshare_pilot import DATASET_ID


def test_publication_is_complete_atomic_resumable_and_preserves_unknowns(tmp_path, monkeypatch):
    monkeypatch.setattr("scripts.publish_akshare_pilot.ACCEPTED_INPUTS", {})
    monkeypatch.setattr("scripts.publish_akshare_pilot.delisting_starts", lambda *_: {})
    staging = tmp_path / "staging"
    repository = tmp_path / "repository"
    root = staging / "pilot-akshare-20260911"
    source_root = root / "dataset-staging"
    history = ["2023-01-03", "2023-01-04"]
    save(root / "calendar-history.json", history)
    save(root / "calendar-history-provenance.json", dict(history_sha256=sha(canonical(history))))
    sid = "CN-A:SSE:123456"
    member = dict(
        security_id=sid,
        symbol="123456",
        exchange="SSE",
        board="SSE_MAIN",
        name="Synthetic",
        listing_date="2023-01-03",
        delisting_date="",
    )
    raw = [
        dict(
            security_id=sid,
            trading_date="2023-01-03",
            raw_open="10",
            raw_close="10",
            raw_high="11",
            raw_low="9",
            pre_close=None,
            volume="100",
            amount="1000",
            adjusted_close=None,
        )
    ]
    factors = [dict(security_id=sid, effective_from="2023-01-03", hfq_factor="2")]
    files = [
        write_table(source_root, "SSE/123456/raw.parquet", raw, ("security_id", "trading_date")),
        write_table(
            source_root, "SSE/123456/factors.parquet", factors, ("security_id", "effective_from")
        ),
    ]
    save(staging / "original-raw.json", raw)
    save(staging / "original-factor.json", factors)
    for kind, payload in (("raw", raw), ("factor", factors)):
        save(
            staging / f"original-{kind}.json.meta.json",
            dict(
                sha256=sha(canonical(payload)),
                retrieved_at_utc="2026-09-12T00:00:00Z",
                url=f"https://fixture.invalid/{kind}",
            ),
        )
    completed = {
        sid: dict(
            raw_path="original-raw.json",
            raw_sha256=sha(canonical(raw)),
            factor_path="original-factor.json",
            factor_sha256=sha(canonical(factors)),
        )
    }
    save(
        root / "partition-checkpoint.json",
        dict(
            partitions={
                sid: dict(
                    raw_rows=1,
                    factor_rows=1,
                    files=[f.model_dump(mode="json") for f in files],
                    source_hashes=dict(raw=sha(canonical(raw)), factor=sha(canonical(factors))),
                )
            }
        ),
    )
    save(
        staging / "raw-failover-v1/amount-impact-current-audit.json",
        dict(
            available_securities=1,
            available_rows=1,
            amount_decisions_ambiguous=0,
            outlier_count=0,
            classification="LIMITED_PRECISION_PARITY",
            cross_source_rows=1,
        ),
    )
    save(
        staging / "sse-st-pilot/completeness-20260910/calendar/pilot-sessions.json",
        ["2023-01-03", "2023-01-04"],
    )
    scope_root = staging / "instrument-scope-20260912"
    save(
        scope_root / "approved-scope-manifest.json",
        dict(status="PASS", total_master_securities=1, counts=dict(COMMON_A_SHARE=1)),
    )
    save(
        scope_root / "approved-classifications.json",
        [
            dict(
                classification=dict(
                    security_id=dict(value=sid),
                    instrument_type="COMMON_A_SHARE",
                    effective_from="2023-01-03",
                    source_publication_date="2023-01-02",
                    source_url="https://www.sse.com.cn/fixture",
                    source_document_sha256="a" * 64,
                    retrieval_timestamp="2026-09-12T00:00:00Z",
                )
            )
        ],
    )
    save(scope_root / "out-of-scope-instruments.json", [])
    save(repository / "docs/research/CN_A_RAW_OHLCV_FAILOVER_V1.json", dict(policy="TEST"))
    rule_path = staging / "pilot-execution-20260911/normalized-rules.json"
    save(rule_path, historical_cn_a_rules().model_dump(mode="json"))
    preflight = dict(
        normalized_rule_sha256=sha(rule_path.read_bytes()),
        market_rule_manifest_sha256="a" * 64,
        canonical_sha256="b" * 64,
    )
    benchmark_root = staging / "benchmark-route-20260910"
    save(
        benchmark_root / "CSI300-1.json",
        dict(data=dict(klines=["2023-01-03,1,2", "2023-01-04,2,3"])),
    )
    save(
        benchmark_root / "acceptance-manifest.json",
        dict(
            files=[
                dict(
                    path="CSI300-1.json",
                    sha256=sha((benchmark_root / "CSI300-1.json").read_bytes()),
                )
            ]
        ),
    )
    monkeypatch.setattr(
        "scripts.publish_akshare_pilot.publication_inputs",
        lambda *args: ([member], completed, preflight),
    )
    monkeypatch.setattr("scripts.publish_akshare_pilot.candidate_members", lambda *_: [member])
    monkeypatch.setattr(
        "scripts.publish_akshare_pilot.status_lookup", lambda *_: lambda *args: "NORMAL"
    )
    rename = Path.rename

    def interrupted(path, target):
        if path.name == "catalog-build":
            assert (path / "manifest.json").is_file()
            assert not target.exists()
            raise OSError("simulated interruption before atomic publication")
        return rename(path, target)

    monkeypatch.setattr(Path, "rename", interrupted)
    with pytest.raises(OSError, match="simulated interruption"):
        publish(staging, repository)
    final = tmp_path / DATASET_ID
    assert not final.exists()
    staged_manifest = (root / "catalog-build/manifest.json").read_bytes()
    monkeypatch.setattr(Path, "rename", rename)
    report = publish(staging, repository)
    assert (final / "manifest.json").read_bytes() == staged_manifest
    assert publish(staging, repository) == report
    assert not report["dataset_frozen"] and not report["dataset_audited"]
    assert report["missing_observations"] == 1 and report["total_bars"] == 1
    assert report["tradeability_status_unknown"] == 2
    assert report["suspension_observations_confirmed"] == 0
    states = parquet.read_table(final / "SSE/123456/daily-state.parquet").to_pylist()
    assert [r["bar_observed"] for r in states] == ["1", "0"]
    assert all(r["is_suspended"] is None and r["is_tradeable"] is None for r in states)
    manifest = load_manifest(final / "manifest.json")
    verify_dataset(final, manifest)
    assert sha((final / files[0].relative_path).read_bytes()) == files[0].sha256
    # Exercise catalog-level audit wiring on this small synthetic publication;
    # original source parsers and the real 2580 checkpoint have separate checks.
    monkeypatch.setattr("scripts.audit_published_pilot.ACCEPTED_INPUTS", {})
    monkeypatch.setattr("scripts.audit_published_pilot.pilot_members", lambda *_: [member])
    monkeypatch.setattr("scripts.audit_published_pilot.candidate_members", lambda *_: [member])
    monkeypatch.setattr("scripts.audit_published_pilot.delisting_starts", lambda *_: {})
    monkeypatch.setattr(
        "scripts.audit_published_pilot.status_lookup", lambda *_: lambda *_: "NORMAL"
    )
    monkeypatch.setattr("scripts.audit_published_pilot.normalized_bars", lambda *_: raw)
    monkeypatch.setattr(
        "scripts.audit_published_pilot.parse_factors", lambda *_: [("2023-01-03", Decimal(2))]
    )
    monkeypatch.setattr(
        "scripts.audit_published_pilot.verify_preserved_checkpoint", lambda *_: "a" * 64
    )
    audited = audit_catalog(staging, final)
    assert audited["dataset_audited"] and not audited["dataset_frozen"]
    assert audited["resume_restart"] == "PASS"
    assert audited["missing_observations"] == 1
    before = (final / "manifest.json").read_bytes()
    save(
        staging / "raw-failover-v1/amount-impact-current-audit.json",
        dict(
            available_securities=1,
            available_rows=1,
            amount_decisions_ambiguous=1,
            outlier_count=0,
            classification="INSUFFICIENT_EVIDENCE",
        ),
    )
    with pytest.raises(ValueError, match="AMOUNT_AUDIT_NOT_PASS"):
        publish(staging, repository)
    assert (final / "manifest.json").read_bytes() == before


def test_publication_controller_cannot_cross_frozen_or_non_r2_gate(tmp_path):
    for state in (
        dict(current_stage="R3", status="RUNNING", dataset_frozen=False),
        dict(current_stage="R2", status="RUNNING", dataset_frozen=True),
        dict(current_stage="R2", status="BLOCKED", dataset_frozen=False),
    ):
        save(tmp_path / ".research/project_state.json", state)
        with pytest.raises(ValueError, match="NOT_AUTHORIZED"):
            publication_inputs(tmp_path, tmp_path)
    assert (
        json.loads((tmp_path / ".research/project_state.json").read_bytes())["status"] == "BLOCKED"
    )


def test_source_metadata_reuses_accepted_combined_manifest(tmp_path):
    (tmp_path / "original.json").write_bytes(b"source")
    checksum = sha(b"source")
    source = dict(
        file="original.json",
        sha256=checksum,
        retrieval_completed_utc="2026-09-12T00:00:00Z",
        url="https://fixture.invalid/raw",
    )
    manifest = dict(sources=[source])
    save(
        tmp_path / "acceptance-manifest.json",
        {**manifest, "canonical_sha256": sha(canonical(manifest))},
    )
    inputs = dict(
        raw_path="original.json",
        factor_path="original.json",
        raw_sha256=checksum,
        factor_sha256=checksum,
    )
    assert len(source_metadata(tmp_path, inputs)) == 2
    with pytest.raises(ValueError, match="PROVENANCE_CHANGED"):
        source_metadata(tmp_path, {**inputs, "raw_sha256": "b" * 64})
