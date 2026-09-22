from scripts.build_adjustment_residual_source_queue import candidate


def test_high_specificity_candidate_windows():
    assert candidate("2012年度分红派息公告", -8) == "OFFICIAL_DISTRIBUTION_TERMS"
    assert (
        candidate("关于重整计划中资本公积金转增股本事项实施的公告", -239)
        == "OFFICIAL_CAPITAL_ACTION_MECHANICS"
    )
    assert candidate("2012年度分红派息公告", -31) is None
    assert candidate("股权分置改革实施进展公告", -7) is None
