import pytest

from scripts.collect_targeted_szse_resumption_metadata import (
    check_page_progress,
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


def test_repeated_official_page_is_not_mistaken_for_complete_coverage():
    seen = set()
    page = {"hasMore": True, "announcements": [{"announcementId": "1"}]}
    check_page_progress(page, seen)
    with pytest.raises(ValueError, match="PAGINATION_NONPROGRESS"):
        check_page_progress(page, seen)
