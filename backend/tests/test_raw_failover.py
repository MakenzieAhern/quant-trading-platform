import json
from datetime import date, timedelta
from decimal import Decimal

import pytest

from scripts.audit_amount_impact import distribution, interval_decisions
from scripts.audit_raw_failover import merged, normalized, parity
from scripts.audit_tencent_amount import comparison
from scripts.probe_raw_failover import candidate, primary_status, run, tencent_url
from scripts.stage_tencent_pilot import cached_request, recover


def test_primary_status_does_not_guess_network_or_rate_limit():
    failure = {"error_type": "RemoteDisconnected"}
    success = {"valid_raw": True}
    assert primary_status([failure] * 6) == "PRIMARY_SYSTEMIC_TRANSPORT_FAILURE"
    assert primary_status([failure] * 3 + [success] * 3) == "PRIMARY_DEGRADED"
    assert primary_status([success] * 6) == "PRIMARY_HEALTHY"
    assert primary_status([{"http_status": 429}]) == "PRIMARY_RATE_LIMITED"
    assert primary_status([{"error_type": "TimeoutError"}]) == "UNKNOWN"
    assert primary_status([]) == "UNKNOWN"
    assert "640%2C" in tencent_url("SZSE", "000001", 2023)
    assert "qfq" not in tencent_url("SZSE", "000001", 2023)
    with pytest.raises(ValueError):
        tencent_url("SSE", "000001", 2025)


def test_finished_probe_and_access_denial_never_restart(tmp_path):
    (tmp_path / "report.json").write_text(
        json.dumps({"status": "PRIMARY_SYSTEMIC_TRANSPORT_FAILURE", "results": []})
    )
    run(tmp_path / "nonexistent-staging", tmp_path)
    (tmp_path / "access-denial-stop.json").write_text("{}")
    candidate(tmp_path / "nonexistent-staging", tmp_path)


def sample(rows=None, *, adjusted=False):
    rows = rows or [["2023-01-03", "10", "11", "12", "9", "100", {}, "1", "11"]]
    return (
        "kline_day2023="
        + json.dumps({"code": 0, "data": {"sz000001": {"qfqday" if adjusted else "day": rows}}})
    ).encode()


MEMBER = dict(
    security_id="CN-A:SZSE:000001",
    symbol="000001",
    exchange="SZSE",
    board="SZSE_MAIN",
    listing_date="1991-04-03",
    delisting_date="",
)


def test_amount_comparison_preserves_precision_and_zero_denominator():
    row = comparison("1761249149.98", "176124.92", "10000")
    assert row["absolute_difference"] == "50.02"
    assert row["raw_secondary_amount"] == "176124.92"
    assert comparison("0", "0", "1")["relative_difference"] == "0"
    assert comparison("0", "1", "1")["relative_difference"] is None
    for invalid in ("NaN", "Infinity", "-1"):
        with pytest.raises(ValueError):
            comparison(invalid, "1", "10000")


def test_amount_interval_propagation_does_not_choose_favorable_boundary():
    rows = [
        dict(trading_date=(date(2023, 1, 1) + timedelta(days=i)).isoformat(), amount="10000000")
        for i in range(20)
    ]
    decisions = interval_decisions(rows, Decimal(100))
    assert all(r["stable"] for r in decisions[:19])  # Presence threshold unchanged.
    assert decisions[-1]["decision_with_lower_bound"] is False
    assert decisions[-1]["decision_with_upper_bound"] is True
    assert interval_decisions(rows, Decimal(0))[-1]["stable"] is True
    high = [{**r, "amount": "10000100"} for r in rows]
    assert interval_decisions(high, Decimal(100))[-1]["stable"] is True
    zero = [{**r, "amount": "0"} for r in rows]
    assert interval_decisions(zero, Decimal(100))[-1]["lower"] == "0"
    with pytest.raises(ValueError):
        interval_decisions(list(reversed(rows)), Decimal(100))
    with pytest.raises(ValueError):
        interval_decisions(rows, Decimal(-1))
    assert distribution([Decimal(1), Decimal(2), Decimal(3), Decimal(4)])["median"] == "2.5"


def test_secondary_failed_slot_is_immutable_and_retry_classification_survives(
    tmp_path, monkeypatch
):
    path = tmp_path / "raw.json"
    path.with_suffix(".json.meta.json").write_text(
        json.dumps(dict(url="https://example.test", error="TimeoutError"))
    )
    monkeypatch.setattr(
        "scripts.stage_tencent_pilot.fetch", lambda *a: pytest.fail("must not repeat a failed slot")
    )
    with pytest.raises(ConnectionError, match="PERSISTED_TRANSPORT"):
        cached_request([], path, "https://example.test")


def test_secondary_recovery_retains_provider_lineage_without_touching_primary(
    tmp_path, monkeypatch
):
    def request(candidates, target, url):
        raw = (
            b'var sz000001hfq={"total":1,"data":[{"d":"1900-01-01","f":"1"}]}'
            if url.endswith("hfq.js")
            else sample([["2023-01-03", "10", "11", "12", "9", "100", {}, "1", "11.00"]])
        )
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(raw)
        return target, raw, dict(retrieved_at_utc="2026-09-11T00:00:00+00:00")

    monkeypatch.setattr("scripts.stage_tencent_pilot.cached_request", request)
    result = recover(
        tmp_path,
        MEMBER,
        dict(error_type="RemoteDisconnected", round=2),
        0,
        ["2023-01-03"],
        lambda sid, day: "NORMAL",
        "policy-hash",
    )
    assert result["status"] == "PRIMARY_FAILED_SECONDARY_RECOVERED"
    assert result["raw_rows"] == 1
    assert result["underlying_source"] == "Tencent"
    assert len(result["sources"]) == 2
    assert not (tmp_path / "pilot-akshare-20260911/recovery-checkpoint.json").exists()
    content = json.loads((tmp_path / result["raw_path"]).read_bytes())
    assert content["rows"][0]["amount"] == "110000.00"
    assert content["rows"][0]["adjusted_close"] is None


def test_candidate_units_raw_only_and_lifecycle_guards():
    rows = normalized(sample(), MEMBER, {"2023-01-03"})
    assert rows[0]["volume"] == "10000"
    assert rows[0]["amount"] == "110000"
    assert rows[0]["adjusted_close"] is None
    with pytest.raises(ValueError, match="RAW_DAY_UNAVAILABLE"):
        normalized(sample(adjusted=True), MEMBER, {"2023-01-03"})
    with pytest.raises(ValueError, match="LIFECYCLE"):
        normalized(sample(), {**MEMBER, "delisting_date": "2023-01-03"}, {"2023-01-03"})
    with pytest.raises(ValueError, match="LIFECYCLE"):
        normalized(sample(), {**MEMBER, "listing_date": "2023-01-04"}, {"2023-01-03"})
    row = ["2023-01-03", "10", "11", "12", "9", "100", {}, "1", "11"]
    with pytest.raises(ValueError, match="DUPLICATE_DATE"):
        normalized(sample([row, row]), MEMBER, {"2023-01-03"})
    with pytest.raises(ValueError):
        normalized(sample([[*row[:5], "-1", *row[6:]]]), MEMBER, {"2023-01-03"})
    with pytest.raises(ValueError):
        normalized(sample([[*row[:3], "10", *row[4:]]]), MEMBER, {"2023-01-03"})


def test_year_overlap_is_reproducible_but_conflicts_fail():
    rows = normalized(sample(), MEMBER, {"2023-01-03"})
    assert merged([rows, []]) == merged([[], rows]) == merged([rows, rows])
    with pytest.raises(ValueError, match="CONFLICTING"):
        merged([rows, [{**rows[0], "raw_close": "10"}]])


def test_parity_does_not_expand_rounding_to_hide_disagreement():
    rows = normalized(sample(), MEMBER, {"2023-01-03"})

    def primary(amount):
        return json.dumps({"data": {"klines": [f"2023-01-03,10,11,12,9,100,{amount}"]}}).encode()

    assert not any(
        r["classification"] == "UNEXPLAINED_DIFFERENCE"
        for r in parity(rows, primary("109950"), False)
    )
    differences = parity(rows, primary("109949.98"), False)
    assert differences[-1]["classification"] == "UNEXPLAINED_DIFFERENCE"
    assert differences[-1]["difference"] == "50.02"
    changed = [{**rows[0], "raw_close": "11.01"}]
    assert any(
        r["classification"] == "MATERIAL_PRICE_DIFFERENCE"
        for r in parity(changed, primary("110000"), False)
    )
    assert parity([], primary("110000"), False)[0]["classification"] == "MISSING_DATE_DIFFERENCE"
