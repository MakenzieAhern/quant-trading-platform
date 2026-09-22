# Research Methodology

## Approved v1.1 instrument scope

PILOT_INSTRUMENT_SCOPE = ORDINARY_A_SHARE_EQUITIES_ONLY.
Human methodology decision approved on2026-09-12: CN_A means ordinary
RMB-denominated A-share equities on SSE/SZSE Main, STAR and ChiNext boards.
Board and instrument type are independent. CDRs, B-shares, ETFs/funds,
bonds/convertible bonds, preferred shares, warrants and other instruments are
outside v1.1 scope before market-data requirements are evaluated. Future versions
require explicit separate instrument support. This is a human scope decision,
not an assertion that the previously ambiguous contract already said this, and
not a performance- or provider-convenience-based exclusion. No strategy results
were inspected. Classification requires authoritative dated evidence; unknown
types cannot be admitted into the final Pilot Dataset.

Instrument evidence distinguishes dated notices from explicit original A-share
listing-register records. For the latter, the exchange's A-share code and A-share
listing date identify the original listed instrument; an undated register is not
given an invented publication date. Retrieval time remains separately preserved.
The mixed STAR stock/CDR register requires dated original IPO evidence, not merely
today's SEC_TYPE paired with an old listing date. Future-effective changes cannot
alter earlier membership, and incomplete/overlapping temporal evidence fails closed.

Execution follows [CN_A_DAILY_OPENING_LIMIT_V1](DAILY_EXECUTION_CONVENTION.md), a
`SIMULATION_ASSUMPTION`, separate from official market-rule authority. Daily OHLCV
cannot reconstruct exact historical auction fills. Missing required evidence
means no fill. This limitation must remain in the final strategy report.

The frozen candidate strategy is `cn_a_cross_sectional_momentum_low_vol_v1`. At completed session
t it computes `MOM_12_1 = adjusted_close[t-21]/adjusted_close[t-252]-1`,
`TREND_120 = adjusted_close[t]/SMA120[t]-1`, and `LOW_VOL` as the negative population standard
deviation of the prior 20 completed-session adjusted returns. Missing inputs exclude the security.

At every twentieth valid session, each factor is deterministically winsorized and population
z-scored. Invalid dispersion makes the factor unavailable. The average of all three z-scores is
sorted descending with `security_id` as tie-breaker. The top decile, capped at 20 securities, is
equal-weighted and rounded down to valid lots. Orders traverse the existing RiskEngine, OMS,
execution broker and Portfolio path.

The immutable split is Development 2010–2017, Validation 2018–2021, and OOS 2022–2025. Development
and Validation completed under frozen inputs. Gate C then froze unchanged S4 and authorized one
Official OOS run; that authorization is now consumed. No post-OOS retuning is permitted.
