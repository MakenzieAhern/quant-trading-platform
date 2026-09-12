import pytest

from scripts.compare_pilot_smoke import compare
from scripts.run_pilot_smoke import LABEL


def test_engineering_comparison_rejects_parameter_tuning():
    before = dict(label=LABEL, strategy_config_hash="original", strategy_config={})
    with pytest.raises(ValueError, match="STRATEGY_CHANGED"):
        compare(before, {**before, "strategy_config_hash": "tuned"})
