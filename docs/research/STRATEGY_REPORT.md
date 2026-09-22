# Frozen strategy report

## Strategy

`cn_a_cross_sectional_momentum_low_vol_v1` is the frozen S4 long-only strategy. It requires 252
completed sessions, excludes ST/*ST and suspended securities, requires a 20-session average daily
amount of at least CNY 10,000,000, and rebalances every 20 valid sessions.

The three factors are:

- `MOM_12_1 = adjusted_close[t-21] / adjusted_close[t-252] - 1`
- `TREND_120 = adjusted_close[t] / SMA120[t] - 1`
- `LOW_VOL = -population_std(prior 20 completed-session adjusted returns)`

Each factor is deterministically winsorized and population z-scored. The equal-weight portfolio
uses the top decile, capped at 20 holdings, with stable `security_id` tie-breaking and valid-lot
rounding. Orders follow the approved daily opening-limit convention and pass through RiskEngine,
OMS, simulated execution and Portfolio accounting.

Frozen strategy record SHA-256:
`91b08cd9190f49dcbc3f8862f00a12b1e6e2db0cc767aa522ac731fb90c7936b`.

## Selection protocol

S0–S4 were fixed before Development. After Development, S2–S4 and quantitative Validation gates
were frozen. Each candidate ran exactly once on Validation. No candidate passed every gate, so the
pre-declared rule selected unchanged S4 as a negative/neutral fallback—not as a winning model.
No post-Validation or post-OOS tuning occurred.

## Results

| Split | Period | Total return | Sharpe | Maximum drawdown | Excess vs CSI300 |
|---|---|---:|---:|---:|---:|
| Development | 2010–2017 | -21.75% | -0.434 | -32.56% | -35.77% |
| Validation | 2018–2021 | -5.17% | -0.141 | -11.98% | -26.04% |
| Official OOS | 2022–2025 | 0.76% | 0.067 | -15.70% | 6.61% |

Development result SHA-256:
`7f73a0ef7ac9ee571be87bf996b002a074cb2512400822d82001e3885d418c29`.
Validation result SHA-256:
`d210739e00c0aa229b0aeaf767230e2dba3dec1764279b0f6c2c2453906a23ee`.
Official OOS result SHA-256:
`ccf5bd2f82f145c9d14bb6ffb912bf035d276b46b8056883b8a18a61a2d92e8c`.

## Interpretation

Validation did not establish robust alpha. Official OOS was weakly positive and outperformed a
declining CSI300, but its absolute and risk-adjusted performance were weak. The result does not
prove future profitability. See [OOS_REPORT.md](OOS_REPORT.md) for the full immutable metrics and
[LIMITATIONS.md](LIMITATIONS.md) for the research boundary.
