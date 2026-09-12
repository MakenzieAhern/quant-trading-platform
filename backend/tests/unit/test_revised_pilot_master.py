import pytest

from scripts.audit_revised_pilot_master import (
    BOARDS,
    overlaps,
    pilot_symbol,
    require_board_coverage,
)


@pytest.mark.parametrize("missing", sorted(BOARDS))
def test_missing_exchange_board_or_exit_segment_fails_closed(missing):
    complete = [{"board": board} for board in sorted(BOARDS)]
    incomplete = [row for row in complete if row["board"] != missing]
    with pytest.raises(ValueError, match="MISSING_EXCHANGE_BOARD_SEGMENT"):
        require_board_coverage(incomplete, complete)
    with pytest.raises(ValueError, match="MISSING_EXIT_BOARD_SEGMENT"):
        require_board_coverage(complete, incomplete)
    with pytest.raises(ValueError, match="MISSING_EXIT_BOARD_SEGMENT"):
        require_board_coverage(complete, [])


@pytest.mark.parametrize(
    "code,listed,exited",
    [
        ("688086", "2020-02-26", "2023-07-07"),
        ("688287", "2022-05-25", "2026-06-10"),
        ("688555", "2020-06-23", "2023-07-07"),
    ],
)
def test_current_exit_does_not_remove_pilot_membership(code, listed, exited):
    assert overlaps(dict(symbol=code, listing_date=listed, delisting_date=exited))
    assert not overlaps(dict(listing_date="2024-08-01", delisting_date=""))
    assert not overlaps(dict(listing_date="2020-01-01", delisting_date="2022-11-30"))


def test_future_code_transition_never_backdates_new_symbol():
    transitions = [dict(old_symbol="300114", new_symbol="302132", effective_date="2025-02-17")]
    assert pilot_symbol("302132", transitions)[0] == "300114"
    assert pilot_symbol("300001", transitions) == ("300001", None)
    with pytest.raises(ValueError, match="INTERVAL_SPLIT"):
        pilot_symbol("302132", transitions, "2025-02-17")
    with pytest.raises(ValueError, match="AMBIGUOUS"):
        pilot_symbol("302132", transitions * 2)
