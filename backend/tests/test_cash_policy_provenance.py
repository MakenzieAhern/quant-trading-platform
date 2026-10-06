"""Published policy compatibility must not accept edited catalog bytes."""

from pathlib import Path

import pytest

from scripts.reconcile_distribution_cash import require_approved_cash_policy


def test_published_cash_policy_is_accepted_but_any_byte_change_is_rejected(tmp_path):
    policy = (
        Path(__file__).resolve().parents[2] / ".research/corporate_action_policy_matrix_v1.json"
    )
    require_approved_cash_policy(policy)
    copy = tmp_path / policy.name
    copy.write_bytes(policy.read_bytes())
    require_approved_cash_policy(copy)
    copy.write_bytes(copy.read_bytes() + b"\n")
    with pytest.raises(ValueError, match=r"^APPROVED_CASH_POLICY_CHANGED$"):
        require_approved_cash_policy(copy)
