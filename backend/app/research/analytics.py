from dataclasses import dataclass
from decimal import ROUND_HALF_EVEN, Context, Decimal, localcontext
from itertools import pairwise

ZERO = Decimal(0)
ONE = Decimal(1)
CONTEXT = Context(prec=28, rounding=ROUND_HALF_EVEN)


@dataclass(frozen=True, slots=True)
class ClosedTrade:
    net_profit: Decimal
    holding_sessions: int


@dataclass(frozen=True, slots=True)
class ResearchAnalytics:
    initial_capital: Decimal
    final_equity: Decimal
    cumulative_return: Decimal
    cagr: Decimal | None
    annualized_volatility: Decimal | None
    sharpe_ratio: Decimal | None
    sortino_ratio: Decimal | None
    maximum_drawdown: Decimal
    calmar_ratio: Decimal | None
    win_rate: Decimal | None
    profit_factor: Decimal | None
    number_of_trades: int
    turnover: Decimal
    average_holding_period: Decimal | None
    transaction_costs: Decimal
    average_gross_exposure: Decimal | None
    average_net_exposure: Decimal | None
    benchmark_return: Decimal | None
    excess_return: Decimal | None
    tracking_error: Decimal | None
    information_ratio: Decimal | None


def analyze_research_period(
    *,
    equity: tuple[Decimal, ...],
    benchmark_equity: tuple[Decimal, ...] = (),
    closed_trades: tuple[ClosedTrade, ...] = (),
    turnover: Decimal = ZERO,
    transaction_costs: Decimal = ZERO,
    gross_exposures: tuple[Decimal, ...] = (),
    net_exposures: tuple[Decimal, ...] = (),
    periods_per_year: int = 252,
) -> ResearchAnalytics:
    """Calculate exact metrics from aligned session-close observations.

    Volatility uses population standard deviation. Sharpe and Sortino use a
    zero risk-free rate. Undefined ratios are ``None``, never synthetic zero.
    """
    if periods_per_year <= 0:
        raise ValueError("periods_per_year must be positive")
    _finite(equity, "equity")
    if not equity or any(value <= ZERO for value in equity):
        raise ValueError("equity must contain positive values")
    for name, values in (
        ("benchmark_equity", benchmark_equity),
        ("gross_exposures", gross_exposures),
        ("net_exposures", net_exposures),
    ):
        _finite(values, name)
    if benchmark_equity and len(benchmark_equity) != len(equity):
        raise ValueError("benchmark equity must align one-to-one with strategy equity")
    if benchmark_equity and any(value <= ZERO for value in benchmark_equity):
        raise ValueError("benchmark equity must contain positive values")
    if gross_exposures and len(gross_exposures) != len(equity):
        raise ValueError("gross exposures must align one-to-one with equity")
    if net_exposures and len(net_exposures) != len(equity):
        raise ValueError("net exposures must align one-to-one with equity")
    _finite((turnover, transaction_costs), "cost inputs")
    if turnover < ZERO or transaction_costs < ZERO:
        raise ValueError("turnover and transaction costs must be non-negative")
    if any(
        trade.holding_sessions < 0 or not trade.net_profit.is_finite() for trade in closed_trades
    ):
        raise ValueError("closed trades must be finite with non-negative holding periods")

    returns = _returns(equity)
    benchmark_returns = _returns(benchmark_equity) if benchmark_equity else ()
    cumulative_return = equity[-1] / equity[0] - ONE
    cagr = _annualized_growth(equity[0], equity[-1], len(returns), periods_per_year)
    volatility = _annualized_std(returns, periods_per_year)
    maximum_drawdown = _maximum_drawdown(equity)
    profitable = tuple(trade for trade in closed_trades if trade.net_profit > ZERO)
    losses = tuple(trade for trade in closed_trades if trade.net_profit < ZERO)
    gross_loss = -sum((trade.net_profit for trade in losses), ZERO)
    benchmark_return = (
        benchmark_equity[-1] / benchmark_equity[0] - ONE if benchmark_equity else None
    )
    active_returns = (
        tuple(
            strategy - benchmark
            for strategy, benchmark in zip(returns, benchmark_returns, strict=True)
        )
        if benchmark_returns
        else ()
    )
    return ResearchAnalytics(
        initial_capital=equity[0],
        final_equity=equity[-1],
        cumulative_return=cumulative_return,
        cagr=cagr,
        annualized_volatility=volatility,
        sharpe_ratio=_annualized_ratio(returns, periods_per_year),
        sortino_ratio=_downside_ratio(returns, periods_per_year),
        maximum_drawdown=maximum_drawdown,
        calmar_ratio=(
            None if cagr is None or maximum_drawdown == ZERO else cagr / -maximum_drawdown
        ),
        win_rate=(
            Decimal(len(profitable)) / Decimal(len(closed_trades)) if closed_trades else None
        ),
        profit_factor=(
            sum((trade.net_profit for trade in profitable), ZERO) / gross_loss
            if gross_loss > ZERO
            else None
        ),
        number_of_trades=len(closed_trades),
        turnover=turnover,
        average_holding_period=(
            Decimal(sum(trade.holding_sessions for trade in closed_trades))
            / Decimal(len(closed_trades))
            if closed_trades
            else None
        ),
        transaction_costs=transaction_costs,
        average_gross_exposure=_mean(gross_exposures),
        average_net_exposure=_mean(net_exposures),
        benchmark_return=benchmark_return,
        excess_return=(
            cumulative_return - benchmark_return if benchmark_return is not None else None
        ),
        tracking_error=(
            _annualized_std(active_returns, periods_per_year) if active_returns else None
        ),
        information_ratio=(
            _annualized_ratio(active_returns, periods_per_year) if active_returns else None
        ),
    )


def rolling_compounded_returns(
    returns: tuple[Decimal, ...], window: int
) -> tuple[Decimal | None, ...]:
    _finite(returns, "returns")
    if window <= 0:
        raise ValueError("window must be positive")
    result: list[Decimal | None] = [None] * min(window - 1, len(returns))
    for end in range(window, len(returns) + 1):
        compounded = ONE
        for value in returns[end - window : end]:
            compounded *= ONE + value
        result.append(compounded - ONE)
    return tuple(result)


def _returns(values: tuple[Decimal, ...]) -> tuple[Decimal, ...]:
    return tuple(current / previous - ONE for previous, current in pairwise(values))


def _annualized_growth(
    initial: Decimal, final: Decimal, periods: int, periods_per_year: int
) -> Decimal | None:
    if periods == 0:
        return None
    with localcontext(CONTEXT) as context:
        return context.power(final / initial, Decimal(periods_per_year) / Decimal(periods)) - ONE


def _mean(values: tuple[Decimal, ...]) -> Decimal | None:
    return sum(values, ZERO) / Decimal(len(values)) if values else None


def _population_std(values: tuple[Decimal, ...]) -> Decimal | None:
    if len(values) < 2:
        return None
    mean = sum(values, ZERO) / Decimal(len(values))
    variance = sum(((value - mean) ** 2 for value in values), ZERO) / Decimal(len(values))
    if variance == ZERO:
        return ZERO
    with localcontext(CONTEXT) as context:
        return context.sqrt(variance)


def _annualized_std(values: tuple[Decimal, ...], periods_per_year: int) -> Decimal | None:
    standard_deviation = _population_std(values)
    if standard_deviation is None:
        return None
    with localcontext(CONTEXT) as context:
        return standard_deviation * context.sqrt(Decimal(periods_per_year))


def _annualized_ratio(values: tuple[Decimal, ...], periods_per_year: int) -> Decimal | None:
    standard_deviation = _population_std(values)
    if standard_deviation is None or standard_deviation == ZERO:
        return None
    mean = sum(values, ZERO) / Decimal(len(values))
    with localcontext(CONTEXT) as context:
        return mean / standard_deviation * context.sqrt(Decimal(periods_per_year))


def _downside_ratio(values: tuple[Decimal, ...], periods_per_year: int) -> Decimal | None:
    if len(values) < 2:
        return None
    downside_variance = sum((min(value, ZERO) ** 2 for value in values), ZERO) / Decimal(
        len(values)
    )
    if downside_variance == ZERO:
        return None
    mean = sum(values, ZERO) / Decimal(len(values))
    with localcontext(CONTEXT) as context:
        return mean / context.sqrt(downside_variance) * context.sqrt(Decimal(periods_per_year))


def _maximum_drawdown(equity: tuple[Decimal, ...]) -> Decimal:
    peak = equity[0]
    drawdown = ZERO
    for value in equity:
        peak = max(peak, value)
        drawdown = min(drawdown, value / peak - ONE)
    return drawdown


def _finite(values: tuple[Decimal, ...], name: str) -> None:
    if any(not isinstance(value, Decimal) or not value.is_finite() for value in values):
        raise ValueError(f"{name} must contain finite Decimal values")
