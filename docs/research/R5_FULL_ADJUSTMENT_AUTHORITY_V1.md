# R5 full adjustment authority

Date: 2026-09-20. Coverage: 2010-01-01 through 2025-12-31.

## Decision

`FULL_ADJUSTMENT_AUTHORITY = PASS_FOR_FULL_DATASET`.

All 5,436 accepted-master intervals have one checksum-consistent retained
factor curve. The 43,019 in-range provider factor changes are classified once,
without overlap or omission:

| Classification | Changes |
| --- | ---: |
| Official supported-event date | 40,691 |
| Official bonus-oracle factor parity | 892 |
| Official special-mechanics parity | 20 |
| Exact official gross-terms parity | 1,348 |
| Official residual-mechanics parity | 33 |
| Official remaining-mechanics parity | 35 |
| **Total** | **43,019** |

The earlier gross-term conflicts were caused by using the ex-date adjusted
reference field as the economic pre-close. Replaying against the prior official
session close yields 1,317 exact gross-term matches plus 31 matches at the
provider's six-decimal cash precision. The 20 special-mechanics conflicts pass
official direct-share or restructuring reference-price formulas. The 33
source-uncovered residuals now pass official mechanics; 000156 is explicitly
rebased at its first observed in-range session rather than assigned an inferred
factor formula. The final 35 cases pass declared reference prices, direct holder
ratios, exact cash terms or explicit first-traded-session boundaries.

Six accepted official events have no provider factor change on the official
ex-date. Three are bound to the provider's first later positive-volume factor
change. The other three—600157 on 2024-08-26, 600781 on 2019-07-22 and 002129 on
2023-05-26—have deterministic official-cash overlay multipliers derived from
the checksum-bound event and official prior close. Materialization must multiply
the provider factor from each effective date forward. Unresolved factor changes
and unresolved supported events are both zero.

Provider factors remain feature-series normalization only. They do not create
cash, shares, entitlements or portfolio corporate actions. The frozen-vintage
source does not establish historical publication availability.

## Evidence

| Artifact | File SHA-256 | Manifest SHA-256 |
| --- | --- | --- |
| residual mechanics v3 | `e1c1d8fb958e89936455efeb04e7bb5495bb5a6474258afb219feda845995e2c` | `5d982ae8f21f545fccd603cc621c819de1ded687c352886f607083ddda23a45c` |
| special mechanics v2 | `21d3a9fbb6dd3f55e90957bdc9a8a7f52f69d944c5f8b03672621ec068bd92bc` | `418ade9cf12bf29bc900cd444891ef5031a21946ca0bd71466274c6e129bff37` |
| remaining mechanics v2 | `bc5de014bfbd4e3fe18d2a395b6f8c6fc3f9e973632602a8ba41fe16ca5b208f` | `d1cc979b22adc88e8f7b5a24505e52975096523c8eb9d490c780f0d3105c9c3a` |
| full authority v2 | `14eabedf0ab539632dc2fe41e10239ca69afb9073c1e3362565e45af95a97f60` | `0d6666849cafbd61b05e0396691c5f63ed128c5a2622b92147be5cf72e8b9bc0` |

Input-order replay and checksum repeatability pass. The Full Dataset remains
uncreated, unaudited and unfrozen. Raw OHLCV and historical-cost methodology
gates remain independent; no Development, Validation or Official OOS study ran.
