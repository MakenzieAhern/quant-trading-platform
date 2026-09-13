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


def test_sse_distribution_schema_does_not_double_count_conversion_or_use_net_cash():
    from scripts.audit_sse_distribution_rows import normalize

    old = dict(
        SECURITY_CODE_A="601360",
        RECORD_DATE_A="2013-04-03",
        EX_RIGHT_DATE_A="2013-04-08",
        BONUS_RATE="8",
        CHANGE_RATE="8",
    )
    assert normalize("bonus", old)["amount"] == "0.8"
    current = dict(
        A_STOCK_CODE="600000",
        A_REG_DATE="20230403",
        A_DERIGHTS_DATE="20230404",
        BONUS_RATIO="2",
        CONVERT_RATIO="3",
    )
    assert normalize("bonus", current)["amount"] == "0.5"
    cash = dict(
        SECURITY_CODE_A="600000",
        RECORD_DATE_A="2013-04-03",
        EX_DIVIDEND_DATE_A="2013-04-08",
        DIVIDEND_PER_SHARE1_A="0.285",
        DIVIDEND_PER_SHARE2_A="0.300",
    )
    assert normalize("dividend", cash)["amount"] == "0.300"
    assert normalize("bonus", {**old, "SECURITY_CODE_A": "-"}) is None


def test_szse_monthly_archive_scope_and_official_link_boundary():
    import pytest

    from scripts.collect_szse_distribution_months import month_links, table_link

    entries = [
        f"value:'./{year}{month:02}.html',text:'{year}-{month:02}'"
        for year in range(2010, 2026)
        for month in range(1, 13)
    ]
    assert len(month_links("\n".join(entries))) == 192
    assert month_links("\n".join(entries)) == month_links("\n".join(reversed(entries)))
    with pytest.raises(ValueError, match="INCOMPLETE"):
        month_links("\n".join(entries[:-1]))
    menu = "https://investor.szse.cn/market/periodical/month/example.html"
    assert (
        table_link('<a href="/market/data.html">分红派息配股</a>', menu)
        == "https://investor.szse.cn/market/data.html"
    )
    with pytest.raises(ValueError, match="NON_OFFICIAL"):
        table_link('<a href="https://example.com/data.html">分红派息配股</a>', menu)


def test_szse_monthly_rights_dates_and_b_share_retention():
    import pytest

    from scripts.audit_szse_distribution_months import extract

    header = ["Code"] * 14
    header[6] = "配股数Rts Issues"
    cells = [
        "000960",
        "锡业股份",
        "",
        "",
        "",
        "",
        "150,664,585",
        "2.400",
        "8.980",
        "1,352,967,974",
        "2010/01/27",
        "2010/01/18",
        "28.470",
        "32.980",
    ]

    def html(row):
        return (
            "<table>"
            + "".join(
                "<tr>" + "".join(f"<td>{cell}</td>" for cell in r) + "</tr>" for r in [header, row]
            )
            + "</table>"
        ).encode()

    result = extract(html(cells), "2010-01")[0]
    assert result["rights_candidate"] and result["ex_date"] == "2010-01-27"
    cells[6] = "0"
    assert extract(html(cells), "2010-01")[0]["rights_candidate"]
    with pytest.raises(ValueError, match="DATE_MISMATCH"):
        extract(html(cells), "2010-02")
    cells[0], cells[11] = "200001", "2010/01/29"
    assert extract(html(cells), "2010-01")[0]["record_date"] == "2010-01-29"
    assert extract(html([""] * 14), "2010-01") == []
    with pytest.raises(ValueError, match="UNPARSED"):
        extract(html(["", "partial"] + [""] * 12), "2010-01")
