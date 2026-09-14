import json
from pathlib import Path

import pytest

from scripts.sse_st_events import extract


def test_official_restoration_keeps_st_and_requires_explicit_date_and_later_name():
    fixture = json.loads(
        (Path(__file__).parent / "fixtures/cninfo_restoration_600870.json").read_bytes()
    )
    event = extract(fixture["pages"], fixture["record"])
    assert (event["old_status"], event["status"], event["effective_from"]) == (
        "STAR_ST",
        "ST",
        "2010-05-14",
    )
    # A first-day display prefix alone cannot establish the later risk classification.
    with pytest.raises(ValueError, match="NAME_TRANSITION_UNRESOLVED"):
        extract([fixture["pages"][0].replace("以后公司的股票简称", "其余简称")], fixture["record"])
    with pytest.raises(ValueError, match="EFFECTIVE_DATE_UNRESOLVED"):
        extract([fixture["pages"][0].replace("2010年5月14日", "待定日期")], fixture["record"])
