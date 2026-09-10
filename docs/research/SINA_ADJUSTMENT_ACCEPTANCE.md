# Sina adjustment candidate acceptance

Convention: `sina-multiplicative-asof-v1`. This freezes the factor convention,
NOT the Pilot Dataset, strategy, methodology freeze or OOS authorization.

## Bound interface and lineage

AKShare 1.18.94, `stock_zh_a_daily(adjust="hfq-factor"/"qfq-factor")`, backed by
Sina `https://finance.sina.com.cn/realstock/company/{symbol}/{hfq|qfq}.js`.
Symbols retain sh/sz prefixes. These factor requests do not honor start/end:
the complete dated factor response is normalized before explicit as-of filtering.
Schema is a JavaScript assignment containing JSON `{total, data:[{d,f}]}`;
`d` is ISO effective date, `f` a positive decimal string. No remote eval is used.
Source timestamps/checksums reside in per-response metadata outside Git.
Parser version: `sina-multiplicative-asof-v1`.

## Financial definition

Let H(t) be the last HFQ factor dated at or before t, Q(t) the analogous QFQ
factor and P(t) raw close. Empirical comparisons and the pinned SDK implementation
support HFQ=P*H and QFQ=P/Q, each rounded to cents for SDK display. H(t)*Q(t)
equals the latest HFQ base within source decimal precision. HFQ's initial base
is 1 where the source supplies that initial row; never invent a missing baseline.
QFQ changes its historical base as later actions arrive. It is diagnostic only.
These multiplicative factors are not interchangeable with Eastmoney HFQ prices.

For cash c and bonus/capital-reserve shares b per old share, the tested event
multiplier is H(after)/H(before)=P(previous)*(1+b)/(P(previous)-c).
Factors remove theoretical ex-right gaps; they are not actual cash flows, tax
records, payment dates, rights subscriptions or a complete corporate-action ledger.
No standalone split, consolidation or rights event was independently validated.
Unsupported economic actions remain unsupported, not silently normalized away.

## Frozen temporal convention

Only research features may use A(t;T)=P(t)*H(t)/H(T), with t<=T and T the decision
date, from a checksum-pinned vintage. Never use the latest provider QFQ base.
Execution/valuation quotes always remain raw. Appending future-effective factors
cannot change A(t;T); a uniform rescaling of all eligible H values cancels exactly.
Automated checks exercise both properties. The implementation refuses missing
baselines, future observations, invalid dates and nonpositive/nonfinite values.

[AKShare's documented distinction](https://akshare.akfamily.xyz/data/stock/stock.html)
is retrospective QFQ rebasing versus HFQ preserving past values as ordinary
actions occur. This is not a guarantee against vendor corrections: historical
nonuniform revisions remain UNKNOWN. This acceptance does not claim that the
2026 snapshot was published or available in 2023. The allowed methodology is
explicitly frozen-vintage effective-state research, not an archival knowledge-time
dataset. Revised historical values require a new data version and renewed audit;
never silently refresh a frozen vintage. Absolute adjusted levels must not become
cross-security signals or execution prices without a separately reviewed method.

## Empirical evidence

Two exact requests per mode for five securities; four boards. Four ordinary
action windows supply 21 matched RAW/QFQ/HFQ dates, all within half-cent display
rounding. Decimal implied ex-right references agree with declared actions within
1e-8 currency units (source precision, not a performance-derived threshold).

| Symbol / role | Effective date | Cash per old share | New shares per old share |
| --- | --- | ---: | ---: |
| sh600000 / SSE main | 2023-07-21 | 0.32 | 0 |
| sz000001 / SZSE main | 2023-06-14 | 0.285 | 0 |
| sh688008 / STAR | 2023-08-11 | 0.30 | 0 |
| sz300750 / ChiNext | 2023-04-26 | 2.52 | 0.8 |
| sz000732 / ST-history control | No returned pilot factor transition | Not inferred | Not inferred |

Action terms were checked against issuer announcements: [浦发银行](https://news.spdb.com.cn/investor_relation/company_report/202307/P020230712640521382645.pdf),
[平安银行](https://epaper.stcn.com/con/202306/07/content_2491471.html),
[澜起科技](https://epaper.stcn.com/con/202311/29/content_2560165.html),
[宁德时代](https://vip.stock.finance.sina.com.cn/corp/view/vCB_AllBulletinDetail.php?id=9009077).
The latter three are issuer disclosures reproduced by financial disclosure media.
The SPDB PDF's relevant page was visually inspected. The attempted SSE PDF
returned HTML and was not used as evidence.

The ST control's ancillary outstanding-share endpoint returns null, so the full
SDK price wrapper fails. Its original Sina history decodes to six identical raw
rows in both snapshots. This is not missing raw price data; no auxiliary share
counts or SDK-adjusted outputs were fabricated. The control tests factor stability,
not independent absence of all economic actions or full delisted-universe coverage.

Artifacts: external staging `sina-acceptance-20260910/`; raw HTTP bodies, metadata,
factor snapshots, normalized factors, issuer evidence, exact sample contract,
SDK outputs/failures and price-comparison audit. No market files enter Git.
Run offline: `python -m scripts.sina_adjustment_audit --root /path/to/snapshots`.
Its sample-math report alone deliberately does not promote source authority;
the final acceptance manifest records the separately reviewed convention and scope.

Full-universe factor availability, suspension classification and market-data audits
still belong to subsequent preflight/materialization checks. Missing securities
or dates must not be replaced by factor=1, current listings, synthetic bars or
unexplained exclusions. This route does not establish overall Pilot readiness.
