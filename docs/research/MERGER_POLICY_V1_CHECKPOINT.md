# Merger fractional-share policy V1 checkpoint

## Result

CN_A_MERGER_FRACTIONAL_SHARE_POLICY_V1 implemented. The retained 000024 official
notices and deterministic accounting regression pass. The former fractional-policy
approval blocker is resolved; this does not certify the full historical merger census.

R5 continued the existing source inventory and verified 600005 -> 600019. Its ratio
0.56 exposes a **zero-whole-share cost-basis policy gap** for a hypothetical Q=1:
T=0.56, floor(T)=0, B>0, but the approved average-cost formula B/0 is undefined.
This is an accounting boundary, not an observed strategy holding or a profitability
finding. No strategy was run to find it. Parent holdings must not be altered to avoid it.

SINGLE_SMALLEST_BLOCKER =
MERGER_ZERO_WHOLE_SHARES_BASIS_UNAPPROVED:CN-A:SSE:600005:2017-02-17.

HUMAN_APPROVAL_GATE = R5_MERGER_ZERO_WHOLE_SHARE_BASIS_POLICY.
HUMAN_APPROVAL_REQUIRED = YES. A human methodology decision must specify how positive
historical basis is represented when the approved floor produces no successor shares.
No residual asset, cash compensation, awarded share, realized loss, security exclusion,
or changed safe-start date has been invented. The guard fails before account mutation.
The approved floor convention itself is not being reopened.

## Official evidence, separate from research convention

000024 -> 001979: official ratio 1.6008; parent last session 2015-12-07;
record date 2015-12-29; A-share termination/conversion/listing 2015-12-30.
CMPD2015-177 (December 28, pages 1,4,5,7) states global fractional-remainder ranking
and computer-random allocation for ties. CMSK2015-003 (December 29, page 1) confirms
successor identity and timing. The December 28 SZSE termination notice confirms delisting.
The listing reference 25.30 is not treated as an actual opening price.

Original files remain outside Git in `full-demerger-v1`; URLs, dates, source SHA-256,
UTC retrieval timestamps and reviewed pages are in `MERGER_000024_SOURCE_REVIEW.json`.
Byte/meta verification and reversed-source replay produce:

- Event SHA-256: `503d20efc9b739e5d4cf5ce74ce5ed491b0c3175ab9e8ea1a4e8f995fb888365`.
- Manifest SHA-256: `72433bfccf310767f34710b57a3592b903d2caa4705969932e75110ff552c604`.
- Parser/version: `MERGER_EVIDENCE_V1`; external manifest:
  `full-merger-v1/000024-accepted-event-manifest.json`.
- Approval attachment SHA-256:
  `42f75ebe501d9b53d2ad8059bafc8e66f0da2f9ba9f268b64bb228160d54945e`.

600005 -> 600019: official implementation notice 2017-016, February 16, page 2,
confirms ratio 0.56 and the same population-dependent remainder/random-tie mechanism.
Notice 2017-018, February 22, confirms February 17 conversion implementation and
February 27 tradability of the newly credited shares. February 14 is the record and
parent delisting date, not the February 17 conversion-registration date.
The later completion notice must not be backdated. The acquirer's original listing
does not establish tradability of newly credited shares. Full event admission remains
pending source chronology work as well as the zero-whole-share methodology decision.

Both originals and HTTP/UTC/checksum receipts are retained in `full-merger-v1`.
Their SHA-256 values are respectively:

- `73e51dca1e5fdc4d687cef7176da275dbd642e2c1a643d4aa2887d7a8338b04c`.
- `3a4f73ce61ef81c24430822974321d4d45e38948bc09c2135908e010ffbb3b23`.

Source URLs and evidence are recorded in `MERGER_INVENTORY_V1.json`.
Canonical inventory SHA-256:
`4730dc54a498733b60830a0ca13d85d0014477964e33ad5f28152aa5a11ff8e3`.
Verified inventory receipt SHA-256:
`63b2c5b7bbdf3a6f697a4c503d816e7e3c3f9fff0b94329614c00cffb940763b`.

## Accounting and materiality

Immutable generic event facts contain identities, ratio, dates, official and research
methods, basis/cash-election policy, sources and canonical event checksum. No symbol
branch, random allocation, binary float, dependency, or modified board-lot rule.

For supported positive-whole conversions, exact Decimal multiplication precedes floor.
The central Portfolio retires the parent, preserves realized PnL/cash, and transfers
all parent basis to a nontradable pending whole-share claim and then the successor.
Pending carrying value uses the last observed parent raw close, never future prices.
Before the effective conversion, an existing halted parent remains a halted parent;
later implementation evidence is not used to manufacture an earlier ownership change.
Activation requires eligible timing and an actual raw price. Existing successor
holdings combine their historical basis with B. Conversion creates no Order or Fill.
Normal later sales use aggregate historical basis, not a rounded average-cost shortcut.

The discarded remainder exists only as UNREALIZED_HISTORICAL_ROUNDING_REMAINDER audit
metadata. It has no asset, cash, buying-power or risk-exposure value. Pending whole-share
carrying value does remain risk exposure. Additive migration 0007 persists pending
claims and rounding metadata; database roundtrip preserves Decimal strings.

Audit metadata records Q, T, whole, remainder, first observed eligible raw opening,
maximum observed raw price, maximum remainder value, and maximum FLOOR-versus-CEIL
difference. For a nonzero remainder the share-count bound is one share, otherwise zero.
CEIL is never used for holdings, cash, basis, orders, signals or performance.
Conversion events are removed from the session supplied to the strategy.

Synthetic unit tests (not historical positions/prices):

| Parent Q | T | Whole | Remainder | Full basis | Max remainder value at synthetic raw high 30 | FLOOR/CEIL bound |
|---|---|---|---|---|---|---|
| 100 | 160.0800 | 160 | 0.0800 | 3000 | 2.4000 | 30 |
| 200 | 320.1600 | 320 | 0.1600 | 6000 | 4.8000 | 30 |
| 1250 | 2001.0000 | 2001 | 0.0000 | 37500 | 0 | 0 |

Full-dataset quantities and materiality totals are **NOT_ESTABLISHED**, not zero.
No historical account position path was fabricated to compute them. The runtime
materiality API is tested, but these independent fixtures are not a full-dataset audit.

## Inventory and validation

Five identified candidates: one supported (000024); four unresolved (600005 plus
unreviewed 600553, 600991, 601299 source leads). Only two official event reviews are
complete; both have global fractional allocation. Full 2010-2025 census remains
NOT_ESTABLISHED. Leads are preserved, not silently dropped or counted as accepted.
No source backlog has been relabelled a methodology blocker.

494 isolated backend tests and 78 frontend tests pass; lint, formatting, mypy,
frontend type checking and additive Alembic schema checks pass. Coverage includes
exact Decimal floor, unchanged cash/realizations/orders/fills, full basis, later sale,
pending risk/eligibility, zero holdings, existing successor positions, rejected unsupported
methods, zero-whole atomic failure, source corruption, source order, repeated engine
execution, strategy ordering and database roundtrip. Synthetic tests are not studies.

The full dataset is not created, audited or frozen. Verified safe start and full
coverage remain NOT_ESTABLISHED. Accepted/frozen Pilot v2, prior authorities, rights V2,
600003 demerger and R4 v2 are unchanged. No Development, Validation, OOS, profitability
inspection, PR #12 merge, release, or background worker. Resume preserved R5 queues
after the zero-whole basis decision; stop at the full dataset freeze approval gate.

Machine report: `.research/reports/r5-merger-policy-v1.json`.
