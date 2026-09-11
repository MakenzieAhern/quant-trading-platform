# CN_A_DAILY_OPENING_LIMIT_V1

Classification: `SIMULATION_ASSUMPTION`. Human decision: APPROVED, 2026-09-11.
This is a conservative daily-bar simulated execution convention, not an
official exchange rule, guaranteed execution, or historically proven actual fill.
The platform cannot reconstruct exact auction queues, matched quantities, or
intraday liquidity from daily OHLCV. Daily participation below is a proxy, not
evidence of actual opening-auction participation.

## Immutable instruction and expiry

Signals are available after the completed session, at 15:00:00.000001 Asia/Shanghai.
Quantity is derived from that completed-session target and current holdings.
Limit L is that security's raw close on signal day (never adjusted close).
The intended session is the next open date in the accepted calendar, not the
next available bar. The local instruction uses only information through t.
No intraday repricing, queue reconstruction, or retries into another session.
All unfilled instructions expire after their one intended session; missing bars
do not become synthetic suspensions or fills. End-of-run orders are cancelled.

## Independent eligibility, then pricing

The next session must have matching dated status/rules and official tradeability
affirmatively true; unknown is not true. Suspension, nonexecutable rules, absent
exchange pre-close, no-limit/first-listing exceptional sessions, corporate-action
opening uncertainty, or single-price/locked bars cause no fill. Ordinary legal
price bounds use the exchange pre-close, not yesterday's unadjusted close, with
half-up tick rounding. L must satisfy bounds and tick size. Integer quantities
must meet board minimum/increment and maximum LIMIT size. SELL cannot exceed
existing holdings; a below-minimum residual must be sold in full.

The raw OPEN must be strictly inside the legal daily bounds; the full daily
range must remain within them. BUY requires OPEN <= L; SELL requires OPEN >= L.
These inequalities are necessary, not sufficient. A non-flat valid bar and
quantity <= 1% of reported daily share volume are additional fixed, ex-ante
conservative proxy conditions. No performance result selected that 1% ceiling.
Later daily observations can veto the simulated fill, never change an order's
parameters. This is not a deployable intraday decision rule or a claim that the
reported OPEN necessarily occurred in the actual opening auction.

Only after all conditions pass is raw OPEN used as the simulated price, with a
logical opening timestamp of 09:25 Asia/Shanghai. No adjusted price and no extra
slippage is applied in V1. This timestamp is model bookkeeping, not reconstructed
trade-time evidence. Where available data do not establish the convention's
required conditions, there is no fill. Continuous-auction price cages, storage,
and intraday halt sequence are not simulated; unbounded sessions are excluded
from execution, not silently removed from the dataset.

## Costs and separate gates

Use the existing effective-dated model exactly once on accepted fills:
commission max(0.0003 * notional, CNY 5), transfer/clearing allowance 0.00001
of notional both sides, seller stamp 0.001 before 2023-08-28 and 0.0005 thereafter.
Commission and the retained transfer/clearing allowance are frozen research
assumptions; the latter's statutory source remains unverified, so this document
does not assert that it is an officially proved settlement rate. The latest
human decision expressly permits already accepted/frozen research costs.
No separate exchange/regulator fee is added on top of the commission assumption.
Stamp effective dates remain authoritative claims. No study has been run.

`MARKET_RULE_AUTHORITY` tests official source claims. It does not prove fills.
`EXECUTION_CONVENTION_VALIDATION` separately tests deterministic conservative
model behavior. Both must pass before R2. Freezing this model specification does
not freeze the Pilot Dataset or authorize strategy research.

This limitation must be included in every final strategy report; a report
omitting it must not be accepted as the final research deliverable.
