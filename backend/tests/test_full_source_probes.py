import json
import subprocess
import sys

from scripts import probe_full_corporate_actions as probe
from scripts import probe_full_exit_factors as factors


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
