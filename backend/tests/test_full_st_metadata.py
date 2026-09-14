import pytest

from scripts.reconcile_full_st_metadata import page_rows


def test_sse_targeted_pages_reject_repetition_and_identity_leakage():
    row = {"SECURITY_CODE": "600000", "SSEDATE": "2010-04-01", "TITLE": "notice"}
    payload = {"data": [[row]]}
    seen = set()
    assert page_rows(payload, "600000", "2010-04-01", seen) == [row]
    with pytest.raises(ValueError, match="REPEATED"):
        page_rows(payload, "600000", "2010-04-01", seen)
    with pytest.raises(ValueError, match="LEAKAGE"):
        page_rows(payload, "600001", "2010-04-01", set())
    with pytest.raises(ValueError, match="LEAKAGE"):
        page_rows(payload, "600000", "2010-04-02", set())
