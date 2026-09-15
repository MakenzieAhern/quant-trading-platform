import json
import subprocess
import sys

from scripts import probe_full_corporate_actions as probe
from scripts import probe_full_exit_factors as factors


def test_full_szse_name_probe_keeps_unknown_anchor_and_rejects_future_leakage():
    import pytest

    from scripts.probe_full_szse_st import probe, yearbook_names

    page = "PRICE CHANGE OF STOCKS\n1 000034\n\ue012ST 深泰\n1\n"
    assert yearbook_names([page])["000034"]["status"] == "STAR_ST"
    with pytest.raises(ValueError, match="DUPLICATE"):
        yearbook_names([page, page])

    member = dict(
        symbol="000001",
        security_id="CN-A:SZSE:000001",
        listing_date="1991-01-01",
        delisting_date="",
        effective_from="1991-01-01",
    )
    event = dict(symbol="000001", effective_from="2010-05-01", old_status="NORMAL", status="ST")
    future = {**event, "effective_from": "2026-01-01", "old_status": "NORMAL"}
    assert probe([member], [event]) == probe([member], [future, event])
    result = probe([member], [event])
    assert result["anchors"][0]["anchor"] is None
    assert result["anchors"][0]["status"] == "NO_PRESTART_DATED_ANCHOR"
    conflict = {**event, "effective_from": "2011-01-01", "old_status": "NORMAL"}
    assert len(probe([member], [event, conflict])["risk_chain_gaps"]) == 1
    assert probe([member], [event, conflict]) == probe([member], [conflict, event])


def test_instrument_resume_checks_identity_lifecycle_and_source_bytes(tmp_path):
    import pytest

    from app.data.catalog.checksums import sha256_file
    from scripts.classify_pilot_instruments import classify
    from scripts.extend_full_instrument_scope import validate_receipt

    source = tmp_path / "register.json"
    source.write_text("{}")
    member = dict(
        security_id="CN-A:SSE:600000",
        symbol="600000",
        exchange="SSE",
        board="SSE_MAIN",
        listing_date="1999-11-10",
        instrument_type="COMMON_A_SHARE",
        sources=[
            dict(
                path=source.name,
                sha256=sha256_file(source),
                source_url="https://www.sse.com.cn/register",
                retrieval_timestamp_utc="2026-09-14T00:00:00Z",
            )
        ],
        source_fields=dict(A_STOCK_CODE="600000", LIST_DATE="19991110"),
    )
    receipt = dict(
        security_id=member["security_id"], status="CLASSIFIED", result=classify(tmp_path, member)
    )
    assert validate_receipt(tmp_path, member, receipt) == receipt
    with pytest.raises(ValueError, match="IDENTITY"):
        validate_receipt(tmp_path, {**member, "security_id": "CN-A:SSE:600001"}, receipt)
    with pytest.raises(ValueError, match="CLASSIFICATION"):
        validate_receipt(tmp_path, {**member, "listing_date": "1999-11-11"}, receipt)
    source.write_text("changed")
    with pytest.raises(ValueError, match="SOURCE"):
        validate_receipt(tmp_path, member, receipt)


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


def test_official_distribution_notice_pagination_cannot_silently_truncate():
    import pytest

    from scripts.collect_distribution_notices import complete_announcements

    pages = [
        dict(totalAnnouncement=2, hasMore=True, announcements=[dict(announcementId="b")]),
        dict(totalAnnouncement=2, hasMore=False, announcements=[dict(announcementId="a")]),
    ]
    assert [r["announcementId"] for r in complete_announcements(pages)] == ["a", "b"]
    assert complete_announcements(pages) == complete_announcements(list(reversed(pages)))
    with pytest.raises(ValueError, match="PAGINATION"):
        complete_announcements(pages[:1])
    with pytest.raises(ValueError, match="DUPLICATED"):
        complete_announcements([pages[0], {**pages[1], "announcements": pages[0]["announcements"]}])


def test_notice_worker_stops_immediately_on_repeated_page(tmp_path, monkeypatch):
    from app.data.catalog.checksums import sha256_file
    from scripts import collect_distribution_notices as notices

    category = tmp_path / "list-search.json"
    category.write_text(
        json.dumps({"sse": {"category": [{"key": "category_qyfpxzcs_szsh", "value": "权益分派"}]}})
    )
    (tmp_path / "list-search.json.meta.json").write_text(
        json.dumps({"sha256": sha256_file(category)})
    )
    calls = []

    def repeated(root, name, url, params):
        calls.append((params["seDate"], params["pageNum"]))
        (root / (name + ".meta.json")).write_text("{}")
        return json.dumps(
            dict(totalAnnouncement=60, hasMore=True, announcements=[dict(announcementId="same")])
        ).encode()

    monkeypatch.setattr(notices, "fetch", repeated)
    monkeypatch.setattr(sys, "argv", ["notices", "--root", str(tmp_path)])
    notices.main()
    assert len(calls) == 32 and max(page for _, page in calls) == 2
    report = json.loads((tmp_path / "implementation-metadata-v2.json").read_bytes())
    assert len(report["failure_manifest"]) == 16
    assert all("REPEATED_PAGE_STOP" in r["error"] for r in report["failure_manifest"])


def test_notice_recovery_reuses_tail_and_includes_partial_boundary_day():
    from datetime import UTC, date, datetime

    import pytest

    from scripts.recover_distribution_metadata import reconcile, recovery_ranges

    def row(day, key):
        return dict(
            announcementId=key,
            secCode="600000",
            adjunctUrl=key + ".PDF",
            announcementTime=int(datetime(2023, 5, day, tzinfo=UTC).timestamp() * 1000),
        )

    retained = [row(23, "a"), row(22, "b")]
    ranges = recovery_ranges(2023, retained)
    assert len(ranges) == 5
    assert ranges[-1] == (date(2023, 5, 1), date(2023, 5, 22))
    combined = [*retained, row(22, "b"), row(22, "c")]
    assert reconcile(combined, 3) == reconcile(list(reversed(combined)), 3)
    with pytest.raises(ValueError, match="COUNT_MISMATCH"):
        reconcile(combined, 4)
    with pytest.raises(ValueError, match="CONFLICTING"):
        reconcile([*combined, {**retained[0], "secCode": "600001"}], 3)
    with pytest.raises(ValueError, match="NOT_DESCENDING"):
        recovery_ranges(2023, list(reversed(retained)))
    assert len(recovery_ranges(2023, [])) == 12


def test_distribution_notice_dates_require_bound_labels_not_unrelated_dates():
    from scripts.link_distribution_notices import notice_dates

    assert notice_dates(
        ["1 \n \n股权登记日为2010年8月5日,除息日为2010年8月6", "2 \n \n日。每10股4.80元"]
    ) == (["2010-08-05"], ["2010-08-06"])
    # A standalone digit without the complete ordinal-header pattern is content.
    assert notice_dates(["除息日为2010年8月", "2\n日。"])[1] == ["2010-08-02"]
    assert notice_dates(["权益登记日为2010年5月24日,除息日为2010年5月25日"])[0] == ["2010-05-24"]
    assert notice_dates(["股权登记日:A股为2010年6月7日,B股为2010年6月10日"])[0] == ["2010-06-07"]

    assert notice_dates(["股权登记日:2010 年 03 月 02 日;除权除息日为:2010年3月3日"]) == (
        ["2010-03-02"],
        ["2010-03-03"],
    )
    assert notice_dates(["股权登记日与除权除息日", "董事会2010年3月2日"]) == ([], [])
    assert notice_dates(["A股股权登记日为2010年5月17日;B股股权登记日为2010年5月20日"])[0] == [
        "2010-05-17"
    ]
    assert notice_dates(["除权(息)日:2010年3月24日;除权(除息日):2010年3月24日"])[1] == [
        "2010-03-24"
    ]
    assert notice_dates(["除权(除息)日:2010年3月2日;除息日:2010年3月3日"])[1] == [
        "2010-03-02",
        "2010-03-03",
    ]


def test_merger_raw_boundaries_use_unadjusted_rows_and_reject_duplicate_dates():
    import pytest

    from scripts.reconcile_merger_implementation_batch import raw_boundaries

    payload = b'kline_day2011={"data":{"sh601992":{"day":[["2011-03-01"],["2011-03-02"]]}}}'
    assert raw_boundaries(payload, "SSE", "601992", "2011-03-01", "2011-03-01") == (
        "2011-03-01",
        "2011-03-01",
    )
    with pytest.raises(ValueError, match="RAW_BOUNDARY_DATES_INVALID"):
        raw_boundaries(
            payload.replace(b"2011-03-02", b"2011-03-01"),
            "SSE",
            "601992",
            "2011-03-01",
            "2011-03-02",
        )


def test_reviewed_distribution_dates_require_pinned_identity_pages_and_chronology():
    import pytest

    from scripts.link_distribution_notices import reviewed_dates

    source = dict(issuer="600000", source_sha256="a" * 64, published_on="2010-05-01")
    review = dict(
        symbol="600000",
        source_sha256="a" * 64,
        pages=[1, 2],
        record_date="2010-05-06",
        ex_date="2010-05-07",
    )
    assert reviewed_dates(review, source, 2) == (["2010-05-06"], ["2010-05-07"])
    with pytest.raises(ValueError, match="IDENTITY"):
        reviewed_dates(review, {**source, "source_sha256": "b" * 64}, 2)
    with pytest.raises(ValueError, match="PAGE"):
        reviewed_dates(review, source, 1)
    with pytest.raises(ValueError, match="DATE_ORDER"):
        reviewed_dates({**review, "ex_date": "2001-05-07"}, source, 2)


def test_master_baseline_excludes_future_and_exited_intervals_without_dropping_paused():
    import pytest

    from scripts.audit_full_master_baseline import active_codes, yearbook_codes

    records = [
        dict(
            symbol="600001", exchange="SSE", effective_from="1998-01-01", effective_to="2009-12-29"
        ),
        dict(symbol="601117", exchange="SSE", effective_from="2010-01-07", effective_to=""),
        dict(
            symbol="600057",
            exchange="SSE",
            effective_from="1997-01-01",
            effective_to="",
            status="PAUSED",
        ),
    ]
    assert (
        active_codes(records, "SSE") == active_codes(list(reversed(records)), "SSE") == {"600057"}
    )
    assert yearbook_codes(
        ["公司表\n\uff16\uff10\uff10\uff10\uff15\uff17 *ST 示例\n"], "公司表"
    ) == {"600057": 1}
    assert yearbook_codes(["公司表\n001696 名称\n001896 名称\n"], "公司表") == {
        "001696": 1,
        "001896": 1,
    }
    # The existing master model uses inclusive effective_to dates.
    assert active_codes([{**records[2], "effective_to": "2009-12-31"}], "SSE") == {"600057"}
    with pytest.raises(ValueError, match="DUPLICATE_DIRECTORY_CODE"):
        yearbook_codes(["公司表\n600057 名称\n600057 名称\n"], "公司表")


def test_prestart_notice_header_requires_issuer_and_does_not_scan_body():
    import pytest

    from scripts.probe_full_szse_st import notice_header

    page = "证券代码\uff1a0 0 0 7 3 2 证券简称;*ST 三农 公告编号:2009-75"
    assert notice_header(page, "000732")["status"] == "STAR_ST"
    assert notice_header(page + "正文" * 100 + "证券代码:600505", "000732")["name"] == "*ST三农"
    with pytest.raises(ValueError, match="AMBIGUOUS"):
        notice_header(page, "600505")
    with pytest.raises(ValueError, match="AMBIGUOUS"):
        notice_header("公司年度报告" + "正文" * 100 + page, "000732")
    with pytest.raises(ValueError, match="AMBIGUOUS"):
        notice_header("证券代码:000732 证券简称:三农", "000732")


def test_full_szse_interval_replay_matches_daily_states_and_retains_unknown():
    from scripts.probe_full_szse_st import replay

    member = dict(
        security_id="CN-A:SZSE:000001",
        symbol="000001",
        listing_date="2000-01-01",
        delisting_date="2010-01-06",
        effective_from="2000-01-01",
    )
    anchor = dict(security_id=member["security_id"], anchor={"status": "NORMAL"})
    event = dict(symbol="000001", effective_from="2010-01-05", old_status="NORMAL", status="ST")
    future = dict(event, effective_from="2026-01-01", old_status="ST", status="STAR_ST")
    sessions = ["2010-01-04", "2010-01-05", "2010-01-06", "2010-01-07"]
    result = replay([member], [future, event], [anchor], sessions)
    assert result == replay([member], [event, future], [anchor], sessions)
    assert result["security_days"] == {"NORMAL": 1, "ST": 2}
    assert result["future_event_leakage"] == "PASS"
    assert replay([member], [event], [], sessions)["security_days"] == {"UNKNOWN": 3}
    ipo = {**member, "listing_date": "2010-01-04"}
    assert replay([ipo], [event], [], sessions)["security_days"] == {"NORMAL": 1, "ST": 2}
    conflict = {**event, "old_status": "STAR_ST"}
    bad = replay([ipo], [conflict], [], sessions)
    assert bad["security_days"] == {"UNKNOWN": 3}
    assert len(bad["ipo_initialization_conflicts"]) == 1


def test_distribution_table_dates_require_fixed_columns_and_a_share_placeholder():
    from scripts.link_distribution_notices import notice_dates

    header = "股份类别 股权登记日 最后交易日 除权(息)日 现金红利发放日\n"
    assert notice_dates([header + "A股 2018/7/5 - 2018/7/6 2018/7/6"]) == (
        ["2018-07-05"],
        ["2018-07-06"],
    )
    assert notice_dates([header + "A股 2018/7/12 - 2018/7/13 2018/7/13"]) == (
        ["2018-07-12"],
        ["2018-07-13"],
    )

    assert notice_dates([header + "B股 2018/7/17 2018/7/12 2018/7/13"]) == ([], [])
    assert notice_dates([header + "A股 2018/7/12 2018/7/13 2018/7/13"]) == ([], [])
    assert notice_dates([header + "A股 2018/7/12 - 2018/7/13\n股权登记日:2018年7月11日"]) == (
        ["2018-07-11", "2018-07-12"],
        ["2018-07-13"],
    )


def test_gross_cash_parser_requires_explicit_tax_basis_identity_and_unique_terms():
    from decimal import Decimal, localcontext

    import pytest

    from scripts.reconcile_distribution_cash import gross_cash

    header = "证券代码:600000 证券简称:浦发银行\n"
    assert gross_cash(
        ["证券代码:6 0 0 0 0 0\n每10股送5股、派发现金股利1.2元(含税,扣税后0.58元)"], "600000"
    ) == Decimal("0.12")
    assert gross_cash(
        ["股票代码:000006\n二、利润分配方案\n每10股送3股派发现金股利0.4元(含税)"],
        "000006",
    ) == Decimal("0.04")
    assert gross_cash(
        ["证券代码证券代码证券代码证券代码:: ::600000 600000\n每股现金红利0.1元(税前)"],
        "600000",
    ) == Decimal("0.1")
    for identity in (
        "股票股票股票股票代码代码代码代码:: ::600000 600000",
        "A股代码 600000 H股代码 00600",
        "证券代码:(A 股)600000",
        "证劵代码:600000",
        "证 券 代 号 : 600000",
        "券代码:600000",
        "股票股票股票股票代码代码代码代码:: ::600000600000600000600000",
        "债券代码:143039 债券简称:17北方01\n股票代码:600000",
    ):
        assert gross_cash([identity + "\n每股现金红利0.1元(含税)"], "600000") == Decimal("0.1")
    with pytest.raises(ValueError, match="ISSUER"):
        gross_cash(
            ["证券代码证券代码证券代码证券代码:: ::600004 600004\n每股现金红利0.1元(税前)"],
            "600000",
        )
    with pytest.raises(ValueError, match="ISSUER"):
        gross_cash(["证券代码:凯诺科技 证券简称:600000\n每股现金红利0.1元(含税)"], "600000")
    assert gross_cash([header + "每10股派0.35元(含税,扣税后0.315元)"], "600000") == Decimal("0.035")
    with pytest.raises(ValueError, match="ISSUER"):
        gross_cash(["证券代码:600004\n其他公司证券代码:600000\n每股现金红利0.1元(含税)"], "600000")
    assert gross_cash(
        ["证券代码:000011 200011\n向全体股东每10股派3元人民币现金(含税;扣税后2.7元)"], "000011"
    ) == Decimal("0.3")
    with localcontext() as ctx:
        ctx.prec = 3
        assert gross_cash([header + "每10股派发现金红利1.234567元(含税)"], "600000") == Decimal(
            "0.1234567"
        )
    assert gross_cash([header + "每股派发现金红利0.1元(含税) 每股税后0.09元"], "600000") == Decimal(
        "0.1"
    )
    for content in (
        "每股派发现金红利0.09元(税后)",
        "每股现金红利0.1元",
        "每股现金红利0.1元(含税) 每股现金红利0.2元(含税)",
        "差异化分红送转:是 每股现金红利0.1元(含税)",
    ):
        with pytest.raises(ValueError):
            gross_cash([header + content], "600000")
    with pytest.raises(ValueError, match="ISSUER"):
        gross_cash([header + "每股现金红利0.1元(含税)"], "600004")
    implementation = "二、本次实施的权益分派方案\n每10股派2元人民币现金(含税)\n"
    text = header + "一、原方案\n每10股派1元人民币现金(含税)\n" + implementation
    text += "三、其他资料\n每10股派3元人民币现金(含税)\n"
    assert gross_cash([text], "600000") == Decimal("0.2")
    assert gross_cash(
        [text.replace("本次实施的权益分派方案", "权益分派方案")], "600000"
    ) == Decimal("0.2")
    duplicate = text + implementation
    assert gross_cash([duplicate], "600000") == Decimal("0.2")
    payment_section = "五、权益分派方案\n本次现金红利将划入股东资金账户。\n"
    assert gross_cash([text + payment_section], "600000") == Decimal("0.2")
    for clause in (
        "每10股派发人民币现金2元(含税;扣税后1.8元)",
        "每10股派发现金股利2元人民币现金(含税:扣税后1.8元)",
        "每10股派2元人民币(含税)",
        "每10股分派现金股利人民币2元(含税)",
        "每10股派2元人民币现金[含税;扣税后1.8元]",
        "每10股派2元人民币现金。(含税;扣税后1.8元)",
        "每10股派2元人民币现金,(含税;扣税后1.8元)",
        "每10股分配现金红利2元(含税;扣税后1.8元)",
        "每10股分配现金红利2元(含税。扣税后1.8元)",
        "每10股派2元人民币现金、送3股红股(含税;扣税后1.5元)",
        "每10股派发现金红利人民币2(含税)",
    ):
        assert gross_cash([header + clause], "600000") == Decimal("0.2")
    for invalid in (
        text + implementation.replace("每10股派2元", "每10股派4元"),
        text.replace("二、本次实施的权益分派方案", "二、拟议方案"),
        text.replace("每10股派2元", "每10股派4元(含税) 每10股派2元"),
        text.replace("每10股派2元人民币现金(含税)", "每10股派发现金红利0.403129(含税)"),
        text.replace("本次实施的权益分派方案", "权益分派方案").replace(
            "每10股派2元人民币现金(含税)", "每10股派发现金红利0.403129(含税)"
        ),
        "差异化分红送转:是\n" + text,
    ):
        with pytest.raises(ValueError):
            gross_cash([invalid], "600000")
    assert gross_cash(
        [text.replace("每10股派2元人民币现金(含税)", "每10股派发现金红利人民币0.403129(含税)")],
        "600000",
    ) == Decimal("0.0403129")
    for counter in ("{page}", "{page} / 2", "- {page} -"):
        pages = [
            counter.format(page=1) + "\n" + header + "每10股派0.62元人民币",
            counter.format(page=2) + "\n现金(含税)",
        ]
        assert gross_cash(pages, "600000") == Decimal("0.062")
        with pytest.raises(ValueError):
            gross_cash([pages[0], pages[1].replace("2", "9")], "600000")


def test_differentiated_cash_selects_only_exact_public_a_final_terms():
    from decimal import Decimal

    import pytest

    from scripts.reconcile_distribution_cash import differentiated_cash

    title = "2021年年度权益分派实施公告"
    prefix = "证券代码:600000 2021年年度权益分派实施公告\n"
    suffix = "\n相关日期 股份类别 A股 2022/6/1\n差异化分红送转:是"

    def parse(summary, *, document_title=title, extra=""):
        return differentiated_cash(
            [prefix + "每股分配比例" + summary + suffix + extra],
            "600000",
            document_title,
        )

    assert parse(
        "无限售股股东每股分配现金红利0.32091元(含税),限售股股东每股分配现金红利0.26472元(含税)"
    ) == Decimal("0.32091")
    assert parse("A股每股现金红利0.32元(含税),H股每股现金红利0.28港元") == Decimal("0.32")
    assert parse("A股每股现金红利0.32元(含税),B股每股现金红利0.04美元") == Decimal("0.32")
    assert parse(
        "A股每股现金红利0.32元(含税)",
        extra="董事会预案曾为每10股派9元",
    ) == Decimal("0.32")
    assert parse("社会公众股每股实际分派现金红利0.32元(含税)") == Decimal("0.32")
    assert parse("A股每10股派3.20元(含税)") == Decimal("0.32")

    with pytest.raises(ValueError, match="NON_APPLICABLE"):
        parse("控股股东每股分配现金红利0.50元(含税)")
    with pytest.raises(ValueError, match="NON_APPLICABLE"):
        parse("非公开发行A股股东每股分配现金红利0.50元(含税)")
    with pytest.raises(ValueError, match="AMBIGUOUS"):
        parse("社会公众股每股实际分派现金红利0.32元(含税),无限售股股东每股分配现金红利0.31元(含税)")
    with pytest.raises(ValueError, match="MISSING_FINAL"):
        parse("A股每股现金红利0.32元(含税)", document_title="利润分配预案")
    with pytest.raises(ValueError, match="MISSING_FINAL"):
        parse("A股每股现金红利0.29元(税后)")
    with pytest.raises(ValueError, match="MISSING_FINAL"):
        parse("", extra="虚拟分派的每股现金红利0.32元(含税)")


def test_reconciled_cash_event_requires_lifecycle_and_roundtrips_existing_accounting():
    from datetime import UTC, datetime
    from decimal import Decimal
    from uuid import UUID

    import pytest

    from app.domain.trading import Fill, OrderSide
    from app.event import EventBus, EventType
    from app.portfolio import PortfolioEngine
    from scripts.reconcile_distribution_cash import cash_event, preserve_accepted_events

    # Retained 600000 official 2017 distribution implementation, published 2018-07-06.
    source = dict(
        url="https://static.cninfo.com.cn/finalpage/2018-07-06/1205128052.PDF",
        published_on="2018-07-06",
        title="2017 annual distribution implementation",
        source_sha256="a04586a37fecb9ad0e3d6ab6506c45b5992ad037a3f81b8dd7036cdf94846bea",
        retrieved_at_utc="2026-09-14T00:00:00+00:00",
    )
    row = dict(
        symbol="600000",
        record_date="2018-07-12",
        ex_date="2018-07-13",
        status="EXACT_GROSS_CASH_CORROBORATED",
        exchange_amounts=["0.1"],
        unresolved_documents=[],
        evidence=[dict(cash_per_share="0.1", source=source)],
    )
    member = dict(
        symbol="600000",
        security_id="CN-A:SSE:600000",
        listing_date="1999-11-10",
        effective_from="1999-11-10",
        effective_to=None,
        delisting_date=None,
    )
    event = cash_event(row, [member], {member["security_id"]})
    differentiated_row = {
        **row,
        "status": "SUPPORTED_ORDINARY_A_PUBLIC_TERM",
        "exchange_amounts": ["0.321"],
        "holder_class": "ORDINARY_EXCHANGE_TRADABLE_A_SHARE_PUBLIC_HOLDER",
        "policy_id": "DIFFERENTIATED_CASH_ORDINARY_PUBLIC_A_V1",
        "evidence": [
            {
                "cash_per_share": "0.32091",
                "holder_class": "ORDINARY_EXCHANGE_TRADABLE_A_SHARE_PUBLIC_HOLDER",
                "policy_id": "DIFFERENTIATED_CASH_ORDINARY_PUBLIC_A_V1",
                "source": source,
            }
        ],
    }
    differentiated = cash_event(differentiated_row, [member], {member["security_id"]})
    assert differentiated.cash_per_share == Decimal("0.32091")
    assert differentiated.source_version == "DIFFERENTIATED_CASH_ORDINARY_PUBLIC_A_V1"
    assert (
        differentiated.event_checksum
        == cash_event(differentiated_row, [member], {member["security_id"]}).event_checksum
    )
    corroborated = {
        **differentiated_row,
        "evidence": [
            *differentiated_row["evidence"],
            {
                "cash_per_share": "0.32091",
                "holder_class": "ORDINARY_EXCHANGE_TRADABLE_A_SHARE_PUBLIC_HOLDER",
                "policy_id": "DIFFERENTIATED_CASH_ORDINARY_PUBLIC_A_V1",
                "source": {
                    **source,
                    "url": source["url"].replace("1205128052", "1205128053"),
                },
            },
        ],
    }
    assert cash_event(corroborated, [member], {member["security_id"]}) == cash_event(
        {**corroborated, "evidence": list(reversed(corroborated["evidence"]))},
        [member],
        {member["security_id"]},
    )
    for field in ("holder_class", "policy_id"):
        with pytest.raises(ValueError, match="POLICY_NOT_BOUND"):
            cash_event({**differentiated_row, field: "WRONG"}, [member], {member["security_id"]})
    prior = dict(
        event=event.model_dump(mode="json"),
        event_checksum=event.event_checksum,
        policy_id="EXISTING_ACCEPTED_CASH_DIVIDEND",
    )
    expanded = cash_event(
        {
            **row,
            "evidence": [
                *row["evidence"],
                dict(
                    cash_per_share="0.1",
                    source={**source, "url": source["url"].replace("1205128052", "1205128051")},
                ),
            ],
        },
        [member],
        {member["security_id"]},
    )
    current = {
        **prior,
        "event": expanded.model_dump(mode="json"),
        "event_checksum": expanded.event_checksum,
    }
    source_keys = {(source["url"], source["source_sha256"])}
    assert current["event_checksum"] != prior["event_checksum"]
    assert preserve_accepted_events([current], [prior], source_keys) == [prior]
    assert preserve_accepted_events(
        [{**current, "event": {**current["event"], "cash_per_share": "0.100000"}}],
        [prior],
        source_keys,
    ) == [prior]
    for candidates, old, sources in (
        ([], [prior], source_keys),
        ([current], [prior], set()),
        ([current, current], [prior], source_keys),
        ([current], [prior, prior], source_keys),
        (
            [{**current, "event": {**current["event"], "cash_per_share": "0.2"}}],
            [prior],
            source_keys,
        ),
        ([current], [{**prior, "event_checksum": "0" * 64}], source_keys),
    ):
        with pytest.raises(ValueError):
            preserve_accepted_events(candidates, old, sources)
    for members, ordinary in (
        ([{**member, "listing_date": "2018-07-13"}], {member["security_id"]}),
        ([member], set()),
        ([member, member], {member["security_id"]}),
    ):
        with pytest.raises(ValueError, match="LIFECYCLE"):
            cash_event(row, members, ordinary)
    for quantity in ("1", "81", "100"):
        bus = EventBus()
        emitted = []
        for kind in (EventType.ORDER_FILLED, EventType.ORDER_CREATED, EventType.ORDER_PROPOSAL):
            bus.subscribe(kind, emitted.append)
        portfolio = PortfolioEngine(bus, Decimal(10000))
        # Engineering seed only; verify that the corporate action adds no fill/order.
        portfolio.apply_fill(
            Fill(
                order_id=UUID(int=1),
                strategy_id="accounting-fixture",
                symbol="600000.SSE",
                side=OrderSide.BUY,
                quantity=Decimal(quantity),
                price=Decimal(10),
                commission=Decimal(0),
                timestamp=datetime(2018, 7, 12, tzinfo=UTC),
            )
        )
        before = portfolio.snapshot_at(datetime(2018, 7, 12, tzinfo=UTC))
        position = portfolio.apply_corporate_action(
            "600000.SSE", event, datetime(2018, 7, 13, tzinfo=UTC)
        )
        after = portfolio.snapshot_at(datetime(2018, 7, 13, tzinfo=UTC))
        assert position == before.positions[0]
        assert after.cash - before.cash == Decimal(quantity) * Decimal("0.1")
        assert (
            after.corporate_action_realized_pnl - before.corporate_action_realized_pnl
            == Decimal(quantity) * Decimal("0.1")
        )
        assert after.realized_pnl == before.realized_pnl
        assert emitted == []


def test_sse_yearbook_risk_names_are_scoped_to_historical_tables():
    import pytest

    from scripts.probe_full_sse_st import table_names

    page = "上市公司基本信息 Listed Companies in 2009\n600681 S*ST 万鸿 0.0 0.0\n"
    assert table_names([page], "company")["600681"]["status"] == "STAR_ST"
    assert (
        table_names([page + "600800 S\nT 磁卡 3606.5 2084.5\n"], "company")["600800"]["status"]
        == "ST"
    )
    assert table_names([page], "price") == {}
    assert table_names(["当期公司列表\n600681 正常名称 1.0"], "company") == {}
    with pytest.raises(ValueError, match="DUPLICATE"):
        table_names([page, page], "company")


def test_full_st_metadata_extension_never_requeries_accepted_pilot_months():
    from scripts.collect_full_st_notices import missing_windows

    windows = [(str(a), str(b)) for a, b in missing_windows()]
    assert len(windows) == 173
    assert windows[0] == ("2010-01-01", "2010-01-31")
    assert windows[-1] == ("2025-12-01", "2025-12-31")
    assert all(end < "2023-01-01" or start > "2024-07-31" for start, end in windows)
    assert ("2024-08-01", "2024-08-31") in windows
