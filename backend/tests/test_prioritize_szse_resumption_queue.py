import re

from scripts.prioritize_szse_resumption_queue import prioritize


def test_prioritize_merges_overlapping_windows_without_promoting_titles():
    row = {
        "url": "https://static.cninfo.com.cn/finalpage/1.pdf",
        "issuer": "000001",
        "announcement_id": "1",
        "title": "关于停牌的公告",
        "published_on": "2010-01-04",
        "affected_suspensions": [["CN-A:SZSE:000001", "2010/01/04 09:30"]],
    }
    extra = {**row, "affected_suspensions": [["CN-A:SZSE:000001", "2010/01/05 09:30"]]}
    selected, total = prioritize([[row], [extra, {**row, "url": "other", "title": "年度报告"}]])
    assert total == 2
    assert len(selected) == 1
    assert len(selected[0]["affected_suspensions"]) == 2
    assert prioritize([[row]], re.compile("停牌"), {row["url"]}) == ([], 1)
