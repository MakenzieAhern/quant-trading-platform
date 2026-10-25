import json
from decimal import Decimal
from pathlib import Path

import pytest

from scripts.reconcile_retained_bonus import approved_fraction_policy, source_ratio


def test_fraction_scope_reuses_exact_terms_without_relaxing_identity_or_conflicts():
    header = "证券代码:600000\n"
    assert source_ratio([header + "每10股转增10股"], "600000", False) == (Decimal(1), False)
    for terms, ratio in (("每10股转增6股", "0.6"), ("每股送0.8股、每股转增1.2股", "2")):
        with pytest.raises(ValueError, match="FRACTIONAL_COMPONENT_ALLOCATION_UNRESOLVED"):
            source_ratio([header + terms], "600000", False)
        assert source_ratio([header + terms], "600000", True) == (Decimal(ratio), True)
    for symbol, terms in (
        ("600001", "每10股转增6股"),
        ("600000", "每10股转增6股。每10股转增8股"),
        ("600000", "重整每10股转增6股"),
        ("600000", "差异化分红送转:是;每10股转增6股"),
        ("600000", "每10股转增6股。实施后总股本为300股,增加200股"),
    ):
        with pytest.raises(ValueError):
            source_ratio([header + terms], symbol, True)


def test_fraction_scope_requires_the_existing_exact_approved_policy(tmp_path):
    source = (
        Path(__file__).resolve().parents[2] / ".research/corporate_action_policy_matrix_v1.json"
    )
    policy = json.loads(source.read_bytes())
    approved_fraction_policy(source)
    changed = tmp_path / "policy.json"
    for change in ({"status": "DRAFT"}, {"revision": 2}, {"lineage": {}}, {"policies": []}):
        changed.write_text(json.dumps({**policy, **change}))
        with pytest.raises(ValueError, match="RETAINED_BONUS_FRACTION_POLICY_NOT_APPROVED"):
            approved_fraction_policy(changed)
    for duplicate in (False, True):
        mutated = json.loads(source.read_bytes())
        fraction = next(r for r in mutated["policies"] if r["class"] == "RETAINED_BONUS_FRACTION")
        if duplicate:
            mutated["policies"].append(fraction.copy())
        else:
            fraction["accounting"] = "Round up and pay synthetic cash"
        changed.write_text(json.dumps(mutated))
        with pytest.raises(ValueError, match="RETAINED_BONUS_FRACTION_POLICY_NOT_APPROVED"):
            approved_fraction_policy(changed)
