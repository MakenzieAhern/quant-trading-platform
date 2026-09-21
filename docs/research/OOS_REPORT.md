# Official OOS performance report

## Scope and lineage

- Strategy: `cn_a_cross_sectional_momentum_low_vol_v1` (frozen S4 fallback)
- Period: 2022-01-01 through 2025-12-31
- Dataset: `cn-a-research-20100101-20251231-v1`
- Dataset SHA-256: `1d7b6134e2c6a7026aa124bed57ab101ea910847e10e3d799c45f6c6a1e17f9e`
- Methodology SHA-256: `91b08cd9190f49dcbc3f8862f00a12b1e6e2db0cc767aa522ac731fb90c7936b`
- Official result SHA-256: `ccf5bd2f82f145c9d14bb6ffb912bf035d276b46b8056883b8a18a61a2d92e8c`
- Run count: 1 of 1; the Official OOS lock is consumed.

## Results

| Metric | Official OOS |
|---|---:|
| Initial capital | 100,000,000 |
| Final equity | 100,758,948.26 |
| Total return | 0.76% |
| CAGR | 0.20% |
| Annualized volatility | 8.84% |
| Sharpe | 0.067 |
| Sortino | 0.089 |
| Maximum drawdown | -15.70% |
| Calmar | 0.013 |
| Win rate | 45.45% |
| Profit factor | 1.213 |
| Trades | 88 |
| Turnover | 4.230 |
| Average holding period | 82.70 sessions |
| Transaction costs | 262,132.74 |
| Average net exposure | 22.38% |
| CSI300 return | -5.85% |
| Excess return | 6.61% |
| Tracking error | 15.72% |
| Information ratio | 0.035 |

Annual returns were 5.01% (2022), -2.75% (2023), 0.87% (2024), and -2.18%
(2025). The immutable machine report retains all 48 monthly returns, 969 equity
and drawdown observations, 717 rolling windows, 48 rebalance/holdings snapshots,
and 88 fills.

## Development, Validation, and OOS

| Period | Total return | Sharpe | Maximum drawdown | Excess vs CSI300 |
|---|---:|---:|---:|---:|
| Development 2010-2017 | -21.75% | -0.434 | -32.56% | -35.77% |
| Validation 2018-2021 | -5.17% | -0.141 | -11.98% | -26.04% |
| Official OOS 2022-2025 | 0.76% | 0.067 | -15.70% | 6.61% |

## Interpretation

Validation did not establish robust historical alpha, so S4 entered OOS only as
the pre-registered negative/neutral fallback. The OOS return is positive and
outperformed a declining CSI300, but its absolute return and risk-adjusted
performance are weak. Win rate is a trade-frequency statistic, not proof of
profitability. No future return is guaranteed, and the strategy was not retuned
after OOS inspection.
