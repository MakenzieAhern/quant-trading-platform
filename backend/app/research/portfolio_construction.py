from decimal import ROUND_FLOOR, ROUND_HALF_EVEN, Context, Decimal, localcontext

from app.domain.markets import SecurityId
from app.research.models import (
    CrossSectionResult,
    FactorValues,
    PortfolioTarget,
    ScoredSecurity,
    TargetPosition,
)
from app.research.standardization import population_z_scores
from app.research.winsorization import robust_winsorize

PORTFOLIO_CONTEXT = Context(prec=28, rounding=ROUND_HALF_EVEN)
ZERO = Decimal(0)
ONE = Decimal(1)


def score_cross_section(values: tuple[FactorValues, ...]) -> CrossSectionResult:
    unique: dict[str, FactorValues] = {}
    for item in values:
        key = str(item.security_id)
        if key in unique:
            raise ValueError("duplicate security in cross-section")
        unique[key] = item
    raw_factors = {
        "MOM_12_1": {key: value.mom_12_1 for key, value in unique.items()},
        "TREND_120": {key: value.trend_120 for key, value in unique.items()},
        "LOW_VOL": {key: value.low_vol for key, value in unique.items()},
    }
    standardized: dict[str, dict[str, Decimal]] = {}
    unavailable: list[str] = []
    for name, factor in raw_factors.items():
        result = population_z_scores(robust_winsorize(factor))
        if result is None:
            unavailable.append(name)
        else:
            standardized[name] = result
    if unavailable:
        return CrossSectionResult(scores=(), unavailable_factors=tuple(unavailable))

    with localcontext(PORTFOLIO_CONTEXT):
        scores = tuple(
            ScoredSecurity(
                security_id=value.security_id,
                alpha_score=(
                    standardized["MOM_12_1"][key]
                    + standardized["TREND_120"][key]
                    + standardized["LOW_VOL"][key]
                )
                / Decimal(3),
                mom_12_1_z=standardized["MOM_12_1"][key],
                trend_120_z=standardized["TREND_120"][key],
                low_vol_z=standardized["LOW_VOL"][key],
            )
            for key, value in unique.items()
        )
    return CrossSectionResult(
        scores=tuple(sorted(scores, key=lambda score: (-score.alpha_score, str(score.security_id))))
    )


def select_top_decile(
    result: CrossSectionResult, *, maximum_holdings: int = 20
) -> tuple[ScoredSecurity, ...]:
    if result.unavailable_factors or not result.scores:
        return ()
    if maximum_holdings <= 0:
        raise ValueError("maximum_holdings must be positive")
    count = min(maximum_holdings, max(1, (len(result.scores) + 9) // 10))
    return result.scores[:count]


def construct_equal_weight_portfolio(
    selected: tuple[ScoredSecurity, ...],
    *,
    capital: Decimal,
    raw_reference_prices: dict[SecurityId, Decimal],
    buy_lot_sizes: dict[SecurityId, int],
) -> PortfolioTarget:
    if capital < ZERO or not capital.is_finite():
        raise ValueError("capital must be finite and non-negative")
    if not selected:
        return PortfolioTarget(positions=(), residual_cash=capital)
    with localcontext(PORTFOLIO_CONTEXT):
        weight = ONE / Decimal(len(selected))
        budget = capital * weight
        positions: list[TargetPosition] = []
        invested = ZERO
        for score in selected:
            price = raw_reference_prices.get(score.security_id)
            lot_size = buy_lot_sizes.get(score.security_id)
            if price is None or price <= ZERO or not price.is_finite():
                raise ValueError("positive raw reference price is required")
            if lot_size is None or lot_size <= 0:
                raise ValueError("positive board-lot size is required")
            lots = (budget / (price * Decimal(lot_size))).to_integral_value(rounding=ROUND_FLOOR)
            quantity = lots * Decimal(lot_size)
            invested += quantity * price
            positions.append(
                TargetPosition(
                    security_id=score.security_id,
                    target_weight=weight,
                    quantity=quantity,
                    reference_price=price,
                )
            )
        return PortfolioTarget(positions=tuple(positions), residual_cash=capital - invested)
