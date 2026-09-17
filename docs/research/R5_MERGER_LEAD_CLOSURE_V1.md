# R5 Merger Implementation Lead Closure V1

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
