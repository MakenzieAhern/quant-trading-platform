# Bias Controls

- Eligible securities, board/symbol periods, listing/delisting, ST, suspension and benchmark
  membership are resolved as of the research date; today's list cannot define history.
- Factors require 252 completed sessions and cannot access t+1. Missing values are excluded, never
  hidden-imputed. Adjusted prices cannot be execution prices.
- Dataset and partition SHA-256 checks reject silent revisions; every run stores Git, dataset,
  provider, rule, strategy, split, benchmark, cost and random-seed lineage.
- Stable tie-breaking and Decimal arithmetic make rankings and accounting deterministic.
- Development, validation and OOS periods do not overlap. Parameter search is absent. OOS requires
  explicit approval after every research choice and the dataset checksum are frozen.
- The full dataset passed all mandatory R5 gates before its immutable Gate B freeze. Development,
  Validation and the one authorized Official OOS run bind to that same manifest checksum.
