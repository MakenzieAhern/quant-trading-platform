# Known limitations

## Research and data

- Daily bars cannot reconstruct exact auction queues, intraday paths or historical fill priority.
  The execution model is a conservative simulation assumption, not an exchange-fill claim.
- The public-source reconstruction is extensive but does not turn free public data into a licensed
  real-time market-data feed.
- Feature-only rows may support approved factor continuity but are never treated as tradable OHLCV.
- Adjustment factors and corporate-action accounting are audited, but tax, account-contract and
  broker-specific treatments can differ from the frozen research convention.
- CSI300 is a comparison series; the implementation does not claim an investable total-return
  benchmark replication.

## Statistical interpretation

- No Validation candidate passed every robustness gate. S4 was the pre-declared fallback.
- Official OOS ran once and cannot be rerun or replaced after inspection.
- The OOS total return (0.76%) and Sharpe (0.067) are weak; positive excess versus a declining
  benchmark does not establish reliable profitability.
- One historical sample cannot prove persistence, capacity or future returns. The project makes no
  profitability guarantee and is not investment advice.

## Product and operations

- Paper trading is local simulation only; there is no live broker, real-money order path or broker
  credential support.
- The A-share Paper route uses a deterministic synthetic 2030 scenario because v1.1 has no
  authoritative post-2025 live feed. It validates the product execution path only; it is not
  research evidence and never replays Official OOS.
- The application is unauthenticated, single-user and loopback-only; it is not approved for public
  internet exposure or production high availability.
- A backend restart marks active paper execution `INTERRUPTED`; it does not silently resume stale
  in-memory execution.
- The system is daily-frequency research, not HFT. It has no options/futures, margin/borrow/locate
  model, distributed execution, ML/GPU strategy, or Hong Kong/US v1.1 scope.
- Large market datasets and formal run artifacts stay outside Git and must be mounted separately.
