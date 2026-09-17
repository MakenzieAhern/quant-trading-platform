# R5 Merger Implementation Lead Closure V1

## Targeted 600631→600827 source-chain audit — 2026-09-18

The bounded ordinary unrestricted 600631 A-share holder **without a cash
election** is source-complete. Six contemporaneous CNINFO issuer documents
establish the chain: [revised merger report](https://static.cninfo.com.cn/finalpage/2011-07-29/59741684.PDF)
(1:0.861 ratio and whole-share/residual rule), [cash-choice implementation](https://static.cninfo.com.cn/finalpage/2011-08-03/59762740.PDF)
and [continuous-halt notice](https://static.cninfo.com.cn/finalpage/2011-08-03/59762741.PDF)
(2011-08-04 last parent trading and cash-choice record, 2011-08-05 continuous
halt), [cash-choice result](https://static.cninfo.com.cn/finalpage/2011-08-11/59801076.PDF)
(zero shareholders elected), [successor progress](https://static.cninfo.com.cn/finalpage/2011-08-19/59839426.PDF)
(parent terminates 2011-08-23), and [registration/listing result](https://static.cninfo.com.cn/finalpage/2011-08-29/59888838.PDF)
(merger registered/completed 2011-08-26; new unrestricted 600827 shares list
2011-08-31). The official master and targeted raw-date boundary agree. The
issuer's reference to exchange/registry handling of fractional residuals
does **not** establish an individual award. Only the separately approved
merger **research floor** may be used for bounded replay. B shares, locked
controlling holders, electing accounts and actual fractional awards are not
claimed.

`backend/scripts/audit_merger_600631.py` verifies the six original PDFs and
receipts, exact page terms, chronology, master lifecycle, raw boundary and
reversed input order. Immutable external audit:
`full-merger-v1/targeted-parent-fraction-v3/600631-official-event-audit-v2.json`,
file SHA-256 `5b90c7fdd7aa263af47de920a1c491d2ad8c5071315e8168732c54c5b8c42d91`,
manifest `03e73decd34373a09f32e62d61561f5dc57ca40780011371a518b25cbc5a00e9`,
event checksum `b3779bae7912ae8f38c2d553d5e73d019cb213a3e18c8293c7c6c7a9b9c723e5`.
The exact `MERGER_NEW:600631:600827` P1 source request is closed by immutable
source-closure manifest
`332efe2929f28923fbcd85927b4f862c087c7496c97196779f559ff8bf5a2427`.
Cumulative P1 v48 is **16,067/16,320** established, **1,988** substitutions,
**253 facts / 252 documents** open; manifest
`967a6459073e6d2a45a77fa7d41bec030b2630be946b17441dd769050c146a63`.
No new economic event was published into the accepted 15-event inventory;
full merger census and Full Dataset remain unestablished.

## Targeted 600832→600637 source-chain audit — 2026-09-18

The bounded ordinary unrestricted 600832 A-share holder **without a cash
election** is source-complete. Four contemporaneous CNINFO issuer documents
are the event evidence: [revised merger report](https://static.cninfo.com.cn/finalpage/2015-04-22/1200884193.PDF)
(final 3.05 old shares to 1 new share), [parent cash-choice result](https://static.cninfo.com.cn/finalpage/2015-05-11/1200992519.PDF)
(no dissenting holder elected, while two predeclared affiliates did),
[conversion implementation](https://static.cninfo.com.cn/finalpage/2015-05-22/1201045132.PDF)
(continuous halt, record date, registry-wide fractional rule), and
[registration/listing result](https://static.cninfo.com.cn/finalpage/2015-05-29/1201078513.PDF).
The [2016 issuer advisor confirmation](https://static.cninfo.com.cn/finalpage/2016-05-12/1202317584.PDF)
corroborates actual 2015-06-03 unrestricted listing **only after the event**;
it is excluded from point-in-time event sources.

The last parent trading date is 2015-04-29; continuous suspension starts
2015-04-30; termination/record is 2015-05-20; registry completed 2015-05-27;
new unrestricted successor shares first trade 2015-06-03. The official master
and targeted raw-date boundary agree. The registry's global remainder ranking
and random tie-breaking cannot establish an individual allocation; only the
separately approved merger **research floor** may be used for a bounded replay.
B/restricted holders, affiliated electors and actual account awards are not
claimed. Source bytes, exact page terms, chronology, raw boundary and reversed
input order passed `backend/scripts/audit_merger_600832.py`.

The immutable external audit is
`full-merger-v1/targeted-parent-fraction-v2/600832-official-event-audit-v2.json`;
file SHA-256 `d09a152f9075ccd980bedda1d8d4b5d00b4e3d595e9512877f2222a227ed850b`,
manifest `4a539fd39a893150cbb24bac65efe4a207c55ce06f163f27013b5905a893a850`,
event checksum `9a3e05a534759822e51bb0427cfe219997c7f0084325f6763b6c58786d6d7e94`.
The exact `MERGER_NEW:600832:600637` P1 request is closed by immutable
source-closure manifest
`0d3a410876d651310da37c51b11229c49ef292596f9ef987ba11d2a957d3b274`.
Cumulative P1 v47 is **16,066/16,320** established, **1,987** substitutions,
**254 facts / 253 documents** open; manifest
`95aca74de51b365239c05a858884eddbccdce3518ea8cc6c7a778cfbe987aeeb`.
No new economic event was published into the accepted 15-event inventory; full
merger census and Full Dataset remain unestablished.

## Targeted older SSE parent-chain source recovery — 2026-09-18

This section is the earlier source-lead snapshot, before the bounded 600832
audit above.

Three previously missing full issuer merger reports were recovered from the
already retained CNINFO metadata, with HTTP-200 original-PDF receipts and
SHA-256 checks in the external `full-merger-v1/targeted-parent-fraction-v2/`
staging directory. Existing implementation-progress/result documents were
cross-checked against the same official bytes; this is source recovery, **not**
new-event or P1 acceptance.

| Parent → surviving security | Newly verified full report | Official terms and implementation crosscheck | Still not established |
| --- | --- | --- | --- |
| 600607 and 600842 → stable 601607 (symbol 600849 at conversion) | [2010-02-02 issuer report](https://static.cninfo.com.cn/finalpage/2010-02-02/57568719.PDF), SHA-256 `a00c485a4082561ef2b6ac8febc915e5209acf1e9ecc6a43e65ed61dbb392b36` | PDF p.82 states 1:1.61 and 1:0.96, whole successor shares and exchange-rule residual treatment. The [progress notice](https://static.cninfo.com.cn/finalpage/2010-02-11/57603961.PDF) confirms both parents terminate on 2010-02-12; the [result notice](https://static.cninfo.com.cn/finalpage/2010-02-25/57623766.PDF) says registry conversion completed 2010-02-23, with unrestricted shares listed 2010-03-01 and the [2010-03-08 resumption notice](https://static.cninfo.com.cn/finalpage/2010-03-08/57663591.PDF) plus [2010-03-09 reminder](https://static.cninfo.com.cn/finalpage/2010-03-09/57667679.PDF) confirm actual trading resumes 2010-03-09. | Exact last-parent trading sessions, parent-specific unrestricted/locked holder treatment, and account-level residual-share award. The master correctly retains one surviving identity across the later 600849→601607 symbol change. |
| 600631 → 600827 | [2011-07-29 revised issuer report](https://static.cninfo.com.cn/finalpage/2011-07-29/59741684.PDF), SHA-256 `1c98b676277a58dc8af791c3f63ff24703f83cb29d954636b589b54e1f51ffb0` | PDF pp.76–77 states each parent A share converts to 0.861 successor A shares, with whole-share and exchange-rule residual treatment. The already retained [progress notice](https://static.cninfo.com.cn/finalpage/2011-08-19/59839426.PDF) confirms parent termination effective 2011-08-23; the [result notice](https://static.cninfo.com.cn/finalpage/2011-08-29/59888838.PDF) says conversion completed 2011-08-26 and newly unrestricted shares list 2011-08-31, while expressly distinguishing locked controlling-holder shares. | Exact last parent trading session, holder-scope/lock treatment, and account-level residual-share award. |
| 600832 → 600637 | [2015-04-22 revised issuer report](https://static.cninfo.com.cn/finalpage/2015-04-22/1200884193.PDF), SHA-256 `7f550aaa4620fc748cc7150a650c5e912e589552f325d782cc6c96273cb287db` | PDF pp.47–48 gives 3.05 parent shares per 1 successor share and whole-share/registry-rule residual treatment. The [2015-05-22 implementation notice](https://static.cninfo.com.cn/finalpage/2015-05-22/1201045132.PDF) identifies a continuous parent halt from 2015-04-30 and termination/record 2015-05-20, and the registry-wide largest-remainder/random-tie rule. The already retained [result notice](https://static.cninfo.com.cn/finalpage/2015-05-29/1201078513.PDF) says registry completed 2015-05-27 and newly unrestricted shares were expected to list 2015-06-03. | Exact last parent trading session, actual first tradable successor session and cash-election/holder scope; exact account-level random award is unknowable but the approved merger research floor is available. |

The registry-wide exact account allocation is not inferred from projected total
shares or a generic rule reference. The separately approved **merger research
floor** can model an unknowable fraction only after the ordinary-A event and
its tradability boundary pass their own source audit; it is not evidence of an
actual account award. These four parent chains remain `SOURCE_INCOMPLETE_NEW_CHAIN`.
The original 601607 resumption PDF hashes are
`f51fea0d6a996ba4c8b9cae6e7551358460789933edf6278702cdf772d6be5ac`
(March 8) and
`1a49666319954ff295783a362050fca396ce4e7b3b4db26a6b2567d7f608fc77`
(March 9); both are checkpointed outside Git.
The 600637 May 22 implementation PDF SHA-256 is
`9143a1fd213b6de73429cfbc9eb35a2e58f045b6a7506d2154e1e0afbb22ea9b`;
its explicit remainder rule supersedes the full report's generic registry-rule
reference for this bounded event.
The existing 15-event accepted inventory, P1 cumulative v46 (16,065/16,320),
full-merger census and Full Dataset status are unchanged. No paid source was used.

## Targeted 000418→000333 source-chain audit — 2026-09-18

The formerly source-incomplete ordinary-A chain now has four original CNINFO
issuer PDFs: the [revised merger report](https://static.cninfo.com.cn/finalpage/2019-03-14/1205897690.PDF),
[parent halt notice](https://static.cninfo.com.cn/finalpage/2019-04-26/1206101714.PDF),
[post-dividend final ratio adjustment](https://static.cninfo.com.cn/finalpage/2019-05-23/1206296146.PDF),
and [implementation/listing notice](https://static.cninfo.com.cn/finalpage/2019-06-19/1206364891.PDF).
For an ordinary unrestricted 000418 A-share holder who did not elect cash,
the last parent trading day is 2019-05-07, continuous halt begins 2019-05-08,
the **final** A-share ratio is 1:1.15144821 (not the earlier 1:1.2110), the
conversion record date is 2019-06-20, and new unrestricted 000333 shares are
listed 2019-06-21. No A-share holder exercised the cash choice. The report's
registry-wide fractional ranking/random-tie rule survives the subsequent ratio
adjustment, whose notice says all other terms remain unchanged; individual
account awards remain unreconstructible and use only the separately approved
research-floor convention. B shares, electing holders, and restricted shares
are outside this reviewed case; the listing notice distinguishes 321,293,876
unrestricted from 2,363,600 restricted new shares.

`backend/scripts/audit_merger_000418.py` verifies all four original PDF
bytes/receipts and page terms, the audited master lifecycle, targeted raw
last-parent/first-converted-share dates, source chronology, and reversed input
order. The immutable external audit is
`full-merger-v1/targeted-parent-fraction-v1/000418-official-event-audit-v2.json`,
file SHA-256 `b948cec937dc3bd7837d532927402daafeb5ab407759063625cb83a1e04c1765`,
canonical manifest SHA-256
`aa76da4feb7265b7e5376fd1388f7a0a7d86933fd219e8b663f824377af1a4f7`,
event checksum `a52b4e6c971686f85b17212ca06cf04120e0983fe48ea531b620a50f13113871`.
This closes exactly one matching P1 official-source request
(`MERGER_NEW:000418:000333`), without creating an economic event. The immutable
source-closure manifest is
`a7de0e6d40166608d5b95fb7a3fc67f4edba0b6d41ef06a498da948b51a385e4`;
cumulative P1 v46 is **16,065/16,320** established, with **255 facts / 254
documents** open. It is **not** a complete merger census, full-dataset admission
or revised frozen inventory. The previously accepted 15-event inventory remains
unchanged pending separate inventory publication.

## Targeted 600253→600056 follow-up — 2026-09-18

Reused the cached 2013 implementation-result notice and recovered only the
identified missing [full revised issuer merger report](https://static.cninfo.com.cn/finalpage/2013-06-04/62552848.PDF)
(412 pages; source SHA-256
`6863c67f6032a118518bd99af0532c9d53a316b7193981f9422fedaa209d8422`).
The result notice confirms 1:0.313, parent termination 2013-07-15, successor
registry transfer 2013-07-26 and unrestricted new-share trading 2013-08-01;
188,668 new shares remain restricted. The full report describes its share
counts as not considering fractional shares, but gives no account-level
allocation/compensation rule. It is not a substitute for the missing parent
holder-fraction treatment. The chain remains `SOURCE_INCOMPLETE_NEW_CHAIN`,
not an accepted new merger event; no P1 count or dataset gate changed.

All 69 retained implementation-document leads have checksum-verified local PDFs
and deterministic terminal classifications. The immutable closure artifact is:

`/home/yuchen/data/research/staging/full-merger-v1/implementation-lead-closure-v1.json`

- Canonical SHA-256: `d78f13e3a1cf817a9e8ea2aaa7773ea758e3bc0251674124f5d8039703dd2cfb`
- File SHA-256: `7f3688175f07c7f38edc0f703acb7950ef7734f552c23d53b4016c165dc25d6c`
- Supported-event evidence duplicates: 34
- Source-incomplete leads for three existing chains: 13
- Source-incomplete leads for eight new ordinary-A parent events: 9
- Out-of-scope B-share parents: 8
- Out-of-scope unlisted absorbed targets without listed-parent mutation: 5

The eight new source-incomplete parent events are 000898→000709,
000761→000709, 600607→600849, 600842→600849, 600631→600827,
600253→600056, 600832→600637 and 000418→000333. Their structures map to the
approved merger policy, but exact holder, fractional and tradability evidence is
not complete, so none was admitted as a supported event.

The full merger/restructuring census remains `NOT_ESTABLISHED`; the existing 15
supported identified events are unchanged.
