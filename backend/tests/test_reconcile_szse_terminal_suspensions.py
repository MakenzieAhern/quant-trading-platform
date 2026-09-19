from scripts.reconcile_szse_terminal_suspensions import build_terminal_closures


def test_terminal_closure_requires_bound_suspension_and_official_lifecycle_end():
    document = {
        "issuer": "000001",
        "published_on": "2024-03-06",
        "retrieved_at_utc": "2026-09-19T00:00:00+00:00",
        "source_sha256": "document",
        "title": "终止上市暨停牌风险提示",
        "url": "https://static.cninfo.com.cn/finalpage/example.PDF",
        "affected_suspensions": [["CN-A:SZSE:000001", "2024/03/06 09:30"]],
        "text": "公司股票不进入退市整理期。",
    }
    unresolved = [
        {
            "security_id": "CN-A:SZSE:000001",
            "symbol": "000001",
            "suspended_at": "2024/03/06 09:30",
        }
    ]
    master = [
        {
            "security_id": "CN-A:SZSE:000001",
            "effective_from": "1991-04-03",
            "effective_to": "2024-04-26",
            "source_id": "terminated.xlsx",
            "source_sha256": "master",
            "source_url": "https://www.szse.cn/terminated.xlsx",
        }
    ]

    result = build_terminal_closures([document], unresolved, master)

    assert len(result) == 1
    assert result[0]["terminal_at"] == "2024-04-26"
    assert (
        build_terminal_closures([{**document, "text": "公司可能终止上市。"}], unresolved, master)
        == []
    )
    assert (
        build_terminal_closures([{**document, "affected_suspensions": []}], unresolved, master)
        == []
    )
