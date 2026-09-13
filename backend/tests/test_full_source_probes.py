import json
import subprocess
import sys

from scripts import probe_full_corporate_actions as probe
from scripts import probe_full_exit_factors as factors


def test_corporate_probe_stops_on_access_denial_and_reuses_checkpoint(tmp_path, monkeypatch):
    sdk = tmp_path / "sdk/baostock"
    sdk.mkdir(parents=True)
    (sdk / "__init__.py").write_text("")
    calls = []

    def denied(*args, **kwargs):
        calls.append(args)
        return subprocess.CompletedProcess(args, 0, 'RESULT={"login_error_code":"10001006"}\n', "")

    monkeypatch.setattr(probe.subprocess, "run", denied)
    monkeypatch.setattr(
        sys, "argv", ["probe", "--sdk-root", str(sdk.parent), "--output", str(tmp_path)]
    )
    probe.main()
    probe.main()
    assert len(calls) == 1
    assert (
        json.loads((tmp_path / "probe.json").read_bytes())["corporate_action_authority"]
        == "NOT_ESTABLISHED"
    )


def test_exit_factor_probe_does_not_drop_missing_baseline(tmp_path, monkeypatch):
    master = tmp_path / "master.json"
    master.write_text(
        json.dumps(
            [
                dict(
                    security_id="CN-A:SSE:600000",
                    exchange="SSE",
                    symbol="600000",
                    listing_date="1999-01-01",
                    delisting_date="2011-01-01",
                )
            ]
        )
    )
    monkeypatch.setattr(factors, "fetch", lambda *args: b'var sh600000hfq={"total":0,"data":[]};')
    monkeypatch.setattr(
        sys, "argv", ["probe", "--lifecycles", str(master), "--output", str(tmp_path)]
    )
    factors.main()
    report = json.loads((tmp_path / "exit-factor-report.json").read_bytes())
    assert report["checked"] == 1
    assert report["results"][0]["status"] == "UNRESOLVED"


def test_full_calendar_clips_future_and_rejects_duplicates():
    import pytest

    from scripts.extend_full_calendar import sessions

    data = ["2009-12-31T00:00:00Z", "2010-01-04T00:00:00Z", "2026-01-05T00:00:00Z"]
    assert sessions(data) == (["2009-12-31", "2010-01-04"], ["2010-01-04"])
    assert sessions(data) == sessions(list(reversed(data)))
    with pytest.raises(ValueError, match="DUPLICATE"):
        sessions(data + data[:1])
    with pytest.raises(ValueError, match="WEEKEND"):
        sessions(["2010-01-03"])


def test_full_benchmark_identity_calendar_and_decimal_prices():
    from decimal import Decimal

    import pytest

    from scripts.audit_full_benchmark import normalize

    row = dict(
        indexCode="000300", tradeDate="20100104", open="10", high="11", low="9", close="10.50"
    )
    payload = dict(code="200", data=[row])
    assert normalize(payload, ["2010-01-04"])[0]["close"] == Decimal("10.50")
    with pytest.raises(ValueError, match="CALENDAR"):
        normalize(payload, ["2010-01-01"])
    with pytest.raises(ValueError, match="CALENDAR"):
        normalize(dict(code="200", data=[row, row]), ["2010-01-04"])
    with pytest.raises(ValueError, match="IDENTITY"):
        normalize(dict(code="200", data=[{**row, "indexCode": "000905"}]), ["2010-01-04"])
    with pytest.raises(ValueError, match="OHLC"):
        normalize(dict(code="200", data=[{**row, "close": "NaN"}]), ["2010-01-04"])


def test_distribution_source_pagination_is_complete_and_order_independent():
    import pytest

    from scripts.collect_sse_distributions import checked_rows

    pages = [
        dict(pageHelp=dict(total=2), result=[dict(code=code)]) for code in ("600000", "600001")
    ]
    assert checked_rows(pages) == checked_rows(list(reversed(pages)))
    with pytest.raises(ValueError, match="PAGINATION"):
        checked_rows(pages[:1])
    with pytest.raises(ValueError, match="DUPLICATED"):
        checked_rows([pages[0], pages[0]])
