from scripts.collect_full_suspensions import sse_url, szse_rows, szse_table_link


def test_official_suspension_source_parsers_preserve_exact_boundaries():
    menu = '<a href="/market/periodical/documents/a.html">证券停牌情况<i></i></a>'.encode()
    assert (
        szse_table_link(menu, "https://www.szse.cn/market/periodical/month/x.html")
        == "https://www.szse.cn/market/periodical/documents/a.html"
    )
    raw = """
    <table><tr><td>000001</td><td>平安银行</td><td>重大事项</td>
    <td>2010/01/04 09:30</td><td>2010/01/05 09:30</td></tr>
    <tr><td>000002</td><td>万科A</td><td>待公告</td>
    <td>2010/01/06 13:00</td><td>&nbsp;</td></tr></table>
    """.encode("gb18030")
    assert szse_rows(raw) == [
        {
            "symbol": "000001",
            "name": "平安银行",
            "reason": "重大事项",
            "suspended_at": "2010/01/04 09:30",
            "resumed_at": "2010/01/05 09:30",
        },
        {
            "symbol": "000002",
            "name": "万科A",
            "reason": "待公告",
            "suspended_at": "2010/01/06 13:00",
            "resumed_at": None,
        },
    ]
    assert "startStopDate=20100101" in sse_url(2010, 1)
    assert "pageHelp.pageNo=1" in sse_url(2010, 1)
