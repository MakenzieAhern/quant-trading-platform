from scripts.build_szse_resumption_gap_queue import candidate_queue, suspension_intervals


def test_candidate_queue_is_limited_to_unresolved_intervals():
    unresolved = [
        {
            "security_id": "CN-A:SZSE:000001",
            "symbol": "000001",
            "suspended_at": "2010/01/04 09:30",
        }
    ]
    suspensions = [
        {"symbol": "000001", "suspended_at": "2010/01/04 09:30"},
        {"symbol": "000001", "suspended_at": "2010/01/08 09:30"},
    ]
    source = {"path": "p", "sha256": "a"}
    announcements = [
        (
            {
                "announcementId": "1",
                "secCode": "000001",
                "announcementTime": 1262620800000,
                "announcementTitle": "公告",
                "adjunctUrl": "finalpage/2010-01-05/1.PDF",
            },
            source,
        ),
        (
            {
                "announcementId": "2",
                "secCode": "000001",
                "announcementTime": 1262880000000,
                "announcementTitle": "下一次停牌公告",
                "adjunctUrl": "finalpage/2010-01-08/2.PDF",
            },
            source,
        ),
    ]
    queue = candidate_queue(announcements, suspension_intervals(unresolved, suspensions), set())
    assert [row["announcement_id"] for row in queue] == ["1"]
