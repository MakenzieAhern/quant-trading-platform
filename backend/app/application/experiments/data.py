"""Registered read-only datasets. No user path or provider request enters this boundary."""

import json
from collections.abc import Iterator
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Any

from app.data.catalog import load_manifest
from app.data.catalog.checksums import canonical_sha256
from app.data.catalog.freeze import MARKER
from app.data.catalog.models import DatasetManifest
from app.data.full_dataset import FullDataset
from app.domain.markets.calendar import TradingCalendar
from app.paper.a_share_fixture import simulated_a_share_fixture
from app.research.models import ResearchPeriodKind, ResearchSession
from app.research.splits import TemporalPeriod
from app.strategies.research import STRATEGY_ID, STRATEGY_NAME_EN, STRATEGY_NAME_ZH

DEMO_ID = "cn-a-exploration-demo-v1"
HISTORICAL_ID = "cn-a-research-20100101-20251231-v1"
DEMO_SHA = canonical_sha256({"dataset_id": DEMO_ID, "generator_version": 1, "sessions": 340})
DEMO_START = date(2030, 1, 2)
DEMO_END = date(2031, 4, 22)
HISTORICAL_ECONOMIC_GAP_SHA = "1d7b6134e2c6a7026aa124bed57ab101ea910847e10e3d799c45f6c6a1e17f9e"


def current_dataset_quality(dataset_id: str, dataset_sha256: object) -> str | None:
    """Later-discovered read advice, never frozen provenance or result mutation."""
    if dataset_id != HISTORICAL_ID:
        return None  # Not covered by this finding, not a financial audit PASS.
    if isinstance(dataset_sha256, str) and dataset_sha256 == HISTORICAL_ECONOMIC_GAP_SHA:
        return "KNOWN_ECONOMIC_COVERAGE_GAP"
    return "HISTORICAL_DATASET_QUALITY_UNKNOWN"


class ExperimentInputError(ValueError):
    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


class ExperimentDatasetRegistry:
    def __init__(self, root: Path) -> None:
        self.root = root.resolve()

    def manifest(self) -> DatasetManifest:
        path = self.root / HISTORICAL_ID
        if not (path / "manifest.json").is_file() or not (path / MARKER).is_file():
            raise FileNotFoundError("DATASET_NOT_MOUNTED")
        manifest = load_manifest(path / "manifest.json")
        record = json.loads((path / MARKER).read_bytes())
        if (
            not isinstance(record, dict)
            or manifest.dataset_id != HISTORICAL_ID
            or manifest.canonical_sha256 != record["dataset_manifest_sha256"]
            or canonical_sha256({k: v for k, v in record.items() if k != "freeze_record_sha256"})
            != record["freeze_record_sha256"]
            or any(not (path / item.relative_path).is_file() for item in manifest.partitions)
        ):
            raise ExperimentInputError("DATASET_INTEGRITY_FAILED")
        return manifest

    def datasets(self) -> list[dict[str, Any]]:
        demo = {
            "dataset_id": DEMO_ID,
            "mode": "synthetic_demo",
            "available": True,
            "reason_code": None,
            "coverage_start": DEMO_START.isoformat(),
            "coverage_end": DEMO_END.isoformat(),
            "default_start": "2030-12-20",
            "default_end": DEMO_END.isoformat(),
            "security_count": 10,
            "sha256": DEMO_SHA,
            "as_of": DEMO_END.isoformat(),
            "universes": ["ALL", "SSE"],
            "benchmark_id": "SYNTHETIC_EQUAL_WEIGHT",
        }
        historical: dict[str, Any] = {
            "dataset_id": HISTORICAL_ID,
            "mode": "historical_exploration",
            "available": False,
            "reason_code": "DATASET_NOT_MOUNTED",
            "coverage_start": "2010-01-01",
            "coverage_end": "2025-12-31",
            "default_start": "2011-01-04",
            "default_end": "2011-06-30",
            "security_count": 0,
            "sha256": None,
            "as_of": None,
            "universes": ["ALL", "SSE", "SZSE"],
            "benchmark_id": "CSI300",
        }
        try:
            manifest = self.manifest()
            historical.update(
                available=True,
                reason_code=None,
                coverage_start=manifest.coverage_start.isoformat(),
                coverage_end=manifest.coverage_end.isoformat(),
                security_count=manifest.security_count,
                sha256=manifest.canonical_sha256,
                as_of=manifest.coverage_end.isoformat(),
            )
        except FileNotFoundError:
            pass
        except (ValueError, KeyError, OSError):
            historical["reason_code"] = "DATASET_INTEGRITY_FAILED"
        historical["current_dataset_quality"] = current_dataset_quality(
            historical["dataset_id"], historical["sha256"]
        )
        return [historical, demo]

    def resolve(self, dataset_id: str) -> dict[str, Any]:
        for item in self.datasets():
            if item["dataset_id"] == dataset_id:
                if not item["available"]:
                    raise ExperimentInputError(item["reason_code"])
                return item
        raise ExperimentInputError("DATASET_NOT_REGISTERED")

    def capabilities(self) -> dict[str, Any]:
        return {
            "strategies": [
                {
                    "strategy_id": STRATEGY_ID,
                    "version": "1",
                    "name_en": STRATEGY_NAME_EN,
                    "name_zh": STRATEGY_NAME_ZH,
                    "description_en": (
                        "Rank shares by momentum, trend and low volatility; buy an equal-weight "
                        "top decile and rebalance on completed sessions."
                    ),
                    "description_zh": (
                        "按动量、趋势和低波动给合格股票排序。"
                        "等权买入前十分之一并按已完成交易日定期调仓。"
                    ),
                    "parameters": {
                        "rebalance_sessions": {"min": 1, "max": 252, "default": 20},
                        "maximum_holdings": {"min": 1, "max": 100, "default": 20},
                    },
                    "limitations": [
                        "EXPLORATORY_NOT_UNSEEN_EVIDENCE",
                        "DAILY_BAR_NEXT_SESSION_EXECUTION",
                        "NO_RETURN_GUARANTEE",
                        "253_SESSION_WARMUP",
                        "LONG_ONLY_NO_LEVERAGE",
                    ],
                }
            ],
            "datasets": self.datasets(),
            "defaults": {
                "initial_cash": "100000",
                "commission_rate": "0.0003",
                "minimum_commission": "5",
                "max_drawdown": "-0.2",
                "max_position_weight": "0.1",
            },
        }


class SyntheticExperimentDataset:
    def __init__(self, end: date) -> None:
        calendar, sessions, self.cost_model = simulated_a_share_fixture(session_count=340)
        self.next_session = next(
            (session for session in calendar.sessions if session.session_date > end), None
        )
        self._sessions = tuple(s for s in sessions if s.trading_date <= end)
        self.calendar = TradingCalendar(
            market=calendar.market,
            sessions=tuple(s for s in calendar.sessions if s.session_date <= end),
        )
        self.calendar_days = tuple(s.trading_date for s in self._sessions)
        first = self._sessions[0]
        bases = {str(bar.security_id): bar.raw_close for bar in first.bars}
        self.benchmark = {
            s.trading_date.isoformat(): sum(
                (bar.raw_close / bases[str(bar.security_id)] for bar in s.bars), Decimal(0)
            )
            / Decimal(len(s.bars))
            for s in self._sessions
        }

    def sessions(self) -> Iterator[ResearchSession]:
        yield from self._sessions


def load_experiment_dataset(
    registry: ExperimentDatasetRegistry,
    dataset_id: str,
    start: date,
    end: date,
) -> FullDataset | SyntheticExperimentDataset:
    if dataset_id == DEMO_ID:
        return SyntheticExperimentDataset(end)
    if dataset_id != HISTORICAL_ID:
        raise ExperimentInputError("DATASET_NOT_REGISTERED")
    # FULL_PERIOD is only a loader date container; no formal study runner or OOS lock is called.
    try:
        return FullDataset(
            registry.root / HISTORICAL_ID,
            registry.manifest(),
            TemporalPeriod(ResearchPeriodKind.FULL_PERIOD, start, end),
        )
    except (OSError, KeyError) as exc:
        raise ExperimentInputError("DATASET_INTEGRITY_FAILED") from exc
    except ValueError as exc:
        if not str(exc).startswith("FROZEN_PARTITION_CHANGED:"):
            raise
        raise ExperimentInputError("DATASET_INTEGRITY_FAILED") from exc
