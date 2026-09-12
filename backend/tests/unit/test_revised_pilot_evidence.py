import pytest

from scripts.audit_revised_pilot_evidence import delisting_start
from scripts.reconcile_revised_pilot_notices import required


def test_delisting_parser_requires_issuer_and_unambiguous_labeled_date():
    text = "证券代码\uff1a688086 公司股票进入退市整理期的起始日为2023年6月8日"
    assert delisting_start(text, "688086") == "2023-06-08"
    with pytest.raises(ValueError, match="WRONG_DELISTING_ISSUER"):
        delisting_start(text, "688555")
    with pytest.raises(ValueError, match="UNRESOLVED"):
        delisting_start(text + "进入退市整理期的起始日为2023年6月9日", "688086")
    assert required("科创板转板上市公告书")
    assert required("关于公司股票将被实施退市风险警示暨停牌的提示性公告")
    assert not required("关于公司股票可能被实施其他风险警示的风险提示公告")
