# R5 consolidated methodology gate v1

## Approval record

Status: **APPROVED**

At `2026-09-20T15:32:14Z`, the user instructed the autonomous controller to
continue with the recommended project path in Goal mode. The only recommended
path awaiting approval was this consolidated gate, so the instruction is
recorded as approval of `R5 RESEARCH CONVENTIONS V1`.

## Purpose

All independently recoverable public-source facts are closed. One human
approval can now resolve the two remaining research conventions without buying
data, inventing facts or inspecting strategy performance.

## Convention A — official partial feature observation

For the 239 ChiNext securities on 2011-07-25:

- retain the exact official close and the official volume/amount bounds;
- retain unknown open/high/low/volume/amount as unknown, never synthesized;
- admit the observation only for close-based factor continuity and the already
  proven invariant liquidity-eligibility decision;
- prohibit orders, fills and execution-price use on the observation;
- persist the `OFFICIAL_PARTIAL_FEATURE_ONLY_NON_TRADABLE` lineage class;
- require the dataset audit to fail if the row reaches any execution path.

This convention is not promotion to complete official OHLCV. It is a bounded
research treatment for one non-rebalance, non-execution session.

## Convention B — full-history research-account costs

Extend the already frozen Pilot simulation model unchanged across 2010-2025:

- commission: `max(0.0003 * notional, CNY 5)`;
- transfer/clearing allowance: `0.00001 * notional`;
- seller stamp duty: `0.001 * notional` through 2023-08-27 and
  `0.0005 * notional` from 2023-08-28.

This is an explicit research-account convention, not a claim that every broker
contract was identical or that the allowance is a statutory historical rate.
The official effective-dated fee history remains separately preserved in the
source ledger. The convention must not be changed after strategy results are
inspected; an actual account contract would require a new dataset version.

## Approval effect

Approval authorizes implementation and audit of these two conventions only.
It does not authorize paid data, dataset freeze before all R5 checks pass,
strategy research before the Full Dataset freeze, PR merge or live trading.

Reference approval text:

`APPROVE R5 RESEARCH CONVENTIONS V1`
