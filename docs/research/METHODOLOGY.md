# Research Methodology

The frozen candidate strategy is `cn_a_cross_sectional_momentum_low_vol_v1`. At completed session
t it computes `MOM_12_1 = adjusted_close[t-21]/adjusted_close[t-252]-1`,
`TREND_120 = adjusted_close[t]/SMA120[t]-1`, and `LOW_VOL` as the negative population standard
deviation of the prior 20 completed-session adjusted returns. Missing inputs exclude the security.

At every twentieth valid session, each factor is deterministically winsorized and population
z-scored. Invalid dispersion makes the factor unavailable. The average of all three z-scores is
sorted descending with `security_id` as tie-breaker. The top decile, capped at 20 securities, is
equal-weighted and rounded down to valid lots. Orders traverse the existing RiskEngine, OMS,
execution broker and Portfolio path.

The initial split is Development 2010–2017, Validation 2018–2021, and OOS 2022–2025. It is a
methodology definition, not evidence that data coverage is ready or that any period has run.
