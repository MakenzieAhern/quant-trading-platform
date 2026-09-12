from collections import defaultdict
from decimal import Decimal

from app.domain.markets import SecurityId
from app.research.factors import FactorUnavailableError, calculate_factors
from app.research.models import (
    AdjustedClosePoint,
    CrossSectionResult,
    FactorValues,
    PortfolioTarget,
    ResearchSession,
)
from app.research.portfolio_construction import (
    construct_equal_weight_portfolio,
    score_cross_section,
    select_top_decile,
)
from app.strategies.research import ChinaAMomentumLowVolConfig

ZERO = Decimal(0)


class ChinaAMomentumLowVolResearchStrategy:
    strategy_id = "cn_a_cross_sectional_momentum_low_vol_v1"

    def __init__(
        self,
        config: ChinaAMomentumLowVolConfig | None = None,
        *,
        minimum_average_daily_amount: Decimal = Decimal("10000000"),
    ) -> None:
        self.config = config or ChinaAMomentumLowVolConfig()
        if minimum_average_daily_amount < ZERO:
            raise ValueError("minimum_average_daily_amount must be non-negative")
        self.minimum_average_daily_amount = minimum_average_daily_amount
        self._history: dict[SecurityId, list[AdjustedClosePoint]] = defaultdict(list)
        self._amount_history: dict[SecurityId, list[Decimal]] = defaultdict(list)
        self._completed_sessions = 0
        self.last_factors: tuple[FactorValues, ...] = ()
        self.last_cross_section = CrossSectionResult(scores=())

    def target_for_completed_session(
        self, session: ResearchSession, available_equity: Decimal
    ) -> PortfolioTarget | None:
        self._completed_sessions += 1
        status_by_security = {item.status.security_id: item.status for item in session.statuses}
        for bar in session.bars:
            if bar.adjusted_close is None:
                continue
            self._history[bar.security_id].append(
                AdjustedClosePoint(bar.trading_date, bar.adjusted_close)
            )
            if bar.amount is not None:
                self._amount_history[bar.security_id].append(bar.amount)

        if self._completed_sessions < 253:
            return None
        if (self._completed_sessions - 253) % self.config.rebalance_sessions:
            return None

        factors = []
        prices: dict[SecurityId, Decimal] = {}
        for bar in session.bars:
            status = status_by_security.get(bar.security_id)
            if (
                status is None
                or status.is_suspended
                or (status.is_st and not self.config.include_st)
            ):
                continue
            amounts = self._amount_history[bar.security_id][-20:]
            if len(amounts) < 20:
                continue
            average_amount = sum(amounts, ZERO) / Decimal(len(amounts))
            if average_amount < self.minimum_average_daily_amount:
                continue
            try:
                factors.append(
                    calculate_factors(
                        bar.security_id,
                        session.trading_date,
                        tuple(self._history[bar.security_id]),
                    )
                )
            except FactorUnavailableError:
                continue
            prices[bar.security_id] = bar.raw_close

        scored = score_cross_section(tuple(factors))
        self.last_factors = tuple(factors)
        self.last_cross_section = scored
        selected = select_top_decile(scored, maximum_holdings=self.config.maximum_holdings)
        lot_sizes = dict(session.buy_lot_sizes)
        return construct_equal_weight_portfolio(
            selected,
            capital=available_equity,
            raw_reference_prices=prices,
            buy_lot_sizes=lot_sizes,
        )

    def reset(self) -> None:
        self._history.clear()
        self._amount_history.clear()
        self._completed_sessions = 0
        self.last_factors = ()
        self.last_cross_section = CrossSectionResult(scores=())
