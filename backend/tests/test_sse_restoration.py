# Source punctuation is intentional parser regression input.
# ruff: noqa: RUF001
import json
import re
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
    for later in ("从恢复上市的第二个交易日起，公司", "恢复上市次日起，公司A股"):
        page = (
            fixture["pages"][0]
            .replace("恢复上市首日的股票简称", "恢复上市首日，公司股票简称")
            .replace("以后公司的", later)
        )
        assert extract([page], fixture["record"])["status"] == "ST"
    with pytest.raises(ValueError, match="CONFLICTING_RESTORATION_EFFECTIVE_DATE"):
        extract(fixture["pages"] + ["实施其他风险警示起始日为2010年5月15日"], fixture["record"])
    normal = (
        re.sub(r"\s+", "", fixture["pages"][0])
        .replace("“NST厦华”", "“N浙传媒”")
        .replace("“ST厦华”", "“浙报传媒”")
        .replace("以后公司的", "自第二个交易日起公司的")
    )
    with pytest.raises(ValueError, match="NAME_TRANSITION_UNRESOLVED"):
        extract([normal], fixture["record"])
    approval = "上海证券交易所批准了撤销对本公司股票实行的退市风险警示或者其他特别处理"
    assert extract([normal + approval], fixture["record"])["status"] == "NORMAL"
