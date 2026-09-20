# Decisions

## 2026-09-20 — accept full adjustment authority with explicit cash overlays

Accept the deterministic 43,019-change partition after official-source replay:
supported-event date binding, bonus parity, special mechanics, exact gross-term
economics and the two residual mechanics sets are disjoint and exhaustive. For
the six official events without a same-date provider change, bind three to the
first later positive-volume factor boundary and persist official-cash overlays
for the other three. Apply an overlay from its official ex-date forward; never
turn it into a portfolio cash or share entitlement. This closes adjustment
authority only. Raw OHLCV and historical costs remain independent blockers.

## 2026-09-20 — close only effective-dated historical cost intervals

Accept the checksum-bound Ministry of Finance, State Tax Administration,
ChinaClear and CSRC notices for their stated stamp-duty, transfer-fee and
handling-fee dates. Treat the SSE 2010 factbook as a point-in-time snapshot.
Treat the 2012 ChinaClear rates as collector-component evidence because the
same official record identifies a separate broker-retained component. Do not
infer a continuous pre-2015 investor-total transfer charge or minimum, and do
not change the account commission convention from public rules alone.

## 2026-09-20 — accept conservative official daily-trade suspension boundaries

Accept a later positive-turnover row in the complete official SZSE daily corpus
as proof that the security traded during that day, but keep execution blocked at
the open because the intraday resumption time is not established. Never use a
same-day row to close a suspension. Where no later trade exists, close only at
an accepted official lifecycle end or right-censor an active suspension at the
research coverage end. This closes suspension authority without inventing a
resumption timestamp or promoting daily prices to raw OHLCV authority.

## 2026-09-20 — reject silent observed-only factor-window drift

The 2011-07-25 SZSE raw gap is not neutral under the current 253-observation
factor implementation. Reject silently skipping the calendar session and using
an older observation. Preserve two auditable choices for explicit approval:
official-only strict continuity with conservative factor unavailability, or
feature-only use of the existing dual-provider candidate. Do not promote the
candidate to official raw authority, synthesize a row, or inspect strategy
performance to choose between treatments.

## 2026-09-20 — stop generic public search for customer commission scope

Accept the checksum-bound Guangdong CSRC notice as authority that net-versus-
all-in commission depends on the written customer agreement and, where absent,
actual account practice. Classify the remaining research-account choice as
`ACCOUNT_CONTRACT_OR_RESEARCH_CONVENTION_REQUIRED`. Do not infer a universal
commission composition, change the executable fee model or run a study from
this source alone.

## 2026-09-20 — classify the 223-row difference as post-close scope

Accept the checksum-bound official SZSE guidance that ChiNext post-close
fixed-price trades execute at the day's close and are added to the final daily
total, together with the technical notice that the spot close file excludes
those trades. Deterministic replay leaves zero unexplained transaction-scope
gaps on 2023-04-10. This closes only the 223-row scope classification; it does
not directly observe those trades, promote a non-official provider, or resolve
the separate 239-row 2011-07-25 official-source gap.

## 2026-09-20 — ChinaClear operative notices resolve the 2012 transfer base

Accept the checksum-bound ChinaClear notices dated 2012-04-30 and 2012-08-02
as the operative authority for the SSE A-share transfer-fee base. They specify
traded face value at 0.375 per mille from 2012-06-01 and 0.3 per mille from
2012-09-01; SZSE remains 0.0255 per mille of traded amount. Preserve the CSRC
news compilation's incompatible traded-amount wording as a source conflict,
but do not let a news summary override the fee collector's original operative
notice. This does not resolve fee minimums, the full pre-2012 interval, the
broker-retained component or the research commission's net/all-in scope, so the
executable model remains unchanged.

## 2026-09-20 — official aggregate prevents raw candidate promotion

Accept the fixed 239-row Tencent/Sina replay as a reproducible diagnostic: OHLC
and volume match exactly, amount differences stay inside the accepted
plus-or-minus 100 CNY interval, and every relevant 20-observation liquidity
window is decision-invariant. The official SZSE yearbook total is larger by
1,385,518 shares and approximately 23.84 million CNY; two official SZSE block
trades close that aggregate difference at published precision. Accept this as
transaction-scope evidence only. Do not promote either candidate provider's
per-security OHLC, infer a mass suspension, or treat the separate 223-symbol
after-hours scope difference as closed. Keep `RAW:FULL_UNIVERSE` open.

## 2026-09-20 — close corporate-action P1 without promoting other authorities

Accept the retained official evidence for 000522-to-600332 and
002013-to-600372 under the already-approved merger policies. Accept 301262's
2023-10-31 accounting boundary only through issuer notice plus official SZSE
factbook corroboration, retaining the malformed notice date. Classify 601607
and 603408 by their 2026-01-05 ex/accounting date as outside the requested
coverage. Corporate-action source facts pass; raw and suspension requirements
remain independently open.

## 2026-09-20 — accept official SZSE disclosure host, fail closed elsewhere

Accept `disc.static.szse.cn/disc/` as an official SZSE disclosure surface with
the SZSE referer, alongside the existing CNINFO static surface. Keep the
allowlist exact and reject arbitrary hosts. The 002186 notice closes one
2013-10-11 market-open resumption; it does not generalize a parser or promote
the remaining 2,009 boundaries.

## 2026-09-20 — retain official transaction-cost contradiction

Accept the five checksum-bound CSRC/SSE/SZSE pages as claim-level evidence and
close the exact 2012-01-01 regulator-fee boundary. Do not choose between the
official face-value and traded-amount descriptions of the 2012 SSE transfer
charge, and do not infer whether the approved research commission is net or
all-in from an unrelated account decision. Keep the executable model unchanged
and full transaction-cost authority PARTIAL.

## 2026-09-20 — superseded v65 public-source checkpoint

Reuse `CN_A_MERGER_FRACTIONAL_SHARE_POLICY_V1` for the fully evidenced
000578-to-000792 and 600253-to-600056 chains. Do not extend that quantity rule
into a cross-market account-registration rule for 000522-to-600332 or
002013-to-600372: the official documents establish ratios and dates but not a
generic portfolio's registered successor account. Keep the three malformed or
out-of-range cash facts, full raw/suspension requirements, adjustment economics
and transaction-cost intervals open. No paid product is required on current
evidence, and no paid-source option report is justified yet.

This checkpoint is superseded by cumulative V68 and the decisions above; its
open cash and cross-market paths are preserved only as audit history.

## 2026-09-20 — visual date review is checksum-bound and date-only

Use direct rendered-page review only for named official documents whose
retained text extraction is ambiguous. Bind each review to symbol, source
SHA-256 and page numbers; keep its scope limited to record/ex dates. Do not use
the review to invent economic terms, repair an internally contradictory year
without corroboration, or shift an official event date to fit a provider factor
step.

## 2026-09-19 — gross official terms do not define historical provider factor cash basis

Reuse all retained CNINFO bytes before network acquisition. Treat exact
implementation dates and parsed gross cash/bonus terms as candidates until
correction precedence, lifecycle and accounting are closed. Do not replace
gross shareholder cash with a tax-net or synthetic ex-price amount merely to
fit a historical factor step: all 463 combined-term checks currently conflict
under the gross formula, so the provider convention remains unresolved and no
authority is promoted.

## 2026-09-19 — adjustment date routing is evidence, not event acceptance

Join unmatched retained factor changes to the checksum-bound official bonus
source oracle by accepted security identity and exact ex-date. Use the accepted
A-share `0.01` price tick to bound displayed pre-close/ex-price rounding, but do
not infer exact issuer terms, registry allocation or economic authority from a
date or displayed-price match. Preserve all conflicts and dates without an
official route instead of classifying them as normal.

## 2026-09-19 — yearbook fee snapshots corroborate, but do not invent intervals

Use the sixteen checksum-bound SZSE yearbooks as official annual fee snapshots.
Accept an effective boundary only when the yearbook itself states the date, as
the 2025 book does for 2023-08-28. Do not turn a change between adjacent annual
tables into an inferred daily boundary. The 2015 inclusion footnote is evidence
that separate component charges can double count commission, not permission to
reinterpret the approved research-account commission assumption.

## 2026-09-19 — replay suspension improvements without promoting raw authority

Reapply the accepted 27 listing intervals to the v32 full suspension ledger and
bind both inputs by file and canonical-manifest hashes. Better suspension
classification may explain source-absent rows, but it cannot establish raw
OHLCV values. The replay changes 377 base classifications while preserving the
same 239 residual security-date keys, so raw authority remains PARTIAL.

## 2026-09-19 — preserve resumption date separately from opening eligibility

An official date closes a suspension interval but does not by itself prove the
security was executable at that session's open. Preserve explicit `开市` as
open-confirmed, explicit afternoon/13:00 as open-blocked, and unstated timing as
unknown. If same-date evidence represents both an opening resumption and a new
intraday halt, keep the conflict and conservatively mark opening execution
blocked. This applies the already-approved daily-opening convention; it does
not create a new fill assumption.

## 2026-09-19 — scan-only official pages require bounded visual corroboration

OCR is a routing/extraction aid, not standalone authority. Accept a scan-only
resumption date only when the retained official PDF checksum, deterministic OCR
cache, strict date parser and direct rendered-page review agree. Applying this
rule to 29 current low-text documents accepts 000545 and 002033 only; the other
27 remain unresolved.

## 2026-09-19 — supersede historical SZSE resumption acceptance counts

Decision: use strict retained-evidence revalidation v4 as the sole resumption
supplement for current suspension authority, together with terminal closure
reports v1-v4. Preserve prior reports as immutable audit history, but do not
admit their deadline, conditional or application-only boundaries. This is a
source-integrity correction, not a methodology change and not a data freeze.

## 2026-09-19 accept explicit intraday timing, not inferred duration

An official notice may close a suspension on the same date when it explicitly
states morning halt/afternoon resumption or one-hour/half-day halt then
resumption. An explicit `复牌时间为` full date is also accepted. Do not infer a
date from `一天`, a disclosure dependency, a deadline, an application or a
condition. This closes four facts without converting relative promises into
trading boundaries.

## 2026-09-19 normal-trading clauses require one attached date

Treat official `恢复正常交易` as a resumption only when a single date is attached
to that clause. In a sentence with disclosure, meeting and resumption dates,
do not let an earlier date bind through a broad text window. Reject conditional
and application-only resumption language. This conservative grammar closes
four facts and deliberately leaves 000981 and 002217 unresolved.

## 2026-09-19 restoration to listed trading is a resumption boundary

Treat an official `恢复上市` date as the suspension exit only when the text
explicitly states that the stock itself resumes listed trading on a full date.
Reject dates for applications, exchange acceptance, progress reports,
supervision, measures, aspirations and the original suspension. Bind the
accepted date to the current suspension interval and preserve all official
source hashes. This closes eight long-duration listing suspensions without
equating an application date with a trading date.

## 2026-09-19 identical official bytes merge event bindings deterministically

When the same official PDF SHA-256 appears in multiple acquisition manifests,
union its exact `affected_suspensions` bindings and retain the earliest UTC
receipt. Require issuer, publication date, title, URL and extracted text to be
identical; otherwise fail closed. This avoids treating repeat retrievals as
conflicting evidence without weakening semantic provenance.

## 2026-09-19 terminal treatment must bind to the manifest event

Accept an SZSE terminal suspension only when the retained official document's
immutable `affected_suspensions` field names the exact event, the document
explicitly says either no delisting-consolidation period or suspension through
termination, and the official master supplies one matching lifecycle end.
Do not choose the nearest prior halt from publication timing and do not create
a `resumed_at` value. This v2 rule adds six closures while preserving the v1
42 and leaves authority PARTIAL.

## 2026-09-19 direct-to-delisting is a terminal closure, not a resumption

When a retained official issuer PDF states the exact suspension date and that
the security will not enter a delisting-consolidation period, and the accepted
official point-in-time master supplies one matching lifecycle end, record an
`OFFICIAL_TERMINATION_NO_DELISTING_PERIOD` closure with `terminal_at`. Never
populate `resumed_at` for that event. Preserve both source chains, hashes and
retrieval timestamps. This source-bound rule closes 42 false resumption gaps;
it does not infer terminal treatment from a missing bar, a title, or a delisted
name and does not apply where the official notice permits a consolidation
trading period.

## 2026-09-19 original issuer zero-cash plans corroborate two final transfers

Treat the 688368 CNINFO-hosted 2024-05-08 shareholder material and 603703
original 2023-04-21 issuer-signed designated-paper disclosure as official
evidence of the **plan's** zero-cash terms, not as standalone final execution.
The final CNINFO implementation notices independently identify shareholder
approval and the same 0.4 transfer and repurchase exclusion; 603703's final
reference-price formula explicitly substitutes zero cash. The official SSE
publication index uniquely identifies both plan titles, but SSE-hosted plan
PDF bytes were not obtained. Retain this distinction in the immutable audit
and keep the 22 account-level fractional-share events unaccepted pending the
existing human methodology decision. Do not infer cash terms from a formula
placeholder alone or alter the cumulative P1 ledger.

## 2026-09-19 original SZSE-signed newspaper notices for 002075

The 2010-04-30 and 2011-03-30 original `证券时报` page PDFs carry notices
signed by 深圳证券交易所, not journalist summaries. They state the effective
2010-05-07 listing suspension and 2011-04-08 restoration of the same
002075 issuer after its name change. Retain the original page bytes,
publication dates, UTC receipts and SHA-256, and apply these narrowly
to the 216 corrected source-absent dates strictly within that interval.
Do not infer prices, volume/amount, execution availability or a mass
ChiNext halt. The retrospective audit classification is not permission
to leak later restoration knowledge backward into a 2010 signal.

## 2026-09-19 original designated-paper issuer notice for 000732

The issuer-signed 2010-09-21 `证券时报` notice is original designated-paper
disclosure, not a media summary: it names that paper as an issuer disclosure
outlet, the unique official CNINFO index identifies the same issuer notice,
and a SZSE-hosted issuer PDF independently names the outlet. Its original
PDF and the supporting source bytes/index are SHA- and receipt-bound.
Apply the previously accepted 600337 designated-paper source-substitution
principle only to 000732's bounded historical listing-suspension interval:
2007-05-11 through the day before 2010-09-30 restoration. The 2010 notice
is retrospective for 2007, not point-in-time signal data. Original CNINFO
PDF bytes are still unverified. Do not infer missing bars, tradability,
volume, amount or a broader source-substitution policy.

## 2026-09-19 retrospective official listing history explains source absence only

The SZSE-hosted 2020 issuer report quotes 000156's 2006-04-13 listing
suspension and 2012-10-19 restoration decision. Its archived PDF and UTC
receipt support a bounded historical reconstruction of **daily export row
absence** for that security, consistent with the approved free official-
public-source policy. The report's 2020 publication is preserved: it is
not a point-in-time 2010 signal, a fabricated contemporaneous notice,
proof of a tradable OHLCV bar, or full execution authority. Only the 665
previously unresolved dates strictly within the official interval change
classification; all other gaps remain open.

## 2026-09-18 derivative notice is not a second distribution

Scope an official issuer's private-placement price/quantity adjustment after
an implemented annual distribution, or a pre-final convertible conversion-halt
hint, as non-primary only when its source bytes are retained and exactly one
accepted final issuer implementation matches the security, annual period and
chronology. Check any quoted record/ex-date against that event; do not create
a second cash or bonus event from the derivative notice. Five v6 notices meet
these guards. This is source-document reconciliation, not a new accounting
policy or permission to impute missing final entitlement terms.

## Previous 2026-09-18 preferred header is not preferred entitlement

For a nonfinal ordinary-A issuer notice, a preferred-stock code/abbreviation
in the identification header does not by itself make the **body** a preferred
distribution. Recheck original official PDF bytes and require that no
preferred entitlement terms occur after the company guarantee. A proposal
still needs explicit conditional language and no executable amount/dates;
a convertible-halt hint still needs a uniquely matched later final ordinary-A
implementation notice. The 601009 and 600919 documents meet these strict
source-scope tests. This is not permission to accept a preferred dividend
as an ordinary-A event.

## 2026-09-18 official correction fact scope

A secondary issuer correction may close an exact P1 source requirement
without creating another dividend only when its original and corrected
sections prove the economic per-share cash and accepted entitlement dates
unchanged, or explicitly identify a metadata/virtual-reference correction.
Match the original official PDF, issuer, publication timing and accepted
cash-event checksum; retain both source bytes and text-cache hashes. The
002457, 603087 and 601678 corrections satisfy these checks. A changed gross
cash or unresolved entitlement date still fails closed. This applies the
existing official-source substitution policy, not a new corporate-action
accounting method.

## 2026-09-18 bounded bonus component-integrality guard

The existing retained-bonus approval preserves basis but does not approve a
fractional-share convention. For the narrow `INTEGER_HOLDINGS_NO_FRACTION`
ledger, require each separately stated stock-dividend and capital-transfer
ratio to yield whole shares for any integer pre-event holding; an integral
*sum* is insufficient. Quarantine mixed-component cases unless official
evidence proves combined account-level allocation or the human approves a
research convention. This is a fail-closed audit rule, **not** a claim that
the registry actually allocated the components separately. The correction
supersedes ledger v28 and dependent P1 reports v6/v53 with v30/v7/v54;
old immutable evidence remains retained. The source ratio and 603023's
retrospective listing-date finding are unchanged. No paid data or new
economic event is asserted.

## Previous 2026-09-18 603023 listing-date conflict: retrospective audit only

For the exact 603023 2016-06-14/15 cash-plus-bonus source request, retain both
listing dates in the contemporaneous issuer implementation PDF (cover
2016-06-16, body 2016-04-16). Accept the issuer's separately published
2016-09-02 official half-year report (revised) as **retrospective corroboration**
that new unrestricted shares listed 2016-06-16. It repeats that date on PDF
pages 15, 21 and 61 and is bound to CNINFO issuer metadata, HTTP receipt and
PDF SHA-256. This closes only the exact P1 source fact after the already
accepted contemporaneous cash/bonus terms match exchange dates and master
identity. Do not use the September report as information available on the
June ex-date, infer individual fractional awards, generalize date repair to
other issuers, or claim full corporate-action census readiness.

## 2026-09-18 original designated-paper issuer disclosure as official evidence

For the exact 600337 2010 distribution, the issuer's signed 2011-06-08
implementation announcement in the original `《证券时报》` issue is official
issuer disclosure, not a third-party mirror or editorial summary: its earlier
CNINFO annual report names that paper as its designated disclosure outlet, and
the official SSE publication index matches security, title and day. Accept
the announcement's gross ordinary-A cash, record/ex, payment and holder
disbursement terms as an official-public-source substitution for the missing
direct SSE-hosted PDF. Preserve all three source hashes and retrieval times;
explicitly mark SSE PDF bytes unverified after bot denial. This closes one
source requirement only, creates no new dividend, and does not authorize
non-designated newspaper, mirror or retrospective-source substitution.

## 2026-09-18 convertible-bond halt hint is not final dividend authority

An official conversion-halt notice with a conditional per-share amount may
close a P1 source-document requirement as a nonfinal reference only if its
original PDF explicitly schedules a later ordinary-A final implementation
notice, and exactly one already accepted official issuer event has that exact
publication date and title before its record date. The two 601998 hints meet
this source-scope rule, but their indicative amounts differ from final issuer
amounts. Preserve both figures and source checksums; accept only the final
amount already present in the cash ledger. Do not create another dividend or
infer a bond-tradability event for the ordinary-A dataset.

## 2026-09-18 preliminary A/H schedule and PIT typo boundary

A dated A-share schedule in an official A/H preliminary notice is a nonfinal
reference, not a new dividend, only when its checksum-verified text explicitly
promises a later A-share implementation announcement and exactly one accepted
official issuer final notice for the same security and A-share record/ex dates
was published later but no later than record date. Do not use H-share dates or
derive a cash amount from the preliminary notice. Seven 601186/601390 notices
meet this existing source-scope rule. Conversely, the later SZSE yearbook and
annual report corroborating 301262's probable ex-date cannot retroactively
repair a malformed date in its contemporaneous final notice. Keep 301262 open
unless contemporaneous official correction/independent evidence is recovered.
This is fact-level classification, not a new research methodology approval.

## 2026-09-18 official secondary cash-leg and derivative-reference handling

For an already accepted ordinary-A primary cash event, a secondary official
implementation result or dated adjustment notice can close only the exact
cash fact it independently repeats: same security, gross cash per share,
record and ex-date, with checksum-bound PDF and point-in-time master identity.
A mixed notice's bonus leg remains source terms pending its own accounting
policy; no second economic event is created. A retrospective derivative
price-adjustment notice is a reference, not a dividend, only when its exact
official PDF states the accepted event completed on the accepted ex-date and
the cash amount and any stated record/ex dates match. The seven new closures
meet these source tests. Unmatched or incomplete notices remain open. This
applies the existing official-source substitution principle and does not
approve a new fractional bonus convention.

## 2026-09-18 bounded official date repair and source-acquisition boundary

For 300207 and 600801, accept the exact original CNINFO implementation PDF
plus a contemporaneous, SHA-verified official issuer supplement/correction
that explicitly replaces only the erroneous entitlement dates. For 000776
and 002050, remove ordinal page headers only when every PDF page starts with
its matching ordinal; this prevents a page number from joining a date split
across pages. For 000826, 300384 and 300852, accept an internally conflicting
issuer date only when the exact original PDF SHA also states independent
correct record/payment/application timing and one exact SZSE monthly row
corroborates security, dates and gross cash. Retain the conflicting text and
both source hashes in each closure receipt. Do not generalize these to other
issuer/exchange conflicts. Acquiring a PDF or finding a parser candidate is
not itself an accepted economic event; the 257 newly accessible P1 queue
remains under separate fact-level review. No paid source was used.

## 2026-09-18 source-pinned retained cash fact reconciliation

Extend the exact 000022 A/B-share conflict handling only to 000028, 000530,
000570 and 000581 after checking each original issuer PDF SHA, ordinary-A
gross CNY cash, B-share conversion rate, dates, matching SZSE monthly-row
SHA, three-decimal conversion and A-share pre-close/ex-price delta. Record
both conflicting values; do not globally reinterpret the exchange DPS field.
For a nonfinal accepted source, a separate final ordinary-A issuer PDF may
substitute only when its official metadata binds the exact event, it precedes
the record date, and preferred/B/H/convertible notices are excluded. The
601818 companion meets this rule. The 600378 original date typo is resolved
only with its SHA-verified official correction, which explicitly supplies
the 2015 record/ex dates and leaves other terms unchanged. When a PDF text
layer is unusable, existing source-bound PyMuPDF/OCR caches may supply
terms only if valid parses agree and the accepted amount, exchange authority
and exact entitlement dates still match. Retain each extraction checksum.
These are fact-level source substitutions, not new economic events or a
complete corporate-action census.

## 2026-09-18 explicit 000022 A/B cash-column conflict resolution

For the 2012-07-19/20 ordinary-A cash event of historical symbol 000022
(stable identity `CN-A:SZSE:001872`), the retained contemporaneous final CNINFO
issuer PDF explicitly states gross CNY 4.00 per 10 shares (CNY 0.40/share)
and the A-share dates. The official SZSE monthly table reports `0.491` in its
A-row DPS column, but its own pre-close/ex-price difference is CNY 0.400; the
issuer's B-share HKD conversion rate `0.8149` maps CNY 0.40 to HKD 0.491 at
the table's three-decimal precision. Treat this as an explicitly retained
official-source conflict, not a generic exchange-field override. Accept the
holder-class-specific issuer A cash only for this exact PDF SHA, point-in-time
code-transition receipt, date pair and exchange row/price/FX crosscheck.
Keep both reported values and source hashes in the closure receipt; no new
economic event is created and no broader cash-census authority follows.

## 2026-09-18 equivalent official issuer implementation source

Apply approved `OFFICIAL_PUBLIC_SOURCE_RECONSTRUCTION_V1` to the two bounded
bonus source gaps 603315 and 603889. The SSE-hosted PDF URLs remain denied,
but the already retained contemporaneous official CNINFO issuer notices state
the same one-for-one transfer ratio, record/ex-dates and scheduled new-share
listing. Accept them only with original PDF/text checksums, implementation-body
evidence, official exchange oracle agreement, point-in-time ordinary-A
identity and existing integer/next-session policy. This is fact-level official
source substitution, not a claim that the SSE URLs were retrieved or that the
full bonus census is complete. Ledger v20 manifest
`82fcdf1d558adfa1e81f6486ab74f73fcfdf920bfdf7a13c1cff6e615db603f0`.

## 2026-09-17 application of existing official cash source precedence

The already accepted fact-level official-source substitution rule applies to
the 23 bounded gross-cash precision discrepancies. A final, pre-record CNINFO
issuer implementation notice with SHA-verified original bytes, exact
record/ex-dates, and explicit ordinary-A gross holder terms supersedes a
rounded exchange-table cash cell for the **same** event. Twenty-one cases use
the same original issuer source as the previous event; two replace an SSE
table/CNINFO composite with the primary issuer notice. The old event checksum
is persisted in each supersession receipt. This changes no research policy,
does not add an event, and does not establish a full issuer cash census.

## 2026-09-16 official SZSE resumption evidence triage

Official CNINFO all-announcement metadata may be queried in bounded windows using
the verified issuer org ID. Duplicate/incomplete pagination is a failed window,
never an empty result; disjoint narrower queries may close it with independent
receipts. Document titles only prioritize retrieval. An official PDF/attachment
supplies a resumption boundary only when its text identifies one exact effective
date within the corresponding suspension lifecycle; source URL, receipt, SHA-256
and deterministic binding are retained. No inferred boundary from missing bars,
title alone, or future announcement order is allowed.

## Current: accept full official SSE/SZSE ST reconstruction only after closed gates

SSE acceptance requires the P0 identity set, official prestart anchor, complete
public title routing, terminal selected-document classifications, deterministic
official-event replay, and zero chain gaps, conflicts, unmapped events or UNKNOWN
states. SZSE acceptance requires the same P0 identity set, the official effective-
dated abbreviation-change export, independent corroboration for every prestart
member, deterministic daily replay, and zero chain gaps, lifecycle violations, IPO
conflicts, UNKNOWN states or future-event leakage. Undated current/display names
remain excluded from both effective-date authorities.

## Current: retained official PDF OCR is evidence recovery, never standalone authority

The autonomous completion mandate permits OCR only when the original official PDF
bytes and checksum-bound receipt are retained. `P1_CASH_PUBLIC_SUBSTITUTION_OCR_V1`
therefore admits a cash fact only when the official issuer identity, record date,
ex-date and gross ordinary-A cash term all exactly match independent official
exchange evidence. OCR errors, missing labels, invalid dates, printed source
conflicts and non-unique terms fail closed. The OCR engine, rendering version,
model checksums, source checksum and extraction checksum are persisted; no model
weights, PDF corpus or extraction cache is committed to Git.

## Current: use free official public reconstruction; no paid P0 purchase

Human decision `OFFICIAL_PUBLIC_SOURCE_RECONSTRUCTION_V1` is implemented. A
reproducible combination of official SSE/SZSE directories, termination records,
yearbooks and retained notices establishes the core point-in-time ordinary-A
master without claiming equivalence to a commercial export. Core identity,
membership, listing/delisting lifecycle, exchange, board and code intervals may
pass independently from cosmetic historical-name enrichment. Undated name order
never creates effective dates; ST and `*ST` remain separate effective-dated rule
facts. The commercial product was not used or purchased.

P1 is also a fact set. The accepted public-official master makes 757 CNINFO
documents non-applicable because their issuers are outside ordinary-A scope; four
yearbook requirements are directly established by the P0 evidence. This is scope
resolution, not an economic-term substitution. Therefore
`P1_RESOLVED_BY_OFFICIAL_SUBSTITUTION=0`. Only the 13,590 in-scope public CNINFO
documents are queued; source bytes remain document leads until parsed and
reconciled. No unofficial mirror or access-control bypass is allowed.

## Current: use official bulk products; do not perform thousands of manual downloads

P0 evidence must remain a complete effective-dated master export. SSEInfo's official
historical/basic-data business application is the accepted acquisition route for
SSE. CNINFO's official package 98 is the accepted candidate route for the SZSE
master because it exposes company/stock basic, name and listing-status histories;
free preview is evidence of availability, not authority completion. Full exports
require the human's account/business authority and may incur fees.

P1 uses five bulk collection families. CNINFO package 11 is the preferred bulk
route for 16,226 announcement documents because its documented daily/market/
`maxID` interface returns official PDF addresses. Seven exact archived PDFs are
reused with receipts; no redownload. No unofficial mirror, denial bypass, inferred
price, new tolerance or methodology change is permitted. This is a source-input
decision only; the accepted Pilot/R4 and all prior authority decisions are unchanged.

## Current: differentiated cash policy approved; source request compressed

Human decision `CN_A_DIFFERENTIATED_CASH_DISTRIBUTION_POLICY_V1` is implemented as
`DIFFERENTIATED_CASH_ORDINARY_PUBLIC_A_V1`. Only exact gross final implementation
cash for an ordinary exchange-traded public A-share holder is admitted. All 664
cached differentiated notices support one terminal public-A term; non-applicable,
ambiguous, missing-final and conflicting counts are zero. Cash ledger v14 supports
24,306 events, leaves 3,541 unresolved and retains 83 quarantines; canonical SHA
`91e9ff1d6f064eb5ca0bc3d1dd97fb3b041b74e112fe95d7b78c6d4766da289a`.

`SOURCE_INPUT_REQUIREMENTS_V2_MINIMAL` deduplicates 16,328 event requests to
16,312 official documents with complete back-references: P0=2, P1=16,304, P2=5,
P3=1. There are 16,311 material unique documents; 16,310 currently require user
copies or restored authorized access because one is already cached. The P3 item is
metadata-only and non-blocking. No 403 bypass, unofficial mirror or manual rename
is permitted. R5 stops under case 2: source input only; no human methodology gate,
full-dataset freeze, study or merge.

## R5 distribution row audit continuation

20,346 candidate groups, three retained B-only rows, no normalization errors.
Eight cash collisions reconciled to official issuer PDFs with exact gross
ordinary-holder amounts; full source-table precision is not accepted automatically.
Four holder-class differences and four combined-period distributions map to the
approved cash policy. Synthetic ex-price reference cash is not shareholder cash.
559 backend tests and quality checks PASS; prior aa372ac CI PASS.
R5 continues independent yearbook rights-census checks; no human gate or study.
Evidence: ../research/R5_FULL_RANGE_SOURCE_EXTENSION_V1.md.

## Current: R5 exchange distribution census; batch closure continues

All 192 official SZSE monthly tables retrieved: 23,682 source rows; all 74
rights candidates match the existing official event ledger, no source-only or
ledger-only entries. SSE eight cash collisions resolved to exact issuer terms.
These are source/census checks, not full cash precision or dataset acceptance.
CNINFO API probe is supplementary only: average cash fields and missing delisted
history cannot replace official issuer evidence. 561 backend tests and quality
checks PASS. See ../research/R5_EXCHANGE_DISTRIBUTION_CENSUS_V1.md.
R5 RUNNING_BATCH_CLOSURE; no new human gate, no dataset creation/audit/freeze.
Remaining independent source and accounting queues continue; no studies/merge.

## Prior milestone: R5 full-range source extension

Calendar: 3,886 target sessions verified. Official CSI300 close history aligns
exactly, matches all 382 accepted Pilot closes and passes deterministic Parquet
replay. Accepted Pilot and raw stock authorities are unchanged.
SSE distribution source tables collected: 17,920 dividend rows / 2,500 bonus
rows including B-only records; source rows are NOT accepted accounting events.
Exact rational merger flooring implemented without changing accepted event IDs.
558 backend / 78 frontend tests and quality checks PASS.
See ../research/R5_FULL_RANGE_SOURCE_EXTENSION_V1.md.
R5 remains RUNNING_BATCH_CLOSURE, no human gate or new methodology blocker.
Full dataset CREATED/AUDITED/FROZEN=NO; remaining source queues continue.

## Prior milestone: R5 rights batch reconciled

153 identified rights events / 142 securities now reconcile to official direct-subscription
notices; material unresolved in this identified queue = 0, metadata-only incomplete = 149.
Full exchange census remains PARTIAL. Source documents and code-transition candidates
are not full-dataset acceptance. 554 backend tests and quality checks PASS.
See ../research/R5_BATCH_SOURCE_CLOSURE_V1.md and
.research/reports/r5-batch-source-closure-v1.json. R5 remains RUNNING_BATCH_CLOSURE;
no human gate, no full dataset creation/audit/freeze, no studies, merge or release.

## Prior milestone: consolidation decision resolved

The approved 15-class policy catalog is frozen (not the dataset):
`CORPORATE_ACTION_POLICY_MATRIX_V1`, file SHA-256
`3784d6817fb7ab30081e57d9693bc1ac7adbfbaccebe200e2903e7021d8a0352`.
600381 consolidation June 25 and separate surrender June 30, 2014 have source-byte,
Decimal accounting, replay and persistence checks. Source receipt:
`dcfa8e2a408629a0be0b8ab9b101ab08206642eaaae621cc5412b94f96a93383`.
Its prior human methodology blocker is RESOLVED. R5 remains RUNNING_BATCH_CLOSURE;
no new human approval requested. Rights, merger/restructuring, master and remaining
full-period authority queues remain independent. Document leads are not accepted events.
Full Dataset CREATED/AUDITED/FROZEN=NO; safe start NOT_ESTABLISHED. No studies,
profitability inspection, merge or release. Accepted Pilot v2 remains unchanged.
The retained merger/capital-adjustment source worker checkpoints under external
`full-merger-v1/batch-v1`; unavailable sources cannot silently pass.

## Historical checkpoint (superseded): 600817 PASS; former 600381 gate

600817 approved net pass-through accounting/source/replay/persistence PASS; old blocker RESOLVED.
R5 reviewed21 further retained-queue plan documents and two600381 implementation/reference PDFs.
600381 ordinary100 ->16 share consolidation occurred2014-06-25, distinct from later12% surrender.
Historical aggregate basis treatment of the consolidation is not covered by accepted policies.
SINGLE_SMALLEST_BLOCKER=RESTRUCTURING_SHARE_CONSOLIDATION_BASIS_POLICY_UNAPPROVED:CN-A:SSE:600381.
HUMAN_APPROVAL_GATE=R5_RESTRUCTURING_SHARE_CONSOLIDATION_ACCOUNTING;
HUMAN_APPROVAL_REQUIRED=YES; HUMAN_SOURCE_INPUT_REQUIRED=NO.
544 backend/78 frontend tests; Ruff/format/mypy and migration checks PASS.
Full dataset CREATED/AUDITED/FROZEN=NO; safe start/full coverage NOT_ESTABLISHED.
No studies, profitability review, PR12 merge or release. No background worker.
Report: ../research/PASS_THROUGH_R5_CHECKPOINT.md. Resume preserved queues after decision.



## Current:600817 approved net pass-through PASS; R5 RUNNING

Human decision b42ec74db5f29f3a1434b96bdc04f9833dcb572a20198ee5b6fe69e3fe7293d6
approves CN_A_RESTRUCTURING_BONUS_PASS_THROUGH_POLICY_V1 /
NET_PASS_THROUGH_NO_BASIS_ALLOCATION. Five official PDF receipts verify25% bonus,
registration2012-07-31, transfer2012-08-01, unchanged originals and suspension.
Generic metadata-only accounting, persistence and raw-price separation checks PASS.
Old600817 methodology blocker RESOLVED; HUMAN_APPROVAL_REQUIRED=NO.
R5 resumes retained census/source queues; no prior acceptance is repeated or changed.
Full dataset CREATED/AUDITED/FROZEN=NO; safe start/full coverage NOT_ESTABLISHED.
No Development/Validation/OOS, profitability inspection, PR merge or release.
Evidence: ../research/RESTRUCTURING_PASS_THROUGH_V1.md.



## Current:600462 PASS; R5 new600817 pass-through methodology gate

600462 boundary and ceiling convention accepted/tested; original registry source
blocker RESOLVED. Historical timestamp/fraction facts remain NOT_PUBLICLY_EVIDENCED.
R5 resumed2010 merger leads and the preserved capital-adjustment queue.
600817 official notices establish temporary25% bonus credit then transfer to the
administrator, while original shares remain. Gross bonus/surrender versus net
issuer-level pass-through would allocate basis differently. Neither selected.
SINGLE_SMALLEST_BLOCKER=RESTRUCTURING_BONUS_PASS_THROUGH_BASIS_POLICY_UNAPPROVED:CN-A:SSE:600817.
HUMAN_APPROVAL_GATE=R5_RESTRUCTURING_BONUS_PASS_THROUGH_ACCOUNTING;
HUMAN_APPROVAL_REQUIRED=YES; HUMAN_SOURCE_INPUT_REQUIRED=NO.
528 backend tests/Ruff/format/mypy PASS. Full dataset CREATED/AUDITED/FROZEN=NO;
safe start/full coverage NOT_ESTABLISHED. No studies, profitability review or merge.
Report: ../research/600462_CONVENTION_R5_CHECKPOINT.md.
No background worker. Resume preserved queues after this new methodology decision.

## Current:600462 approved boundary/fraction convention PASS; R5 RUNNING

Human decision6f14546633e87d4a3dfec3564d92e03de07b6778b0636e4f86193994772f03b1
approves FIRST_POST_EVENT_TRADING_BOUNDARY_V1 and CEIL_SURRENDER_FLOOR_RETAINED_V1.
Historical registry date and official fraction rule remain NOT_PUBLICLY_EVIDENCED.
Research application before2012-11-19 resumed tradable Bar; no future-price input
to quantity/basis. Generic ceiling and zero-retained accounting/replay/persistence PASS.
600462 source blocker RESOLVED_BY_APPROVED_CONVENTION, not by fabricated historical facts.
18 source PDF receipts verified; flat-start2010 quantity lattice remains100*n before
surrender, so reachable fractional/positive-zero-retained cases0, economic bound0.
Edge stress Q1/6/101 separately tests ceiling; not historical strategy holdings.
528 backend tests/Ruff/format/mypy PASS. No schema migration needed for JSON audit extension.
HUMAN_APPROVAL_REQUIRED=NO; HUMAN_SOURCE_INPUT_REQUIRED=NO; STATUS=RUNNING.
Resume preserved R5 queues. Full dataset CREATED/AUDITED/FROZEN=NO; coverage/safe start
not established. No studies/profitability inspection/merge/release.
Review/lineage: ../research/600462_APPROVED_CONVENTION_REVIEW_V1.json.
Evidence manifest a4d49ac37c9bff57485be7087122707ad0e03b788cfc39d776e509fdb00fd83a.

## Latest registry recovery: trading boundary and aggregate totals verified

Official first post-event trading boundary2012-11-19 established; exact registry
book-entry/daily valuation mutation date remains unverified. Actual aggregate
share-capital reconciliation PASS/difference0; plan-to-actual gap28163 and
non-exhaustive exception arithmetic residual116 remain distinct.
Fractional rule NOT_EVIDENCED; generic Portfolio odd quantities reachable,
actual600462 historical reachability NOT_ESTABLISHED (round-lot-only subset safe).
16 official PDF receipts/checksums reverified;3 targeted PDFs added, no restart.
Report: ../research/600462_REGISTRY_RECOVERY.md; manifest
231c167a765e79673cdb5517ec95e4b7a27eecdc53c4451d7014fe63ae3e0aa2.
Original source blocker remains. No new methodology approval; human source input YES.
Approved accounting and all prior acceptance decisions unchanged; no formal studies/freeze/merge.

## Current: partial-surrender policy implemented;600462 source evidence unresolved

CN_A_MANDATORY_PARTIAL_SHARE_SURRENDER_POLICY_V1 APPROVED.
Generic exact-whole-quantity accounting/replay/persistence PASS; historical600462
admission PARTIAL. Ordinary nonexempt20% surrender and separate30% issuer issuance
verified; no direct holder compensation. Do not apply the issuance fractional rule.
Registry effective date and surrender-specific allocation remain unverified after
targeted plan/progress/court/annual-report review. No historical date is invented.
SINGLE_SMALLEST_BLOCKER=PARTIAL_SURRENDER_REGISTRY_EXECUTION_EVIDENCE_UNVERIFIED:CN-A:SSE:600462.
This is source recovery, NOT a repeated basis approval or established new fractional mechanism.
HUMAN_APPROVAL_GATE=NONE; HUMAN_APPROVAL_REQUIRED=NO; HUMAN_SOURCE_INPUT_REQUIRED=YES.
518 backend/78 frontend tests PASS; source replay/Ruff/mypy/schema checks PASS.
Prior Pilotv2/R4v2, rights/demerger/merger/source acceptances remain unchanged.
Full2010-2025 CREATED/AUDITED/FROZEN=NO; safe start/full coverage NOT_ESTABLISHED.
No formal studies, profitability inspection, PR12 merge or release.
Report: ../research/PARTIAL_SURRENDER_CHECKPOINT.md.
Resume preserved R5 source queues after registry evidence recovery; do not restart.
Next dataset gate remains GATE_FULL_RESEARCH_DATASET_FREEZE, not reached.

## Historical checkpoints below (superseded)

## 2026-09-13 UTC: new partial-surrender gate identified, no policy selected

R5 continued beyond zero-whole accounting. Full-period CNINFO merger-title query
completed95 pages/2849 announcements;69 implementation/listing document leads remain
separate from accepted events. Capital-adjustment query completed6 pages/175 notices.
These query inventories are not full corporate-action census acceptance.
Official600462 notice2012-71 confirms20% compulsory surrender for ordinary holders
outside four named holders and30% capital-reserve shares diverted to a bankruptcy
disposal account. Source review retains PDF/hash/date and both-page visual verification.
Approved merger full-successor-basis transfer and zero-successor loss do not select
basis treatment for partial surrender in the same security. No extension was inferred.
HUMAN_APPROVAL_GATE=R5_MANDATORY_PARTIAL_SHARE_SURRENDER_BASIS_POLICY.
This is a methodology choice, not another source-availability or rounding-policy request.
The notice's capital-reserve ex-date is not assumed to date the earlier surrender transfer.
No whole-security exclusion, full freeze, strategy study, PR merge or release authorized.

## 2026-09-13 UTC: zero-whole successor policy approved and verified

Human attachment SHA256 098914ab7b25587a5774c107cd9f335e0027831e2c4d073d3cf501522373892d
approves WRITE_OFF_PARENT_BASIS_AS_CORPORATE_ACTION_LOSS_V1 as an extension to
CN_A_MERGER_FRACTIONAL_SHARE_POLICY_V1. W=0 extinguishes parent with no successor,
pending asset or compensation; corporate-action realized PnL=-B, trading delta=0,
cash unchanged. W>0 retains full-basis transfer. Known official compensation never
falls through to this fallback; unimplemented compensation variants fail closed.
Separate corporate-action/trading/unrealized/total PnL persists with result lineage.
Dividend cash income is classified in corporate-action PnL without changing cash economics.
600005 source review and source-byte replay PASS; event SHA256
456fc000cf23e493384bb0857deeffde046a21977d0ce4c90454bed3e232aa30.
January16 last-trade year typo is superseded by January24 official confirmation.
February22 completion evidence is separately dated, not represented as known before February17.
Full inventory/account materiality remain unestablished; no strategy execution authorized.

## 2026-09-13 UTC: merger fractional-share V1 approved and implemented

Human receipt .research/approvals/merger-fractional-policy-v1.json pins the approval.
Retained000024 official notices reverified:1.6008, global remainder ranking/random ties,
December29 record and December30 conversion/listing. Research floor is not historical truth.
Generic immutable event and central Portfolio use exact Decimal floor, whole-share pending
claim, full basis transfer, unchanged cash/realizations/orders/fills and raw successor marks.
Remainders/CEIL uncertainty are audit-only; no new dependency or board-lot policy change.
000024 accounting/replay/source checks PASS; previous fractional-approval blocker RESOLVED.

R5 resumed existing inventory. Two official event reviews plus three source leads remain
a partial census.600005 official ratio0.56 gives zero credited shares for hypothetical Q=1;
positive B/0 is undefined. This is not an observed strategy position. No unapproved loss,
cash/share award, residual basis asset, exclusion or manipulated parent quantity selected.
Single new blocker:MERGER_ZERO_WHOLE_SHARES_BASIS_UNAPPROVED:CN-A:SSE:600005:2017-02-17.
Gate R5_MERGER_ZERO_WHOLE_SHARE_BASIS_POLICY; the approved floor method is not reopened.
Full-dataset materiality remains NOT_ESTABLISHED, never filled using synthetic fixture totals.
494 backend/78 frontend tests pass, with additive migration0007 and schema/source/type checks.
Prior authorities/frozen Pilotv2/R4v2/rights/demerger decisions unchanged. No full freeze,
formal studies, profitability inspection, PR12 merge, release or background worker.
Details: ../research/MERGER_POLICY_V1_CHECKPOINT.md.

## 2026-09-13 UTC: mandatory demerger policy V1 verified and implemented

Human receipt .research/approvals/mandatory-demerger-policy-v1.json pins the approval.
600003 ->601188+601518 uses official pre-listing references2.08/1.79, preserving
aggregate cost B and pending raw carrying value Q*3.87. No cash election, synthetic
order/fill, realized conversion PnL, factor history transfer or exclusion.
Pre-effective conversion evidence is separate from laterMar18 allocation evidence;
pending snapshots expose no future reference weights. Activation precedes trading.
Generic event/central Portfolio path; exact pending/basis persistence via additive migration.
600003 blocker RESOLVED; accounting/replay PASS; full census is not certified.

R5 continued targeted inventory against retained master and official notices.
000024 mandatory merger ratio1.6008 requires integer allocations using every
holder's remainder and random ties (final CMPD2015-177, PDF page5).
Single-account Q alone cannot recover that outcome. No rounding/monetization/
fractional-trading/exclusion convention was selected without approval.
New exact blocker: MERGER_FRACTIONAL_SHARE_POLICY_UNAPPROVED:CN-A:SZSE:000024:2015-12-30.
Gate R5_MERGER_FRACTIONAL_SHARE_POLICY, not a renewed rights/demerger approval.
484 backend/78 frontend tests and source/schema/lint/type checks PASS.
Frozen Pilotv2/rights V2/prior authorities unchanged; no full freeze, formal studies,
profitability review, PR12 merge or release. See ../research/DEMERGER_POLICY_V1_CHECKPOINT.md.

## 2026-09-12 UTC: human rights entitlement classification V2 implemented

Approval receipt: .research/approvals/rights-entitlement-classification-v2.json.
Standard direct subscription is separate from entitlement tradability; NOT_EVIDENCED
is not non-tradable and does not alone block no-subscription/no-monetization accounting.
000960 source structure/effective date reverified; former exact blocker RESOLVED.
Four standard complete events,144 material-source unresolved; census remains PARTIAL.
No incomplete provider row was promoted simply because policy changed.
Full-history safety review now stops on600003/2010-02-26 mandatory demerger:
successor cost allocation/intervening valuation convention not approved. No automatic
election, synthetic no-effect treatment or exclusion. Required human gate is
R5_DEMERGER_ACCOUNTING_POLICY, not rights tradability and not dataset freeze.
R4v2/Pilotv2 and prior authorities unchanged; no formal studies/merge/release.
See ../research/RIGHTS_ENTITLEMENT_V2_CHECKPOINT.md for evidence and test results.

## 2026-09-12 UTC: human rights-decline convention implemented; event scope remains fail-closed

Latest approval pins CN_A_RIGHTS_ISSUE_POLICY_V1 / DECLINE_SUBSCRIPTION. Preserve
the security and raw mark impact; no subscription, capital/cash reservation, added shares,
cost-basis transfer or compensation. Event data and participation remain separate.
Receipt: .research/approvals/rights-issue-policy-v1.json. Existing shared accounting
and deterministic pre-open ordering extended; no dependency or strategy change.
Engineering PASS resolves FULL_HISTORY_RIGHTS_ISSUE_TREATMENT_REQUIRES_HUMAN_DECISION.
Do not extrapolate the policy to unverified or materially different event types.
Source inventory148/137 is not a full census;2 supported,146 unresolved. The exact
earliest reviewed gap is000960/2010-01-27 entitlement non-transferability, not a new
choice to subscribe. Stop under user section8 pending source/classification resolution;
do not silently accept, omit or exclude it. No other source acceptance changed.
R4 v2 PASS explicitly has0 real-data fills; synthetic tests are fill-path evidence.
No full dataset, verified safe start, full freeze, formal study, merge or release.
See ../research/RIGHTS_ISSUE_POLICY_CHECKPOINT.md for all evidence and limitations.

## 2026-09-12 UTC: v2 frozen, fresh R4 passed, R5 rights policy decision required

Executed the latest human approval: exact v2 immutable freeze, unchanged strategy
full/reversed/prefix replay, persisted API/UI parity PASS. R4 v2 acceptance is new,
not reused v1 acceptance. V1 remains permanently frozen/superseded/INVALIDATED.
R5 resumed existing evidence: current BaoStock0.9.3 endpoint works,124 exited
security factor baselines present; no accepted Pilot authority replaced.
Official6000362010 rights issue proves dividend-query coverage is insufficient.
Existing RIGHTS_RELATED_EVENT policy is explicitly unsupported. Do not choose
subscription/forfeiture/cash funding or a new exclusion rule autonomously.
Stop for the single methodology decision documented in
`../research/PILOT_V2_FREEZE_R4_R5_CHECKPOINT.md`. This is not a v2 defect and not
the full-dataset freeze gate; no full dataset or research-safe start is certified.

## 2026-09-13: human approves exact revised Pilot v2 freeze and engineering continuation

GATE_A_REVISED_DATASET_FREEZE is APPROVED for manifest187b8c31...92600 only.
Approval receipt `.research/approvals/gate-a-pilot-v2.json` pins the unchanged
audited review and revision context. Final read-only verification must reproduce
all approved component hashes and25 R3 checks before the existing immutable writer
publishes separate v2 freeze metadata. Preserve v1 permanently, frozen/superseded
and acceptance INVALIDATED. No in-place v2 corrections after freeze; use v3/review.
Then rerun unchanged R4 on v2 only, labelled PILOT_ENGINEERING_SMOKE_ONLY,
including authorized v1/v2 engineering counts/equity/return diagnostics, no tuning.
On R4 PASS continue R5 targeting2010-2025 with genuinely historical authorities;
do not extrapolate Pilot rules/sources. Stop at full dataset freeze gate, unfrozen,
or a genuine blocker. Formal Development/Validation/OOS, merge/release remain locked.

## 2026-09-12: human approves revised Pilot rebuild, not freeze

Approval authorizes a full impact audit, corrected v2 materialization and fresh
R3 audit, with cryptographically qualified partition reuse. Preserve frozen v1
as superseded, research-acceptance INVALIDATED evidence. The next approval gate
is GATE_A_REVISED_DATASET_FREEZE; do not freeze v2, rerun R4, resume R5, merge,
release or run formal studies. R5 remains blocked pending revised Pilot acceptance.

Full four-board inventory additionally identified SSE A/B listing-date conflation:
STOCK_TYPE=2 must not supply A-share LIST_DATE even when A_STOCK_CODE is populated.
Use A-only types 1,8, with new source filenames. The new source corrects 600190
from 1998-05-19 to 1999-06-09. This is a lifecycle change, not a reusable v1
partition by default. Official SZSE notice 2025-027 preserves 300114 in Pilot;
302132 becomes effective 2025-02-17, never retrospectively. Evidence hashes and
effective-dated mapping are in `../research/PILOT_CODE_TRANSITIONS.json`.
These are source-backed engineering corrections, not changes to accepted
instrument/provider/execution methodology. Candidate census is not R3 acceptance.

## 2026-09-12: independent counterevidence after approved freeze

Gate A approval was executed only after exact read-only R3 identity/hash checks.
R4 engineering passed without tuning or optimistic fills. During R5, the official
STAR exit census independently proved three securities omitted before Pilot
publication. The original byte-equality audit did not certify a complete universe.
Withdraw current master/readiness acceptance; preserve v1 frozen bytes and all
historical receipts. Do not transfer Gate A approval to a corrected version/hash.
Pause for revised dataset review. This is an engineering evidence disposition,
NOT a newly granted human approval and NOT a new conservative scope exclusion.
Fix the common source-query cause, preserve old source filenames, retain targeted
repair probes. A v2 still needs source closure and full audit before freeze review.
Full research acceptance remains unestablished and all formal studies locked.
Evidence: `../research/PILOT_FREEZE_R4_R5_CHECKPOINT.md`.

## Human Gate A approval and revised stage scope

2026-09-12: Human explicitly approved freezing the exact audited Pilot manifest
0696a5c7454f044a3f0ea8886b1c08fbe2228b19598894ddb44ac54498978490.
Approval receipt: `.research/approvals/gate-a-pilot-v1.json`. Verify unchanged
R3 evidence and all partition hashes read-only before writing a separate immutable
freeze record. Unknown executable liquidity remains NO FILL. Future corrections
require another dataset version/hash; never overwrite Pilot v1.
After freeze, R4 is PILOT_ENGINEERING_SMOKE_ONLY, not formal Development, despite
overlap with intended future OOS dates. No economic parameter changes are authorized.
Then R5 builds/audits a full 2010-2025 dataset, subject to actual source coverage.
Next approval gate is GATE_FULL_RESEARCH_DATASET_FREEZE. Formal Development,
Validation, Official OOS, live/ML/GPU, merge/release/publicity remain unauthorized.

## Gate A checkpoint: approved scope applied; no freeze decision made

2026-09-12 UTC: existing ordinary-A-share decision implemented across the full
5178-member candidate master:5177 COMMON_A_SHARE,1 CDR,0 unclassified.
No additional methodology/provider/tolerance/performance decision was introduced.
Existing valid2580 partitions preserved; remaining2597 ordinary securities recovered
under frozen failover policy. R2 atomic catalog published; real full R3 all22 checks
PASS. READY/AUDITED YES, FROZEN NO. STOP at GATE_A_DATASET_FREEZE; approval required.
This records an observed engineering outcome, not human dataset-freeze approval.
Unknown official daily suspension/tradeability remains null/no-fill under the
already approved execution convention; audit PASS does not promote unknown facts
to tradeable states. No studies, OOS, PR merge or release authorized/performed.
Detailed evidence: [R2/R3 report](../research/R2_R3_ORDINARY_A_SHARE_REPORT.md).

## Approved human methodology decision: ordinary A-share equities only

2026-09-12: PILOT_INSTRUMENT_SCOPE=ORDINARY_A_SHARE_EQUITIES_ONLY;
PILOT_INSTRUMENT_SCOPE_DECISION=APPROVED. Scope decision blocker is resolved;
STATUS=RUNNING, HUMAN_APPROVAL_REQUIRED=NO while applying the approved policy.
Ordinary RMB equities on Main/STAR/ChiNext remain potentially eligible. CDR,
B-share, ETF/fund, bond/convertible, preferred, warrant and other instruments
are outside this release before data completeness is evaluated. No results or
profitability inform this decision. Source-backed classification and generic
eligibility must precede denominator correction; unknown types stay explicit.
689009's preserved SSE CDR listing evidence establishes its out-of-scope type;
its absent Sina factor is not required by the approved Pilot scope. Existing
source/checkpoint artifacts must be retained, not rewritten to hide earlier counts.
Continue existing R2 then R3; no freeze, study, OOS, PR merge or release authorized.


## Current: instrument-scope decision required

R2 BLOCKED; SINGLE_SMALLEST_BLOCKER=PILOT_INSTRUMENT_SCOPE_REQUIRES_HUMAN_DECISION.
The pre-blocker97eebf3 contract names CN_A and four boards but does not establish
ordinary-equities-only versus CDR-inclusive scope. Official SSE notice confirms
689009 is a CDR, listed2020-10-29; this fact alone does not authorize exclusion.
Full5178-row type-evidence inventory:1 confirmed CDR,5177 UNCLASSIFIED (not assumed
ordinary, not excluded). No other nonordinary instrument was positively established;
this is NOT a complete certified instrument census or zero-leakage PASS.
New sourced InstrumentClassification model is independent of eligibility. No filter,
master checksum, scope, strategy, factor baseline or frozen failover policy changed.
All657 primary/1923 secondary successes and2580 partitions/951927 raw rows unchanged.
The prior689009 empty-factor evidence remains unresolved if CDR is included.
Human must specify ordinary A-share-only versus CDR-inclusive Pilot scope before
classification/eligibility changes and R2 resume. Worker remains stopped.407 tests
and lint/type checks passed. No dataset publication, R3 PASS, freeze, study or merge.
Evidence:docs/research/R2_INSTRUMENT_SCOPE_AUDIT.md. HUMAN_APPROVAL_REQUIRED=YES;
this is not Gate A. Earlier master authority PASS does not certify instrument scope.

## Earlier checkpoints (superseded)



## Current: R2 factor availability blocker

R2 BLOCKED; HUMAN_APPROVAL_REQUIRED=YES; HUMAN_APPROVAL_GATE=NONE (not Gate A).
SINGLE_SMALLEST_BLOCKER=SINA_FACTOR_BASELINE_UNAVAILABLE_689009.
Accepted Sina HFQ URL returned HTTP200 with total=0/data=[] for689009.
No baseline can be inferred; no approved substitute/exclusion applies. No retry
of a non-transport failure, fabricated factor1 or third provider was introduced.
657 primary +1923 secondary complete inputs preserved;2580 securities partitioned,
951927 raw rows /6250 factor rows. One factor failure,2597 unattempted;2598 unresolved.
Worker stopped safely at a complete batch for human source resolution; no background
worker remains. Resume this checkpoint after resolving689009, never from zero.
All accepted R1 authorities and Tencent LIMITED_PRECISION_PARITY remain intact.
Entire available amount sample:17068 potential decisions,zero ambiguous (includes
7 separately audited decisions from689009's saved382 raw rows). Dataset unpublished,
unaudited,unfrozen; no studies,merge or release.406 tests/lint/type checks passed.
Full source/error/checksum evidence:docs/research/R2_SINA_FACTOR_COVERAGE_BLOCKER.md.

## Earlier checkpoints (superseded)


## Current decision-invariance acceptance

R2 RUNNING; HUMAN_APPROVAL_REQUIRED = NO. Prior amount-semantics stop RESOLVED
under the new human-authorized decision-invariance criterion, not guessed rounding.
Tencent upstream unit=10,000 CNY; AKShare returned unit=CNY; nominal granularity100 CNY.
659 available securities/244,772 rows,4,334 potentially evaluated amount decisions,
zero ambiguous decisions. All-date600666/2024-01-19 stress ambiguity is retained,
not hidden: already ST-excluded and not a scheduled evaluation date.
Expanded2,478-row overlap has no OHLC/date mismatch or outside-envelope amount outlier.
SECONDARY_ACCEPTANCE = PASS_FOR_PILOT; LIMITED_PRECISION_PARITY, not exact tick parity.
CN_A_RAW_OHLCV_FAILOVER_V1 frozen SHA256
3fb1941b93f127774ec228d27bb78074d48dc2d35ee29e98826a3b207472f740.
Impact audit SHA256=d950fdc3543fbf8373370c8013f8a8a8579140e8b82523f7d0961033a280323c.
Every recovered partition must pass the same unchanged rule/interval check before
admission. Preserve657 primary successes; resume4,521 pending, no primary refetch.
No new exclusion, dataset freeze, study, merge or release. All R1 authorities intact.
Full trace/evidence:docs/research/PILOT_AMOUNT_DECISION_IMPACT.md.

## Earlier checkpoints (superseded)


- Latest human continuation authorized focused amount acceptance, not tolerance
  widening or automatic Tencent promotion. Controller resumed RUNNING for review.
  Existing strategy code establishes amount REQUIRED for20-observation liquidity
  screening despite nullable provider schema. Audit reused1,719 rows and preserved
  every snapshot; unit mapping verified, rounding/error bound still undocumented.
  Terminal classification INSUFFICIENT_EVIDENCE, SECONDARY_ACCEPTANCE FAIL; stop
  BLOCKED on RAW_SECONDARY_AMOUNT_PRECISION_AUTHORITY_UNRESOLVED, not Gate A.
  No methodology change, new provider, primary retry, freeze, study or merge.
  Details and reproducible metrics: docs/research/TENCENT_AMOUNT_ACCEPTANCE.md.


- Failover candidate review completed: six additional primary diagnostics failed
  before HTTP; classify operationally SYSTEMIC_TRANSPORT_FAILURE without
  downgrading primary historical authority. Tencent returned eight repeatable
  histories and matched 1,719 primary dates/OHLC; four amount differences remain
  unresolved after reuse of Sina snapshots plus one targeted raw request.
  CN_A_RAW_OHLCV_FAILOVER_V1 stays disabled; no secondary promotion, production
  failover, bulk retry or new exclusion. Stop only for the remaining narrow
  amount-precision evidence/policy decision, preserving all 657 original inputs.

- Current human failover authorization: resume R2 RUNNING for a bounded six-member
  primary operational diagnostic and independent secondary-route acceptance.
  Preserve primary historical authority and all 657 successful partitions. No
  bulk primary retry or automatic provider substitution. Version the selection
  policy; secondary use requires independent authority and cross-source parity.
  Prior exhausted-run stop is superseded only within this new diagnostic scope.
  Dataset publication/freeze, studies and PR merge remain prohibited until gates.

- 2026-09-11 bounded R2 recovery completed: all 5,178 members accounted for;
  657 RECOVERED_PRIMARY and 4,521 UNRESOLVED_REQUIRED_DATA after all three rounds.
  The final pass recovered 600605 and 600739; it did not resolve 600070, whose five
  actual requests are exhausted. All terminal failures are RemoteDisconnected,
  cause UNKNOWN. Existing policy permits neither fallback nor transport-gap
  exclusion. Stop BLOCKED for source-access/policy resolution, not Gate A; retain
  all partial partitions and evidence. No further retry, R1 reopening, incomplete
  publication, dataset freeze, study or PR merge is authorized.

- 2026-09-11 R2 recovery continuation: user explicitly directs successful
  securities to continue while failures queue as PENDING_RETRY. No R1 reopening,
  new provider, new exclusion, synthetic data, freeze or research. Source snapshots
  and failed-attempt metadata are immutable; final publication requires complete
  required inputs. Existing OHLCV acceptance defines no fallback. Final failed
  members must remain UNRESOLVED_REQUIRED_DATA unless actual recovery or existing
  authoritative policy explains them. Request controls and transport diagnostics
  do not justify guessing an anti-bot or lifecycle cause.

- 2026-09-11 implementation checkpoint: both source authority and separate
  CN_A_DAILY_OPENING_LIMIT_V1 validation PASS. Approval section9 permits retained
  frozen research costs: the unchanged 0.00001 transfer/clearing allowance is
  explicitly SIMULATION_ASSUMPTION, not a verified statutory rate. Its unresolved
  old source claim remains preserved in model_assumptions; no data authority
  was re-audited or weakened. R2 started with the accepted 5,178-member master.
  Stop at new external blocker R2_RAW_ROUTE_CONNECTION_CLOSED_600070 after three
  bounded transport failures. No substitution, security omission or incomplete
  dataset publication. Resume only after source access recovery/authorized route.

- 2026-09-11 human execution approval: PILOT_EXECUTION_CONVENTION_DECISION =
  APPROVED. Resume RUNNING without another execution-methodology approval.
  CN_A_DAILY_OPENING_LIMIT_V1 is a SIMULATION_ASSUMPTION, not an official exchange
  rule or proof of actual auction fills. Precommit parameters using completed t
  only; evaluate t+1 eligibility separately; raw open may price a fill only after
  conservative legal/status/liquidity-proxy gates pass. Missing/uncertain evidence
  means no-fill and explicit expiry. No future inputs may set order parameters.
  Source authority and execution-convention validation are separate gates; both
  must pass before R2. Dataset freeze and all studies remain unauthorized.

- 2026-09-11 source-recovery decision supersedes the original-PDF requirement.
  Historical locations return 404 in automated and user normal-browser access;
  classify them SOURCE_LOCATION_RETIRED_OR_UNAVAILABLE, never SOURCE_CONTENT_INVALID.
  Exact retired URLs are in docs/research/SZSE_RULE_CLAIMS.json. No retry this run.
  Accept reproducible rule-level evidence from accessible official SZSE materials;
  do not use mirrors or fabricate downloads. All four alternatives downloaded.
  Technical PDF p18 proves 2023-04-10 implementation; later notice proves publication
  2023-02-17 / 深证上〔2023〕98号 and 2026-07-06 supersession. It supplies identity,
  never 2026 behavior. Investor guidance retains its proper source classification.
  Preserve snapshots outside Git and per-source hashes/claim mapping inside Git.

- 2026-09-11 semantic review: source recovery exposed an execution-methodology
  mismatch, not just missing source bytes. Existing MARKET-at-next-open is not an
  exchange MARKET submission at opening auction. Ask for explicit limit/auction
  convention decision before materially changing that assumption. No decision has
  yet been received. Do not infer auction liquidity from daily OHLCV. No studies.
  Rule .5 corrects only preceding-regime identity/IPO classification; existing
  first-session no-fill preserved. A 2015 yearbook under a 2023 URL is rejected for
  Pilot fees; 0.0003 commission is a model assumption, not statutory rate. The
  0.00001 transfer-fee claim remains open, not fabricated or silently zeroed.

- 2026-09-11 user source resolution: intended SZSE source is the 2023 revision,
  publication 2023-02-17, 深证上〔2023〕98号, effective 2023-04-10, not publication
  day. The supplied April 10/11 official listing pages were retrieved and agree.
  Source identity is resolved. Fresh requests to the supplied notice and both
  PDF routes still returned 404; PDF bytes/hash remain unavailable. Do not
  promote MARKET_RULE merely from the user's link identification. Version .4
  and transition tests are complete; request file attachment to finish provenance.

- 2026-09-11: Docker runtime failure RESOLVED; existing volumes/containers
  preserved, API/frontend and database services verified. No accepted data
  authority was reaudited. Delisting fix .3 passes regression; MARKET_RULE remains
  PARTIAL because official SZSE 2023 source text could not be recovered. Do not
  substitute current rules or promote source acceptance from code tests alone.

- 2026-09-11: The previously specified GitHub identity 'MackenzieAhern' was a
  prompt typo. The intended and authenticated repository identity is
  'MakenzieAhern'. Existing Git configuration and attribution remain unchanged.
  PUSH_IDENTITY_MISMATCH = RESOLVED. Resume R1 without further identity approval.

- 2026-09-10 checkpoint: OHLCV/CSI300 route binding passes; market-rule acceptance
  remains UNVERIFIED. Do not begin R2 with unresolved delisting-period semantics.
  Pause publication for the explicit MackenzieAhern/MakenzieAhern spelling
  mismatch; preserve existing Git identity. This is not Gate A.

- 2026-09-10 acceptance: Sina factor route passes under
  `sina-multiplicative-asof-v1`: P(t)*H(t)/H(T), t<=T, pinned vintage, raw execution.
  Seven route gates pass; no claim of archived publication-time observations or
  full-universe availability. Continue R1 without another provider-choice prompt.

- 2026-09-10 approval: Sina adjustment-factor data is approved as a candidate
  acceptance route for the v1.1 A-share Pilot. It becomes authoritative only after
  reproducibility, semantic, temporal-safety and lineage validation passes.
  Legacy BaoStock acceptance recovery is no longer a prerequisite. No dataset
  freeze, Development, Validation or Official OOS is authorized by this decision.

- 2026-09-10: Continue on existing branch/PR. No scheduler, new branch or conversation.
- Preserve accepted SSE/SZSE/master/calendar work. Ancient 600721 is full-history-only.
- A legacy PASS claim is not checksum-linked pilot authority acceptance.
- Execution always uses raw prices. Provider adjusted close is not an economic cash flow.
- Persist Gates A/B/C and false OOS/release flags. Current research CLI already refuses
  execution without readiness; state files do not grant permission to bypass it.
- Keep generated evidence outside Git; commit small reproducible code and summaries only.
- 2026-09-10 R1: New Sina factors are CANDIDATE_ONLY, not an implicit provider
  substitution. Different adjusted-price algorithms are not treated as corrupt
  data or interchangeable factors. Stop under the explicit authority-ambiguity
  exception while preserving all new recovery evidence; no normal gate reached.
