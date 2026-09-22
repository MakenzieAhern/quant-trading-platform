import json
from pathlib import Path

import pytest

from app.domain.markets.corporate_actions import CorporateAction
from scripts.audit_full_adjustment_inventory import audit
from scripts.reconcile_sse_cninfo import canonical, sha


def test_retained_factor_inventory_preserves_baseline_future_and_unresolved_gaps(tmp_path):
    sid, symbol = "CN-A:SSE:600000", "sh600000"
    source_path = tmp_path / (symbol + "-hfq.js")
    rows = [
        {"d": "2008-01-01", "f": "1"},
        {"d": "2009-01-01", "f": "2"},
        {"d": "2010-06-10", "f": "3"},
        {"d": "2011-01-04", "f": "4"},
        {"d": "2026-01-05", "f": "8"},
    ]
    raw = b"var sh600000hfq=" + canonical(dict(total=len(rows), data=rows)) + b";"
    source_path.write_bytes(raw)
    source = dict(
        path=source_path.name,
        sha256=sha(raw),
        url="https://finance.sina.com.cn/realstock/company/sh600000/hfq.js",
        retrieved_at_utc="2026-09-14T00:00:00+00:00",
    )
    source_path.with_suffix(".js.meta.json").write_text(json.dumps(source))
    target = dict(
        security_id=sid,
        exchange="SSE",
        symbol="600000",
        instrument_type="COMMON_A_SHARE",
        effective_from="1999-11-10",
        effective_to=None,
    )
    inventory = dict(
        results=[
            dict(
                target,
                symbol=symbol,
                effective_from="2010-01-01",
                effective_to="2025-12-31",
                sources=[source],
            )
        ]
    )
    event = CorporateAction.model_validate(
        dict(
            security_id=dict(value=sid),
            action_type="CASH_DIVIDEND",
            announcement_date="2010-06-01",
            effective_date="2010-06-10",
            ex_date="2010-06-10",
            cash_per_share="0.1",
            completeness="COMPLETE",
            source_provider="OFFICIAL_ISSUER_CNINFO_EXCHANGE_RECONCILED",
            source_version="test-v1",
            source_record_hash="a" * 64,
        )
    )
    ledger = dict(
        events=[dict(event=event.model_dump(mode="json"), event_checksum=event.event_checksum)]
    )
    report = audit(tmp_path, [target], inventory, dict(results=[]), Path("."), [ledger])
    assert report["authority_accepted"] is False
    assert report["counts"]["change_date_statuses"] == {
        "NO_SUPPORTED_EVENT_DATE": 1,
        "SUPPORTED_EVENT_DATE_MATCH_ONLY": 1,
    }
    interval = report["intervals"][0]
    variant = next(iter(interval["in_interval_variants"].values()))
    assert variant["baseline"] == ["2009-01-01", "2"]
    assert variant["period_rows"] == [["2010-06-10", "3"], ["2011-01-04", "4"]]
    assert interval["sources"][0]["after_interval_rows_not_used"] == [["2026-01-05", "8"]]
    assert interval["sources"][0]["prior_rows_not_used"] == [["2008-01-01", "1"]]
    assert report == audit(tmp_path, [target], inventory, dict(results=[]), Path("."), [ledger])
    missing = dict(results=[dict(inventory["results"][0], source=source)])
    assert report == audit(
        tmp_path,
        [target],
        dict(results=[dict(inventory["results"][0], sources=[])]),
        missing,
        Path("."),
        [ledger],
    )
    with pytest.raises(ValueError, match="MASTER_INTERVAL_MISMATCH"):
        audit(
            tmp_path,
            [{**target, "effective_to": "2024-12-31"}],
            inventory,
            dict(results=[]),
            Path("."),
            [ledger],
        )
    source_path.write_bytes(raw + b"changed")
    with pytest.raises(ValueError, match="CHECKSUM_CHANGED"):
        audit(tmp_path, [target], inventory, dict(results=[]), Path("."), [ledger])
