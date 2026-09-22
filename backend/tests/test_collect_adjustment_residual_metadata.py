from datetime import date

from scripts.collect_adjustment_residual_metadata import (
    complete_bounded_announcements,
    gaps,
    org_ids,
)


def test_bounded_gap_windows_and_retained_org_identity(tmp_path):
    metadata = tmp_path / "metadata.json"
    metadata.write_text(
        '{"announcements":[{"secCode":"000010","orgId":"gssz0000010"}]}',
        encoding="utf-8",
    )
    report = {
        "uncovered": [
            {
                "factor_change": "FACTOR:CN-A:SZSE:000010:2013-07-19",
                "reason": "NO_RETAINED_CNINFO_IMPLEMENTATION_METADATA_WITHIN_60_DAYS",
            }
        ]
    }

    assert org_ids([metadata], {"000010"}) == {"000010": "gssz0000010"}
    row = gaps(report, 365, 7)[0]
    assert date.fromisoformat(row["start"]) == date(2012, 7, 19)
    assert date.fromisoformat(row["end"]) == date(2013, 7, 26)

    duplicate = {"announcementId": "1", "title": "same"}
    assert complete_bounded_announcements(
        [
            {"totalAnnouncement": 2, "hasMore": True, "announcements": [duplicate]},
            {"totalAnnouncement": 2, "hasMore": False, "announcements": [duplicate]},
        ]
    ) == [duplicate]
