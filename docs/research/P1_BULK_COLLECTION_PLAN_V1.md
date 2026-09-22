# P1 bulk collection plan v1

This plan is an acquisition overlay for immutable
`SOURCE_INPUT_REQUIREMENTS_V2_MINIMAL`; it does not change that manifest or any
accepted methodology. It turns 16,320 P1 event back-references into 16,304 unique
official documents and five source-family collections. Sixteen duplicate document
requests are already collapsed by the V2 back-references.

## P0 before P1

| Exchange | Required official export | Official route | Destination | Status |
| --- | --- | --- | --- | --- |
| SSE | Complete point-in-time listing, delisting, code, name and board history, 2010-01-01 through 2025-12-31 | [SSEInfo historical data](https://www.sseinfo.com/services/assortment/historical/) and [SSE intelligent data](https://www.sseinfo.com/services/sseai/aidata/) (`证券基本信息` / `主参考数据`) | `/home/yuchen/data/research/manual-official-input/sse/cross-year/` | Public product page verified; full delivery requires business application, approval and agreement. |
| SZSE | Complete point-in-time listing, delisting, code, name and board history, 2010-01-01 through 2025-12-31 | [CNINFO listed-company incremental basic data](https://webapi.cninfo.com.cn/n#/product/package?packageId=98): company basic, stock basic, institution/name changes and listing-status changes | `/home/yuchen/data/research/manual-official-input/szse/cross-year/` | Free preview verified; full export requires login and may charge. |

P0 remains 0/2 resolved. Current/annual tables and yearbooks are corroboration,
not substitutes for these complete historical exports.

## P1 collection families

| Collection | Unique documents | Event back-references | Partition/checkpoint | Official route and acceptance |
| --- | ---: | ---: | --- | --- |
| CNINFO A-share announcement archive | 16,226 | 16,242 | Calendar day, then `market`; resume with maximum `OBJECTID`/`maxID`; store by year | [Announcement information package](https://webapi.cninfo.com.cn/n#/product/package?packageId=11). The documented interface returns announcement date/title/address/format/size/market, limits each response to 20,000, and requires one-day requests for market-wide categories. Full export requires login and may charge. Download only official returned PDF addresses. |
| SSE ST/name notices | 61 | 61 | One bundle for each manifest year/category, with the 59 cross-year gaps retained as one explicit queue | Official SSE archive or an SSE-provided bulk export. Two known endpoints remain 403; no retry loop or bypass. |
| Issuer implementation/registry/tradability chains | 11 | 11 | One manifest-keyed cross-year bundle for the eleven security IDs | Original issuer official-site files or an official archive export; no inferred execution terms. |
| SZSE statistical yearbooks | 4 | 4 | 2017, 2018, 2019 and 2024 | Exact official `docs.static.szse.cn` URLs in the V2 manifest; preserve original filenames. |
| Other authoritative full-range inputs | 2 | 2 | One raw-unadjusted partition bundle and one daily suspension/resumption bundle | Exact manifest destination; authority must remain the already approved source class. |

Operationally, each acquired file keeps its original bytes and name, plus a receipt
containing source URL, retrieval timestamp UTC, byte size and SHA-256. Downloads are
checkpointed by collection/year/day and resumed only from the last durable receipt.
No large source files enter Git.

## Existing archive reuse

A filename/official-URL scan of existing source archives found seven P1 CNINFO PDFs
missed by the V2 access disposition. Their prior HTTP-200 receipts, timestamps and
SHA-256 values were revalidated, and the original bytes plus receipts were copied to
the exact `manual-official-input/cninfo/{year}` destinations. No event is accepted
merely from the copy; the normal strict parser/intake remains required.

Therefore:

- P1 raw event requirements: 16,320
- P1 unique official documents: 16,304
- P1 already local after archive reuse: 7
- P1 duplicate event requests collapsed: 16
- P1 net-new official documents: 16,297
- P1 collection families: 5

No existing generic intake/matcher was found in the repository, so no second intake
framework was added while P0 remains blocked.
