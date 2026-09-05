from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path

from app.data.providers import CSVDataProvider, MarketDataProvider
from app.strategies import (
    BaseStrategy,
    MovingAverageCrossoverStrategy,
    RSIMeanReversionStrategy,
)


class UnknownDatasetError(LookupError):
    """Raised when an API dataset identifier is not explicitly approved."""


class UnknownStrategyError(ValueError):
    """Raised when a strategy name is not explicitly approved."""


class InvalidStrategyParametersError(ValueError):
    """Raised when approved strategy parameters fail their contract."""


@dataclass(frozen=True, slots=True)
class DatasetDefinition:
    dataset_id: str
    symbol: str
    directory: Path


class DatasetRegistry:
    def __init__(self, definitions: tuple[DatasetDefinition, ...]) -> None:
        self._definitions = {item.dataset_id: item for item in definitions}

    @classmethod
    def phase7(cls, fixtures_directory: Path) -> "DatasetRegistry":
        return cls((DatasetDefinition("AAPL_fixture", "AAPL", fixtures_directory.resolve()),))

    def resolve(self, dataset_id: str, symbol: str) -> MarketDataProvider:
        definition = self._definitions.get(dataset_id)
        if definition is None or definition.symbol != symbol:
            raise UnknownDatasetError(f"unknown dataset for symbol: {dataset_id}")
        return CSVDataProvider(definition.directory)


class StrategyRegistry:
    def build(
        self, strategy_type: str, strategy_id: str, symbol: str, parameters: dict[str, object]
    ) -> BaseStrategy:
        try:
            if strategy_type == "moving_average_crossover":
                self._require_keys(parameters, {"short_period", "long_period"})
                return MovingAverageCrossoverStrategy(
                    strategy_id,
                    symbol,
                    self._integer(parameters["short_period"], "short_period"),
                    self._integer(parameters["long_period"], "long_period"),
                )
            if strategy_type == "rsi_mean_reversion":
                self._require_keys(parameters, {"rsi_period", "oversold", "overbought"})
                return RSIMeanReversionStrategy(
                    strategy_id,
                    symbol,
                    self._integer(parameters["rsi_period"], "rsi_period"),
                    self._decimal(parameters["oversold"], "oversold"),
                    self._decimal(parameters["overbought"], "overbought"),
                )
        except (KeyError, TypeError, ValueError) as exc:
            raise InvalidStrategyParametersError(str(exc)) from exc
        raise UnknownStrategyError(f"unknown strategy: {strategy_type}")

    @staticmethod
    def _require_keys(parameters: dict[str, object], expected: set[str]) -> None:
        if set(parameters) != expected:
            raise InvalidStrategyParametersError(
                f"parameters must be exactly: {', '.join(sorted(expected))}"
            )

    @staticmethod
    def _integer(value: object, name: str) -> int:
        if isinstance(value, bool) or not isinstance(value, int):
            raise TypeError(f"{name} must be an integer")
        return value

    @staticmethod
    def _decimal(value: object, name: str) -> Decimal:
        if not isinstance(value, Decimal):
            raise TypeError(f"{name} must be a Decimal")
        return value
