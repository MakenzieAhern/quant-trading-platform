import pytest

from scripts.audit_pilot_observations import missing_intervals


def test_missing_intervals_preserve_lifecycle_and_do_not_invent_suspension():
    member = dict(listing_date="2023-01-04", delisting_date="2023-01-10")
    sessions = ["2023-01-03", "2023-01-04", "2023-01-05", "2023-01-06", "2023-01-09", "2023-01-10"]
    expected = [
        dict(effective_from="2023-01-04", effective_to="2023-01-05", sessions=2),
        dict(effective_from="2023-01-09", effective_to="2023-01-09", sessions=1),
    ]
    assert missing_intervals(member, sessions, ["2023-01-06"]) == expected
    assert missing_intervals(member, sessions[::-1], ["2023-01-06"]) == expected
    assert missing_intervals(member, sessions, sessions[1:-1]) == []
    for invalid in (["2023-01-03"], ["2023-01-10"], ["2023-01-06"] * 2):
        with pytest.raises(ValueError, match="DUPLICATE_OR_OUT_OF_LIFECYCLE"):
            missing_intervals(member, sessions, invalid)
