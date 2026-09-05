from dataclasses import dataclass
from datetime import datetime
from decimal import ROUND_HALF_EVEN, Context, Decimal, localcontext
from itertools import pairwise

from app.domain.analytics import EquityPoint, PerformanceMetrics
from app.domain.trading import PortfolioSnapshot

ANALYTICS_CONTEXT = Context(prec=28, rounding=ROUND_HALF_EVEN)
ZERO = Decimal(0)
ONE = Decimal(1)
SECONDS_PER_YEAR = Decimal("31556952")


class AnalyticsInputError(ValueError):
    """Raised when a metric has no finite mathematical definition."""


@dataclass(frozen=True, slots=True)
class AnalyticsConfig:
    periods_per_year: int = 252
    risk_free_rate_per_period: Decimal = ZERO

    def __post_init__(self) -> None:
        if isinstance(self.periods_per_year, bool) or not isinstance(self.periods_per_year, int):
            raise TypeError("periods_per_year must be an integer")
        if self.periods_per_year <= 0:
            raise ValueError("periods_per_year must be positive")
        _require_finite_decimal(self.risk_free_rate_per_period, "risk_free_rate_per_period")


def build_equity_curve(snapshots: tuple[PortfolioSnapshot, ...]) -> tuple[EquityPoint, ...]:
    previous_timestamp: datetime | None = None
    points: list[EquityPoint] = []
    for snapshot in snapshots:
        if previous_timestamp is not None and snapshot.timestamp < previous_timestamp:
            raise AnalyticsInputError("portfolio snapshots must be chronological")
        points.append(
            EquityPoint(
                timestamp=snapshot.timestamp,
                equity=snapshot.equity,
                cash=snapshot.cash,
                market_value=snapshot.market_value,
            )
        )
        previous_timestamp = snapshot.timestamp
    return tuple(points)


def calculate_total_return(initial_equity: Decimal, final_equity: Decimal) -> Decimal:
    _require_finite_decimal(initial_equity, "initial_equity")
    _require_finite_decimal(final_equity, "final_equity")
    if initial_equity <= ZERO:
        raise AnalyticsInputError("initial_equity must be positive")
    with localcontext(ANALYTICS_CONTEXT):
        return final_equity / initial_equity - ONE


def calculate_period_returns(equity_curve: tuple[EquityPoint, ...]) -> tuple[Decimal, ...]:
    _require_chronological_curve(equity_curve)
    returns: list[Decimal] = []
    for previous, current in pairwise(equity_curve):
        if previous.equity == ZERO:
            raise AnalyticsInputError("period return is undefined after zero equity")
        with localcontext(ANALYTICS_CONTEXT):
            returns.append(current.equity / previous.equity - ONE)
    return tuple(returns)


def calculate_max_drawdown(equity_curve: tuple[EquityPoint, ...]) -> Decimal:
    _require_chronological_curve(equity_curve)
    if not equity_curve:
        return ZERO
    running_peak = equity_curve[0].equity
    if running_peak <= ZERO:
        raise AnalyticsInputError("drawdown requires a positive initial equity point")
    maximum_drawdown = ZERO
    with localcontext(ANALYTICS_CONTEXT):
        for point in equity_curve:
            running_peak = max(running_peak, point.equity)
            drawdown = point.equity / running_peak - ONE
            maximum_drawdown = min(maximum_drawdown, drawdown)
    return maximum_drawdown


def calculate_sharpe_ratio(returns: tuple[Decimal, ...], config: AnalyticsConfig) -> Decimal | None:
    if len(returns) < 2:
        return None
    excess = tuple(value - config.risk_free_rate_per_period for value in returns)
    mean, variance = _mean_and_population_variance(excess)
    if variance == ZERO:
        return None
    with localcontext(ANALYTICS_CONTEXT) as context:
        ratio = context.sqrt((mean * mean) / variance)
        if mean < ZERO:
            ratio = -ratio
        return ratio * context.sqrt(Decimal(config.periods_per_year))


def calculate_sortino_ratio(
    returns: tuple[Decimal, ...], config: AnalyticsConfig
) -> Decimal | None:
    if len(returns) < 2:
        return None
    excess = tuple(value - config.risk_free_rate_per_period for value in returns)
    with localcontext(ANALYTICS_CONTEXT) as context:
        mean = sum(excess, ZERO) / Decimal(len(excess))
        downside_variance = sum((min(value, ZERO) ** 2 for value in excess), ZERO) / Decimal(
            len(excess)
        )
        if downside_variance == ZERO:
            return None
        ratio = context.sqrt((mean * mean) / downside_variance)
        if mean < ZERO:
            ratio = -ratio
        return ratio * context.sqrt(Decimal(config.periods_per_year))


def calculate_cagr(
    initial_equity: Decimal,
    final_equity: Decimal,
    start_time: datetime | None,
    end_time: datetime | None,
) -> Decimal | None:
    _require_finite_decimal(initial_equity, "initial_equity")
    _require_finite_decimal(final_equity, "final_equity")
    if initial_equity <= ZERO:
        raise AnalyticsInputError("initial_equity must be positive")
    for name, timestamp in (("start_time", start_time), ("end_time", end_time)):
        if timestamp is not None and (timestamp.tzinfo is None or timestamp.utcoffset() is None):
            raise AnalyticsInputError(f"{name} must include a timezone")
    if start_time is None or end_time is None or end_time <= start_time or final_equity <= ZERO:
        return None
    elapsed = end_time - start_time
    elapsed_microseconds = (
        elapsed.days * 86_400 + elapsed.seconds
    ) * 1_000_000 + elapsed.microseconds
    with localcontext(ANALYTICS_CONTEXT) as context:
        years = Decimal(elapsed_microseconds) / Decimal(1_000_000) / SECONDS_PER_YEAR
        return context.power(final_equity / initial_equity, ONE / years) - ONE


class AnalyticsEngine:
    def __init__(self, config: AnalyticsConfig | None = None) -> None:
        self._config = config or AnalyticsConfig()

    def analyze(
        self,
        snapshots: tuple[PortfolioSnapshot, ...],
        initial_equity: Decimal,
        total_commission: Decimal,
        number_of_fills: int,
        start_time: datetime | None,
        end_time: datetime | None,
    ) -> tuple[tuple[EquityPoint, ...], PerformanceMetrics]:
        curve = build_equity_curve(snapshots)
        final_equity = curve[-1].equity if curve else initial_equity
        returns = calculate_period_returns(curve)
        metrics = PerformanceMetrics(
            initial_equity=initial_equity,
            final_equity=final_equity,
            total_return=calculate_total_return(initial_equity, final_equity),
            cagr=calculate_cagr(initial_equity, final_equity, start_time, end_time),
            max_drawdown=calculate_max_drawdown(curve),
            sharpe_ratio=calculate_sharpe_ratio(returns, self._config),
            sortino_ratio=calculate_sortino_ratio(returns, self._config),
            total_commission=total_commission,
            number_of_fills=number_of_fills,
        )
        return curve, metrics


def _mean_and_population_variance(values: tuple[Decimal, ...]) -> tuple[Decimal, Decimal]:
    with localcontext(ANALYTICS_CONTEXT):
        mean = sum(values, ZERO) / Decimal(len(values))
        variance = sum(((value - mean) ** 2 for value in values), ZERO) / Decimal(len(values))
    return mean, variance


def _require_finite_decimal(value: Decimal, name: str) -> None:
    if not isinstance(value, Decimal):
        raise TypeError(f"{name} must be a Decimal instance")
    if not value.is_finite():
        raise AnalyticsInputError(f"{name} must be finite")


def _require_chronological_curve(equity_curve: tuple[EquityPoint, ...]) -> None:
    for previous, current in pairwise(equity_curve):
        if current.timestamp < previous.timestamp:
            raise AnalyticsInputError("equity curve must be chronological")
