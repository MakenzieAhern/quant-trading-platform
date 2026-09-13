# Corporate Action Policy

## Current approved merger accounting extension

`CN_A_MERGER_FRACTIONAL_SHARE_POLICY_V1` uses exact Decimal T=Q*R, W=floor(T),
F=T-W for verified mandatory stock-for-stock events with unreconstructible global
remainder allocation. W>0 transfers all parent aggregate basis B into W whole shares;
F is an audit-only conservative forfeiture, not an asset or cash payment.
`WRITE_OFF_PARENT_BASIS_AS_CORPORATE_ACTION_LOSS_V1` explicitly extends W=0:
extinguish parent, no successor/pending asset, successor and unallocated basis zero,
corporate-action realized PnL delta=-B, trading realized PnL delta=0, cash unchanged.
Classification: `CORPORATE_ACTION_FRACTIONAL_FORFEITURE_LOSS`. No Order, Fill,
fee, synthetic compensation, second market-value deduction or closed strategy trade.
Known official compensation cannot fall through to this convention; unsupported
deterministic compensation mechanisms remain fail-closed until implemented from terms.

Snapshots persist legacy `realized_pnl` as TRADING_REALIZED_PNL, separate
`corporate_action_realized_pnl`, `unrealized_pnl`, and `total_pnl=equity-initial_cash`.
`pnl_breakdown()` names the four reporting components explicitly. With no external
cash flows: TOTAL_PNL=TRADING_REALIZED_PNL+CORPORATE_ACTION_REALIZED_PNL+
UNREALIZED_PNL-cumulative_commission. Cash dividend income enters corporate-action
PnL; its pre-tax cash economics remain unchanged. Zero-share loss changes equity once
through removal of parent market value; realized basis reclassification is not cash.
Trade count, fill count, closed-trade win rate and profit factor are not enlarged by it.

Policies are pinned in source manifests, immutable event checksums, audit snapshots,
research execution results/replay and persisted research-run diagnostics. Existing
accepted source/dataset manifests and frozen Pilot bytes are not rewritten. Additive
schema0008 stores the two new totals; legacy total PnL is backfilled from equity and
the run's initial cash, not from newly simulated results.

600005 ->600019 ratio0.56 is the historical fixture. Last trade2017-01-23,
termination/record2017-02-14, conversion2017-02-17, new-share tradability2017-02-27.
600019 original listing2000-12-12 is not the new-share activation date. Existing
acquirer holdings remain separately orderable; pending merger claims are not shares.
Later completion evidence retains its actual publication date in activation sources;
it is not a pre-conversion signal or full-history PIT acceptance.

Full-account zero-event/position/writeoff/removed-value statistics remain unknown until
an authorized account path exists. Synthetic Q=1/2/100/3 checks do not establish full
historical materiality. No strategy or profitability inspection is authorized.

This policy does NOT select basis treatment for compulsory PARTIAL surrender in the
same continuing security. Verified600462's ordinary-holder20% surrender and diverted
30% capital-reserve issuance require separate methodology; see
`MANDATORY_SHARE_SURRENDER_SOURCE_REVIEW.json`. It must not be normalized as an
ordinary30% bonus-share credit or a mandatory merger to a new successor.

The historical paragraphs below are superseded where they describe merger rounding
as unapproved. All unrelated accepted rights/demerger/source decisions remain intact.

## Separate price and accounting paths

Adjusted close (`adjustflag=2`) is used only for factor features. Raw, unadjusted OHLC
(`adjustflag=3`) remains the execution and mark source. Adjustment factors never imply a cash flow.

BaoStock dividend rows are hashed and normalized into immutable events. Supported fields are
announcement date when present, record date, ex/operation date, cash payment date, stock-listing
date, pre-tax cash per share, stock-distribution ratio and capital-reserve-to-stock ratio. Missing
source fields remain null.

| Normalized event | Portfolio treatment |
|---|---|
| `CASH_DIVIDEND` | Apply cash per share only when the economic amount and ex-date are complete. |
| `STOCK_DIVIDEND` | Increase long quantity and reduce per-share cost basis by the exact supplied ratio. |
| `BONUS_SHARE` | Same share/cost-basis transformation, preserving its distinct source type. |
| `RIGHTS_RELATED_EVENT` | Verified standard direct subscription: `CN_A_RIGHTS_ISSUE_POLICY_V1` / `NO_SUBSCRIPTION_NO_MONETIZATION_V1`, independent of tradability evidence. |
| `SPLIT_OR_SHARE_CHANGE` | Unsupported unless explicit source terms are later available. |
| `MERGER_REORGANIZATION` | Unsupported; preserve successor/election evidence, never map to a no-effect rights event. |
| `DemergerEvent` | Separately verified mandatory demerger: approved reference-value allocation and non-tradable pending carrying state. Never infer one from a generic reorganization row. |
| `UNKNOWN_UNSUPPORTED` | Persist provenance; block accounting and eligibility. |

Materially unresolved or unsupported events raise a portfolio error rather than silently altering holdings.
Short-position corporate-action accounting is outside this long-only study. The current BaoStock
endpoint recovered in the preceding checkpoint; dividend-only responses still do not establish
rights or full corporate-action coverage. Corporate-action readiness remains PARTIAL.

## Human-approved mandatory demerger convention

`CN_A_MANDATORY_DEMERGER_POLICY_V1` applies to a verified immutable `DemergerEvent`,
not to every merger/reorganization row. No production symbol special case exists.
600003 is the historical regression fixture; its official source review is in
`DEMERGER_SOURCE_REVIEW.json`. Full event census remains unfinished.

At effective conversion, remove the parent from order eligibility/marks/ordinary
positions and retain Q, aggregate cost B and Q times the last verified raw close in
`PendingDemergerEntitlement`. The accounting label is
`CORPORATE_ACTION_PENDING_CARRY_VALUE`; it is never a quote, signal, factor, order,
fill, cash proceeds or executable liquidity. Risk exposure includes the carrying
value; buying power does not treat it as cash. No parent feature history is copied.

600003 termination is2010-02-26; legal completion2010-03-01; both successors list
2010-03-19. Pre-effective conversion evidence is separate from later pre-listing
reference evidence published2010-03-18. Preserve aggregate basis while pending;
allocate only after that evidence is available, before ordinary trading logic.
601188 receives B*2.08/3.87;601518 receives the Decimal residual of B, equivalent
to B*1.79/3.87 within the fixed28-digit accounting context. Sorted stable IDs fix
residual assignment. Aggregate basis is authoritative after conversion, including
partial sales and distributions; display average price does not replace it.

Activation requires legal/listing eligibility and actual positive raw openings for
every successor. A missing opening fails closed without partial ownership mutation.
After activation raw marks determine unrealized PnL; later actual fills determine
realized PnL. Conversion creates no realized PnL, synthetic orders/fills or cash.
`NO_ELECTION_UNLESS_EXPLICITLY_PREDECLARED_AND_ELIGIBLE`: mandatory path only here.

Unsupported allocation methods, asynchronous successor activation, fractional
successor quantities, pre-existing successor-position collisions or unavailable
pre-listing allocation evidence fail closed; no fallback is silently selected.
The explicit allocation enum does not authorize its unimplemented alternatives.
Snapshot JSON preserves pending entitlements and exact aggregate basis; additive
Alembic20260913_0006 adds default-empty JSONB without rewriting historical results.

R5 later identified000024's materially different1:1.6008 merger. Official integer
allocation depends on all holders' remainders and random ties. No deterministic
simulated-account convention has been approved. See `DEMERGER_POLICY_V1_CHECKPOINT.md`.

## Human-approved rights convention

`CN_A_RIGHTS_ISSUE_POLICY_V1` / `DECLINE_SUBSCRIPTION` is a predeclared research assumption,
not a profitability choice. It applies to later Development/Validation/OOS only after separate
stage authorization. No study is authorized by this policy.

The immutable `CorporateAction` captures the event independently of portfolio participation.
Rights fields retain announcement, record, ex/effective dates, subscription window, payment
deadline (date precision, no invented intraday time), positive subscription price and ratio,
eligible share basis, optional new-share listing, source document/URL/version/document hash,
UTC retrieval time and a derived event checksum. Unknown fields remain null. Source total
company capital must not substitute for the eligible A-share base. Later listing facts belong
to their later source availability, not an earlier ex-date record. The rights inventory is
explicitly not admitted as a full point-in-time event ledger.

For a supported event, holdings Q, cash C and historical acquisition basis B remain unchanged
through subscription and lapse. No entitlement asset, borrowing, capital injection, cash
reservation, subscription Order/Fill, additional shares or compensation is created. Actual
raw/unadjusted marks reflect price impact; the engine does not restore a theoretical ex-rights
value. Adjustment factors/adjusted prices remain feature-only and never enter portfolio cash
or share accounting. Rights do not remove the underlying security from the historical universe.

Standard structure is explicit, never inferred from a provider row or missing variant.
`rights_event_class` and `entitlement_tradability` are independent immutable source facts;
the portfolio action policy is a separate constant. `NOT_EVIDENCED` remains exactly that,
never `NON_TRADABLE_CONFIRMED`. A standard direct subscription with any tradability evidence
state uses no subscription and no monetization. A separately listed/transferable instrument,
separate entitlement market price, mandatory conversion, cash settlement, automatic compensation
or another explicit nonstandard structure fails with `RIGHTS_EVENT_UNSUPPORTED_VARIANT`.
Legacy explicit nonstandard evidence cannot be overridden by assigning a standard class.

### Required fields and downstream dependencies

| Fields | Dependency and acceptance rule |
|---|---|
| Stable security ID, rights event structure, ex/effective date, source identity/hash | Essential for event identity, deterministic effective ordering and auditable authority. Missing/contradictory values fail `EVENT_IDENTITY_UNRESOLVED`. |
| Subscription price/ratio, eligible share basis, deadline, record date | Preserved metadata; no subscription or monetization calculation consumes them. Missing values stay null and may be `STANDARD_PARTIAL_BUT_ACCOUNTING_SAFE`. |
| Announcement/source availability | Preserve actual publication. Missing availability cannot authorize PIT feature use; accounting-safe classification is not PIT dataset admission. Never backdate later result/listing evidence. |
| Suspension window/resumption | Must come from independent dated evidence before permitting a fill. Missing subscription metadata does not imply trading permission; existing unknown-tradeability no-fill gate remains. |
| Adjustment alignment | Uses separately accepted effective-dated factors. Rights accounting classification does not certify factor authority or compute a substitute factor from incomplete terms. |
| New-share listing | Retain later evidence separately; no subscribed shares exist under this policy. Never use a future listing as an earlier eligibility fact. |

Complete versus partial metadata is reported independently from accounting safety. Known
contradictory material dates remain blocked; the policy never repairs them by assumption.
For all standard events, entitlement-sale proceeds and synthetic entitlement value are zero.

## Deterministic session precedence

The point-in-time master/lifecycle and accepted calendar/status/rules supply the session.
All session actions are validated before any corporate-action mutation, including unsupported
structural events. Pre-open accounting order is: cash dividend on existing shares, stock
dividend, bonus shares, then declined rights; exact event content breaks same-type ties.
Structural split/merger/unknown events fail closed, not an invented ordering-dependent payout.
Then pending ordinary orders face the existing independent execution/suspension gate, raw
OPEN execution if eligible, raw CLOSE marks, and completed-session strategy observation.
The existing corporate-action opening-uncertainty guard remains unchanged; it is not a
whole-security universe exclusion. Subscription and lapse schedule no portfolio transactions.
No future listing date changes eligibility before the accepted lifecycle says it can.

## Acceptance boundary

Event model/accounting/replay engineering PASS does not certify the full historical inventory.
See `RIGHTS_ISSUE_POLICY_CHECKPOINT.md` and `RIGHTS_ISSUE_SOURCE_REVIEW.json` for the current
historical checkpoint. The current V2 inventory and material full-history stop are in
`RIGHTS_ENTITLEMENT_V2_CHECKPOINT.md`. No census acceptance follows from policy permissiveness.
R4 v2 remains PASS with **R4_REAL_DATA_FILL_COUNT = 0**: it proves orchestration, replay,
no-look-ahead and API/UI parity, not real historical filled-trade corporate-action accounting.
The focused synthetic execution/portfolio tests are the current fill-path engineering evidence.
No strategy was changed to generate fills; no R4 replay or profitability inspection was performed.

Readiness is measured using four explicit counts: securities queried over the declared period,
source rows returned, complete economically actionable events, and unsupported/incomplete events.
It also records the number of independently reconciled ex-dates. Coverage remains PARTIAL until the
2010–2025 provider range is reachable and these denominators are frozen; adjusted-price availability
does not raise the corporate-action score.
