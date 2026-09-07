from dataclasses import dataclass
from datetime import date
from itertools import pairwise

from app.research.models import ResearchPeriodKind


@dataclass(frozen=True, slots=True)
class TemporalPeriod:
    kind: ResearchPeriodKind
    start: date
    end: date

    def __post_init__(self) -> None:
        if self.end < self.start:
            raise ValueError("period end must not precede start")


@dataclass(frozen=True, slots=True)
class TemporalSplit:
    development: TemporalPeriod
    validation: TemporalPeriod
    out_of_sample: TemporalPeriod

    def __post_init__(self) -> None:
        periods = (self.development, self.validation, self.out_of_sample)
        expected = (
            ResearchPeriodKind.DEVELOPMENT,
            ResearchPeriodKind.VALIDATION,
            ResearchPeriodKind.OUT_OF_SAMPLE,
        )
        if tuple(period.kind for period in periods) != expected:
            raise ValueError("temporal period kinds are invalid")
        for previous, current in pairwise(periods):
            if current.start <= previous.end:
                raise ValueError("temporal periods must be chronological and non-overlapping")


INITIAL_SPLIT = TemporalSplit(
    development=TemporalPeriod(
        ResearchPeriodKind.DEVELOPMENT, date(2010, 1, 1), date(2017, 12, 31)
    ),
    validation=TemporalPeriod(ResearchPeriodKind.VALIDATION, date(2018, 1, 1), date(2021, 12, 31)),
    out_of_sample=TemporalPeriod(
        ResearchPeriodKind.OUT_OF_SAMPLE, date(2022, 1, 1), date(2025, 12, 31)
    ),
)
