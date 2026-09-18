# Autonomous Quant Project Checkpoint

## 2026-09-19 002075 original SZSE suspension/restoration notices

Two original `证券时报` page PDFs carry SZSE-signed notices establishing
002075's 2010-05-07 suspension and 2011-04-08 restoration. Their PDF
bytes, UTC receipts, SHA-256 and publication dates are bound in the v5
report; pages were visually checked. Exactly 216 002075 absent daily rows
are reclassified within that interval, conserving all 15,655 rows and
leaving only 239 dates across 239 ChiNext securities on 2011-07-25.
File SHA-256 `e34597c37fcfea2bfc193d165a40a8f56537b9bf247f809f8317ddbe6f3ac09d`,
manifest `36120ebb15c625e936bd77b8584230f7dc9c5d885af3a848ead5281c7e6f3127`.
Byte-identical replay, focused test and lint pass. No mass halt, bar,
raw/execution authority, Full Dataset, freeze, study or PR merge is inferred.
The official SZSE 2011 statistical yearbook was separately archived and
visually checked at PDF page 165: 2011-07-25 had 48.48 ten-thousand
ChiNext deals. PDF SHA-256
`38289a861878de122015747d09ca3dc1f7e05de127c572ae2ac4792206460bd4`.
This confirms a daily-export omission, not per-security prices or fills.

## 2026-09-19 000732 original issuer-notice interval

An original issuer-signed designated-paper notice, its unique official
CNINFO index entry and a SZSE-hosted issuer designation PDF were archived
with UTC receipts and SHA-256. The issuer notice was visually checked.
The corrected-v4 overlay reclassifies exactly 177 000732 absent daily rows
inside the 2007-05-11 to 2010-09-30 suspended-listing interval, conserves
all 15,655 source-absent rows, and leaves 455 dates across 240 symbols
unresolved. Report file SHA-256
`85d19024f2781cdaa50a766ebbe1e6302938830005ec088a9b798dd22dc07a44`,
manifest `4b0b729fba816ece90a3a8c8f2c0fbc3e836530435fb936c1533773963b56826`.
Byte-identical replay, focused test and lint pass. Original CNINFO PDF bytes
were not obtained; retrospective source-presence evidence is not a 2007
signal or raw/execution authority. Full Dataset, freeze, study and PR merge
were not promoted.

## 2026-09-19 000156 official retrospective interval

The SZSE-hosted issuer report was archived with a UTC receipt and SHA-256,
then visually checked at its 2006-04-13 suspension and 2012-10-19
restoration passages. The corrected-v3 overlay reclassifies exactly 665
000156 no-row dates, conserves all 15,655 absent active-master rows,
and leaves 632 unresolved dates across 241 symbols. File SHA-256
`c0612a6f95e0726c16caa42217a7e563eda876fd273f40c1b3f8de7f8d53fc8a`,
manifest `9fe0011dc16b7ac285eae3e6bc70c315bc6b079bedfa5987059d277ff65cfbca`.
Byte-identical replay, lint and 763 backend tests pass. The report
remains source-presence only; no raw/execution authority or Full Dataset
gate was promoted. The prior corrected-v2 report remains immutable.

## 2026-09-19 non-destructive Docker recovery

After two stale Unix-socket failures, Docker was stopped, the zero-byte
socket-only `Docker/run` and `docker-secrets-engine` runtime folders were
preserved as timestamped siblings, and Docker Desktop was restarted.
Ubuntu integration, Engine 29.7.2 and Compose v5.5.0 respond. The existing
PostgreSQL/Redis/backend/frontend stack started without rebuilding or
removing volumes; database readiness, Redis PONG, backend health,
`/api/health` HTTP 200 and frontend HTTP 200 passed. Final release
rebuild and restart-durability checks are not yet claimed.

## 2026-09-19 corrected SZSE source-presence replay

A regression test caught slash-formatted `resumed_at` values incorrectly
compared to ISO dates. A complete SHA-checked replay of 3,886 cached
official SZSE daily XLSX files corrected the 15,655-row classification:
227 bounded dated halts, 145 delisting boundaries, 11,448 no matching
halt and 3,835 unknown-resumption rows before official interval overlay.
Corrected base file SHA-256
`45bd345c122d9ced5807be65ae427b61b6ef6fe63a6c9f1e7da2719126596aca`.
The 24 prior PDF-verified intervals were re-applied with strict date
bounds and conservation checks, leaving **1,297** unresolved dates across
**242** symbols; overlay file SHA-256
`23038aa4068abddaf475ba027c3afa78e0a0bd4e1424337f3ee045eea1f3982b`,
manifest `78634cdb2e076e0938f60ea130eaf0848fe7c67863c5cb0de3f20b57d64898bf`.
The old v1–v7 row-gap counts are superseded, not acceptance evidence.
Focused tests, lint and byte-identical overlay replay pass. Three
multi-day official PDF leads are not accepted without archived bytes;
targeted retrieval hit DNS and HTTP 403 bot denial. No raw/execution
authority, Full Dataset, freeze, study or PR merge was promoted.

## 2026-09-19 three terminal-listing source-presence closures

Issuer CNINFO originals, visually checked and receipt/SHA-bound, explain
**363** more SZSE no-row dates for 000805, 000787 and 000594. The v7
overlay conserves all 15,655 dates and leaves **153** unresolved across
**34** symbols (48 unknown resumption; 105 no matching halt source).
File SHA-256 `b44fe8de96244136055a090c03f71644aed226b0c23f99643af1873b05d7ec89`,
manifest `e4da16bfa9d8ac2be3264bcfc6c9588be46c073662b441c37fa4c7cac62f11af`.
Focused test, lint and byte-identical replay pass. Additional official
leads for 000156, 002075 and 000732 were not promoted: the first 000156
PDF hit bounded transient-DNS retries and the others were not fetched.
One Windows-side targeted retry also failed DNS resolution.
No exact execution/raw authority, Full
Dataset, freeze, study or PR merge was promoted.

## 2026-09-19 five 2010-plus official source-presence closures

Five targeted CNINFO issuer/sponsor PDFs, visually checked at their
suspension and actual first-trading passages, explain **505** more SZSE
daily source-absence dates. The v6 SHA-verified overlay conserves the
15,655-row total and leaves **516** unresolved dates across **37** symbols
(85 unknown resumption; 431 no matching halt source). File SHA-256
`e450c15f1ff3f3ddbc193106450f51b32bacb3975c0237633dc35b0984ef1b81`,
manifest `0ea44f9ed6fbe484cce9327f41470ddc551a24cd636baa04c0bc5fa0ccc2ce68`.
Focused test, lint and byte-identical replay pass. No exact execution/raw
authority, Full Dataset, freeze, study or PR merge was promoted.

## 2026-09-19 six-security official source-presence closure

Six more CNINFO issuer/sponsor disclosures establish actual pause and first
trading dates. The v5 SHA-verified overlay closes 1,012 source-absence
dates, preserving the 15,655-row total and distinguishing 323 post-2009
listing-suspension dates from 3,560 pre-2010 ones. **1,021** dates across
**42** symbols remain unexplained. File SHA-256
`8b286641b05ab550b1e25b154b2f179d181c10c2718532435addee588dcbaea2`,
manifest `e9b6c6b0eee99535d6c012f07cbd12ddf155b2876c1f3a16f734706a4c6ee07f`.
Focused test, lint and deterministic replay pass. No exact execution/raw
authority, Full Dataset, freeze, study or PR merge was promoted.

## 2026-09-19 three-security official source-presence closure

Official CNINFO disclosures bound 000038, 000670 and 000719 from their
pre-2010 suspended-listing starts to actual first trading dates. The v4
SHA-verified overlay closes only their 683 previously unexplained no-row
dates; it conserves the 15,655-row total and leaves 2,033 unresolved dates
across 48 symbols. File SHA-256
`86905153277c0ca28ef26347fd86ca702a814e1d9664317d1357fe236cb5b847`,
manifest `d60480a6ac37bdeda7e1630eb16f15ddb2e5a43b3b9ec24b0c834827bc07cb0b`.
Exact execution authority remains partial, especially where shorter halt
feed events overlap a long suspended-listing interval. Focused test, lint
and deterministic replay pass. No Full Dataset, freeze, study or PR merge.

## 2026-09-19 six-security official pre-2010 interval batch

Six targeted CNINFO issuer PDFs, visually checked at the pause and first-
trading-day passages, close 1,727 further missing SZSE daily rows. The
checksum-bound v3 overlay conserves the 15,655-row total and leaves 2,716
unresolved dates across 51 securities (913 unknown resumption; 1,803 no
matching halt source). File SHA-256
`9f42a73d16e70d9665fd9966718c93a131aa0789cc81a7ad4d259a478232c1b1`,
manifest `0c456a64a54131b49b7a2d38c132b3d75a08832a9364d3793e4ccc5eac2bab78`.
Focused tests and lint pass; raw and exact execution authority remain partial.
No Full Dataset, freeze, study or PR merge followed.

## 2026-09-19 000693 bounded official source closure

Two archived CNINFO issuer PDFs establish 000693's 2007-05-23 suspended-
listing start and 2014-01-10 first actual trading day. A SHA-verified overlay
on the immutable full SZSE row-gap v1 audit reclassifies exactly 461 dates
inside that interval. The v2 report preserves all 15,655 missing-row records
by category and leaves 4,443 unresolved across 57 symbols (1,186 unknown
resumption; 3,257 without a matching halt source). File SHA-256
`b9d8250bce1fa18362f7c81f78b302a14a5123907ee40499ccca973ef0940719`,
manifest `1cef5be1bdc702dc9a21ed1e32ca46dc772a8162231dd446cc3c349ad2cf26b9`.
Focused tests pass. No raw/execution authority, Full Dataset, freeze or study
was promoted.

## 2026-09-19 SZSE official row-absence source triage

Replayed all 3,886 cached SZSE daily XLSX files with SHA-256 checks against
the accepted P0 master, calendar and normalized halt-event evidence. Of
15,655 missing active-master stock rows, 10,606 match bounded dated halt
intervals, 145 match delisting dates, and 4,904 remain unresolved across
58 symbols (1,186 unknown resumption; 3,718 no matching halt source).
All unresolved dates are in 2010–2014; the per-date external report has
file SHA-256 `5c54e94fc10e35d16c37257aab22afdb47046f6a416418134eab42d17e9ae713`
and manifest `7442324d22eb169599d8d04ab68b9a39205d812410487fdc8033153278b847b2`.
No missing row was inferred suspended, no raw authority was promoted, and
no dataset or study was run.

## 2026-09-19 SSE official bar-presence reconciliation

Reused the completed official SSE chart cache, accepted master/calendar and
exchange halt cache, then added only targeted public CNINFO issuer notices.
The deterministic audit accounts for all 134,465 no-bar active SSE sessions:
133,771 source open-blocked interval dates, 646 official 600705 suspended-
listing dates, 19 dated issuer halt dates, and 29 master delisting dates.
Unclassified source-presence gaps are zero; report file SHA-256
`7ba780bf09e8e1f684247cf698d348c6ea2fb25ec24356aba792bbcd8ca14668`,
manifest `f7e28d9e67c2a889e72c370e8919586cafef4c29b52b6cb0f4924b089f7f4d65`.
No suspension/resumption or full raw authority was promoted. `ruff` and
focused tests pass; full backend validation is partial (689 passed, 62
database-setup errors, one database-dependent failure) because PostgreSQL
is unavailable and Docker WSL integration is absent. No Full Dataset, freeze,
strategy study or PR merge followed.

## 2026-09-19 complete exchange source-scope checkpoint, no raw promotion

The existing SSE/SZSE official caches were completed after targeted bounded
retries: 2,405/2,405 symbol records and 3,886/3,886 sessions, zero transport
failures. Full SSE interval audit admits 5,550,031 bars, quarantines the same
2,306 cross-code aliases and retains the 600003 no-target-bar control. Every
frozen Pilot-v2 SSE partition has a source: 852,354 overlapping bars show no
OHLC mismatch, no volume/amount gap beyond display precision, and no missing
days. Full SZSE audit counts 7,861,158 point-in-time ordinary-A daily rows,
zero unmatched A-prefix candidates; 15,655 active rows absent from the daily
export are not inferred as suspensions. Checksums and exact source-scope
boundaries are in `CURRENT_STATE.md`. Source collection is complete but the
SZSE all-methods versus auction-only transaction scope, exact suspension,
and full corporate-action census remain open. No source or dataset was
promoted and no strategy was run. The older section below is historical.

## 2026-09-19 official raw source checkpoint at human gate

Reused the existing SSE per-symbol and SZSE per-session caches, recovered
transient failures only through bounded same-request retries, then re-parsed
the retained files. Atomic reports now cover 1,525/2,405 SSE master-symbol
records and 3,275/3,886 SZSE sessions, with zero transport failures in those
scopes. Independent source replays find 4,438,675 accepted-interval SSE bars,
2,306 quarantined duplicate code-interval labels, 6,121,757 point-in-time
SZSE ordinary-A stock rows, and zero unmatched A-prefix candidates. SZSE
absent rows are not treated as proof of suspension. Full raw authority,
transaction-scope parity and Full Dataset readiness remain open. Collectors
are stopped at the retained-bonus fractional-share methodology gate without
losing cached sources; no strategy study was run.

## 2026-09-18 source-bound restructuring diagnostic, no P1 closure

Reused 48 checksum-verified CNINFO issuer PDFs/text caches to prove only
their no-original-holder-share and no-cash-dividend clauses. A cross-check
found issuer-specific opening-price and resumption facts in the same notices;
the current P1 record cannot safely split those obligations. The initial
v59 recount and queue v12/triage v21 were therefore **not promoted**.
Diagnostic v2 records 48 narrow findings, zero P1 facts/documents closed,
zero events created and reverse-order PASS; file SHA-256
`60a787eecb596768abf1233ce34fb1d4d0e80f5601c0fccbb4eea9b92a6cb91a`.
Authoritative cumulative P1 remains v58: 16,073/16,320 established;
247 facts / 242 documents open. This correction prevents a false readiness
claim while preserving the new source evidence.

## 2026-09-18 SSE old-symbol chart alias quarantined

Replayed an atomic 875/2,405-symbol official source checkpoint against
accepted point-in-time code intervals and the full calendar. Of 3,068,745
target-date bars, 3,067,830 are inside the matching symbol interval; 915
post-boundary 600849 bars are quarantined and match successor 601607 exactly.
No master identity was changed and no source was promoted. Partial audit
SHA-256 `367ec87b51e73f6245657a4a35620bd721a55b4379f8fc992930a0d4adb21c16`;
manifest `7f1af85a8c2fede82867875168e9b3097ef11d4e4e84c9a12a55db12041d3c4e`.

## 2026-09-18 SZSE official block-trade scope reconciliation

Recovered the exchange-hosted 2023-04-10 block-trade XLSX summary and
agreement/fixed-price detail, preserving original URLs, UTC receipts and
SHA-256s. The deterministic one-day audit compares them with the previously
checksum-bound SZSE/Pilot overlap: 2,504/2,761 direct matches, 34 more
reconciled by official block trades, 223 ChiNext close-price-pattern gaps
still **unproven** by direct after-hours records, and zero other scope gaps
under the bounded 0/100-share diagnostic. The 000001 control's two block
trades total 1,000,000 shares / CNY 12,030,000. Report SHA-256
`2a6251120f7ac80b371a5889653f61d2b5c44c4c6a41f0c995cbfd06b3aef78a`;
canonical manifest SHA-256
`762a0d3c4fd9f6b61586cb9498755bc8b146685b1ec60a12ba54320bbe08c47e`.
This is not full-period, full-universe authority and does not alter Pilot
data, source acceptance, freeze, or research locks. A prior statement below
that no single-day rows were unexplained meant only that OHLC/day-presence
matched; it did not resolve volume/amount scope.

## 2026-09-18 partial official raw-source acquisition, paused at human gate

Reused the accepted P0 master (2,405 SSE symbol intervals / 2,403 identities)
and 3,886-session calendar to checkpoint official SSE day-chart JSON and SZSE
daily XLSX outside Git. Acquisition paused cleanly at the existing retained-
bonus fractional-share decision gate: 575/2,405 SSE requests (574 with target
bars; the 600003 no-bar case agrees with its accepted pre-2010 halt and
2010 termination), 825/3,886 SZSE sessions, no transport failures. Every
cached response has its original URL, UTC receipt and SHA-256; rerunning the
collectors checks and reuses cached bytes. Partial collection-report SHA-256s:
SSE `72039f8fdc9a4755a0e479ef4c279943315be77b49cbb0958421aeb65a413d6c`,
SZSE `28dc9c5076be33750b46d7918c902938358ed46edefeba98cd438194f4f08f1c`.
The counts are canonical report rows; four more sequential SSE and four more
sequential SZSE responses were cached after the last 25-row checkpoint,
besides earlier controls. Every cached payload has a matching receipt; the
next run reuses it. No collection worker remains active.

Read-only SSE/Pilot-v2 parity on 201,711 available overlapping bars found
zero OHLC discrepancies, zero volume/amount discrepancies beyond combined
100-share/CNY-100 display precision, and zero day-presence discrepancies
within compared partitions. The partial report SHA-256 is
`a1ac7fed4ce5415a36873d49a89a3f0eefe1cafd342b863cd8c8f7314ba23455`;
1,752 Pilot SSE partitions are not yet snapshotted. The SZSE official
[trading FAQ](https://investor.szse.cn/knowledge/stock/deal/t20191225_572858.html)
explains why post-session block-trade totals can exceed instantaneous-feed
volume, but the observed 211/257 same-day gaps are not yet matched to
official per-security block records. Full raw authority and suspension/
resumption authority stay open. No dataset, freeze or study was run; PR #12
remains open. The single smallest human blocker is still the deterministic
retained-bonus fractional-share convention documented in
`../research/R5_RETAINED_BONUS_FRACTION_GATE.md`.

## 2026-09-18 bounded official exchange raw-data route controls

Added replayable bounded probes `backend/scripts/probe_sse_official_daily.py`
and `backend/scripts/probe_szse_official_daily.py`, reusing the existing
checkpointing fetcher and retaining original JSON/XLSX bytes, UTC receipts,
request URLs and SHA-256s outside Git. SSE controls cover a survivor, a
2011-exited stock and STAR; SZSE controls span the 2025-09-01 archive/catalog
boundary. Five SZSE days return 872/2812/2913/2913/2924 unique rows;
these stock-tab counts are not ordinary-A census counts. The three SSE
controls return 3839/212/1566 bars inside 2010–2025.
SSE 600000's 2023-04-10 OHLC and amount match the frozen Pilot, with only
seven shares' volume precision difference. SZSE 000001's OHLC matches but
official all-methods volume/amount exceed Pilot by 999,900 shares and
CNY 12,029,952.38. The responses remain **probes only**: full-universe
completeness and source-scope parity are not established; no dataset was
created or frozen. Probe report SHA-256s: SSE
`f6c5a7f7d8f061d6be2b9244f26f57e3f87cadfbb71fe02a8d894d3bb69bd3f2`,
SZSE `f7e1af8b165e332c3648d261be0319c5263570927dce75e6a53cc4922d412de9`.

An independent read-only overlap audit of the entire 2023-04-10 SZSE
official export against frozen Pilot-v2 matched 2,761 of 2,765
point-in-time ordinary-A rows. All matched OHLC prices agree. Beyond the
sources' combined 100-share / CNY-100 display precision, 211 volume and
257 amount gaps remain, all official-higher; 4 official zero-turnover rows
correctly have no Pilot raw bar. Zero rows remain unexplained within this
single-day comparison, but it is not a 2010-2025 authority pass. Audit file
SHA-256 `29401b9649ed77f3207871d85404cdc7cce4b88927000f5cf3d52841ec66e84a`.
Subsequent partial acquisition is reported above; no raw source was promoted.

## 2026-09-18 five official non-primary derivative notices scoped

Reused five checksum-verified issuer PDFs and accepted cash events: two
post-distribution private-placement price/quantity adjustments (002521,
688065) and three pre-final convertible conversion-halt hints (300517,
601860, 001283). Strict source-type, annual-period, timing and unique-event
guards close only their P1 document requests. Derivative report v6 closes 22
cumulative notices, creates zero events, and passes reverse-order replay;
manifest `534de27e99a8075012a3242c5650350d71351d8e846e1f135e430b20bc4108f2`.
P1 cumulative v58: **16,073/16,320** facts established, **247 facts / 242
documents** open (231 distribution, 11 other), manifest
`0e5bb98ed6daf54ba29e48bef2b6ad6201ab4b1482dfdf96b277800067641e9c`.
Queue v11 triage: 94 bonus-only, 1 both, 3 cash-only, 133 neither. No Full
Dataset, freeze or study.

The disjoint 11 non-distribution requests were checked against the current
P1 v58 closed-ID set and original P1 manifest: four merger/account chains,
five cash-plus-bonus dual chains, raw full-universe coverage and exact daily
suspension/resumption. This prevents interpreting “11 other” as 11 missing
PDF downloads. Full-range Tencent control responses exist, but only as
coverage probes: `CN_A_RAW_OHLCV_FAILOVER_V1` is explicitly Pilot-only.

## Previous 2026-09-18 two official nonfinal bank notices scoped

The already retained 601009 shareholder-proposal PDF has no executable
cash/bonus ratio or entitlement dates and explicitly requires later approval.
The 600919 convertible-halt PDF explicitly names its later final ordinary-A
implementation publication day; the accepted 2023-07-11 issuer event is the
unique exact-date/title match. In both documents, preferred-security words
occur only in the code header, not the entitlement body. They are nonfinal
references, not additional dividends. Source/checksum and reverse-order audit
is nonfinal report v8, manifest
`aff961accf0b3743c903f70b28a0c7064fdf48e283813e97be236e4004abc58c`.
Cumulative P1 v57: 16,068/16,320 established, 1,989 substitutions,
252 facts / 247 documents open (236 distribution, 11 other), manifest
`7de0765893210ae796b24c1acd84edb7254051ca6f28f4d0b0a40c5485ba2896`.
Current triage: 94 bonus-only, 1 both, 3 cash-only, 138 neither. No Full
Dataset, freeze or study.

## Previous 2026-09-18 three official cash-correction sources closed

Reused original checksum-verified CNINFO issuer notices and their accepted
cash-event checksums to audit three correction PDFs without redownloading:
002457 (payment/liability record metadata swap), 603087 (virtual ex-price
formula only), and 601678 (repurchase/participating counts and aggregate
payout, same 0.03 gross cash per participating share). The 002457/601678
before/after sections reject other changed text; 603087's explicit
reference-only correction repeats the unchanged gross term. The old and new
601678 payouts each equal participating shares times 0.03. Correction report v9
adds three closures to prior seven, with no new economic event; manifest
`ba642def749d419361cde7d996e57da68b138b2799e83f126d279f18ba5e4571`.
Cumulative P1 v56: 16,066/16,320 established, 1,989 substitutions,
254 facts / 249 documents open (238 distribution, 11 other); manifest
`a0640f11699434ed644add3426f861b0244c29dd58e765c2a5167f625dbf2545`.
The remaining 238-document triage is deterministic: 94 bonus-only, 1 both,
3 cash-only, 140 neither. No Full Dataset, freeze or study.

## Previous 2026-09-18 retained-bonus component-integrality replay

Rechecked the original CNINFO issuer notices behind all 288 bounded candidates.
The prior 282 accepted events included 39 whose total ratio was integral but
whose individual stock-dividend or capital-transfer ratio was fractional.
The existing approved policy cannot guarantee account-level whole shares for
those components. A strict option in the shared terms parser now fails closed
only for the bounded accounting ledger; source-term extraction still retains
the exact total. Targeted tests pass. Immutable ledger v30: 243 accepted, 45
unresolved, 7,119 outside the subset; file SHA-256
`05421d892782d219316c47952e21f3e87ce16c6b55acf8041b01132f9b6d939d`,
manifest `e5df58295be544873872d40b10dc82a591d921f8dd2108ac4144943afcd0e2e4`.
No official source bytes were reacquired.

The dependent source replay keeps 11/16 exact dual notices closed, 5 open;
dual v7 manifest `d188d0c169a6adc81c501c01fa13dc211a017ff2534ad0ac2f76e5205b369838`.
Cumulative P1 v54 has 16,063/16,320 facts established, 1,986 substitutions,
257 facts / 252 documents open (241 acquired distribution, 11 other), manifest
`f87e6ac60c05397794891891651f3195cd11d92ed029bf938f825e07a2b63d25`.
The old v28/v6/v53 reports remain immutable historical checkpoints, not
current acceptance. Full Dataset and studies remain locked.

## Previous 2026-09-18 603023 retrospective official source closure

The original issuer PDF lists new unrestricted shares on 2016-06-16 in its
cover and the impossible 2016-04-16 in its body. A separately retrieved,
official CNINFO issuer half-year report (revised, published 2016-09-02;
SHA-256 `e66612fa75a69524c32469c563618dfde70867a3bd7eee089b8339f25d2e8d30`)
retrospectively confirms 2016-06-16 on PDF pages 15, 21 and 61. The exact
issuer metadata, HTTP receipt, original conflicting terms and page positions
are source-bound; the later report is audit-only, not a backdated trading
signal. P1 dual v6 closes all 16 documents/32 facts, preserving its previous
15 closures, manifest
`343002c25a3c070cb451678f6e07dbcaedb5f18937a675055ba3f25dfccb1271`.
Cumulative v53 has **16,073/16,320** handled, **1,991** substitutions and
**247 facts / 247 documents** open (241 acquired distribution, 6 other),
manifest `3a7d57f3b3c8ce4839cdad846bdc0e1a20c0e8246e2578d40432fbacf6776db3`.
No new economic event, full-census acceptance, Full Dataset, freeze or study.

## Previous 2026-09-18 603023 tax-component parser correction

The exact official 603023 PDF was already retained; a targeted duplicate
fetch matched its SHA-256 and introduced no new authority. Its tax section
describes 1.3 tax-free plus 0.2 taxable shares within the 1.5 capital-reserve
transfer, not an additional entitlement. The shared parser now excludes tax
explanation from ratio extraction while preserving full-document nonstandard
guards. Full 288-candidate replay leaves all prior 281 event checksums intact
and adds only 603023: bounded ledger v28 is 282 supported / 6 unresolved,
manifest `2b65dfe5bd7807363f833e5a7d00a686fc8a798dccc4c5330022a039a2260027`.
The issuer notice has conflicting new-share listing dates, and actual
tradability is not independently proven. The 603023 two-leg P1 requirement
therefore stays open; cumulative v50, accepted 15-event merger inventory,
full-census, Full Dataset and research locks are unchanged.

## 2026-09-18 河北钢铁 false-parent identity audit and 600253 follow-up

Reused the original 000709 issuer implementation PDF and obtained a single
targeted official SSE notice. The issuer names 邯郸钢铁 and 承德钒钛; SSE assigns
them 600001 and 600357. The audited official SZSE master gives unrelated
continuing identities 000761 本钢板材 and 000898 鞍钢股份. Two P1 requests were
rejected as false parent identities, not official substitutions. Immutable
source-rejection manifest
`adb7ef14c48a69dfc7a02e270d338d4ef7a352f69d630236dc4306e67c9faa80`.
Cumulative v50 is 16,071/16,320 handled (including these two out-of-scope
requests), 1,990 substitutions, 249 facts / 248 documents open (241 acquired
distribution, 7 other), manifest
`9261b0dcae51b3330bcb7644e8b617e1f2649fa824ce3359510b057e6f1f0a08`.
Targeted 600253 cash-choice and successor notices establish last parent trading
2013-06-06 and 1,122,431 valid elected shares; no official account-fractional
allocation/compensation treatment was found. It remains source-incomplete.
The 15-event inventory, full census, retained-bonus methodology gate, Full
Dataset and study locks are unchanged.

## 2026-09-18 dual-parent 600607/600842 official source closure

Resumed the targeted CNINFO fetch from the retained metadata and recovered
only the missing 2010 issuer PDFs; the transient DNS failure below is resolved.
Eight original documents for 600607 and seven for 600842, including shared
successor disclosures, passed byte/receipt and exact-term checks. The official
master's stable `CN-A:SSE:601607` identity spans the 600849→601607 code change.
The issuer distinguishes the 2010-03-01 listing of new unrestricted shares
from actual 2010-03-09 trading resumption. Cash choice was exercised for
160,440,885 affiliated 600607 shares, excluded from the reviewed ordinary-A
non-electing scope; 600842 reported no elections. Per-account fractional
awards remain unobservable. Exact P1 requests `MERGER_NEW:600607:600849` and
`MERGER_NEW:600842:600849` close, with no new accepted economic event.
Audits: 600607 manifest `c5c2912a936b6d8bd473f2fd7ae088a480da75fef2a891526a0379c09bea158a`;
600842 manifest `42031dd15328cfd8ab100058d6e3a03957c7525d98ca9a4fd5e2620e1fe7f8a1`.
Cumulative v49: 16,069/16,320 established, 1,990 substitutions, 251 facts /
250 documents open (241 acquired distribution, 9 other), manifest
`81b39252d789a38af4e1d0b001adcc727291ac84ec9a3870ec45720bd84b2994`. The 15-event
inventory, full-merger census, retained-bonus methodology gate, Full Dataset
and study locks remain unchanged.

## 2026-09-18 next older SSE merger lead, not accepted

Targeted CNINFO metadata for the 600607 and 600842 parent chains was saved
under external `full-merger-v1/targeted-parent-fraction-v4/`, eight issuer
announcements per parent across 2010-01-29 to 2010-03-10. The 600607
cash-choice implementation PDF (official ID `57568627`, SHA-256
`cd462a91bcb21f3110cfafddeb260654f1534984d763c29dfe4b63babd0b7dc1`)
was acquired with its receipt. A later targeted PDF request failed with
temporary WSL DNS resolution; its failure receipt is retained for bounded
resume. No 600607/600842 chain or P1 request was closed, and no count or
accepted event changed. Do not restart metadata acquisition from zero.

## 2026-09-18 targeted 600631 merger source-chain audit

Reused the official CNINFO report, parent halt, successor progress/result
notices and recovered only the identified 2011-08-03 cash-choice implementation
and 2011-08-11 zero-election result PDFs. For ordinary unrestricted 600631
A shares with no cash election, the official ratio is 1:0.861; 2011-08-04
is the last parent trading/cash-choice record day, continuous halt begins
2011-08-05, parent terminates 2011-08-23, registration completes 2011-08-26,
and converted unrestricted 600827 shares list 2011-08-31. Six original issuer
PDF bytes, exact page terms, master lifecycle, targeted raw-date boundary and
reversed input order pass. The official individual residual allocation remains
unknowable; only the merger-specific research floor is available. Event
checksum `b3779bae7912ae8f38c2d553d5e73d019cb213a3e18c8293c7c6c7a9b9c723e5`;
immutable event-audit manifest
`03e73decd34373a09f32e62d61561f5dc57ca40780011371a518b25cbc5a00e9`.
The exact `MERGER_NEW:600631:600827` P1 source request closes with no new
economic event; source-closure manifest
`332efe2929f28923fbcd85927b4f862c087c7496c97196779f559ff8bf5a2427`.
Cumulative v48 is 16,067/16,320 established, 1,988 official substitutions,
253 facts / 252 documents open (241 acquired distribution PDFs, 11 other),
manifest `967a6459073e6d2a45a77fa7d41bec030b2630be946b17441dd769050c146a63`.
The 15-event accepted inventory, full merger census, retained-bonus human
gate, Full Dataset and study locks are unchanged.

## 2026-09-18 targeted 600832 merger source-chain audit

Reused official CNINFO PDF receipts and fetched only the identified missing
cash-choice result and retrospective tradability confirmation. Four
contemporaneous issuer documents establish the bounded ordinary unrestricted
A-share, non-cash-electing 600832→600637 event: 3.05:1 old-to-new ratio,
last parent trading 2015-04-29, continuous halt from 2015-04-30, record and
termination 2015-05-20, registration 2015-05-27, and new unrestricted-share
trading 2015-06-03. A 2016 issuer confirmation corroborates tradability only
in the audit, not as a point-in-time event source. Official PDF bytes/terms,
master lifecycle, targeted raw date boundary and reversed input order pass.
Event checksum `9a3e05a534759822e51bb0427cfe219997c7f0084325f6763b6c58786d6d7e94`;
immutable event-audit manifest
`4a539fd39a893150cbb24bac65efe4a207c55ce06f163f27013b5905a893a850`.
The exact `MERGER_NEW:600832:600637` P1 source request closes with no new
economic event; source-closure manifest
`0d3a410876d651310da37c51b11229c49ef292596f9ef987ba11d2a957d3b274`.
Cumulative v47 is 16,066/16,320 established, 1,987 official substitutions,
254 facts / 253 documents open (241 acquired distribution PDFs, 12 other),
manifest `95aca74de51b365239c05a858884eddbccdce3518ea8cc6c7a778cfbe987aeeb`.
The 15-event accepted inventory, full merger census, retained-bonus human
gate, Full Dataset and study locks are unchanged.

## 2026-09-18 older SSE merger source-chain recovery

Retained CNINFO metadata yielded three exact full official reports for the
600849, 600827 and 600637 surviving-company chains. Original PDF receipts and
source hashes were verified; existing progress/result notices were reconciled.
Ratios and several effective boundaries are evidenced, while actual first/last
trading boundaries and holder/lock scope remain incomplete. This is an audited
source lead, not a new event or P1 closure. Current P1 v46 and all R5 gates
remain unchanged; details are in `../research/R5_MERGER_LEAD_CLOSURE_V1.md`.

## 2026-09-18 targeted 000418 merger source-chain audit

Recovered three exact missing CNINFO issuer PDFs and reused the already cached
final implementation/listing PDF. The final 000418 A-share conversion ratio
is 1:1.15144821 after both companies' distributions; 2019-05-07 is the last
parent trading day, 2019-06-20 the conversion record date, and 2019-06-21 the
new 000333-share listing date. Global fractional allocation remains
unreconstructible per account; the approved merger research floor is separate
from historical registry truth. Source-byte, exact-term, master, raw-boundary,
chronology and reverse-order audits pass. Event checksum
`a52b4e6c971686f85b17212ca06cf04120e0983fe48ea531b620a50f13113871`;
immutable source audit manifest
`aa76da4feb7265b7e5376fd1388f7a0a7d86933fd219e8b663f824377af1a4f7`.
The reviewed case is ordinary unrestricted A shares without a cash election;
it does not admit B/restricted/electing accounts, change the 15-event accepted
inventory or establish the full merger census. Its matching P1 official-source
request closes with no new economic event. Cumulative v46 is 16,065/16,320
established, 1,986 official substitutions and 255 facts / 254 documents open
(241 acquired distribution PDFs, 13 other). See
`../research/R5_MERGER_LEAD_CLOSURE_V1.md`.

## 2026-09-18 targeted 600253 merger report recovery

Recovered the exact official CNINFO 2013-06-04 full revised merger report
`62552848.PDF` from the retained metadata lead, SHA-256
`6863c67f6032a118518bd99af0532c9d53a316b7193981f9422fedaa209d8422`.
The full 412-page report still does not establish account-level fractional
conversion; it explicitly excludes fractional handling from projected share
totals. The existing final result notice confirms ratio and registry/trading
boundaries but distinguishes restricted shares. The 600253→600056 event is
still source-incomplete, with no new event/P1/dataset acceptance. See
`../research/R5_MERGER_LEAD_CLOSURE_V1.md` for the exact residual fact.

## 2026-09-18 R5 600337 final dividend source recovery

Recovered the original signed 600337 issuer implementation notice on the
2011-06-08 edition of its designated `《证券时报》` disclosure paper. Official
SSE query metadata confirms exact security/title/publication day, and the
issuer's earlier CNINFO annual report confirms the designated paper. Parsed
only the issuer's boxed announcement, not neighboring companies. Gross cash
0.05 CNY/share, record/ex 2011-06-13/14, payment 2011-06-20 and holder
disbursement terms agree with the preexisting accepted event and exchange
oracle. The direct SSE PDF returned `denied by bot`; its bytes are **not**
claimed as verified. Report v2 is immutable and repeatable, with no new event;
P1 cumulative v45 is 16,064/16,320 established, 1,985 official substitutions,
256 facts / 255 documents open (241 acquired queue, 14 other). Full Dataset,
safe start, freeze and studies remain locked. Source checksums and retrieval
timestamps are in `p1-original-designated-disclosure-cash-v2.json` outside Git.
Immutable replay and reverse-input checks pass; the local backend suite passes
719/719 tests and Ruff check/format passes.

## 2026-09-18 Docker Desktop/WSL non-destructive recovery

The Docker Engine was unreachable and `docker-desktop` WSL integration had
stopped; backend error identified the recurring stale `sailor-ingest.sock`
rename failure. A normal Desktop stop failed, so the already failed process
was force-stopped. Its two-entry runtime directory was preserved as
`run.recovery-20260918-quant-r5.bak`, and Desktop recreated a working runtime.
No Docker image, volume, PostgreSQL/Redis data, project file or frozen dataset
was removed. Engine 29.7.2, Compose v5.5.0 and Ubuntu WSL integration pass.
Existing Compose services restarted without rebuilding: PostgreSQL and Redis
healthy, Redis PONG, backend healthy, API health 200, frontend 200 on 5173.
The now-database-backed local backend suite passes 718/718 tests; frontend
passes 78/78, Ruff check/format, strict mypy (121 files), ESLint, TypeScript
and production Vite build pass. This repairs local integration testing only;
R5 source/census gates are unchanged.

## 2026-09-18 R5 convertible-halt preliminary cash reference closure

Two retained official 601998 notices schedule an exact later final A-share
implementation notice while warning that the per-share distribution can
change with convertible-bond share count. Each later accepted issuer notice
matches the scheduled publication date and full title. Indicative 0.356 and
0.1847 CNY/share differ from final 0.3261 and 0.1825; the hints are not
economic-event authorities. Nonfinal scope v7: 32 closed, manifest
`4fd9861ea5eb5524b5b89b7a8208c120d78117d94662e56081ef49e14dd7511c`.
Cumulative v44: 16,063/16,320 established, 1,984 official substitutions,
257 facts / 256 documents unresolved (241 acquired queue, 15 other), manifest
`f62f73a38ed45060f55b9c641445b7465c77c8e65bc507672f1c45b06dfcb0b9`.
Input-order replay passed; no new economic event, Full Dataset, freeze or study.

## 2026-09-18 R5 nonfinal A-share schedule scope closure

Reused the already acquired official CNINFO PDFs. Seven 601186/601390 A/H
preliminary schedule notices are nonfinal references: each explicitly defers
the final A-share implementation announcement and exactly matches one later
accepted issuer primary A-share event by security, record date and ex-date.
The parser isolates A-share dates from H-share dates and rejects nonunique or
unmatched cases. No economic event or cash amount was inferred from a hint.
Nonfinal v5 closes 30 documents (23 prior + 7), manifest
`65741fb57ca0394ed5d4fed49b389293a3736cad869d8216d62ea91c3fc19447`.
Cumulative v42 establishes 16,061/16,320 facts, 1,984 official substitutions;
259 facts / 258 documents remain (243 acquired queue, 15 other), manifest
`e48e0a00c98bf66ef6f1a112fa2827a1c3ed1f47bbf2825ede4e9535c3d6e873`.
Ruff and focused tests pass; immutable input-order checks pass. The 301262
retrospective yearbook/annual-report ex-date crosscheck does not repair its
contemporaneous issuer typo for PIT acceptance, and no related event was
promoted. Full Dataset, freeze, studies and PR merge remain blocked/unrun.

## 2026-09-18 R5 exact cash-leg and derivative scope closure

Reused the 257 acquired, SHA-bound official CNINFO PDFs. Shared labeled-date
parsing now accepts slash dates only under exact record/ex labels. Five more
non-primary/mixed notices match the accepted issuer primary cash ledger on
ordinary-A identity, gross cash, record and ex-date: 688556, 688093, 688583,
688615 and 002129. The mixed notice's bonus leg remains accounting-pending;
none creates a new economic event. Two derivative notices, 600339 and 688767,
explicitly state that a matching accepted distribution had completed on the
same ex-date. Their price-adjustment references are not distributions.

Matched-cash v4: 45 closed, file SHA-256
`f57ae2a4430aadc05438dc9a57a9e1199f76e6a34dc11f496db9e585576a0f5d`,
manifest `784637aea78238d62017268e696cb0868a887eb8a38eb8960f18b0229a3b1ffc`.
Derivative-scope v4: 17 closed, file SHA-256
`627c03be8a63fed18ccf21b7f360bd694f1de32fb3ac8e03a8c18a786d8a7620`,
manifest `24d8a42f9d26a1a671500deeab121511ac593601f0b18ea1ca3da2129851c7bf`.
Cumulative P1 v41: 16,054/16,320 established, 1,984 official substitutions,
266 missing facts / 265 documents (250 remaining acquired distribution PDFs,
15 other); byte-identical immutable replay and reverse-input check pass.
Focused tests: 31 passed; Ruff check/format pass. The fractional retained-bonus
methodology gate remains pending, and no Full Dataset, freeze or study was run.

## 2026-09-18 R5 stop on retained-bonus fractional-allocation policy

After the independent official-source corroboration below, R5 reached a new
material methodology gate. Three official 688339 retained-bonus notices have
0.4/share ratios; the 2024 issuer notice specifies registry-wide whole-share
remainder allocation with random tie-breaking. An illustrative 100-share
position becomes 140, 196, then 274.4 theoretical shares under the current
engine. Existing approved policy covers basis preservation but not this
fractional quantity; merger floor cannot be transferred by assumption. The
human decision is documented in
`../research/R5_RETAINED_BONUS_FRACTION_GATE.md`. No fractional bonus event
was accepted, no dataset created/frozen, and no study or PR merge occurred.

## 2026-09-18 R5 official bonus-source corroboration

The 257 retained official PDFs were not reacquired. Exact SSE listing-table
dates and a documented SZSE `转增股` spelling now parse 94 bonus-only notices;
92 have independently matching official exchange ratio/date rows and PIT
ordinary-A identity. The 60 previously corroborated source terms retain the
same identity, dates, ratio and source/exchange hashes; 32 are new. The
remaining 002982 lacks the matching exchange oracle row, and 688692 is a
secondary implementation-result notice. Immutable bonus-source v4 replayed
byte-identically (file SHA-256
`09fb6e2368b70e9275926588b5a66cc52ceb731c66ae470e24c5b8ba0eb10f29`,
manifest `77c70f05b5aa7a14c48915b3bdeae8754c626fc431e797d2d389544c2ee58097`).
This is source-term corroboration only: no bonus event/accounting acceptance,
no P1 denominator change, no Full Dataset, freeze or study.

## 2026-09-18 R5 targeted official P1 source recovery and exact cash closure

The exact 257-URL unresolved distribution queue was generated from the
immutable P1 base/closure reports (queue SHA-256
`0de6e2121d218e950c82abf09303f4f1cb7fcf7fc0cde1306859c45f93a02a55`).
CNINFO static PDF access returned valid official bytes again. The existing
bounded/resumable batch reused five prior verified PDFs and retrieved 252;
all 257 receipts are PASS, zero failures/non-PDFs. Replaying the batch was
byte-identical. Source-manifest file SHA-256
`7fc0e792322b50ba7ce09d82d57b66308585c09691a5a379bf117f971a5fb5c2`,
canonical manifest SHA-256
`b5f786f7888e9828452e200a01e0d9cfee0abe7974f2717aabd5e2686fbde9be`.
Original PDF checksums bind page-addressable text. Conservative triage v6
finds 7 cash-only, 93 bonus-only, 6 both and 151 neither; these are parser
candidates, **not** newly accepted economic events.

Two official issuer correction PDFs were retrieved with metadata/UTC/SHA
receipts: 300207 replaces 2017-04-18/19 with 2017-04-20/21; 600801 replaces
its 2014-06-18 ex-date with 2014-06-17. A shared ordinal-page-header parser
fix recovers 000776 and 002050 dates split across PDF pages. Three exact
original issuer PDFs (000826, 300384, 300852) each contain a wrong date but
also independent correct holder/payment/application timing, corroborated by
one official SZSE monthly row and gross amount. No blanket override or new
event was introduced. The original 263 accepted economic identities, cash
amounts and dates are unchanged; 000756's classification tightens to exact.

Retained cash v22 closes 270/271 (file SHA-256
`0fd7bcc62fcf2dcd8162b08845f5cfa557d75777ce2e11d05a94fa00f2f79430`,
manifest `35a757cc218fd0bd94b323626240d0742939fa1cb736383187560665bc10cbce`).
Cumulative P1 v39 establishes 16,047/16,320 facts with 1,979 official
substitutions; 273 facts / 272 documents remain (257 queue, 15 other), file
SHA-256 `eb33e2dcd35d80e5ee04df2ffa5c0344904dd7a9c60614a30e46b659e8549281`,
manifest `b79f7870c9c7bd3fcca4cf641d7f01834328d41e4dc2594fc6ed78c2eac431d6`.
Input-order checks pass. Full corporate-action census, Full Dataset, freeze
and studies remain blocked/unrun.
Focused parser/closure tests and repository-wide Ruff pass. The local full
backend suite is not green: 652 passed, 62 setup errors and one failure because
PostgreSQL at `127.0.0.1:5432` refused connections; `docker` is unavailable in
this WSL session. This is a separate nonblocking runtime/CI validation gap,
not evidence that database-dependent tests passed.

## 2026-09-18 retained official cash-source milestone

Official public evidence closes 12 additional retained-source candidates
since v12: four source-pinned 2012 A/B currency-column conflicts; the 601818
final ordinary-A notice; the 600378 issuer date-correction pair; and six
garbled/image-text PDFs with source-bound PyMuPDF/OCR cash/date extraction.
The 300041 scanned PDF was visually checked after targeted offline OCR.
Every accepted amount and date still matches the existing event and official
exchange audit; no new economic event was created. Previously closed v16
rows are unchanged in v18. The eight retained rejections remain explicit
(seven issuer-date conflicts and one no-final-source case).

Retained-source v18: 263/271, PDF/text/manifest hashes retained, input-order
and repeated-output checks PASS. File SHA-256
`3a326b2e2a65fee2a2806ed221226bf691cad529f8a76fd43fb0653c05e005b6`,
manifest `6c3504821626b2c9342528af51e2f5d6a50f67e3a0ac8d0d3ea9edb6983239b3`.
Cumulative v36: 16,040/16,320 facts established; 1,972 official
substitutions; 280 facts / 279 documents remain (257 cash-queue, 22 other).
File SHA-256
`80e49f25fd99f3256406d81c1fcfdf3c3ff0037c020af86b83d29b2ff9755e06`,
manifest `2a02f9dcb6b0e3204321cb7957f8ca30780a4ae4b3744599218de220e8b9f72e`.
Focused tests and Ruff pass. This does not establish Full Dataset readiness,
and no dataset, freeze, study, purchase or PR merge was performed.

## 2026-09-18 historical 000022 official cash-source conflict closure

An earlier retained official CNINFO final PDF (`61255655.PDF`, SHA-256
`5ee3949582e2c5c967b4a3059c2b8c7a8077d50b0067608af584542b5deabee6`)
explicitly establishes CNY 0.40/share for A holders and the 2012-07-19/20
dates. The P0 point-in-time master binds historical 000022 to stable 001872,
and the accepted ledger event references the same PDF. The official SZSE row
reports A DPS 0.491, while its pre-close/ex-price difference is 0.400 and
the issuer's B-share HKD conversion rate maps 0.40 to 0.491. A narrowly
source-pinned exception records that conflict and accepts the issuer's A
holder-class term; no generic override or new event was introduced. All 250
prior retained-source closure rows are unchanged. Source v12 file SHA-256
`019e59611c9aad04c07f056b7578cd3397a967b264519220497f117b6d524e69`,
manifest `fc8005c3097f95166dd448c9e2bcb940ed9e784b0f39fc282c0de0ef869a70be`.
Cumulative v30 establishes 16,028/16,320, leaving 292 facts / 291 documents
(257 cash-queue, 34 other), 1,960 official substitutions; file SHA-256
`9fe049e0c315d427f56a65d11ceefea62ff411e544baa67d08abc37cd1298918`,
manifest `2ab3a12fad49b846d7b6d59091fa47ed63be95648347ffc071541614a06251f6`.
This does not establish a full cash or corporate-action census.

## 2026-09-18 official cash correction reconciliation

The retained original/corrective CNINFO PDFs for 002866 and 600586 pass exact
before/after parsing, PDF/text SHA verification, original-source lineage and
unique accepted-event amount/date matching. 002866 corrects a 2022-to-2023
entitlement-year typo; 600586 corrects gross cash to CNY 0.03/share. Correction
v7 keeps five prior rows and adds two, SHA-256
`c67b0ce0beb9ef5c09f0a75350ef6165b204f210b8c40dd68fec324549c34ebe`,
manifest `720c4032fecd0996be6d8514efb3a11d5c52172ff62f35f46100484f7d5a7e00`.
Cumulative v29 establishes 16,027/16,320 facts, 1,959 official substitutions
and leaves 293 facts / 292 documents (257 cash-queue, 35 other), SHA-256
`9174b3461a28cf1a63be40c071c271e48d82a136a76da909bee29332d4ae38de`,
manifest `c4d4e0d7d842a74e1ddb92509670a407d4c52de1d3c118597730df7906f81f5d`.
No new event, dataset, freeze, study or PR merge followed.

## 2026-09-18 nonfinal notice classification and targeted cash source probe

Original retained official PDFs/text and source-manifest hashes establish four
additional no-executable-terms notices: 301233, 002611, 600157 and 603363.
The 601009 proposal remains unclosed because it includes a preferred-share
marker. Scope v4 closes 23 documents total, preserving its 19 prior rows;
SHA-256 `c8fdbeeea3bab0bae92559d45cf15f14efb972b825bd266586983a84008f34ad`,
manifest `d93ff588b4c20abdd318a9aa8009d6aad6c3e633d1ec280b7279e136795f2e18`.
Cumulative v28 establishes 16,025/16,320 facts, leaving 295 facts / 294
documents (259 cash-queue, 35 other); substitution count stays 1,957.
SHA-256 `446a732b0d78a90fd844f4c09acd850f2356861b64e6ea52b3ac0e0020291228`,
manifest `3ba4c92765883614c34ecd1877d8135cd7ca7a3796a3cde204c18f038aa659d5`.
No new economic event was created. A newer targeted CNINFO download of the
2012-07-12 000022 notice failed DNS on three bounded attempts; the original
PDF was later located in a previously retained official batch and reconciled
above. No purchase, Full Dataset, freeze or study followed.

## 2026-09-18 official dual-leg distribution source closure

The retained CNINFO corpus contains the identical original source PDF for
both accepted cash and bounded bonus legs of 15 P1 requests. The new source
audit rechecks PDF/text bytes, finality, issuer/date/terms, exchange cash
targets, bonus oracle ratio and event checksums. It partitions all 16
candidates: 15 closed (30 facts) and 603023 rejected for missing accepted
bonus evidence. The 600845 A/B date set is disambiguated by its A-share
exchange dates using the pre-existing dated-source rule. Dual report v3
SHA-256 `b05b809985dd8c8ad1c6ba5bed3c849220b0afa503c85970c3057e1923ab898a`,
manifest `aec400280226fcb64b4e8c99ff1aba36c8993b289a29984c0f621bc10a87891e`.
P1 cumulative v27 establishes 16,021/16,320 and leaves 299 facts / 298
documents (263 cash-queue, 35 other, including one dual-leg request); 1,957
substitutions. All prior 2,265 closures are identical. Cumulative SHA-256
`882d73197051ea24064d5fc80ae39b936c48cef82e6c42388557c121a31d8e49`,
manifest `9924282d5b416b67b0f99b87fc77f03be0e06973cefa414966d975be0d2bf95e`.
No new economic event, Full Dataset, freeze, study or PR merge follows.

## 2026-09-18 retained official bonus term reconciliation

The shared official-issuer terms parser now handles an explicit final
post-total/increase share-capital crosscheck for superseded or duplicate
component labels and a narrow capital-reserve `转赠股本` heading typo when the
body states the actual transfer. Three previously unresolved cases (600056,
601233, 603686) now agree with independent exchange ratios and stable ordinary-A
identities. The immutable v24 bounded ledger accepts 281/288 (up from 278),
preserves all 278 prior event checksums, and leaves seven explicit unresolved
plus 7,119 outside scope. Reversed input order reproduced identical base bytes.
Ledger SHA-256 `08ae99961bfeb74d81d94144881db3a5faca1732993bbcc768a8b344dca5a107`;
manifest `8f3ebac218ae4f335cc305bbfd246031db73af2e13dc85b0cc394e3cdfb2ffed`.
All 635 database-independent backend tests and focused Ruff/format checks pass.
The 63 database-backed cases cannot pass locally while PostgreSQL is unavailable
(full run: 635 passed, 62 errors, one failure). No commercial source, Full
Dataset, freeze, strategy study or PR merge followed.

## 2026-09-18 official CNINFO recovery of two bounded bonus source gaps

Previously inaccessible SSE-hosted implementation PDFs for 603315 and 603889
were replaced, for the same facts, by already retained official CNINFO issuer
implementation notices. Source PDF/text hashes, implementation-body finality,
one-for-one transfer ratio, record/ex-dates, official exchange oracle, stable
ordinary-A identity and scheduled next-session listing all pass. The 276 prior
bonus events are unchanged; v20 accepts these two source-bound events and
leaves 10/288 bounded cases unresolved, plus 7,119 oracle rows outside the
integer next-session subset. Manifest
`82fcdf1d558adfa1e81f6486ab74f73fcfdf920bfdf7a13c1cff6e615db603f0`.
No commercial source, full bonus census, Full Dataset or study was accepted.

## 2026-09-18 issuer-body finality cross-check

Thirteen generic-titled retained issuer PDFs supply explicit implementation
method text, exact ordinary-A cash and entitlement dates matching accepted
events and independent exchange targets. Their source-body finality marker and
original PDF/text SHA-256 are preserved in each new closure. All prior 237
closures remain identical. Source v10 closes 250/270 candidates; 20 remain
explicitly rejected. Manifest
`134db8ba9c28f4a60f62c6f599aa94c4838f7ff9473e833d82bb3969004047bd`.
Cumulative P1 v25 establishes 15,991/16,320 facts and leaves 329 facts / 313
documents (263 distribution, 50 other); 1,942 official substitutions.
Manifest `04cc6edc70787f8ec17f6877ce2db480147b62ee066fb9324d9a680276e995d3`.
No new economic event or Full Dataset was accepted.

## 2026-09-18 SSE-composite official issuer cash receipts

Eleven accepted SSE-table/CNINFO-composite cash events were cross-checked
against unique retained final issuer PDFs. Each original source amount and
record/ex-date matches the accepted event and official exchange target; the
2020 special-dividend slash-date table needed a narrow header variant in the
existing date parser. Previous 226 closures remain byte-for-byte identical.
Source v8 closes 237/270 candidates, 33 rejected; manifest
`1a3246c76ec777da95e91c4ebec4413a8fb4d10844373edf79a72e829c9f17a8`.
Cumulative P1 v23 establishes 15,978/16,320 facts; 342 facts / 326 documents
remain, including 263 distribution notices and 63 other documents. Official
substitutions total 1,929; manifest
`abc8888f39801cbe3fe47aae0d297e3869202bc7e510712e39b8bd5bf0c1da54`.
No new economic event or Full Dataset was created.

## 2026-09-18 differentiated-public-A official cash receipts

Six existing differentiated-public-A cash events are corroborated by the same
retained final issuer notices, exact holder-specific gross payout, issuer
entitlement dates and official exchange targets. No event or holder policy was
invented. Source v7 closes 226/259; 33 candidates remain explicit. Manifest
`8edb4a40f7c53aaebc83e346c7765ea60845221c913a75373c5753dc1063a8c7`.
Cumulative P1 v22 establishes 15,967/16,320 facts, leaving 353 facts / 337
documents, including 263 retained distribution PDFs requiring separate
corporate-action classification. Manifest
`be12aaf8a9c6c5e038dc6e22740b8686bcb738b155159c4ea2e100ba56730cf1`.

## 2026-09-18 historical-code official cash receipts

Six 601360 stable-ID P1 requests are supported by the issuer's historical
601313 implementation notices and the official point-in-time code-transition
receipt. All six have exact issuer cash and entitlement dates, accepted event
checksums and official exchange corroboration. Source v6 closes 220/253;
33 remain explicit (15 title/master, eight date, four amount, six nonunique
gross-cash). Manifest `d125a9d83737bf6251efbb3c82148a819378c7e0e89db9be374db46fce20d095`.
Cumulative P1 v21 leaves 359 facts / 343 documents, with 15,961/16,320
established and 1,912 substitutions. Manifest
`1a9987a52b879be1b6338e252e5d5cbc21d77cb7212152eb592b09fbf000e0c3`.
All 634 database-independent backend tests, Ruff, formatting and input-order
checks pass. Database-backed tests remain unrun locally until Docker recovers.
The current Windows Docker Desktop processes started after reboot but the
Linux engine pipe and WSL CLI integration remained absent. A non-destructive
`com.docker.service` start returned `Cannot open ... service`; no reset,
volume deletion or database mutation was attempted.

## 2026-09-17 retained official full-cash source closure

Original retained official issuer PDFs, text hashes and source-manifest hashes
closed 214 URL-less P1 final cash fact requests against unique accepted cash
events and independent official exchange targets. The scoped final-title
extension permits clear implementation or actual-payout variants, never
proposals, board resolutions or tips. Sixty-three source PDFs label the
correct month-days with a year before publication; the exact effective dates
come from official exchange targets, not an inferred issuer year. All 253
candidates are partitioned: 214 closed, 39 rejected (21 title/master
unmatched, eight date conflicts, four amount conflicts, six nonunique gross
cash terms). Source v4 manifest
`83551f6d84c11db717f88c134347b9dfc039b75d19d05e90889a0e263ba90e5e`.
P1 v19 leaves 365 facts / 349 documents (263 distribution, 86 other),
with 15,955 facts established and 1,906 substitutions. Manifest
`ab39ff3a3acdf8c61b2cb07651fcda472d37fdb363a8aaafeec1a29335ea8d97`.
All 633 database-independent backend tests pass. The full suite cannot pass
locally while PostgreSQL at `127.0.0.1:5432` refuses connections; Docker
recovery remains deferred and separate from research-source acceptance.
No new economic event, Full Dataset, freeze or research study followed.

## 2026-09-17 historical derivative-reference scope

Four additional retained official derivative/employee-plan notices are linked
to unique accepted final issuer distributions without becoming new events.
Older cash references require the exact distribution year in the notice and
final implementation title; the convertible-pause notice uses the existing
bounded forward window. Source bytes and text checksums pass. Derivative scope
v3 closes 15 notices; manifest
`832e9c7d9643ba231eeb7c51d9151c3039673f472607dcc80deb01593935abcd`.
P1 cumulative v15 leaves 579 facts / 563 documents (263 distribution, 300
other); 15,741/16,320 are established, with 1,692 substitutions. Manifest
`ea29e9ddc363f4f7a652487de22815b51f0e49d7d0439d3930a34e774501e931`.
No Full Dataset, freeze or strategy study follows this partial closure.

## 2026-09-17 buyback-notice wording closure

Three previously unmatched official notices about adjusting a share-repurchase
price cap after a dividend are non-primary cash records. The accepted final
issuer notices uniquely corroborate issuer, exact gross amount and dates;
source PDF and text checksums pass. Derivative scope v2 closes 11 notices in
total, manifest `f6be92067cd621017bb93441118e4bd1b4b763d1bd0007e23068b65283ac9fd7`.
P1 cumulative v14 leaves 583 facts / 567 documents (267 distribution, 300
other), with 15,737/16,320 established and 1,692 official substitutions.
Manifest `aaab2b753fe70f6b2aafdbfce6bb4e920e50e4397c422150fd06432630bf8b19`.
No new economic event or Full Dataset was created.

## 2026-09-17 nonfinal official cash proposal closure

Seven more P1 notices with undated tentative gross-cash amounts are closed as
nonfinal, not as economic events: each source has contingent implementation
language and an exact unique later official final issuer event. Original PDFs,
text checksums and accepted final event checksums were verified; reverse input
order passed. Proposal scope v3 closes 19 documents total; manifest
`8d259671fa7ec84ebf0e2de53451e3db5e989d456786082d07e7d1171f9820a9`.
P1 cumulative v13 now leaves 586 missing facts / 570 documents of 16,320
raw requirements; 15,734 are established or out of scope, with 1,692 official
substitutions. Cumulative manifest
`eeaa54e9616416d443705bb0184c7cb8ce445c702fb188516941936fe5b9835a`.
No new economic event, Full Dataset, freeze, or strategy run followed.

## 2026-09-17 retained bonus source-replay correction

Official 601558 issuer text confirms per-share bonus/transfer ratios at both
the 2011-06-07 and 2012-06-26 ex-dates. Two generic extraction defects were
corrected without a symbol-specific production rule. Replaying the complete
bounded subset now yields 276/288 supported, 12 unresolved, and preserves all
274 previously accepted event keys and checksums. Reverse input order and
canonical bytes match (ledger v19 SHA-256
`acdfbc219cb826471769ea229482f8ada4eb9b728d50f0905cf8d66c69f29edb`,
manifest `edacba885961547fb484a20a82dd2e6e635e6df5e00c16f568ad9f77a3161788`).
The full 7,407-row oracle remains PARTIAL; P1 stays at 593 missing facts,
SZSE exact resumption at 1,921, and full issuer cash census PARTIAL. CI for
the preceding cash-precision milestone passed backend/compose/frontend.
No Full Dataset was created, audited, frozen or used for strategy research.

## 2026-09-17 retained official issuer precision and current R5 gate

Fresh source replay restored all 32 old 2016 cash events previously missed by
raw parsing; 2016 now has 1,872 source-supported events versus 1,784 in the
old year replay. The complete cash ledger already contained those exchange
events, so this did not raise its event count. The 2018 diagnostic's old-prior
guard remained fail-closed on the real 300387 0.11 versus 0.1100224 precision
discrepancy. A deterministic full-ledger supersession, with original PDFs,
extraction checksums and date/amount reparse, corrected that event and 22
other rounded amounts. Cash v43 has 40,479 accepted events, 40,376/40,376
exchange target coverage, 103 issuer-only events, zero exchange gaps,
input-order PASS and checksum PASS. Its SHA-256 is
`ac2e996fcd8b9e20578e1b8ea08f6725e545bec8b6cb7152c0119b1bcbb3e191`;
manifest `e95886c38a38deca04f3d530f3a93a2e132156f670f5b6b17df8e3040b547cb8`.
Full issuer notice/corporate-action census is still PARTIAL. The retained
bonus subset is 274/288, with 7,119 oracle rows outside it; P1 still has 593
facts / 577 documents, and SZSE has 1,921 exact resumption boundaries open.
No Full Dataset was created, audited, frozen or used for any study. PR #12
remains open.

## 2026-09-17 retained integer-bonus source reconciliation

Existing retained official source receipts, exchange ratio oracle and
effective-dated master establish 20 additional exact integer/next-session
bonus events. The 254 preexisting event checksums did not change; the new
ledger has 274 accepted / 14 unresolved of 288 candidates. Reversing all
date-link inputs reproduces file SHA-256
`f8bc4b47c0df4f13ed23ceefd2ed1d1666f0c9b726318d2e83a9d905a34ea76b`.
The two absent PDF sources have exact official SSE catalog leads, but each
download returned `ACCESS_DENIED_STOP`; no source terms were inferred from a
title. Retrieval receipts remain under `bonus-targeted-source-recovery-v1`.
`HUMAN_SOURCE_INPUT_REQUIRED=YES` for authentic copies of
`603315_20160601_1.pdf` and `603889_20160412_1.pdf`, or equivalent official
implementation evidence. Other P1, cash, SZSE suspension and fractional-bonus
gaps remain partial; no Full Dataset is created or frozen.
The shared date-label parser recovered 849 additional official links across
2011–2022, with zero old matches lost. The 2016 gross-cash diagnostic moved
from 1,786 to 1,827 accepted on fresh parsing, but the preservation guard
initially blocked replacement of 35 old events. Three are now explicitly
classified A/H date-only tips with matching final implementation notices;
the remaining 32 were already absent from an old-link fresh parse. Cash v41
is not superseded; no new cash event is accepted on this basis.
No fraction, nonstandard entitlement or missing issuer source was accepted.
The wider bonus census, P1 fact closure and Full Dataset remain incomplete.

## 2026-09-17 non-primary derivative source scope

Eight official notices about convertible conversion pauses/prices, employee
option exercise prices or repurchase limits quote the same gross cash as a
unique accepted issuer implementation event, but provide no independent
entitlement date. Original PDF SHA-256 and cached-text SHA-256 are verified;
accepted-event checksum and primary source URL are recorded per document.
These are non-primary derivative facts, not an authority substitution or new
ordinary-A cash event. Four unmatched/conflicting derivative notices remain.
Report SHA-256 `f9a8830ebbaedc267e00d4253c286086bbe255a8e92055a4e92f9f0625331cee`,
manifest `0b807f1ae4529416b99589b20256801ae9142d474602bf6b2845f84b2a0fc848`.
Cumulative v12 SHA-256
`76b5e5a492164ece79323002da9f6114a0b26200ecb6eb20a023b6603ab85649`,
manifest `f69bf64aec243e9c91387e4b2b9913093eb5887d7d9f7dcc769a156347e21f91`:
593 facts / 577 documents remain. Input order and checksum PASS; no Full
Dataset, freeze or study.

## 2026-09-17 exact issuer A-share gross cash replacement

Four SHA-verified, pre-record official CNINFO implementation PDFs separately
state a unique A-share headline and identical final gross-cash body amount,
with matching official record/ex-dates and no accepted bonus leg. The exact
0.16502, 0.19006, 0.24014 (600459) and 0.07471 (603200) amounts supersede
four rounded SSE-table cells with checksum-bound old-event references.
Source report SHA-256
`7cbb62c819804e12d08d06eebec291f2cf0991836c6b6a248fff0eee90a24b79`,
manifest `de97170d183b81f349a99e8ed2a724d96d7ed6b49a5c447f5c90140fd6542737`.
Cash v41 SHA-256 `edc51e1f5da16efe2d4a52454a102ba9501921d13bcb990ffedeabda424a773a`,
manifest `8b35132432a3ca6400eb401ce9a7dc34a907ca0c3dfa9da7230b34608df33073`:
40,479 accepted events, 40,376/40,376 exchange targets, no duplicate dates,
checksum and input-order PASS. Cumulative P1 v11 SHA-256
`7b51b3409c93a4a17c83e644e2575290b06f7a2979b7bbafee5374d7ab8ba9ea`,
manifest `3453857f0e7a1a85285720449ffc4991800349eaaa50100edc951158c8313e85`:
601 facts / 585 documents unresolved. Full issuer cash census remains PARTIAL;
no dataset or study.

## 2026-09-17 exact-date orphan cash replay

The common official-source composite classifier previously rejected exact
issuer and exchange record/ex-date pairs for ordinary cash, despite accepting
that same case for differentiated cash. Three 600705 original implementation
notices have exact issuer/exchange dates, gross 0.07/0.07/0.086 per share,
published before entitlement. A full checksum-verified replay also resolves
688388's issuer date set via the official exchange target. No event was added.
Composite v10 file SHA-256
`a294a26eb846101957ca1be4b8d3bfc78dd9354b2ed0984ab2a685b27942e3d2`,
manifest `23daf8481aeae8de4dba09986c7f22a7aea90e56ffeac1dfd475461110ffdba0`;
1,080 closed, 76 rejected, input-order/checksum PASS. Cumulative v10 file
SHA-256 `3334df807a0a2cf7dcd6e2b89575721f0b68b4d5abcca6805b49362c4bb52d1e`,
manifest `b5ab47e0a99f4617a23dda4c798a620beb3332f3c9edfba2a4d9235b0773956a`;
605 facts / 589 documents remain. Dataset gates unchanged.

## 2026-09-17 nonfinal issuer proposal scope

Twelve official proposal/authorization documents have no final executable
cash or bonus ratio, record date or ex-date, and explicitly reserve terms for
future approval. Original PDF bytes, cached text and source manifests are
SHA-256 checked, then terms reparsed; input-order replay passes. Cash-bearing
or instrument-ambiguous proposals are retained unresolved. Report v2 SHA-256
`1f2ef146a8c03f334a9547bf4b4bfc35da72cc4fa0922477080b601697762997`,
manifest `33dc149fac61d102ae0820c3b33bf9739c63672e2bd74fd88173e48534dc66b6`.
Eleven-report cumulative v9 SHA-256
`8bbed1f222e5bb170f6e0c700724cccd45a129bed34ce0011a6bab07ec9f5256`,
manifest `f8044228720156d103e6e8f351d1751339c3abe5fad60d59dbeb0031a51164db`:
15,711/16,320 established or out of scope, 1,684 official substitutions,
609 facts / 593 documents unresolved (289 distribution, 304 other). This is
scope closure only; no event, dataset publication, freeze or study.

## 2026-09-17 301262 bounded official evidence recovery

Windows-side official CNINFO retrieval recovered the 189-page 2023 annual
report (published 2024-04-26, PDF SHA-256
`63c5b7258c4355c6219300d8dfc1a103519bc7bcfcf43c758f4bc8b4e4491144`).
Page 45 independently confirms the 2023-10-30 record and 2023-10-31 ex-date,
but only retrospectively. An official CNINFO issuer announcement query for
2023-10-24–2023-12-31 has six results and no correction to the original
misprinted ex-date; response SHA-256
`b6277239a95aab132fc72a73e95164a3ce1f85ffe1d31ab3eefd18ba4efbf14e`.
The contemporaneous 2023-10-27 Q3 report (PDF SHA-256
`815338812cb9381cfb4e668a080838ef4fa6eb0f8ce6a3192ff701c5bab6a30b`)
does not establish the date. Source receipts and UTC times remain outside Git
at `/home/yuchen/data/research/staging/p1-301262-annual-evidence-v1/`.
The 301262 cash event remains UNACCEPTED; no inference from a malformed date
or a post-event source, no P1 closure claim, no change to cash v40 or full
dataset gates. Independent R5 source work continues.

## 2026-09-17 003041 bonus false-positive correction

Retained issuer original PDF SHA-256
`81a580bf7b2c76999c9a75432c3425a2e55b5b643f7ec28925f3cac3d782ab70`
and correction SHA-256
`273e2deb2e394d15176aae036f45b3f695ef9129d0d972388cf9911f7c98a27a`
were compared before/after publication on 2024-05-29/30, before record
2024-06-04. The correction deletes only “每10股转增2股”; gross cash 0.4/share
and ex-date 2024-06-05 remain the existing accepted event. No bonus event
was created. Correction v5 manifest
`295259b4bd4e7e209dfd92c670484953f4b58ea27f46d29c549ed99413dcab9c`;
cumulative v7 manifest
`8b166012a405f99c0f2da303000d0bc36a521a5feda216187e7356df95d17ec4`.
P1 remains 621 facts / 605 documents (301 distribution, 304 other), with
15,699/16,320 established/out of scope and 1,684 substitutions.
Actual 301106 4-for-10 conversion is not closed by this cash-only correction;
full corporate-action census/accounting still PARTIAL. No dataset or studies.

## 2026-09-17 revised differentiated issuer cash cross-check

Retained 603506 and 600837 official “修订版” implementation PDFs uniquely
corroborate the existing ordinary-A cash amount and entitlement dates, with no
bonus leg and no new event. Revised notices are rejected as new-event sources
unless separately reviewed. The 37-source differentiated replay v7 adds two
exact accepted-event matches and leaves all other classifications unchanged
(manifest `dc79e47128618c4c5e064ae5f9ab2d06bab8c8ff2ad67d41800916442783b3b3`,
file SHA-256 `e7d24161c0e9dcfdd0d5359f51a78ebadbde9fd8c9e7370fd8d2e4c044539eb1`).
Cumulative v6 leaves 622 P1 facts / 606 documents (302 distribution,
304 other), with 15,698/16,320 established/out of scope and 1,683
substitutions (manifest `5042155dd92d723e67ff45f8f6543152391104e376241847dd30f0affd036469`,
file SHA-256 `4fb8de9aa946f14f0e31d818495f112baffdb050a5c68a203d129b8374bceda4`).
Input-order reproducibility and checksum repeatability pass. No Full Dataset,
freeze or study; cash full census is still PARTIAL.

## 2026-09-17 official correction source replay

Four retained issuer correction/supplement PDFs and their original accepted
notices were checksum-verified. One share-count-only supplement (002026) and
three payment-date-only corrections (300800, 002895, 002812) leave the accepted
gross per-share cash and entitlement dates unchanged. No economic event was
created. The correction manifest is
`b5d45da39b0874594b8871146b9fdaa90633b03baa5e4fefc1d37b62511b7aa0`
(file SHA-256 `fdc1ad5584bbee6173149ea36a673c42f69c8d558c4a3b01fa40706d4cd62d66`).
Ten-report disjoint P1 replay v5 closes 1,970 baseline fact requests and
leaves 624 facts / 608 documents (304 distribution, 304 other), with
15,696/16,320 established/out of scope and 1,683 official substitutions.
Its manifest is `6a18008cb6414714ce5201a9375ffe06c09a8716341a84830445c3a8222643d0`
(file SHA-256 `5efa63fd01c24e6dc19fec06c90a2d0bc28a248e7e8fa90d8942184878e113ea`);
input-order replay and repeat manifest checks pass. This is not a bonus
reconciliation; 301106/003041 corrections change bonus facts and remain open.
Full cash census remains PARTIAL. No Full Dataset, freeze or study.

## 2026-09-17 additional official issuer cash event

The retained 002852 2023-11-17 primary implementation notice uniquely
establishes record 2023-11-24, ex 2023-11-27 and gross ordinary-A cash
0.22/share. Its SHA-verified PDF is accepted as one newly absent event by
primary ledger v4 (108 notices, 102 missing-census additions, six precise
corrections; manifest `142a427e3c2bcf7c31f0577f379bea278bd3b06973577bf9fb4045bf9f66b7d9`).
Cash replay v40 has 40,479 events and 40,376/40,376 exchange targets covered,
103 issuer-only additions, checksum/order PASS (manifest
`187938f5ad214c9d8ad0e9620ed74a03df8171df505a7bda47febbec65897abb`).
Full issuer census is not certified. P1 cumulative v4: 628 residual facts /
612 documents, including 308 retained distribution PDFs and 304 others;
manifest `f1f66d06b7333b2a8e48a351536f7bd2f69336f7c3fb8beb58cc416010125b87`.
Repository-wide Ruff/check and Ruff-format pass. Local full backend pytest
reached 619 passing tests, 62 setup errors and one golden-path failure, all
at PostgreSQL `127.0.0.1:5432` connection refused; no test assertion
regression was demonstrated. The focused parser/source tests pass and the
current PR's prior CI run was green. `docker info` in this Ubuntu WSL distro
currently reports that `docker` is not installed and recommends enabling
Docker Desktop WSL integration. Docker is a separate nonblocking recovery
item before final release; no reset or deletion was attempted.
Separately, 301262's official 2023-10-24 PDF visibly misprints its ex-date;
a later annual report is an official corroboration lead but its bytes are not
locally verifiable yet (CNINFO HTTP 403; issuer-host timeout). No 301262 event
was added. Dataset, freeze and studies remain locked.

## 2026-09-17 shared cash-table date replay

The common official issuer-date parser was fixed for unlabelled SSE
three-/four-column schedules and B-share guarding; 29 parser/probe tests
passed. A full 625-document triage replay changed ten date classifications:
eight already closed by the differentiated cash report, one exact existing
688533 cash event and one fully post-2025 688059 event. Matched primary
notices rise 39→40 (11 exact, 29 substitutions); out-of-period primary
notices rise 23→24. The two 2025-12-31 record-date cases stay open. No
economic event was added or overwritten. Cumulative closure v3 has
1,965 disjoint facts/documents closed and 629 facts / 613 documents remaining
(309 distribution, 304 other); 15,691/16,320 P1 facts established/out of
scope. Manifest `487c2f52fbc55668892a5be4f7bbb25d00f9f2e4c0a182b5badb981b6e86759d`
(file SHA-256 `8df78d53961fa3ea4367b3ab186e9c705a0c0c0d2b08194a1d1e3df721a7b5cd`).
Cash full census remains PARTIAL; SZSE exact resumption residual remains
1,921. Full dataset, freeze and all studies remain locked.

## 2026-09-17 differentiated issuer cross-check

Official SHA-verified retained issuer PDFs were compared to immutable cash v39.
The four-column STAR date-table parser now handles the two combined cash/bonus
notices without date inference. Of 37 candidates: eight exact accepted-event
matches, one earlier 688320 cash amount superseded by the issuer's official
pre-record corrected implementation notice, three post-2025 entitlement
chains, 22 without final cash terms, and three non-primary documents. Seven
exact matches are new P1 fact closures; 600157 was counted in v39 already.
The 688320 correction closes one P1 requirement by official substitution,
without replacing the accepted 0.11038/share event with the earlier 0.11.
Cross-check manifest `008648c4c7c55a0abc0eb775f19ac16b8683b88bc780006240a587ee6f00f620`
(file SHA-256 `294303d16f25534da4301e0f20447b3b1075ee26fe9c9b9ae53cc6d37d948e1c`),
input-order and repeat checksum PASS. A nine-report disjoint-set recount
also catches three earlier omitted post-2025 scope closures. Authoritative P1
residual: 631 facts / 615 documents, 311 retained distribution PDFs and 304
other documents; 15,689/16,320 established/out of scope, 1,679 substitutions.
Cumulative manifest `1f0f42e908b70ed71f059e0d22fa535aff0e20e3b914aa1279e3f8ebd85be59e`
(file SHA-256 `3a586dbe403cbba7f64e06340699b367802f85074a6363f43a7bfc965d9a9d26`),
reverse input and repeat checksum PASS. Cash full census remains PARTIAL; SZSE
resumption residual remains 1,921. No research dataset/study or freeze.

## 2026-09-16 differentiated public-A cash correction

The existing approved differentiated-cash parser reviewed 37 retained P1
issuer notices under immutable original PDF/text checks. Exactly one new
ordinary-A cash event passed strict final-title, unique issuer dates,
pre-record publication and point-in-time master checks: 600157 record
2024-08-23, ex 2024-08-26, actual cash 0.00555/share. The same notice's
0.00551/share diluted value is an ex-price reference, not a holder payout.
Classification manifest `2ff343d68a7edc5638fd1fa6a6ab7d7dfb95623911148f755ceb57254556c7bb`
(file SHA-256 `3fde9e305d23c35f85b6ac4b8ba709f4e973670cd0606b1b8efd64ced7b9f296`).
Cash v39 replay accepts 40,478 events, covers all 40,376 official exchange
targets, retains 102 issuer-only additions separately, and has zero duplicate
accepted dates, checksum and reverse-order PASS (manifest
`00e2780d2777904e4ebaf4c21667203e9e8cce397b93ebca6e2e71290b3ac2a8`,
file SHA-256 `750a18877cabd5d071a5f97390c285b00e3fe16f70df1f00ad7985347da7c5ea`).
Three differentiated final notices with both record and ex-dates in January
2026 were explicitly excluded from the 2010–2025 dataset window. They are
disjoint from the earlier 23 out-of-period notices, one P1 fact each. This
does not exclude either 2025-12-31 record-date case. Full issuer cash census
remains PARTIAL. P1 15,678/16,320 established or out of scope, 642 residual
facts / 626 documents (322 retained distribution docs).
P0/ST and the 1,921 unresolved SZSE resumption boundaries are unchanged.
Full Dataset, freeze and all studies remain unrun; PR #12 stays open.

The 22 differentiated final notices rejected as cash events were then
cross-checked against original SHA-verified issuer PDF text and official SSE
bonus source rows. All 22 have matching pre-record issuer dates and exact
ratios with unique ordinary-A master identity. Twenty explicitly state no
cash; two have a cash leg not yet established. Twenty-one are capital-reserve
conversions; 688466 is a red-stock dividend with tax terms that must not be
silently modeled as tax-free capital reserve. No economic bonus action or P1
closure was claimed. Evidence manifest
`e3169ff82117534bfcaa03870966433c16261580c41a9409ce3941b54eed1f25`
(file SHA-256 `ad634eedf842e044923f7ff40687a338f108771359cf2ab5684b998fc2883725`);
input-order reverse replay was not run for this diagnostic report.

## 2026-09-16 official P1 counterexamples and day-91–180 SZSE coverage

The prior cash v35 40,376/40,376 result remains a reproducible replay of its
input census, **not a complete ordinary-A cash authority**. An expanded strict
audit of retained primary implementation PDFs found 101 in-period SZSE cash
events absent on their ex-dates and six precise SSE issuer-amount conflicts,
alongside ten exact matches and 25 2026 out-of-period notices. Immutable
cross-check manifest: `d99465a98a534fd4449a6d89f0750bb7295ca2baf4781ca732fc585bc6f1c58f`.
The source PDFs are already retained; no commercial source or repeat acquisition
is needed. The SSE table-substitution code has a regression guard against
issuer/table amount disagreement. An official-primary ledger independently
validated and accepted the 101 absent events and six precise issuer replacements
(manifest `67ee85513cc2a83e2d4a1929ff03555b15b6ef71edf02b303abe19772d1fcb7c`).
The v37 replay now has 40,477 events, 40,376 exchange-census targets covered,
101 issuer-only additions, zero duplicate accepted dates, and checksum/order PASS
(manifest `0928e86d1dd208f6796b31be98ede517ce9724a27eaf8f1df8f00cb421c5f6b3`).
Replaying the SSE table-substitution path with exact issuer-amount checks exposed
15 additional table-rounding cases already present in official cached PDFs.
All 15 matched exact issuer record/ex dates and were replaced in v38, which still
contains 40,477 events (21 precise replacements total; manifest
`5ff94f3178d874abcb02017476adbe2f781ff48ebdcc7b78cad3e218b70e74a4`).
The repaired exchange census still does not prove a full issuer-source census.
An independent official-PDF instrument check classified 133 preferred-share
notices outside ordinary-A scope (manifest
`9d8b65e122f7bdce208605e7ef002be3b745c2dbffd3aa6123bd5dd53665c863`),
An exact official-source comparison then closed 39 more cash-only documents:
ten primary corroborations and 29 substitutions by stronger accepted official
issuer implementation notices (manifest
`1b85bbeaca6dd59292348055e2e02ef652b4a800a003cbbe08b0f55e2305be40`).
An additional checksum-verified date/scope audit excluded 23 primary cash
notices with both record and ex-dates after 2025; two 2025-12-31 record-date
notices remain open (manifest
`0f6188b41f08160572c8542642282f9ab67e2fda626d59d3a0d360c6ca621a4d`).
The provisional fact-level count is now 14,025/16,320 established or excluded
by scope; 2,295 facts / 2,279 unique documents remain, including 326
distribution documents at this step. A further source-hash and text-verified
substitution audit linked 512 URL-less cash requests to already retained final
CNINFO issuer notices with exact point-in-time identity, record/ex dates and
gross amount (manifest
`b668a82fa6313ae92af873c0efd63750925f9e2b815204c8340c9b39060f3cb3`).
The additional 002859 requirement uses an independent retained final issuer
notice instead of the accepted event's derivative bond-price adjustment source;
official PDF gross cash and both entitlement dates match exactly.
For another 917 URL-less cash requests, the official issuer PDF independently
establishes the exact gross amount and the accepted official exchange census
establishes missing record/ex dates; 116 issuer-date conflicts or multi-date
candidates were initially withheld. Fifty of those PDFs do contain the exact
dates among multiple extracted dates; an official exchange row uniquely
disambiguates them. Reusing the previously approved ordinary-public-A
differentiated-cash policy then closed 96 more notices (52 with exact issuer
dates and 44 with exchange-completed dates). Thirteen more exact gross terms
were selected from multi-amount issuer notices by the already existing parser
using official exchange amounts, with exact post-parse equality required.
The 1,076-document composite manifest is
`680fb5c58f672dcb24687247581bd482e0d215ee83d0093ac1d6393f496a9d31`.
Its rejected-candidate ledger retains 80 exact-source notices: 71 official
date conflicts, three nonunique cash terms, four issuer-header mismatches and
two invalid page sequences. These remain within the 646 unresolved facts.
An independent non-title SZSE resumption probe checked the first unresolved
event, 000516 at 2010-01-04 13:00. The retained official January SZSE table
has a blank resume field (SHA-256
`ff12178efac04b300ed3b19f6ce6c0125c6e938d46bced4110d2a9db6812b9f3`);
three exact CNINFO issuer notices published 2010-01-05 were retrieved and
text-checked (PDF SHA-256 `345d2c52d3d8f59fd715058691240a57c72081b64c76d2a274591d32dcf16427`,
`4ed43f959839382977fa78b9c0f6ae909103bda6df9feead1c50ade78c4daaf3`,
`2070812d6948063fa775671b7679d327e8bd6cf91d605ff704d94bcb8b414fec`).
None states an exact resumption boundary; later same-symbol suspension is not
treated as proof of this earlier resumption.
The accepted official SSE ST fact-set authority also closes 61 obsolete P1
ST-document requests (59 chain gaps and two legacy PDF mirror links) with
per-request mapping and no new ST event (manifest
`1b3cbf245ee1212499eec315a218cc1de182ee0a6514e3046653c7ad23d1ebc8`).
The current provisional P1 count is 15,674/16,320 established or out of scope;
1,678 are explicit official substitutions and 646 facts / 630 unique
documents remain. Three mixed notices have their
cash leg reconciled but their bonus leg remains pending. Cash full-census authority
and dependent P1 fact closure remain PARTIAL/provisional. P0/ST authorities remain
PASS; no dataset/study/freeze/merge was performed.

The retained-distribution bonus cross-check re-parsed SHA-verified issuer PDFs
and compared exact record/ex dates and ratios to the official SSE/SZSE source
oracle. Sixty pre-record implementation notices match with unique point-in-time
ordinary-A identities; three otherwise matching documents were published on or
after the record date and were not admitted as pre-event authority. Manifest
`dba59fcca0a03dddf19c6ab1744da3ab20affd356b917ccdc2a14ac19118426e`
(file SHA-256 `e75919ba1d93455350f602d5300f4bf653e806abd5447364a7ea1b4c26ac22b9`).
No bonus economic event was created, no P1 requirement counted closed, and
fractional allocation/tradability/cash-leg accounting remain separate R5 work.

Separately, all 949 applicable official CNINFO day-91–180 resumption metadata
windows were closed (18,129 records; zero query gaps; checksum/order PASS), with
closure manifest `d1c5cbc12b800334f948a0ae6c712d626287db8645833fb087cf8fc3d57ebc4f`.
A nonoverlapping 895-document PDF queue was fully acquired with zero failures
(source manifest `5eb282502d6a4b90dd3b5e1014ea0847481fad8ff4c5a289a8a552ebc34f4abb`).
Text indexing found 12 unique exact dates, ten of which bound new unresolved
events (reconciliation manifest
`4b08a511cdf652ac2c238ec6722451de01b6f4c6c8663d6950a1c90ce28bb3db`).
The complete authority replay now has SZSE 1,922 unresolved, zero conflicts,
8,883 supplements; SSE remains zero unresolved (manifest
`c88ce498b2c394023b2398282d944d087d508bea41d3a0f6cd71ebffbe021569`).
The day-181–270 official metadata extension closed all 659 applicable windows
after eight failed first-pass windows were retried in 104 seven-day slices:
12,523 official records, zero query gaps, checksum/order PASS (manifest
`2a6b17bcf9d0b6f406d9d4fe35c05bcdd961f12671e2fe1276dfb929b318c887`).
A disjoint 360-document priority batch completed with zero retrieval failures
(359 PDFs, one supported JS attachment; source manifest
`4bc8aa040a19f3c4627884f51bba2e837e23b9471705e80c3920ab197aa04b5a`).
Only one exact new resumption boundary was accepted by reverse-order full
replay, leaving SZSE 1,921 unresolved with zero conflicts (manifest
`f7cd758325d177e4c0a923938a90b193abaad18ef79cfab9bba2c8c16f67756a`).
The bounded day-271–360 official metadata extension then closed all 528
applicable windows after two 90-day failures and one seven-day HTTP 502 were
recovered in bounded retries. Its 9,280 official records have zero query gaps,
checksum and input-order PASS (manifest
`fbbd59452682fd3480a0f6ac7ad44fd0250d2fdacfcd89b2bc87fab5aceeceac`).
A disjoint 217-document title-priority batch completed with zero retrieval
failures (215 PDFs, two supported JS attachments; manifest
`74b11b9301c8d23ee214f390b19d14f0d185f9645d436d6f0d572a14bfbf2526`).
All PDFs were indexed, but exact-date review added zero boundaries. Full
reverse-order authority replay remains SZSE 1,921 unresolved, zero conflicts,
PARTIAL (manifest `81c8fab217945ffaf180560f4ad970790eff29382bd2a5cc9fb1ee57215fea33`).
Titles and metadata are not event facts.

## 2026-09-16 full cash acceptance and targeted SZSE suspension recovery

The full cash audit v35 accepted 40,376/40,376 official ordinary-A cash events,
with zero unresolved or accepted extras, checksum repeatability PASS and reverse
input order PASS. Canonical manifest SHA:
`679f003562068bbacbc7de884c522339d07313d77ed5c9df22c5e014f487b7fb`.
The P1 fact-level replay conservatively closes 12,965 open requests against
the same official cash-document URLs, checking publication date and the
effective-dated master identity. Established P1 facts are now 13,726/16,320;
2,594 facts / 2,578 unique documents remain unestablished, with zero new
source substitutions claimed. Canonical manifest SHA:
`ff54f0e67bce7331f02d8d29fae926b7900f695a696d45bf4851c62ebf0f9eda`.
The 625 unestablished cash-queue documents are all retained with checksum-valid
official bytes in existing P1 acquisition v10; none requires a new source
download merely to inspect it. Three later redundant official downloads were
byte-identical to the older smoke cache and did not change acceptance.
Diagnostic-only parsing of the 625 remaining documents found 303 cash-only, 92
bonus-only, ten mixed and 220 neither candidates (126 preferred markers). No
new economic event or source substitution was accepted: the 40 exact amount/date
overlaps include post-distribution price-adjustment notices that are not
equivalent to final implementation terms. Triage manifest:
`6c6ce88078e760787e341669fa192e398e14e5094879ff02c95c0b026791f361`.

The official suspension audit has SSE 16,393 events / zero unresolved and SZSE
22,077 events / 1,932 unresolved, with zero conflicts and 8,873 official document
supplements. Canonical manifest SHA:
`a4bd5b71700d5182e583812f2e0a32a21e89d0f6a63610586c77ae38dde259ae`.
The all-announcement CNINFO query completed 2,686/2,696 initial 14-day windows;
nine failed windows were closed in a new immutable retry batch, while unstable
pagination for 002665 was resolved by two disjoint seven-day official queries.
Its 34 announcement IDs are unique. The aggregate official-query closure audit
verifies all 2,696 original windows, 21,809 official records, zero unclosed
windows and source checksums (manifest
`1e8cd5c9c7965620008466bf990cc2ca6bcf47f22fabadb9ea36796a6884f760`).
This is metadata coverage, not resumption acceptance. The self-check result PDF provides an exact
2014-03-27 resumption; the suspension audit accepted that single boundary.
The 2,011-document first title queue completed with zero download failures and
315 newly bound exact resumptions (first-pass reconciliation manifest
`2092a8224da2a424542ba63c35b82b07049d5f8ec140d977e890f1d0bfd130f5`).
The disjoint 1,209-document second queue closed 354 more exact boundaries
(reconciliation manifest `4b00c2482e07c4c4ccbca0c1edeffc8c61e05fdbfd2e9ba3006081d0689e4534`).
One HTTP 502 was recovered with a one-document official retry; it established no
additional exact date. The source audit now actually replays both exchanges in
reverse input order. A nonoverlapping day-15–44 official metadata extension is
complete for all 2,022 applicable original windows, after a targeted 67-window
page-size-30 retry corrected the official API's repeated-page behavior. The
independent query-closure audit verifies 17,062 official records, zero unclosed
windows, checksums and input order (manifest
`f489b7ce45a97cbfcec8f3f5980cd298cd3c41ee7edb90f8d5240970134747b1`).
Title-priority PDF batches of 1,389 and 127 official leads added 29 and two
accepted exact dates respectively. One transient 502 was recovered and proved
to be a continuing-suspension notice. The day-45–90 targeted query closed all
1,278 applicable windows after three failures were recovered in 21 seven-day
queries, with 15,071 official metadata records and zero unclosed windows
(closure manifest `f5a4e5d43c0c2ee5a70cccf3722b461471ca3dc8cfff064a2115930f22152925`).
Ninety-two disjoint hearing/review-result official PDFs added 43 exact resumption
boundaries (38 + 5). The disjoint day-45–90 priority batch completed all 1,313
leads without retrieval failure (1,311 PDFs, two supported JS attachments),
adding 20 more exact boundaries. Its reconciliation manifest is
`b9b18a5fb44e2ef12d36d44c6c1483b433d2890bcc13c3e39f7a7289428a8f3a`.
The combined reverse-order authority audit accepted all 63 incremental
boundaries, leaving 1,932. Query and title coverage are not event acceptance.
Full dataset and research studies remain unstarted; no freeze or PR merge.

## 2026-09-16 full official SSE/SZSE ST authority closure

SSE is `PASS_PUBLIC_OFFICIAL_RECONSTRUCTION` for all 2,403 P0 identities. The
full public title census closes 6,724 leads and the selected-document corpus closes
1,580 documents with zero unresolved classifications. The 1,242 accepted official
events replay into 3,414 state intervals with zero chain gaps, conflicts, unmapped
events or UNKNOWN states. Authority manifest:
`0b11bd3fcf4f62b530a551365dfa974b7db3cef63156d5a311e0f714ae0b012f`.

SZSE is `PASS_PUBLIC_OFFICIAL_RECONSTRUCTION` for all 3,028 P0 identities. The
official dated abbreviation source yields 1,276 risk transitions; 836/836 prestart
members are independently corroborated. Replay covers 7,876,813 security-sessions
with no chain gap, lifecycle error, IPO conflict, UNKNOWN state or future leakage.
Authority manifest:
`8cb0c481cd8bd004dc689eee3370eb2fd9f592daec6ced717b40c45d1401c3a8`.

P1 official CNINFO acquisition remains the active workstream. No full dataset was
created, audited or frozen; no study or PR merge was run.

## 2026-09-15 free official P0 reconstruction and P1 scope reduction

P0 public reconstruction passes for SSE 2,403/2,403 and SZSE 3,028/3,028, with
no missing security, official conflict or true unresolved P0 fact. Annual official
yearbooks independently reproduce every year-end membership set after explicit
B-share alias and event-boundary classification. Survivorship, future IPO,
delisting retention, stable identity and reverse input order pass; 269 delisted
securities remain present. The immutable report canonical SHA is
`3b80a13fb816ce8b9f3442d57a4b84ae31f7616d7c89235cc6d98e12a8150faf8`;
the reconstructed master canonical SHA is
`c1a78056947232249fa4b139dd4d4ceb09636cd221863d7e64a0a56574ae1b48`.

P1 fact reassessment reduces 16,320 raw requirements to 15,559 material facts and
15,543 unique documents. Exactly 757 CNINFO documents are outside the accepted
ordinary-A master and four yearbook facts are already established; there is no
economic-term source substitution. The 13,590 in-scope CNINFO URLs are being
acquired through the existing bounded, resumable checksum pipeline. A standard
request header fixed the original public 403; a process-local stdlib DNS cache
fixed repeat resolution failure without changing the official domain or TLS.
Downloaded documents remain unaccepted leads until parsed and reconciled.

## 2026-09-15 P0 official access verification and P1 bulk plan

V2 file/canonical checksums pass. Exact P0 rows were preserved: complete 2010-2025
point-in-time SSE and SZSE listing/delisting/code/name/board histories. Public
current lists and annual books were not promoted to complete history. SSEInfo's
official product/application path was verified; it requires business application,
approval, agreement and delivered media. CNINFO package 98 was verified through its
normal browser: historical company/stock/name/listing-status APIs preview data, but
full export opens a login dialog and warns that paid downloads deduct fees. No form,
account or purchase action was submitted.

P1 was compressed operationally into five source-family collections. CNINFO package
11 explicitly supports one-day market queries, up to 20,000 records, `maxID` resume,
and returns official PDF addresses. The 16,320 back-references are 16,304 unique
documents after 16 duplicate requests. A local-archive URL/filename scan found seven
valid PDF/HTTP-200 receipt pairs missed by the V2 access label; their bytes and
receipts were copied to exact manifest destinations. P1 already-local=7 and
net-new=16,297. Report:
`.research/reports/r5-source-acquisition-p0-p1-v1.json`; plan:
`../research/P1_BULK_COLLECTION_PLAN_V1.md`.

P0 is still 0/2. The smallest blocker is authorized official full-export access,
not code or methodology. Full safe start remains unestablished and full dataset
CREATED/AUDITED/FROZEN=NO. Docker was not retried; it is deferred/non-blocking for
this source task. No studies, profitability inspection, PR merge or release.

## 2026-09-15 differentiated cash decision and source-input compression

The human-approved ordinary public A-share differentiated cash rule passes all 664
cached final implementation documents. Ledger v14 supports 24,306 events, leaves
3,541 unresolved and retains 83 quarantines. Its canonical SHA is
`91e9ff1d6f064eb5ca0bc3d1dd97fb3b041b74e112fe95d7b78c6d4766da289a`;
input-order replay and prior-event preservation pass.

The V2 minimal machine manifest maps 16,328 event requirements to 16,312 unique
official documents: P0=2, P1=16,304, P2=5, P3=1; 16,311 are material and 16,310
currently need user input. Canonical SHA
`96839c742cb12c9e0ea0c8301b990474554f64bfd2abf34579f8190b2e8017c7`.
R5 is blocked on source input only. Full safe start remains unestablished; full
dataset creation, audit and freeze remain NO. Development, Validation and Official
OOS remain NOT_RUN; PR #12 remains open and unmerged.

Docker recovery remains separate: after one safe Desktop start, Windows backend
processes existed but the `docker-desktop` WSL distribution stayed stopped and
Ubuntu exposed neither the Docker socket nor CLI. No destructive recovery or
repeated retry was attempted.

Focused cash/accounting tests: 32 PASS. Ruff, format and strict mypy PASS. The
full local backend run reached 552 PASS; one failure and 62 setup errors require
PostgreSQL at `127.0.0.1:5432` and are blocked by the separate Docker failure.

## 2026-09-15 final offline closure and consolidated source manifest

Cached cash replay v12 supports 23,642 events and leaves 4,205 unresolved; 83
historical records remain quarantined. The unresolved partition is 1,879 missing
source, 844 exact-authority conflicts and 1,482 parser/policy review. Ledger
canonical SHA `cb9164039dfb21bc1a1ab38bb158bfb1f826b8063fbd9f193c26f2fa1668220c`.
No tolerance or differentiated-distribution policy was added.

Bounded bonus ledger v8 supports 254 of 288 integer next-session candidates and
leaves 34 explicit: 16 missing linked sources, 14 parser/exact-term conflicts and
four nonstandard cases. Canonical SHA
`3815a14cc22c5a3a28291ce6ce6775aacfcdb6f8475be63ef3aaa2e2d31a7e6b`.

SSE parser v36 has 771 main plus 16 restoration provisional transitions, 786 main
parser plus four restoration unresolved and three metadata variants. Chain v26:
337 chains / 59 gaps / zero conflicts. All 771 main provisional terms reproduce
under the current parser. Canonical SHAs: parser
f8118dd2a6912067e40bf2d4158720c92efdeb036d5af2fdfdbe843d43cd3033,
chain 9006c5b9f99912ac45f5794c0329e66e2af11c875e4ce5a8370455ff1b2b977a,
integrity b9591e52257d076dffa4c0a60fa493e62f2a73ec4440d1a14d6b0e6aad27fd25.

All 69 cached merger leads received terminal classifications. Closure canonical
SHA `d78f13e3a1cf817a9e8ea2aaa7773ea758e3bc0251674124f5d8039703dd2cfb`:
34 supported-event evidence duplicates, 13 source-incomplete existing-chain leads,
nine source-incomplete new-chain leads, eight B-share-only parents and five
out-of-scope unlisted targets. No unsupported event was admitted.

The consolidated immutable `SOURCE_INPUT_REQUIREMENTS_V1` contains 16,328 exact
source items and 664 differentiated-distribution methodology items. Canonical SHA
`e20492797f1249ecf2dc8dd5ef8b06f252199df2883425dca4c82a1045365edc`; file SHA
`20dcd8d612927dc91080d91c55fe2ac1d7da110099f021900de19940eefcbf53`.
Former PID 434 remains absent and was not resumed or bypassed. Full dataset,
studies and freeze remain unchanged. Focused backend tests: 42 PASS; Ruff, format
and strict mypy PASS. The prior full local run remains 551 PASS / one failure / 62
errors, all service-dependent after PostgreSQL became unavailable. Frontend was not
rerun locally while Docker remains unavailable; CI is recorded after push.

## 2026-09-14 explicit bare risk-start labels and cached merger review

Cached correction notices 1203488074 (600877) and 1203476445 (600733) correct
the cited risk-trigger rules, not effective dates or name-transition clauses.
They do not resolve the original date/name gaps; no backdated event synthesized.

The exact bare field "退市风险警示起始日" and quoted "改为" verb retain all issuer,
date-conflict and name-pair checks. Parser v28 canonical
0cde9e3b73649d4530dcf784b92e30bc6a539a37cf46ad7b82750e83b0c6022e:
760 provisional / 817 parser unresolved / three metadata variants.
Chain v21 canonical 0ddfebc4f7709f6509c2062db3a5d08af592ffc51cf077467b5e194a81163ba4:
335 chains / 74 gaps / zero conflicts, input-order PASS, full acceptance zero.
Integrity v5 canonical fcb8645b65deabc60d552eb2a6fb96e3c998ad9425b5fc72015e48ae57e00a6d:
all 744 main-parser provisional records unchanged. 612 backend tests and all
quality checks PASS. No frozen Pilot authority altered.

Parallel read-only cached merger review found no new fractional allocation proof
for 600253 or 600631. SHA-verified 62552849, 62823703, 62559538, 59839566 and
59762741 corroborate ratios and halt/delist dates, not every registry/tradability
boundary or fraction treatment. No assumption fills those gaps. Cached metadata
identifies absent PDFs 62874558/62848719 and 59888838/59839426; these remain source
leads only. No download attempted against the denied endpoint, no accepted merger
event changed. Fifteen supported mergers remain a bounded subset, not a census.

## 2026-09-14 effective date inside exact name clause

Explicit embedded dates recover 600083 60902291 (2012-04-26), 600115 57998913
(2010-05-28), 600149 60724334 (2012-03-27), 600716 57760132 (2010-04-02).
The clause's own date is required; adjacent suspension dates are not substituted.
Wrong issuers and two conflicting embedded dates fail closed.
Parser v27 canonical 2b5f81c16f1baf222482341bfeb45ca5175556e775223515abb49ae9353f5e1d:
757 provisional / 820 parser unresolved / three metadata variants.
Chain v20 canonical 91468bf2c31f6a35f5e0fc7b0edb041efdfb848af69597e438a47bd3c1a0ef98:
334 chains, 76 gaps, zero conflicts, no full authority acceptance.
Integrity v4 canonical eabbb1a938d1eeddf5c603c45ffc8d08bc291f6d24fd6ee4dcaa402da9e10dfc:
all 741 main-parser events unchanged. 612 backend tests PASS; formatter applied
to a line-wrap-only difference, followed by quality checks. No source acquisition.

## 2026-09-14 space-delimited issuer code field

Retained notices print an exact six-digit security code after whitespace without
a colon. Accept that field separator, preserving digit boundaries and all issuer,
subject, name and effective-date checks. Wrong and seven-digit codes fail tests.
Parser v26 canonical ea3b7f79e9634741cde4781f8bcbfdb1f67875b7a928a4d472a57631e5a9462f:
753 provisional / 824 parser unresolved / three metadata variants.
Chain v19 canonical ccec8e8efdf82702b8a5aa88fe623fddce0eabf9fac800666147afa8595a5177:
332 chains / 78 gaps / zero conflicts, input-order PASS, accepted full events zero.
Integrity v3 canonical b285d60a6092efcc6379adf9803d524199b455e3d01049e4a4562372fa0be5fb:
737 main-parser provisional events retain unchanged terms. 611 backend tests PASS;
initial lint found only a long line, reformatted without semantic change.

## 2026-09-14 linked dates and provisional replay integrity

Parser report v25 canonical SHA
2192e63cf9c1683240ab73405918e180750193ba71b34fd5d85e4f6fba66b5ed:
752 provisional (736 main parser plus 16 restoration), 825 parser unresolved,
three metadata variants. Chain diagnostic v18 canonical SHA
64a07e1c200e21b21210e9a806b88eb48e1391a5c2aea54c2bb1ea856cb47aab:
332 chains, 79 gaps, zero conflicts; full authority acceptance remains zero.
Explicit linked dates are collected across name-clause variants; weekday conflicts
fail closed. Historical pairs are discarded only with their own explicit past
dates and one independently dated current pair; undated ambiguity remains blocked.

Integrity replay v1's 16 header/title discrepancies were audit extraction-selection
errors: those records bind alternate_extraction_sha256, not extraction_sha256.
Reusing the exact SHA-verified saved extraction resolves all 16 without relaxing
the parser. Immutable current-parser-integrity-v2.json reports all 736 main-parser
events with unchanged terms; canonical SHA
a428b57cadeddbd81b53b855ffb5f8be333a3efd0f539da39ad5d6235b3efe94.
The first report is retained, superseded only for extraction selection.
610 backend tests PASS; Ruff, formatting and mypy PASS. PID 434 remains suspended;
no source retries, full dataset publication, freeze, or strategy execution.

## 2026-09-14 short implementation headings fail closed

Inspection of 000723's 2010 notice established that its unqualified numbered
"权益分派方案" heading is the final implementation section. The earlier broad
heading experiment's revert is superseded: increased quarantine count is not a
reason to ignore a final section. Explicit "本次实施" headings take precedence;
otherwise a unique short implementation heading is required when present.
Unparseable section terms never fall back to the introductory proposal/summary.
The notice's gross-tax full stop is normalized without changing its amount.

Audit v7 of original 22,864 records: 22,768 unchanged / 96 quarantined.
Canonical ba48a88125402d4cec978566079fe5ef7793fff0b85e564b6e94723dd6cc7aaf;
revalidated subset v3 cc709a9bcb2ea453ed6e67983d8ad37cc069c2e4c8cb36233b2f63db4c6ac53c.
Thirteen source-input replays v2 produce 23,199 supported / 4,648 unresolved.
Combined cash-current-implementation-ledger-v2.json canonical SHA
1167033ec372bdb5860c3ba2365dd8cf8eaec8105716d286add1a1a2a5ee895b.
23,144 historical identities preserved; 96 quarantined with current evidence.
Versus combined v1: 57 additions (two reinstatements), 66 quarantine removals;
55 genuinely new identities. Restored 002737 2018 and 002810 2019 match current
section terms exactly. No conflicting candidate forced through. Reverse ordering
PASS; full dataset still uncreated. One replay launch waited on an unpublished
audit path and failed before writing; the corrected launch reused existing input
receipts. Consolidation completed without a duplicate writer; future reporting
uses a precomputed key set instead of repeated set construction.

## 2026-09-14 further dated SSE labels

Label variants and explicit suspension-then-effective-date fields recover nine
additional provisional events beyond v19. The suspension date is never used as
the warning start. Parser v21 canonical SHA
356507f2875c70a5f65619e8398362fb587743bb21d5730b39cc7d899df9ebaa;
chain v14 60e5b522f9fad9bf53e369e6d35f58f5effd7559676ecbd88a5740cebbd6f347.
731 provisional / 846 parser unresolved / three metadata variants; 327 chains,
83 gaps, zero conflicts. Full authority acceptance remains zero.
Cached gap queue v1 (based on earlier parser v20, not a completion assertion):
93 document leads, canonical 821277b4dbf1509f2170c04e0c31b1c7644161ed1bc9e72b026db5a5147fee31.
No denied-source acquisition, dataset publication, freeze or study execution.

## 2026-09-14 explicit legacy issuer-name labels

Two additional retained notices close provisional entry gaps: 600077 effective
2010-03-01 (57628128, PDF 60a5c4ae8cfdc5eabc851205847f5b8cbeaf6403a83f580fc54e8196b0d2aaa6)
and 600179 effective 2010-04-16 (57813819,
95a0505090e90a43384e743ae623c0604f2fdb9d935b588ce81f253ac08ba0f5).
Both two-page notices were read. New-name-only prose requires an adjacent exact
security code or the explicit issuer post-warning label, plus an independently
explicit effective date. Undated historical-name ordering supplies neither.
Parser v19 0bcca9b7b31449de0f00a87828dbd02733a73e8d5cd27104ace7925c30b5bb4c;
chain v12 b22e50ea46ba6f184d179b2dce0231b2da19e743c20aa3951755f43b4d8e76fa.
722 provisional / 855 parser unresolved / three metadata variants; 326 chains,
85 gaps, zero conflicts. Thirty-two focused ST tests PASS. No full acceptance.

## 2026-09-14 checksum-bound title reconciliation batch

Seven first-page title reviews reuse the existing checksum/announcement-bound
review mechanism; all three earlier reviews are preserved. Five more provisional
events parse (600696, 600702, 600781 twice, 603007); 600180 still needs an explicit
name chain, and 600239 retains conflicting printed 2020/2021 effective years.
No identity or date guard was relaxed. 600191's non-About filename title and
600733's pre-loss forecast remain outside this narrow title-review mechanism.
Parser v18 canonical SHA
9934aad3aaf7424281025df313f8b300a74418f2f0707367502acb3592ac725e;
chain v11 20429849b0271c37abf518bad51f2b4c40683fa29f8d80053dc173abeba12d68.
720 provisional, 857 parser unresolved, three metadata variants; 326 chains,
87 gaps, zero conflicts. Full-authority acceptance remains zero.
Backend 608 tests and lint/format/mypy PASS before this data-only review addition.
CI 34824298020 SUCCESS for 90c3863; PR12 OPEN, no merge or study execution.

## 2026-09-14 targeted cached chain-date closure

Cross-referencing 91 chain gaps with retained unresolved notices identified 111
candidate documents; source leads remain distinct from accepted transitions.
The directly linked date word "开始" adds five provisional transitions (600179,
600217, 600538, 600699, 600769); explicit dated removal of the issuer's own risk
treatment adds 600209. No publication-date substitution or conflicting-date
override is allowed. The 600198 notice has contradictory 2018/2019 printed dates
and remains unresolved; 600221's undated continuing warning also remains unresolved.
Parser v17 manifest 648b4fefd9ea954482cb4aa5b3b8ff7a2d0c8b1b9cf7dae8cea65876e63010b4;
chain v10 f9dc15931a9c411258fa1aea73ca59e6f216dcf3c3390505fd3dc5d330d9cf68.
715 provisional / 862 parser unresolved / three metadata variants; 326 chains,
91 gaps, zero conflicts. New evidence can expose additional missing chains; the
gap count is never a target to force downward. Full-authority acceptance remains
zero. All prior event records preserved by unresolved-only replay.

## 2026-09-14 cached SSE explicit-measures clause

CNINFO 59060232 (600083), both pages read, explicitly dates ST-to-*ST at
2011-03-02, separately from its 2011-03-01 suspension. Exact old-name syntax
"由原" and the directly linked "具体处理措施为" clause are now recognized.
PDF c00e0c91aa4164d9f481f6146e49023393295d445b45aa1da8a69c211a2c378b.
Wrong risk category/issuer and adjacent unrelated dates remain rejected.
Thirty ST tests PASS. Unresolved-only replay preserves all previous events:
709 provisional transitions, 868 parser unresolved, three metadata variants.
Parser manifest 4bee4340793840ccd215267a679598bdf2ef417889c32eb37cfa4484fde488ca;
chain diagnostic bca9dceb4b2a996cb0c20ef218237c1e79e0ea24491093ad6c09ec60be9a677e.
325 chains / 91 gaps / zero conflicts; accepted full-authority events remain zero.
Initial diagnostic command used a duplicated staging-directory prefix and exited
before publication; corrected root completed offline with deterministic ordering.

## 2026-09-14 complete cached cash input replay

Replayed all thirteen existing yearly cash input sets (2010-2021 and partial
2022), with zero prior-row shortcut and no acquisition. Source, extraction,
policy, lifecycle and exact exchange-amount guards remain active. Immutable
cash-current-implementation-replay-YYYY-v1.json files retain individual results.
Combined cash-current-implementation-ledger-v1.json supports 23,208 events;
376 newly reconciled, all 22,832 revalidated event identities preserved exactly.
The 32 quarantined prior events are disjoint from the new accepted set.
4,639 cash-term groups remain unresolved, not metadata-only or silently excluded.
Combined canonical SHA
0aea2a9f09b470f52169aebd420a34ddeb17ef96b23202d060d561f1fc075837.
Reverse input order, duplicate protection, model/policy and event checksum checks
PASS. This is a bounded ledger, not complete 2010-2025 coverage. All study/freeze
locks remain in force. Commit db74a25 CI 34823766586 SUCCESS; PR12 remains open.

## 2026-09-14 cached cash syntax and page-boundary revalidation

Integrity audit v6 revalidates 22,832 unchanged event identities and retains 32
quarantined records. Only complete, consistently formatted leading page-number
sequences are stripped; body digits and partial sequences are never deleted.
Explicit RMB without a redundant yuan suffix, gross-tax punctuation, and the
distribution verb are recognized without rounding or old-proposal fallback.
Audit canonical SHA f1a0d1be29a1b7a19bf4ce1d66a824b65d2c1f3faaa74fa0719814a204f040ee;
external cash-current-terms-revalidated-v2.json canonical SHA
2c57b57f927a564d62e2dec206f33e2fe3d72194f2d77ef706a7a86d5addad02.
Prior immutable audit and ledger versions remain available. These are bounded
revalidated candidates, not full corporate-action census acceptance.

A broader unqualified section-heading experiment increased review to 112 and
was reverted; its immutable audit v5 is diagnostic only. Manual inspection shows
002737 2018 contains unrelated historical dividends later in the same PDF;
300002 2015 and 300014 2017 have genuinely changed final per-share amounts.
No ambiguous record is readmitted by choosing the first/last number.
PID 434 remains suspended with receipts intact; no denied-source retries.
Full dataset uncreated/unfrozen and studies not run. Offline closure continues.

## 2026-09-14 proposal/current-implementation integrity audit

The explicit current-section parser found a genuine integrity reason to revisit
prior full-range cash candidates: 000555 2022 proposal 0.04 versus current
implementation 0.0403129. An accepted-prior gate correctly refused publication;
no final ledger was written by that failed command. This is not permission to
preserve erroneous cash merely for checksum continuity.

Offline audit of all 22,864 prior supported events: initial strict syntax left
83 review cases. Narrow RMB/gross-tax punctuation normalization revalidated 33 net
cases; final 22,814 unchanged / 50 quarantined. Two explicit amount differences
(300034 2020, 002973 2022); 48 current-section extraction/term gaps. No tolerance,
rounded table amount or old proposal fallback. Existing 2010-2014 counts unchanged.
Audit v2 226decc829844befdc37e42335805c14d941717ea598f40066d6292fdf581eb6;
revalidated subset 419b1c04183a27ad324187b0b068b401b60c494dd01f9de173f45f25537eca4e.
Old records remain immutable, with per-event quarantine reasons/source hashes.
Frozen Pilot v2 covers a different period and was not modified. No full dataset
or strategy run. This is an engineering/data-integrity correction, not a new
methodology approval or terminal stop. 607 backend tests / quality checks PASS.

The first audit launch stopped before output on a stable-ID/old-code alias lookup;
source URL plus record/ex dates correctly identifies the retained row without
rewriting stable identities. Corrected audit completed with duplicate guards.

## 2026-09-14 access-denial suspension and offline receipt preservation

Latest twenty main-worker receipts were HTTP 403 Forbidden, not transient DNS.
PID 434 suspended with SIGSTOP at 21,029 durable receipts; process preserved,
not killed. No automatic resume or alternate-host access-denial retry. A proposed
Windows DNS-only distribution queue failed its assertion when non-DNS failures
appeared; no queue or requests were created. Its attempted CLI launch exited for
missing queue before requests. Targeted Windows merger downloads preceded the
access-denial discovery. Runtime manifest
e69890ebeaa22b46b5dc92ef73c9290d91e97e39293b83153b13bf2a6cc4652b.

All 3,005 successful PDFs in partial 2022 v3 indexed; 576 failures and nineteen
uncompleted original leads remain explicit. Date links 2,541/3,404, zero parsing
or extraction gaps, SHA 8a013623175e7994d77bf2a220afa049855f2a547d312cf025c31b7aeca9072f.
Cash 2,181 supported / 1,174 unresolved. A supersession check detected one event
identity drift: 002950 selected its newly recovered earlier implementation rather
than the original correction notice. Economics were identical. Optional
accepted-prior reuse now requires fresh source/economic corroboration, checksum
validation and no duplicate keys; missing/conflicting prior events fail closed.
All original 1,478 event records are preserved in final partial v3 cash ledger v2;
intermediate v2/v3 ledger v1 snapshots are superseded, not additive.
Ledger 099582114271ea081508ad8f95fa95786aa354c868c9fc480f6b8def124758c3;
preservation audit eedd5c946ab9ae176abdb170c13ce4379308bcd5056fd953a760aa0744305831.
607 backend tests and Ruff/format/mypy PASS. CI 34820748059 passed for d4a5b75.
Full R5 closure remains incomplete; source-access suspension is not a freeze gate
or a claim that all independent offline work is exhausted.

## 2026-09-14 600591 source recovery and merger reconciliation

One bounded August 2009 issuer query returned five notices (complete response),
recovering official CNINFO 55643861: SHA
55d3d2db9f21eefc0c8b0f2eb70edb8be04f5931be028eb62a847582c08d2f49.
PDF page 29 explicitly ranks fractional remainders and uses computer lottery for
ties; no invented exchange-rule enum. Page 19 defines exchange day as registry
registration to holders; retained result 57556389 confirms completion 2010-01-28
and unrestricted new-share listing 2010-02-02. Original successor IPO 1997-11-05;
parent last trading 2010-01-11, suspension 2010-01-12, delisting 2010-01-25.
Ordinary unrestricted holder/no cash election only; 288,888,860 restricted shares
with 2012-06-25 listing remain distinct. Approved floor/basis policy unchanged.

WSL DNS failure preserved; Windows same-official-URL transport retained the PDF
and two previously unavailable older-merger documents, without overwriting failed
receipts. Extraction manifest 7d2bda915f502da30ba3144ed8d29553f3cb789757f73a1b52c5b7dab279b30e.
600253 prospectus and 600832 termination recovered but not accepted as closed
chains; referenced fractional rules and further boundaries still require review.
Two targeted raw controls corroborate dates, manifest
1fe4d8bb24f3cae0bf0b596fba595e47f8add39be12720dd5760a183e0b5c831.
600591 audit ef0c924421dcd1ebba2abdce214a2ae8880b3fde711ffd912c9e04e2fd69044b;
fixture SHA 6f655e4f5a981363629dbb609980d2bce180e1ed851167304f826bb9fc5f382e.
Inventory V7 fifteen supported / three reviewed unresolved, prior fourteen event
records preserved exactly; full market census unknown. 607 backend tests and
Ruff/format/mypy PASS. Original worker continues; no valid stop gate reached.

## 2026-09-14 cached SSE syntax and terminal recovery reconciliation

Parser v13 supports abbreviated name only directly after the matching security
code, plus explicit quoted name transition verb 变成. Identity, exact subject and
effective-date guards preserved. Three cached transitions newly provisional:
600069 2015-03-24, 600130 2012-07-17, 600365 2012-08-16. The separate 600069 bond
risk notice is not an A-share event. 600131 printed 2009/2010 date contradiction
remains unresolved; no silent correction. Full parser report v14 SHA
dae5500665aa468e48c42c9c21bdfa0f21577101befa41df3a11e0f82dbad6d6:
708 provisional / 869 parser unresolved / three metadata variants, accepted zero.
Chain diagnostic v7 SHA ad950a4161396b4dffaa55ac87d9ee070ab78cd2055e756234f64947e1fc7c1a:
325 chains / 91 gaps / zero conflicts, reverse-order PASS. Previous event records
preserved. 606 backend tests PASS; format corrected, Ruff/format/mypy PASS.

408-request terminal DNS recovery completed with 301 PASS / 107 temporary DNS
failures, all originals retained. Recovery manifest
2594b22b0e2e62279662e9ea887e002c5d93d04f16f1644ad95ff1d87a09be6e.
Partial 2022 snapshot v2 reuses the same 2,425 terminal requests, replacing only
failed entries with recovered bytes: 2,318 PASS / 107 unresolved, SHA
9829b3ce408fa267b90b2d2cec489369644131d006d34df90593088457c9dbcd.
Date links 1,941/3,404, zero parsing/extraction errors, SHA
a1ff2ef9f76f9206454a29fc215ea18f9e47dba063b9a68180dae486f9670617.
Cash 1,698 supported / 1,657 unresolved, unchanged parser, SHA
77a6df59758722c2f84c2a3459e4dd37b12049b2a1d20ba42218a3f9dfa0e01f.
This supersedes partial v1, not additive and not year/full-census acceptance.
Original PID 434 continues; no duplicate main-queue worker or research run.

## 2026-09-14 2025 and 000780 merger evidence closure

600837 to 601211 ratio 0.62, new-share boundary 2025-03-17; 601989 to
600150 ratio 0.1339, boundary 2025-09-16. Official parent implementation,
suspension and successor listing sources verified. Existing 601211 shares traded
before converted shares became tradable; original raw response retained and the
official new-share window separately filtered, never treating old shares as the
new entitlement. Two-event audit ebbd2af9c8d6b73008dbbd735b4eba726b985eba7508503e4632eced1202633d.
000780 to 001289 ratio 0.3407, record 2022-01-21, first ordinary-holder trading
2022-01-24; controller lockup separately identified. Audit
037f32be7e436a6244cb0f7147fca061b2a1677fab3e3fa1ff0ab52307f3b921.
Inventory V6 preserves eleven prior events; fourteen supported/four unresolved,
full market count unknown. 605 backend tests, Ruff/format/mypy PASS.

000578 targeted six-lead query complete, four implementation/correction PDFs
retained. Actual extra-share transfer delayed to 2011-03-09 from 2011-03-01;
ratio 2.071671 per ten, referenced CSDC fractional rules not reconciled. Extraction
d6772e6af1e94dc82facf8e474aaff36927f4abc5e3e4b6ea758e2c7f0fdfe5f.
002013 official account guide requires confirmation or assigned sell-only account
plus trading designation; no assumed account completion or unrestricted buy path.
Guide/boundary evidence df22bdfe8aaebafe71bcc30d8786295fedd1936f3025e27eb14f6e8f710e498a.

2022 live snapshot 2,425 receipts: 2,017 PASS indexed, 408 terminal DNS failures
(402 temporary resolution, six name/service unknown). Snapshot SHA
36758c1f00c18a02d2715a7de834c5ef6b0121d4ac022e7817166f17ea6be09d.
Separate failed-only queue SHA 844dce1a8e2cf5c9fae9d13cd3c7fd8ec96883d0a1f79eb869c1da54aa649bfb.
Initial recovery launch had no queue because the assertion recognized only one
DNS wording; it exited before issuing requests. Both DNS variants verified,
queue published, one valid recovery worker launched. Original receipts unchanged;
original downloader retains all remaining work. No year-completeness claim.

## 2026-09-14 two further supported mergers and explicit remaining chains

600317 to 601880: official ratio 1.5030, merger record 2021-01-28,
delisting 2021-01-29, unrestricted new-share boundary 2021-02-09.
600723 to 600859: official ratio 0.3058, merger record 2021-10-21,
delisting 2021-10-22, unrestricted new-share boundary 2021-11-02.
Both explicitly use global remainder ranking/random ties; approved floor and
zero-whole policies unchanged. Parent cash-option notices separately establish
last trading and continuous suspension, not merger record dates. Six targeted raw
controls corroborate dates; manifest 82335f430129fea3875c25e6c30ca9512bceef54bbf5d91803153e9a21482df8.
Audited two-event manifest 82c0c256e2aa767e811d2b49333123892b41944cc68b9141a956d000ce4728fb.
Inventory V5 preserves nine prior events: eleven supported, three reviewed
unresolved, full census unknown. 000578 ratio 1/2.90 and listing boundary verified,
but its additional pre-merger share transfer remains separately unresolved.
No complete-chain claim. Adapter now retains existing denominator/activation
fields. 602 backend tests, Ruff/format/mypy PASS. No strategy or publication.

## 2026-09-14 cross-exchange merger routing and retained evidence gaps

Parent/successor exchanges are now independently routed through event identity,
master validation and raw-boundary parsing. Legacy same-exchange event checksums
are preserved. Synthetic cross-exchange accounting regression passes; 599 backend
tests, Ruff, formatting and mypy PASS. No additional merger is accepted.

600591 prospectus 57457359 (2009-12-31), SHA
95e116eed63402e4a90068c5d5a51fc0e521f26d4ccdee1a3a16e2c392870c66,
states integer shares and residual treatment under SSE rules, not the explicit
global-allocation mechanism required by the current supported classification.
Cash-option record date must not be substituted for merger registration timing.
Termination notice SHA 517bcc60840f6dae7c8d1003224a276353892da66dd3fea1b620a1081cd835a3;
cash-option notice SHA 3d2d18890ce2863d71a00df5be68c439712edf2f874dca6ac60177de225de0be.
Same official URL retrieved through Windows after WSL DNS failure; both receipts
preserved under full-merger-v1/600591-boundary-recovery-v1. No guard relaxation.
000522/600332 retained listing notice makes trading dependent on account
registration; unconfirmed holders cannot be assumed tradable on listing day.
These gaps remain unresolved while independent R5 work continues. Original
distribution worker PID 434 remains alive; no duplicate worker launched.
No full dataset publication, freeze, strategy, merge or release.

## 2026-09-14 integer retained-bonus subset and historical fee evidence

288 candidates use integer ratios, already retained 2010–2021 issuer notices,
and a next-accepted-session scheduled new-share listing. 169 supported events
(159 ratio-one, ten ratio-two), 119 unresolved candidates; remaining 7,119 oracle
rows are deferred/outside this subset, not assumed absent or excluded.
Policy BASIS_CONSERVED_RETAINED_BONUS unchanged. Source/date/master/instrument
checks, exact official/exchange ratio agreement, event serialization and hashes
required. Cash components remain separately reconciled; no double-crediting.
Ledger v2 SHA bf1ac5428237ff2a4980242a02637e1940b741b50948f7b24f260512fc61b703;
v1 event checksums preserved, reverse date-link-file ordering/idempotent publication
reproduces v2. Accounting regressions cover both admitted ratios at precision 6/50,
integer quantity and aggregate-basis conservation, unchanged cash, no order events.
598 backend tests plus Ruff/format/mypy PASS. Full census/actual tradability NOT PASS.

CSRC 2012-08 bulletin PDF retained, SHA
b556e44b3784d03922c04cb5b77e9f5fcf9bbec9439b0e20ca9512f94c161bc2.
PDF page127 / printed114 visually reviewed because text extraction yields glyph
names. Article dated 2012-08-02, transition 2012-09-01. Printed transfer denominator
conflicts with face-value evidence; full investor fee/broker component/minimum
not established. Review SHA 16cb65e50bdf0fa5b71474c1f283c5bbadbf206216615ea03218c52b82f38767.
Two HTML retrieval failures preserved (DNS, HTTP403); no HTML retry. Separate annual
report timeout recovery returned non-PDF and is rejected, no further retry:
d9e4506d37357440c60016218a802e195b3fbd5adc4f792294bcd56b77528762.
No historical fee-model change, full dataset publication, strategy or merge.

## 2026-09-14 remaining restoration parser review

Coordinate extraction removes overprinted glyphs from 59806624 and 60050789
without changing source bytes; both now yield provisional dated STAR_ST-to-ST.
Optional A-share wording and explicit next-day phrases resolve three more
document records. 600633 normal relisting requires an explicit exchange approval
removing risk treatment; normal-looking names alone remain rejected.
Restoration v3: 16 provisional documents, four unresolved, SHA
8d366f27e5cf4de171ad38f4dc19da360a9feb17d809dba30631d109bbb4f021.
Full v12 preserves all prior records: 705 provisional / 872 parser unresolved /
three metadata variants, SHA 5d37f9da5cd7e09f821093fc1af0d1162db302d5530d744b92b1bf26c4ca2b38.
325 chains / 92 gaps, zero conflicts, reverse-order PASS; not full authority.
600057 PDF header visibly prints 600870 while body and official metadata say
600057. Header guard remains intact. Targeted original SSE mirror denied access;
no retry, manifest e83f6b5dae8dda6446aba118766c8d5f0c0b2b9b9f50187d899c13d1c3338428.
Windows-to-WSL hard-link publication is unsupported; alternate extraction was
published locally on Windows then imported with the existing WSL immutable writer.
No source overwrite or replacement fallback. 596 tests PASS; intentional fixture
punctuation lint annotation added. ed209a9 CI 34813352211 SUCCESS. Continue R5.

## 2026-09-14 2021 cash and restoration recovery completed

2021 snapshot 3,187 PASS / 18 DNS failures; all 18 recovered separately.
Reconciled 3,205-PDF manifest SHA
328436fd05258da983c276c4bf968bdd9780112981f0bbc3fcf5b3a0f17a7c2c.
Date links 2,859/3,139, four parsing errors, zero extraction gaps; SHA
24a5ab92080b5d7927d4b9d26e7040a1d2797c93362083899e8a5d03d7c6ef8c.
Cash 2,420 supported / 688 unresolved, ledger SHA
b022439bb1784333004eaaaa9126706d532ab4b58a0c749e3e850122e435f7bd.
Total twelve-year bounded cash 20,683/3,809; full census remains PARTIAL.
After confirmed DNS recovery, one missing-only SSE retry resolved 17 documents
across 16 failed issuer/days; three earlier cached matches retained. Recovery SHA
9ce1657ab1ec59758b880c75273d303be68ea4c4ca2c9ade1329924c3a12ad55.
Failed fetch metadata is retained as a gap, not opened as a nonexistent response;
regression covers this checkpoint recovery path. Original failures unchanged.
Narrow relisting parsing requires explicit dates and matching first-day NST/later
ST names. Ten provisional events; ten documents remain unresolved. Union SHA
5ac88e9c4f1d795f5223165fde392e1dc5116d9b513313f9a1c963e8f25b18cd;
all prior 689 event records preserved, total 699. Chain v3 has 324 chains, 95 gaps,
zero conflicts; SHA 884352702f607f6559cdbb0e6dfac276b2011b07247509fe62f99a44e954b2a7.
18 year-window Tencent controls returned target rows without duplicate dates;
outside-year rows require explicit filtering. Not accepted full raw authority.
Probe SHA 56911f5929916c06b6c606fbc909fea6fae19dca781b07777789c5b0a7c30c5f.
596 backend tests/quality PASS; e4e5bbf CI 34812475961 SUCCESS. Continue R5.

## 2026-09-14 restoration coverage and chain diagnostic

Fact-book restoration inventory: 17 explicit dated rows, no accepted events;
SHA 5a67fdb7cde1757e975ddb33fa545406bd10b32583078205da1aa40d2a907ad0.
CNINFO routing: 38 leads, 20 selected documents, 18 other leads retained.
PDF manifest SHA b089eb8e259b46178ec1731431fc221d65c8a7bd30c4596b2fdba02605aaeea4;
all 20 retained/indexed, zero PDF retrieval failures. Separate SSE batch has
three cached exact matches and 16 explicit DNS failures, not source acceptance;
manifest SHA 88ff4194d02dc8daa470d4d568c737913fe327914197e4221efe26e3aaaaabd3.
No repeated DNS retry or denied static-mirror retry. 600057 PDF 59855729 prints
600870 in its header but 600057 in body: identity conflict remains explicit.
600385 correction 1200096190 changes first-day intraday suspension rules, not
the restoration date/name; retain correction SHA
e679eb09cc7a4b2fb4b024489d0f32d5fac713174b3420aeec35e8105b6bff17.
Chain diagnostic v2 SHA 6b8e5516183881a0382ac8de04fb3d16dabc4ffafa21ebce20fb846ec3ddd95c:
322 chains, 102 missing-transition gaps, zero same-day conflicts, zero unmapped
events; 15 pre-target observations counted separately. This does not certify
no-event securities or daily states. Reversed event order check PASS.
594 backend tests and all quality checks PASS; 76d4851 CI 34810743949 SUCCESS.
Existing distribution worker continues. No full publication/freeze/studies/merge.

## 2026-09-14 source-oracle and ST constraint continuation

Provisional SSE transitions 689; 868 parser cases and three metadata variants
remain unaccepted. Full-v8 SHA 8bdb95ce9d11060909315d056bddadc555bbe081989674bbb4cca90ea8728e22.
v7/v8 preserve prior event rows; v9 parser adds document-bound reviewed title
equivalence only. Wrong document/code remains rejected. Full backend 593 and
Ruff/format/mypy PASS. Prior 220d75c CI 34809275007 SUCCESS.
Earlier 683-transition plus 345-retained-evidence chain diagnostic: 321 chains,
103 gaps, zero same-date state conflicts; 15 pre-target observations retained
outside target. Diagnostic is not complete daily state/authority acceptance.
Source-mirror gap probe: two access-denial responses, one timeout; no further
mirror retries. Existing CNINFO evidence preserved. Mirror manifest SHA
9cf3c0d2ca8dbb87c5d1ed0fc366efe9cb11b7135b78e344350de49bb8e30d7f.
Bonus oracle/lifecycle/boundary joins reuse accepted source tables and master;
no accepted Pilot recomputation. See bonus report. Four bounded Tencent requests
show 640-row truncation and empty 5,000-count daily payloads; empty is not proof
of missing history. Root full-raw-coverage-v1/long-range-count-probe-v1;
manifest SHA bd67f0a9307123698bc9be9f78a571df012af7e21866b835465b1cbc561fe8f0.
No strategy, full dataset publication, freeze or merge. Continue independent R5.

## 2026-09-14 2017 cash and missing-case parser continuation

2017 source snapshot verified against its 2,564 queue URLs and PDF hashes.
Date links 2,451/2,538; cash supported 2,241 / unresolved 233. Eleven processed
years total 18,263 supported / 3,121 unresolved cash groups, full census PARTIAL.
Source/date/cash manifests are in distribution-2017-snapshot-v1; cash SHA
d508f0fd10d572f6fa6942ad564e1483b7a3650a06333872d7bbf9d68c8e184a.
SSE whitespace/leading escaped-newline normalization resolves two metadata
matches; all 1,555 earlier exact matches preserved. Homophone and old/new-name
differences remain explicit review cases, not fuzzy matches. Parser v6 accepts
only direct resumption/name clauses with company/A-share prefixes: 677 provisional
transitions, 880 parser gaps, three metadata gaps. Full-v4 SHA
03509aa33b03694fcc571efb0731d584d2cb2500755d84680794941b79df358f.
Full-v3 intermediate matcher regression preserved; punctuation boundaries restored
before publication of v4. 600392 annual table says May 3, 2012; retained issuer
notice says May 2. This date conflict remains unresolved, not silently preferred.
Bonus accounting regression failed under ambient precision and missing explicit
basis. Fixed at shared portfolio path using existing context and original basis;
no fractional-share choice or strategy run. 592 backend tests/quality PASS.
Prior milestone CI 34808558506 SUCCESS; PR12 remains OPEN. Continue independent R5.

## 2026-09-14 SSE pagination and alternate PDF extraction

52 repeated-page failures recovered using beginPage and grouped result counts;
all original failures preserved. Exact metadata 1,555 / unmatched five.
133 identity/header failures received separate coordinate-deduplicated text;
16 additional provisional transitions, total 660 / parser unresolved 895.
No accepted event or full authority promotion. Earlier 644 records unchanged;
reverse-input normalization PASS. Windows immutable writer now removes its
temporary hard link before applying Windows read-only attributes; actual Windows
idempotence/replacement rejection check PASS, existing Linux regression PASS.
590 backend tests, Ruff/format/mypy PASS. CI 34806671415 PASS for prior 63353cc.
Nine fact books retained/indexed; 389 dated name rows (366 A-code), 105 risk
changes require event reconciliation. No undated-name ordering or backdated
source publication. External hashes in ST report/state. Continue independent R5.

## 2026-09-14 ST PDF source batch and bounded parser continuation

1,560 selected ST PDFs retrieved/indexed; zero retrieval failures. SSE metadata
corroboration continues with cache reuse and issuer/day-only queries. Snapshot
193 explicit transitions remain provisional, not complete ST authority. Thirteen
additional dates use directly connected resumption/name-change clauses; existing
180 records preserved. Backend 588 / quality checks PASS. See ST extension report.
All 128 distribution JS summaries identified as retained-PDF companions; no new
event or retrieval. Existing economic/date gaps remain, including 300137 typo.
CI 34805678054 PASS at 8a34438. Full dataset not created/audited/frozen; no studies.

## 2026-09-14 six-year cash batch continuation

2011–2016 source reconciliation completed: 11,551 PDFs / 128 JavaScript summaries,
zero remaining retrieval failures after 35 separate transient recoveries.
Existing date and gross-cash parsers produce 8,134 additional supported events,
1,547 unresolved groups. Combined bounded ten-year result: 16,022 supported /
2,888 unresolved. All event serializations validated by the existing pipeline.
No code, policy, accepted Pilot, strategy or freeze change. Full census PARTIAL.
See ../research/R5_CASH_DIVIDEND_BATCH_V1.md for immutable hashes.

## 2026-09-14 missing-only factor and ST source extension

Cached factor evidence supplies 5,301 full-target code-interval baselines;
135 missing intervals were fetched separately using the existing parser and
bounded source helper. All have a baseline, including old code aliases, but
baseline presence does not certify full factor completeness or corporate-action
alignment. No accepted Pilot artifacts were changed. External manifests and
checksums are recorded in project_state.json.

346 ST keyword/month windows now have complete query responses; one HTTP 502
was recovered in a separate immutable checkpoint. 6,724 unique leads remain
source leads. 1,560 transition PDFs are queued, with warnings/applications and
unexpected attachments retained separately. Full ST authority remains PARTIAL.
2011–2016 distribution receipts form a verified 11,679-row snapshot; 35 transient
failures are being retried separately, and 128 JavaScript summary attachments
are not treated as full PDF evidence. Indexing and other queues continue.
CI 34804569207 SUCCESS for cc4b7b9; no domain code changed in this continuation.

## 2026-09-14 SSE starting anchor / cash missing-only extension

SSE official 2009 yearbook capital table supplies 860 starting risk names; a split
S/newline/T cell is normalized, with regression test. Three paused issuer rows
visually checked. PDF and extraction hashes preserved; publication date unknown,
not backdated. Separate ST metadata collector has 173 missing months × two keyword
queries, skips accepted 2023-01..2024-07, verifies counts/order and keeps failures.
Cash v2 adds 186 events while reusing 7,702 accepted rows and preserving their IDs.
586 backend tests/Ruff/format/mypy PASS; prior milestone CI 34803545764 SUCCESS.
See ../research/R5_SSE_PRESTART_ANCHOR_V1.md and cash report continuation.

## 2026-09-14 exact cash-dividend batch

7,702 supported cash events / 1,527 unresolved source groups in four audited source
years. No rounded-price tolerance, net/gross substitution or ambiguous document
discard. Reuses existing CorporateAction/PortfolioEngine; no new domain policy.
1/81/100-share accounting regression checks conserve quantity/basis and create no
order/fill; source-record and event serialization/checksum checks pass. All 7,005
2018–2020 events reproduce under reversed evidence/master order. 584 backend and
78 frontend tests, lint/type/build PASS. See ../research/R5_CASH_DIVIDEND_BATCH_V1.md.

## 2026-09-14 2018–2020 source recovery and date-table links

All 32 DNS failures recovered once in a separate batch; 8,590/8,590 source PDFs
now verified/indexed. Original receipts and manifest remain unchanged. Fixed
official A-share table columns increase date links to 8,113/8,409 groups.
296 gaps and 15 malformed-text parsing errors remain explicit, not accepted
events. No economic terms promoted. See ../research/R5_DISTRIBUTION_2018_2020_V1.md.

## 2026-09-14 SZSE interval replay

3,028 candidates / 7,876,813 lifecycle security-sessions; no UNKNOWN, no IPO
old-state conflicts, no future-event or ordering differences. Existing accepted
Pilot IPO initialization reused explicitly. Overall full authority still PARTIAL.
Probe v8 hash is recorded in project_state.json. Prestart milestone CI 34802149128 PASS.
2018–2020 download manifest completed: 8,558 PASS, 32 DNS failures. The failed-only
32-document recovery has a separate immutable queue; original receipts preserved.

## 2026-09-14 SZSE prestart risk-state corroboration

Reused official dated export and yearbook; only 16 missing trading-table issuers
received targeted 2009 metadata queries. All 32 PDFs PASS; all 16 headers agree
on STAR_ST. 820 yearbook names agree independently. No current-name backfill,
future event use or assumed NORMAL gaps. Full ST authority remains PARTIAL.
580 backend tests PASS; follow-up formatting/type checks recorded at milestone.
See ../research/R5_SZSE_PRESTART_CORROBORATION_V1.md. No stop gate reached.

## 2026-09-14 targeted 2010 distribution coverage

45 issuer/date metadata windows complete; 75 plus seven document leads acquired
or reused, no failures. Reconciled source union: 1,179 documents. 14 reviewed date
ambiguities are source-pinned and exchange-corroborated, including visual PDF QA.
1,056 date links + three existing rights + one structural queue = 1,060 groups.
No ordinary dividend events promoted. 16 focused tests PASS; instrument CI PASS.
See ../research/R5_DISTRIBUTION_2010_DATE_CLOSURE_V1.md. R5 continues.

## 2026-09-14 candidate instrument extension

All 251 missing candidate classifications supported; accepted 5,181 facts reused.
Two connection-reset failures recovered with targeted requests, original receipts
preserved. Prior 600190 correction reused from frozen v2 evidence, not reopened.
15 focused source tests PASS; baseline milestone CI 34798601016 PASS.
See ../research/R5_INSTRUMENT_EXTENSION_V1.md. Independent R5 work continues.

## 2026-09-14 baseline membership source closure

Both exchange baseline membership cross-checks PASS; 18 directory omissions now
have reviewed annual-report identity evidence. 28 targeted PDFs retained, zero
retrieval failures. CNINFO keyword/category false negatives and PDF text issues
are documented, not interpreted as absent issuers. Backend 576 PASS; lint/type PASS.
See ../research/R5_MASTER_BASELINE_CROSSCHECK_V1.md. Full acceptance remains partial.
Previous milestone CI 34797320955 PASS. R5 independent queues continue.

## 2026-09-14 merger suspension batch

600553/600991 retained evidence and three targeted 601299 official notices close
the prior three chronology gaps under approved policy. Nine reviewed candidates
supported, full-market census still incomplete. Source audit manifest:
62f5d5a3068cb1ee02e9d36523e08f58e1d5aa5e4454507d7db8fc028009b676.
31 focused tests PASS. Previous milestone CI 34796787068 PASS. Workers continue.
See ../research/R5_MERGER_SUSPENSION_BATCH_V1.md. No new gate or studies/merge.

## 2026-09-14 retained merger batch

Four official implementation records normalized; nine reviewed candidates now have
six supported events and three retained gaps. Full census is not established.
Source hashes and lifecycle corroboration PASS; two metadata-only cash-offer unknowns.
Backend 571 / frontend 78 PASS; frontend lint/build and backend lint/type checks PASS.
See ../research/R5_MERGER_BATCH_CLOSURE_V1.md. R5 continues; no new approval gate.

## 2026-09-14 runtime recovery

WORKER_RECOVERY_STATUS=PASS_RESUMED_DURABLE_RECEIPTS; DUPLICATE_WORKER_PREVENTED=YES.
No live old workers, PID/lock files or temporary manifests found. Verified 44,504
unique, disjoint queued URLs and all processed PDF hashes. Two existing batch
names resumed from 1,977 and 584 processed receipts respectively; 2010 not restarted.
14 focused local source tests PASS. Docker was not started; Desktop launched
without reset/deletion for the isolated full suite. No research acceptance changes.
See .research/reports/r5-worker-recovery-20260914.json for the timestamped snapshot.

## R5 retained distribution notice recovery

2010: 1,113 PDFs indexed, one explicit HTTP 502 failure. 2018–2020: 8,590
document leads downloading with source/checkpoint reuse. Missing-date-range
recovery reuses retained pages; 2011/2012 reconcile to original annual totals.
566 backend tests/quality checks PASS; recovery focused source suite 11 PASS.
See ../research/R5_DISTRIBUTION_NOTICE_RECOVERY_V1.md and external manifests.
R5 RUNNING_BATCH_CLOSURE; no new gate, dataset creation/audit/freeze or studies.

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



Final current validation:529 backend/78 frontend tests, Ruff/format/mypy PASS.
600817 source bytes and receipt verified; manifest
8e3f61bf12d377b225c042aefdf3acb1342db7138cab6caad75f8f59ec9a23d0.

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

Registry recovery validation:520 backend tests, Ruff/format and mypy119 files PASS.
Frontend unchanged; no rerun this turn. No production accounting code changed.

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

## Current: 600005 zero-whole PASS; R5 partial-surrender methodology STOP

Approved WRITE_OFF_PARENT_BASIS_AS_CORPORATE_ACTION_LOSS_V1 implemented in shared
Portfolio accounting. Official600005 ->600019 ratio0.56, conversion2017-02-17,
new-share activation2017-02-27 reverified. Zero parent basis is written off only
as corporate-action PnL; cash/trading PnL/orders/fills remain unchanged.
MERGER_ZERO_WHOLE_SHARES_BASIS_UNAPPROVED:CN-A:SSE:600005:2017-02-17 RESOLVED.
504 backend/78 frontend tests, source replay, lint/format/types and schema checks PASS.
R5 resumed:95 pages/2849 merger announcements,69 implementation-document leads;
five prior candidates updated,2 supported/3 source-unresolved. Full census unknown.
Broader review:6 pages/175 capital-adjustment notices; official600462 confirms20%
ordinary-holder compulsory surrender, with30% issuance diverted to bankruptcy account.
This is not a merger or zero-successor case; partial-surrender historical-basis treatment
requires a new explicit policy. No loss/full-basis retention, bonus credit or exclusion chosen.
SINGLE_SMALLEST_BLOCKER=MANDATORY_PARTIAL_SHARE_SURRENDER_BASIS_POLICY_UNAPPROVED:CN-A:SSE:600462.
HUMAN_APPROVAL_GATE=R5_MANDATORY_PARTIAL_SHARE_SURRENDER_BASIS_POLICY;
HUMAN_APPROVAL_REQUIRED=YES. Exact surrender transfer chronology remains separate source work.
Full dataset CREATED/AUDITED/FROZEN=NO; verified safe start/coverage NOT_ESTABLISHED.
Preserved Pilotv2, R4v2, rights/demerger/prior source decisions remain unchanged.
No Development/Validation/OOS, full freeze, PR12 merge or release.
Report: ../research/ZERO_WHOLE_SHARE_CHECKPOINT.md;
machine report: .research/reports/r5-zero-whole-policy-v1.json.
After human decision resume preserved R5 queues, not acquisition from zero.
No background worker remains. Full freeze gate has not been reached.

## Historical checkpoints below (superseded)

## Current: 000024 merger PASS; R5 zero-whole-share basis decision STOP

CN_A_MERGER_FRACTIONAL_SHARE_POLICY_V1 implemented; 000024 evidence/accounting/replay PASS.
Prior MERGER_FRACTIONAL_SHARE_POLICY_UNAPPROVED:CN-A:SZSE:000024:2015-12-30 RESOLVED.
Official global allocation remains distinct from approved deterministic floor/no-cash accounting.
Full parent basis transfers to whole successor shares; remainder and CEIL bounds are audit-only.
R5 resumed the historical inventory; five candidates, two official reviews, one supported,
four unresolved including three retained source leads. Full census/materiality NOT_ESTABLISHED.
Official 600005 ratio0.56 exposes hypothetical Q=1 ->0 whole shares: positive B/0 is undefined.
No actual strategy holding is claimed; no loss, residual asset, cash, extra share or exclusion chosen.
SINGLE_SMALLEST_BLOCKER=MERGER_ZERO_WHOLE_SHARES_BASIS_UNAPPROVED:CN-A:SSE:600005:2017-02-17.
HUMAN_APPROVAL_GATE=R5_MERGER_ZERO_WHOLE_SHARE_BASIS_POLICY; HUMAN_APPROVAL_REQUIRED=YES.
494 backend/78 frontend tests; source replay, lint/format/types and additive schema checks PASS.
Rights V2/600003/prior authorities/frozen Pilotv2/R4v2 unchanged. R4 actual fills remain0.
Full2010-2025 CREATED/AUDITED/FROZEN=NO; safe start/verified coverage NOT_ESTABLISHED.
No formal studies, profitability inspection, PR12 merge, release or background worker.
Report: ../research/MERGER_POLICY_V1_CHECKPOINT.md;
machine report: .research/reports/r5-merger-policy-v1.json.
Next after zero-whole basis decision: resume preserved R5 sources/materialization/audit;
stop at GATE_FULL_RESEARCH_DATASET_FREEZE without freezing.

## Historical checkpoints below (superseded)

## Current:600003 demerger PASS; R5 merger fractional-allocation decision STOP

CN_A_MANDATORY_DEMERGER_POLICY_V1 implemented;600003 accounting/replay/source audit PASS.
Prior DEMERGER_ACCOUNTING_POLICY_UNAPPROVED:CN-A:SSE:600003:2010-02-26 RESOLVED.
One identified demerger supported; full event census NOT_ESTABLISHED.
R5 resumed existing lifecycle/inventory evidence and verified000024 ->001979 merger.
Official1:1.6008 conversion requires all-holder remainder ranking with random ties.
SINGLE_SMALLEST_BLOCKER=MERGER_FRACTIONAL_SHARE_POLICY_UNAPPROVED:CN-A:SZSE:000024:2015-12-30.
HUMAN_APPROVAL_GATE=R5_MERGER_FRACTIONAL_SHARE_POLICY; HUMAN_APPROVAL_REQUIRED=YES.
No arbitrary rounding, cash-in-lieu, fractional trading or exclusion was chosen.
484 backend/78 frontend tests, Ruff/format/mypy, schema and source replay checks PASS.
Rights V2 queue/accepted authorities/frozen Pilotv2 unchanged; R4v2 remains PASS with0 fills.
Full2010-2025 CREATED/AUDITED/FROZEN=NO; safe start/verified coverage NOT_ESTABLISHED.
No formal studies, profitability inspection, PR merge, release or background worker.
Report: ../research/DEMERGER_POLICY_V1_CHECKPOINT.md;
machine report: .research/reports/r5-demerger-policy-v1.json.
Next after decision: resume preserved R5 source queues, materialize/audit, stop at full freeze gate.

## Historical checkpoints below (superseded)


## Current: rights entitlement V2 PASS; material demerger methodology STOP

Human V2 separates event structure, tradability evidence and portfolio policy.
CN_A_RIGHTS_ISSUE_POLICY_V1 / NO_SUBSCRIPTION_NO_MONETIZATION_V1 implemented.
000960/2010-01-27 verified STANDARD_DIRECT_SUBSCRIPTION_RIGHTS_ISSUE;
tradability NOT_EVIDENCED; prior exact rights blocker RESOLVED.
148 events reprocessed:4 STANDARD_COMPLETE,0 STANDARD_PARTIAL_BUT_ACCOUNTING_SAFE,
0 EXPLICIT_UNSUPPORTED_VARIANT,144 EVENT_IDENTITY_UNRESOLVED source-work queue.
20 independently identified occurrences match provider records; full census PARTIAL,
not zero unexplained differences. No source backlog is re-labelled a tradability decision.
R5 safety review confirms600003/2010-02-26 one-parent/two-successor demerger.
SINGLE_SMALLEST_BLOCKER=DEMERGER_ACCOUNTING_POLICY_UNAPPROVED:CN-A:SSE:600003:2010-02-26.
Required methodology: successor historical cost allocation and intervening valuation.
HUMAN_APPROVAL_GATE=R5_DEMERGER_ACCOUNTING_POLICY; HUMAN_APPROVAL_REQUIRED=YES.
472 backend/78 frontend tests PASS; replay/Ruff/mypy PASS.
R4v2 PASS with0 actual fills; no rerun, strategy changes or profitability review.
Frozen Pilotv2/accepted authorities unchanged; full2010-2025 CREATED/AUDITED/FROZEN=NO.
Safe start NOT_ESTABLISHED; no formal studies, merge or release. No worker running.
Report: ../research/RIGHTS_ENTITLEMENT_V2_CHECKPOINT.md;
machine report: .research/reports/r5-rights-entitlement-v2.json.

## Historical checkpoints below (superseded)


## Current: rights policy engineering PASS; R5 exact event-evidence STOP

CN_A_RIGHTS_ISSUE_POLICY_V1 / DECLINE_SUBSCRIPTION approved and implemented.
Event model/accounting/reproducibility PASS; old participation-methodology blocker RESOLVED.
Inventory148 events/137 securities:2 supported,146 unresolved,0 positively confirmed
non-standard variants. No rights-based exclusion or full authority promotion.
User section8 STOP: RIGHTS_EVENT_UNSUPPORTED_VARIANT:CN-A:SZSE:000960:2010-01-27.
Its entitlement non-transferability remains unverified; this is not a finding of tradability.
HUMAN_APPROVAL_GATE=R5_RIGHTS_EVENT_VARIANT_REVIEW; HUMAN_APPROVAL_REQUIRED=YES.
R4_V2_STATUS=PASS, R4_REAL_DATA_FILL_COUNT=0; no R4 rerun or frozen Pilot modification.
Full2010-2025 CREATED/AUDITED/FROZEN=NO; verified safe start NOT_ESTABLISHED.
No formal studies, strategy changes, profitability review, PR merge or release.
Current report: ../research/RIGHTS_ISSUE_POLICY_CHECKPOINT.md;
machine state: .research/reports/r5-rights-policy.json. No background worker remains.

## Historical checkpoints below (superseded)

## Current: Pilot v2 frozen; R4 v2 PASS; R5 methodology decision STOP

R1 COMPLETE; R2 v1 SUPERSEDED; R3 v1 INVALIDATED; R2/R3 v2 COMPLETE.
GATE_A_REVISED_DATASET_FREEZE APPROVED and executed, v2 current accepted/frozen.
R4 v2 PASS including fresh replay/no-look-ahead, persistence/API/actual UI.
R5 resumed source preflight, then STOP: FULL_HISTORY_RIGHTS_ISSUE_TREATMENT_REQUIRES_HUMAN_DECISION.
Official6000362010 paid rights issue is absent from the dividend-only response;
existing accounting policy rejects rights. No automatic subscription, forfeiture,
cash injection or exclusion decision. HUMAN_APPROVAL_REQUIRED=YES for this policy,
not full dataset freeze. Full2010-2025 dataset CREATED/AUDITED/FROZEN=NO;
verified research-safe start NOT_ESTABLISHED. No formal studies/merge/release.
Current BaoStock endpoint recovered;124 exited-security factor baselines verified.
Other full-history authorities remain unfinished, not inferred from Pilot PASS.
See `../research/PILOT_V2_FREEZE_R4_R5_CHECKPOINT.md` and
`.research/reports/r5-source-preflight.json`. All probes complete; no worker running.

## Historical checkpoints below (superseded)

## Current: revised Pilot v2 frozen; R4 v2 RUNNING

Latest human approval supersedes prior revised-freeze STOP. All eight approved
component hashes, partition bytes, counts,25 R3 checks and preserved v1 verify.
V2 freeze complete, canonical receipt f9add5f2...635bcb3. Unchanged R4 v2 running;
R1 COMPLETE; R2/R3 v2 COMPLETE; R2 v1 SUPERSEDED, R3 v1 INVALIDATED. On PASS, R5 full-history
materialization/audit. Next gate GATE_FULL_RESEARCH_DATASET_FREEZE, unfrozen.
No formal studies, PR merge or release. Previous acceptance decisions unchanged.

## Historical checkpoints below (superseded)

## Current: revised Pilot Dataset review

V2 CREATED=YES; AUDITED=YES; FROZEN=NO; readiness READY.
25 fresh R3 checks PASS; cross-source2478 rows replayed from original snapshots,
not a copied verdict. All1755700 secondary-source Pilot rows had amount precision
rechecked.433 backend tests passed; full Ruff/format/mypy passed.
5180 ordinary shares;1922643 bars;382 sessions. Candidate master5178 ->5181;
three added STAR exits,zero removed,one corrected A/B listing date (600190).
15528 reused partitions,12 rebuilt,9 new. Complete lists and all hashes:
`../research/REVISED_PILOT_DATASET_REVIEW.md`, `.research/reports/revised-pilot-v2.json`.
V1 immutable checksum verification PASS; original manifest/freeze/R3/R4 preserved.
STOP at GATE_A_REVISED_DATASET_FREEZE. R4 v2 NOT_RUN; R5 blocked; no formal studies.

## Historical checkpoints below (superseded)

## Current: frozen Pilot retained; R4 engineering passed; R5 counterexample

PILOT_DATASET_FROZEN=YES; immutable0696a5c7...manifest remains unchanged.
R4 pipeline/replay/no-look-ahead/metric/API/UI parity checks PASS on the supplied
data:382 sessions,7 rebalances,140 orders,0 fills. All results remain explicitly
PILOT_ENGINEERING_SMOKE_ONLY. No strategy economics changed.
R5 source expansion independently proved three absent STAR exit candidates.
Current dataset acceptance INVALIDATED; original R3 receipts preserved as history.
Full dataset CREATED=NO, AUDITED=NO, FROZEN=NO; all full counts/hash unavailable.
Stop for revised Gate A review, not full freeze approval of an unbuilt dataset.
Blocker=FROZEN_PILOT_MASTER_OMITS_STAR_EXIT_SECURITIES.
Detailed evidence and completed/unfinished work:
`../research/PILOT_FREEZE_R4_R5_CHECKPOINT.md`.

## Historical checkpoints below (superseded)

## Current: approved freeze complete; R4 underway

Pilot freeze PASS after final read-only R3 identity/partition/source verification.
Original manifest/partitions unchanged. Freeze record74870e7d...committed separately.
R4 runs PILOT_ENGINEERING_SMOKE_ONLY with full/reversed/prefix replay and existing
research persistence/API/UI; no economic parameter changes or assumed fills.
Backend422 tests,frontend76 tests,lint/type/build checks pass at this checkpoint.
Full R4 acceptance remains pending actual persisted API/UI parity. No formal
Development/Validation/OOS,merge/release. Next stage is R5 full historical data.

## Historical checkpoints below (superseded)

## Current: R2 published and R3 audited; Gate A stop

RUN_ID=20260912-R2-R3-ORDINARY-A-SHARE; CURRENT_STAGE=R3;
STATUS=AWAITING_HUMAN_APPROVAL. GitHub account MakenzieAhern verified.
Implementation HEAD=5be77b05fa0b674c0f37bc04e19267bdac50b24b;
419 backend tests/Ruff/mypy PASS; CI34665563160 backend/frontend/compose SUCCESS.
Final report-only commit: resolve with `git log -1 --format=%H -- docs/orchestration/RUN_REPORT.md`;
verify its CI separately. Branch feature/a-share-research-v1.1; PR12 OPEN/UNMERGED.

R2 resumed from the original657+1923 inputs;2597 remaining ordinary A shares
recovered, not reacquired from zero. Final657 primary +4520 secondary,5177
securities/1922088 raw rows/12528 factor rows. Required failures/unresolved=0.
Missing observations4210 remain explicit; rejected observations0. Full amount
audit34799 reachable scheduled decisions,0 ambiguous,0 outliers; two all-date
stress ambiguities retained, not used to change policy. Full source-policy pins intact.

Real atomic publication completed. Second invocation verified resume without
source fetch or partition rewrite. Real published-data R3 exited0:22 checks PASS,
5725 rule cases, zero unclassified/non-A-share leakage. Original2580 receipt
reconstruction exactly matches ff844abd20b651ae9a962515a6feb6cc551f90468daf7b984959da7121149ca6.
Canonical manifest0696a5c7454f044a3f0ea8886b1c08fbe2228b19598894ddb44ac54498978490;
audit artifact88fa6df2892876bb7318ceabd24883539ca9b7920ec7abf1f2d88be5e9d892d1.

SOURCE_AUTHORITY_PREFLIGHT=PASS; PILOT_DATASET_CREATED=YES;
PILOT_A_SHARE_DATA_READINESS=READY; DATASET_AUDITED=YES; DATASET_FROZEN=NO.
HUMAN_APPROVAL_GATE=GATE_A_DATASET_FREEZE; HUMAN_APPROVAL_REQUIRED=YES.
SINGLE_SMALLEST_BLOCKER=NONE (intentional human approval gate).
DEVELOPMENT_STUDY=NOT_RUN; VALIDATION_STUDY=NOT_RUN; OFFICIAL_OOS=NOT_RUN;
PR_MERGED=NO; V1.1.0_CREATED=NO. Stop; no background data worker remains.

Official daily suspension/tradeability remains unknown/null on1926298 lifecycle
security-sessions. No missing bar was labeled suspended; no fill may be assumed
without separate official evidence. This approved fail-closed handling is audited,
not complete execution coverage. Detailed counts,22 checks,classification evidence,
limitations and hashes: [full checkpoint](../research/R2_R3_ORDINARY_A_SHARE_REPORT.md).

## Historical checkpoints below (superseded)

## Current running milestone: approved instrument scope

Latest running snapshot:4074 completed inputs (657 primary,3417 secondary),1103
remaining,zero required failures;4020 Parquet securities/1498998 raw rows.
Original2580 partition receipts still reproduce
`ff844abd20b651ae9a962515a6feb6cc551f90468daf7b984959da7121149ca6`.
Incremental amount audit:4032 securities/1503570 rows,26922 potentially reachable
decisions,zero ambiguity/outliers; SHA-256
`052c1067c455f0d9cdb4556509c0409c29ca02cbbbac61141175a73baedcafbd`.
Live worker remains active; external checkpoint supersedes these snapshot counts.
Publication/audit code based on8d6a835 passes419 tests, lint and typing. The offline
synthetic full publication/resume/audit test is not an actual Pilot audit PASS.

Human decision recorded in DECISIONS and research methodology. R2 RUNNING,
approval not required. Shared explicit COMMON_A_SHARE gate preserves four boards
and listing/delisting; unknown/late/overlapping classification fails closed.
Source inventory reuses existing master snapshots and checksums; targeted SSE
SEC_TYPE/IPO metadata supplies the mixed STAR stock/CDR distinction. A current
SEC_TYPE snapshot alone is not accepted as historical classification.
Full scope gate PASS: 5178 candidates, 5177 COMMON_A_SHARE, one CDR (689009),
all other instrument categories zero; zero unclassified. Classification checksum:
`28d56696d2dc3de6d3c217dc557b9d8139729b3389245beb8fa580897ce8b7d7`.
The previous complete suite passed 415 tests; the added shared-source integrity
regression also passes, with Ruff and strict typing. R2 has resumed the remaining
2597 required securities. Existing 657 primary /1923 secondary inputs and 2580
partitions are retained. Historical failure evidence remains separate from the
scope-filtered required-data denominator.
Dataset not created/audited/frozen; no strategy, studies, merge or release.
This is an intermediate engineering milestone, not the terminal Gate A report.

## Historical checkpoints below (superseded)


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


## Ongoing R2 observation inventory

1,505 materialized securities /554,152 raw rows /3,450 factor rows; failures0.
657 original primary successes remain unchanged. Worker continues from its live
secondary checkpoint. Expanded available-input amount audit:1,544 securities,
568,116 rows,9,891 potential decisions,zero ambiguous. No strategy invocation.
New offline observation inventory records3,369 missing lifecycle-session
observations across213 securities; zero-volume observations0. Missing observations
are not inferred suspensions. Exact intervals persist outside Git in
pilot-akshare-20260911/observation-coverage-current.json. Partition snapshot SHA256:
502a7712bc06840bd2febaa7218e34e23064515f29a7f721be15849f013db66b.
Inventory validates partition SHA/identity/count and listing/delisting boundaries;
its runnable test covers disjoint intervals, input reversal and duplicate rejection.
Dataset remains unpublished, unaudited, unfrozen. No studies or merge.

## Current running recovery milestone

R2 RUNNING. Primary657 preserved; secondary516 now materialized, total1,173
securities /428,646 raw rows /2,584 factor rows, zero partition failures.
4,005 inputs remained at this snapshot; live secondary-checkpoint.json is newer
as the worker continues. No dataset publication, full R3, freeze, studies or merge.
The original primary partition-report subset still hashes to
7c2916446fc867a39b41aa45a7062c44452be15fd2708a9b0e65882f5e573896.
Two-query/one-query normalized equality proved on260 recovered securities;
future requests omit the redundant second query without changing policy/coverage.
Delisting-period rule reachability is explicitly included: initial sample4335
potential checks (one more stable primary check than4334 previously reported).
The expanded current audit covered6429 checks with zero ambiguity. Old authority
artifacts retained; current audit writes separate amount-impact-current-* files.
405 backend tests and lint/type checks passed at acquisition milestone74f8c8c;
CI34612957718 SUCCESS. Latest refinements receive their own checks/CI.

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


## Current focused amount audit checkpoint

STATUS = BLOCKED; CURRENT_STAGE = R2; HUMAN_APPROVAL_REQUIRED = YES; not Gate A.
The authorized audit ran RUNNING without an approval pause, then stopped because
amount is REQUIRED under the pre-existing liquidity screen, not OPTIONAL merely
because the interchange schema accepts null. No methodology change was made.
SECONDARY_ACCEPTANCE = FAIL; amount classification INSUFFICIENT_EVIDENCE.
Six cached primary controls cover four boards, high/low price and volume, ST/*ST,
and retained adjustment-event periods.1,719 rows have raw strings and Decimal
unit/difference calculations; max absolute51 CNY, max relative0.0002227431347383828848417993403.
Observed2 decimals are not a documented provider rounding/error guarantee.
SINGLE_SMALLEST_BLOCKER = RAW_SECONDARY_AMOUNT_PRECISION_AUTHORITY_UNRESOLVED.
Amount audit SHA256 = 3807e6cc28f043b3cdff4d2bca22d0ddea8d99b918d09771171b5467e9da3c93.
Observation SHA256 = b7efbaa5571a63ed4a73e7e4f0adc1d908c9c8517079b234cc6702b6af9d7e96.
No market-data requests,657 primary securities unchanged,4,521 required gaps retained.
No dataset creation/audit/freeze, studies or merge. Existing authorities/policy preserved.
401 backend tests, Ruff/format/strict mypy PASS. GitHub MakenzieAhern verified.
Full report: docs/research/TENCENT_AMOUNT_ACCEPTANCE.md. CI checked after milestone push.

## Previous candidate checkpoint (superseded)


## Latest R2 systemic diagnosis and candidate failover checkpoint

STATUS = BLOCKED; HUMAN_APPROVAL_REQUIRED = YES; HUMAN_APPROVAL_GATE = NONE.
SINGLE_SMALLEST_BLOCKER = RAW_SECONDARY_AMOUNT_PRECISION_AUTHORITY_UNRESOLVED.
PRIMARY_ROUTE_STATUS = PRIMARY_SYSTEMIC_TRANSPORT_FAILURE (6/6 fixed probes).
RAW_OHLCV_PRIMARY_AUTHORITY = PASS; SOURCE_AUTHORITY_PREFLIGHT = PASS (existing,
unchanged primary manifest, not a secondary promotion).
SECONDARY_ACCEPTANCE = NOT_PROMOTED; CROSS_SOURCE_PARITY = PARTIAL.
CN_A_RAW_OHLCV_FAILOVER_V1 = CANDIDATE_NOT_ENABLED.

32 Tencent candidate requests cover 8 securities/two years/two repetitions;
2,418 normalized candidate rows repeat exactly. Six cached primary controls share
1,719 dates, with zero material OHLC/date mismatches. Four unexplained amounts
remain; prior Sina histories plus one targeted 300336 request corroborate the
rounding base but do not prove the remaining primary vendor precision behavior.
No additional tolerance, source substitution, arbitrary exclusion or strategy
performance criterion was introduced. Source snapshots and field-by-field parity
are external; full details in docs/research/R2_RAW_FAILOVER_ACCEPTANCE.md.

PRIMARY_SUCCEEDED = 657; PRIMARY_FAILED_SECONDARY_RECOVERED = 0;
PRIMARY_FAILED_SECONDARY_FAILED = 0 (no production secondary attempts);
AUTHORITATIVELY_NO_DATA_EXPECTED = 0; UNRESOLVED_REQUIRED_DATA = 4521.
All original raw/factor inputs, Parquet files and checkpoint hashes verified
unchanged. Partial production raw rows = 244,073. Candidate rows are not admitted.
No final manifest or Pilot Dataset was published; no R3, freeze, Development,
Validation, OOS, strategy, PR merge or release occurred. All R1 decisions preserved.

Primary probe SHA256 = 513f04d0ec47408b1f49503af5168eb07d2fbf5270b6a661f4c8e32bf3157d9c
Candidate audit SHA256 = ff0e31d2ffca13fb174995a1bd31eb3f4a6342c0c013dfc26779708469c3db47
Policy SHA256 = 47316572b10b3e1f8cc35362614958a7265463be25432f3de2b4a149841d3dcc
Tests: 11 focused recovery checks PASS; full backend 400 PASS; Ruff/format/mypy PASS.
Finished probes and persistent access-denial stops cannot restart on rerun.
Existing feature branch/PR12 retained. No Git identity change. Final milestone CI
is checked after push; this checkpoint does not claim a future CI result.

## Prior checkpoint (superseded by current failover review)

## Terminal R2 recovery checkpoint

STATUS = BLOCKED; HUMAN_APPROVAL_REQUIRED = YES; HUMAN_APPROVAL_GATE = NONE.
SINGLE_SMALLEST_BLOCKER = R2_RAW_ROUTE_CONNECTION_CLOSED_600070.
Initial pass: 5,178 / 5,178 processed, 504 completed, 4,674 pending.
First retry: 4,674 / 4,674 processed, 151 recovered, 4,523 pending.
Final retry: 4,523 / 4,523 processed, 2 recovered (600605, 600739), 4,521 unresolved.
Last terminal source failure UTC: 2026-09-11T11:49:51.552627+00:00.
The worker ended with FINAL_PUBLICATION_PROHIBITED; no retry process remains.
657 RECOVERED_PRIMARY (493 SSE, 164 SZSE); 0 accepted fallback recoveries;
0 AUTHORITATIVELY_NOT_EXPECTED_TO_HAVE_DATA; 4,521 UNRESOLVED_REQUIRED_DATA
(1,794 SSE, 2,727 SZSE). Every terminal error is RemoteDisconnected from the
accepted Eastmoney raw endpoint. Error classification UNKNOWN, not assumed
anti-bot, outage or lifecycle-driven. 600070 actual requests = 5, all exhausted.
No accepted fallback or existing transport-gap exclusion permits publication.

All master IDs accounted for exactly once in completed/pending sets; no overlap
or silent drop. Failure history has unique security/round slots, every pending
entry is round 2 terminal, and failure manifest exactly matches checkpoint.
No provider access-denial flag or abandoned .tmp file was found.
657 partial securities: 244,073 raw rows, 1,565 factor rows, quality failures 0.
Source/partition SHA checks pass during offline materialization. These are partial
raw/factor checks, NOT full R3 dataset audits or proof of complete observations.
No final input-manifest.json exists. All data and failure evidence remain outside Git.

External evidence under pilot-akshare-20260911:

- recovery-checkpoint.json SHA-256: ffdc46937ecbd30f74a28660ef1769d2a7b8506ef65d0f1c2ae45ddac4841a68
- recovery-failure-manifest.json SHA-256: e1279921716ebf3c3d424acfedceb7b8f70b950dcdd4f6372829e41c811488ce
- partition-checkpoint.json SHA-256: 7c2916446fc867a39b41aa45a7062c44452be15fd2708a9b0e65882f5e573896
- 600070-recovery-result.json SHA-256: 115ed5b78155e53e9f71396eab1c3baee21ef746808f14b4be7e360ea5ac4185
- recovery-completion-report.json SHA-256: be02bd9cba43320007fe7d6731fcdd060f947d63ca23d6d942ee07c6dcafc887

Final offline repeat reproduced the same partition-checkpoint SHA-256 with no
new network request; six focused recovery tests re-run PASS. Controller JSON
verified BLOCKED with all dataset/study permissions unchanged. GitHub login
re-verified MakenzieAhern; branch feature/a-share-research-v1.1.

SOURCE_AUTHORITY_PREFLIGHT = PASS; all R1 authority decisions unchanged.
PILOT_DATASET_CREATED = NO; PILOT_A_SHARE_DATA_READINESS = BLOCKED.
DATASET_AUDITED = NO; DATASET_FROZEN = NO; R3 = NOT_RUN.
DEVELOPMENT_STUDY = NOT_RUN; VALIDATION_STUDY = NOT_RUN; OFFICIAL_OOS = NOT_RUN.
PR12 remains OPEN/unmerged; no new PR, release or strategy execution.
Existing feature branch and MakenzieAhern identity retained. Backend 395 tests,
Ruff/format/strict mypy and preceding milestone CI passed; terminal documentation
checkpoint CI is checked after its single milestone push.

## Preserved active R2 recovery continuation (superseded by terminal state above)

STATUS = RUNNING; HUMAN_APPROVAL_REQUIRED = NO. Prior stop below superseded.
Independent queue continues through per-security failures; 600070 = UNRESOLVED_REQUIRED_DATA.
Three same-construction SSE controls succeeded, 382 rows each. No fallback is in
the current accepted OHLCV manifest; no new exclusion policy is introduced.
At this checkpoint: 657 securities partitioned, 244,073 raw rows, 1,565 factor rows;
quality failures 0, final publication NO. Periodic counts are checkpoint snapshots,
not final-universe acceptance. External pilot-akshare-20260911/recovery-checkpoint.json
and partition-checkpoint.json retain current counts and exact file hashes.
First acquisition pass completed all 5,178 members: 504 completed, 4,674 pending.
Round 1 completed all 4,674 pending members and recovered 151 additional inputs.
Final round 2 is RUNNING after the fixed 60-second backoff for the remaining 4,523
members; the full queue's retries are not yet exhausted. No dataset publication or full R3 audit
is claimed. The last first-pass completion, 300750, reused accepted raw/factor sample snapshots; it
does not establish a new live network recovery.
Round-1 result: 4,674 / 4,674 processed, 151 additional primary recoveries.
The first two were 600419 and 600420, each 382 rows. 4,523 inputs entered final retry.
600070 exhausted its last authorized request at 2026-09-11T08:29:25.145713Z;
RemoteDisconnected before HTTP response, recorded at 08:29:26.078749Z. Actual
requests total five (three prior client diagnostics and two new recovery slots).
Its terminal classification is UNRESOLVED_REQUIRED_DATA; root cause UNKNOWN.
No accepted fallback or existing transport-gap exclusion exists. Evidence is in
600070-recovery-result.json outside Git. No further 600070 request is authorized;
other securities continue their independent final pass, with final publication barred.
Final-pass progress snapshot: 4,390 / 4,523 processed, two additional primary recoveries.
Milestone feabf7055fab86d72ccde1d0d75ae8ef8d442036 is pushed; CI 34579627544 SUCCESS.
First-pass milestone bfb89fb26dd39422da14bf2f1eab2e6c1de9637f is pushed;
CI 34563889226 completed SUCCESS. No PR merge or dataset freeze occurred.
After recording the source failure at 2026-09-11T05:07:34.160687Z, the Windows
process hit WinError 5 while replacing the WSL-backed checkpoint (no separate
exact error timestamp was captured). Both old and newer temporary checkpoints were preserved;
the newer one was verified as the same state plus two failure records and restored
using WSL-native publication. Exact failure timestamps and provider attempt slots
were retained; no network request was replayed. Evidence is external
checkpoint-publication-recovery.json and its before/after snapshots.
Progress reads now use WSL-native Python, avoiding Windows file-sharing locks.
The shared atomic save retries only PermissionError during publication of the same
bytes, at most five attempts with 0.1/0.2/0.4/0.8-second backoff; persistent failure
still retains the prior checkpoint and temporary bytes. Six focused tests and
395 backend tests PASS; Ruff, format and strict mypy PASS. R2 resumed from the
preserved round-1 checkpoint, not from zero.
Checkpoint-fix milestone b1be221fc793642be07356cbf98764011a34eb08 is pushed;
CI 34565166603 completed SUCCESS. The active recovery worker uses this fix.
The scheduler now uses two workers with two-second inter-batch pacing and a
20-second cooldown after ten consecutive failed batches. Three fixed rounds,
30/60-second round backoff, no jitter; no repeated failed request on restart.
Original failure evidence remains untouched. Backend 395 tests PASS; Ruff,
format and strict mypy PASS. Request construction comparison is external
request-comparison.json; no proxy, standard Python-urllib/3.12 header, 35s timeout.
The earlier budgeted 600070 request used the standard requests 2.34.2 Session on
the same accepted URL at 2026-09-11T01:54:36.190841+00:00. It also closed before
HTTP response (ConnectionError wrapping RemoteDisconnected). This consumes the
round-1 recovery slot; it is not an additional provider or a repeated slot.
At that point, three prior diagnostic requests plus this request made four actual
requests; the round-2 slot subsequently failed as recorded above. Root cause remains UNKNOWN.
Five focused ingestion tests PASS, including physical checksum repeatability,
lost-receipt reconstruction and detection of modified partition bytes.
Recovery-test milestone 6cf7623c05844559540af76d5b3f71af1a9233f5 is pushed to the
existing feature branch; CI 34554480884 completed SUCCESS. PR #12 remains unmerged.
Lifecycle-only expected-session check: every one of the 5,178 accepted members
has at least one calendar session on/after listing and before delisting in the
Pilot interval. Zero members qualify as having no expected sessions solely from
listing/delisting boundaries. This does not infer suspension or excuse missing bars.

## Preserved prior checkpoint (superseded by active R2 recovery above)

RUN_ID = 20260911-R1-R2-07
START_SHA = 14c9f8c4c5a616442775d070f26aa34e858785e6
END_SHA = Resolve with git log -1 --format=%H -- docs/orchestration/RUN_REPORT.md
CURRENT_STAGE = R2
STATUS = BLOCKED
BRANCH = feature/a-share-research-v1.1
PR = 12 OPEN / UNMERGED
CI = Verify final publication HEAD after push

PILOT_EXECUTION_CONVENTION_DECISION = APPROVED
MARKET_RULE_AUTHORITY = PASS_FOR_PILOT
EXECUTION_CONVENTION_VALIDATION = PASS
SOURCE_AUTHORITY_PREFLIGHT = PASS
FULL_HISTORY_RULE_AUTHORITY = PARTIAL

Official source claims and simulated execution are now independent gates.
The existing 14 SZSE snapshots support 27 official claims, all VERIFIED.
The old unverified transfer-fee claim remains preserved as an explicitly
non-statutory frozen research allowance under approval section9, not deleted
or promoted to official fact. Rates unchanged. SSE STAR quantity metadata was
checked against official 2019-07-19 Q5-Q6 at
https://edu.sse.com.cn/tib/qa/c/4866268.shtml (raw/meta retained outside Git).

CN_A_DAILY_OPENING_LIMIT_V1 is a SIMULATION_ASSUMPTION. Immutable limit=raw close(t),
signal after close(t), intended next calendar session, independent legal/status/
conservative daily-proxy eligibility, raw OPEN only after acceptance. Unfilled
instructions expire; no synthetic missing bars or extra slippage. The existing
RiskEngine/OMS/broker/portfolio path remains shared. No exact auction-fill claim.
The 1% daily-volume cap is ex-ante model conservatism, not auction liquidity proof.
README, methodology and research report permanently link the limitations.

Backend = 390 tests PASS
Execution convention = 36 focused tests PASS
Ruff / format / strict mypy = PASS

R2 input acquisition started against the 5,178-member accepted master.
A targeted delisting canary 300336 has 91 raw bars and a parsed HFQ curve.
The first fixed-order staging member 600070 failed before receiving HTTP bytes
in three bounded clients. Complete-universe staged count=0; no Parquet publication,
dataset manifest or dataset audit is claimed. A resumable acquisition command,
source metadata and explicit failure manifest remain. Full partition materialization
and R3 audit remain future work after this external access failure is resolved.
Previously accepted master/ST/adjustment/OHLCV/benchmark work was not repeated.

RULE_MANIFEST_SHA256 = cf8689d3e8269ba83bf03fe0b872689d10c441fabd7bf38ded72e30e38ca6583
NORMALIZED_RULE_SHA256 = 5569489384b3af7c7a81c39e6245e27b30bd064e7b801e411fe71de1fd7fd7f1
EXECUTION_VALIDATION_SHA256 = eae4180d8ac77495a82939a165dd94e8fbcf44ff9ad81cc3380c47d97a65f77a
SOURCE_PREFLIGHT_SHA256 = c549b64c562a5b5a08bd7ec7f9c62ba8d58df77ce0eac5eb66ebcc1d7d2ea859
R2_FAILURE_MANIFEST_SHA256 = dc3de6a08fb5377161e17cbf745c4bb51a3ee4535aa30964717b55b3ce3a43ff

DOCKER_RECOVERY = PASS
DOCKER_ENGINE_HEALTHY = YES
DOCKER_COMPOSE_HEALTHY = YES
POSTGRESQL_HEALTHY = YES
REDIS_HEALTHY = YES (PONG)
BACKEND_HEALTHY = YES (/api/health 200)
FRONTEND_HEALTHY = YES (configured 5173 HTTP200)

PILOT_DATASET_CREATED = NO
PILOT_A_SHARE_DATA_READINESS = BLOCKED
DATASET_AUDITED = NO
DATASET_FROZEN = NO
DEVELOPMENT_STUDY = NOT_RUN
VALIDATION_STUDY = NOT_RUN
OFFICIAL_OOS = NOT_RUN
HUMAN_APPROVAL_GATE = NONE (not Gate A)
HUMAN_APPROVAL_REQUIRED = YES
SINGLE_SMALLEST_BLOCKER = R2_RAW_ROUTE_CONNECTION_CLOSED_600070
PR_MERGED = NO
V1.1.0_CREATED = NO

Next external action: restore the accepted 600070 raw-history request or authorize
a complementary source. Do not restart acquisition, discard source failures,
reopen accepted authorities, merge PR12, freeze, or run any study.
