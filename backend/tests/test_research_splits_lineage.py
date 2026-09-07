from dataclasses import asdict
from datetime import date

import pytest

from app.research import INITIAL_SPLIT, ResearchPeriodKind, TemporalPeriod, TemporalSplit
from app.research.lineage import reproducibility_hash
from app.strategies.research import ChinaAMomentumLowVolConfig


def test_initial_split_is_frozen_without_overlap() -> None:
    assert INITIAL_SPLIT.development.start == date(2010, 1, 1)
    assert INITIAL_SPLIT.validation.start == date(2018, 1, 1)
    assert INITIAL_SPLIT.out_of_sample.end == date(2025, 12, 31)


def test_temporal_split_rejects_leakage_at_boundary() -> None:
    with pytest.raises(ValueError, match="non-overlapping"):
        TemporalSplit(
            TemporalPeriod(ResearchPeriodKind.DEVELOPMENT, date(2010, 1, 1), date(2018, 1, 1)),
            TemporalPeriod(ResearchPeriodKind.VALIDATION, date(2018, 1, 1), date(2021, 12, 31)),
            TemporalPeriod(ResearchPeriodKind.OUT_OF_SAMPLE, date(2022, 1, 1), date(2025, 12, 31)),
        )


def test_reproducibility_and_strategy_hashes_ignore_mapping_order() -> None:
    assert reproducibility_hash({"b": 2, "a": 1}) == reproducibility_hash({"a": 1, "b": 2})
    config = ChinaAMomentumLowVolConfig()
    assert config.configuration_hash == reproducibility_hash(asdict(config))


def test_initial_strategy_parameters_cannot_be_silently_changed() -> None:
    with pytest.raises(ValueError, match="top decile"):
        ChinaAMomentumLowVolConfig(top_fraction_numerator=2)
