from dataclasses import asdict, dataclass

from app.data.catalog.checksums import canonical_sha256

STRATEGY_ID = "cn_a_cross_sectional_momentum_low_vol_v1"
STRATEGY_NAME_EN = "China A-Share Cross-Sectional Momentum and Low-Volatility Strategy"
STRATEGY_NAME_ZH = "中国A股横截面动量与低波动策略"


@dataclass(frozen=True, slots=True)
class ChinaAMomentumLowVolConfig:
    rebalance_sessions: int = 20
    maximum_holdings: int = 20
    top_fraction_numerator: int = 1
    top_fraction_denominator: int = 10
    include_st: bool = False
    minimum_history_sessions: int = 252
    long_only: bool = True
    weighting: str = "EQUAL"
    leverage: str = "1"

    def __post_init__(self) -> None:
        if self.rebalance_sessions <= 0 or self.maximum_holdings <= 0:
            raise ValueError("rebalance_sessions and maximum_holdings must be positive")
        if self.top_fraction_numerator != 1 or self.top_fraction_denominator != 10:
            raise ValueError("v1 strategy uses a frozen top decile")
        if self.minimum_history_sessions != 252:
            raise ValueError("v1 strategy uses a frozen 252-session minimum")

    @property
    def configuration_hash(self) -> str:
        return canonical_sha256(asdict(self))
