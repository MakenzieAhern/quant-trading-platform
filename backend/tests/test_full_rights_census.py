from scripts.certify_full_rights_census import _ordinary_a_result


def test_result_title_scope() -> None:
    assert _ordinary_a_result("A股配股发行结果及股份变动公告")
    assert _ordinary_a_result("配股发行结果暨复牌公告")
    assert not _ordinary_a_result("H股配股发行结果及股份变动公告")
    assert not _ordinary_a_result("配股公开发行证券预案")
