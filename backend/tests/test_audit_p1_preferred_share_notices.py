from scripts.audit_p1_preferred_share_notices import preferred_only


def test_preferred_share_notice_does_not_close_ordinary_a_cash():
    assert preferred_only(
        "银行优先股股息派发实施公告",
        ["A股代码:601166 优先股代码:360005 本次优先股股息派发。"],
    )
    assert not preferred_only("银行A股与优先股股息实施公告", ["优先股股息派发。"])
