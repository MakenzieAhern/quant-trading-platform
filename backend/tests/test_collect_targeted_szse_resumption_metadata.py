from scripts.collect_targeted_szse_resumption_metadata import (
    offset_windows,
    query_windows,
    queue_rows,
    retry_windows,
)


def test_query_windows_stop_before_next_suspension_and_queue_deduplicates():
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
    windows = query_windows(unresolved, suspensions, 14)
    assert windows[0]["end"] == "2010-01-07"
    result = {
        **windows[0],
        "records": [
            {
                "announcementId": "1",
                "secCode": "000001",
                "announcementTime": 1262620800000,
                "announcementTitle": "公告",
                "adjunctUrl": "finalpage/2010-01-05/1.PDF",
            }
        ],
    }
    assert len(queue_rows([result, result], set())) == 1
    assert retry_windows(windows, {"failures": [windows[0]]}) == windows
    assert offset_windows(query_windows(unresolved, suspensions, 14), 3)[0]["start"] == "2010-01-07"
