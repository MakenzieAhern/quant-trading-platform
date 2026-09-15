# Source input user action plan v1

`SOURCE_INPUT_REQUIREMENTS_V2_MINIMAL` remains the immutable checklist: 16,328
event-level requests, 16,312 unique official documents, P0=2, P1=16,304, P2=5 and
P3=1. The approved 664 differentiated-cash groups are not source gaps.

## Smallest human action

1. Use an organization able to contract for [SSEInfo historical/basic data](https://www.sseinfo.com/services/assortment/historical/) and request a 2010-01-01 through 2025-12-31 SSE point-in-time security-master export containing listing, delisting, code, name and board history. Put the delivered original files in `/home/yuchen/data/research/manual-official-input/sse/cross-year/`.
2. Log in to [CNINFO Data Service](https://webapi.cninfo.com.cn/n#/product/package?packageId=98) and obtain the full historical outputs for company basic information, stock basic information, institution/name changes, security-abbreviation changes and company listing-status changes. Filter the SZSE records into the same 2010-2025 lifecycle scope and put the original export in `/home/yuchen/data/research/manual-official-input/szse/cross-year/`.
3. In the same CNINFO account, obtain authorized access to the [announcement information package](https://webapi.cninfo.com.cn/n#/product/package?packageId=11) for the P1 2011-2025 archive. Use its date/market/`maxID` bulk interface; do not download 16,226 documents by hand. Save returned original PDFs under the manifest's `cninfo/{year}` destinations.

The official pages are public and previews work, but SSE full delivery requires a
business application and CNINFO full export requires login and may deduct fees.
No purchase, account creation or business application was submitted automatically.
Once access or exported bytes are supplied, resume from the V2 manifest; do not
restart source acquisition.

Machine manifest:
`/home/yuchen/data/research/staging/source-input-requirements-v2-minimal/manifest-v2.json`

- canonical SHA-256: `96839c742cb12c9e0ea0c8301b990474554f64bfd2abf34579f8190b2e8017c7`
- file SHA-256: `e9b7bb31868958c4bffd1dd9a31b26c33f0ad71c3b46c2e83adb7dd691b37559`

## Priority

| Priority | Unique documents | Action |
| --- | ---: | --- |
| P0 | 2 | Provide full official SSE/SZSE master exports first. |
| P1 | 16,304 | Provide material event/rule/corporate-action evidence. |
| P2 | 5 | Provide supporting authority documents after P0/P1. |
| P3 | 1 | Optional metadata-only mirror; not a readiness blocker. |

## Source groups

| Official source group | Documents | Event back-references | Material | Years |
| --- | ---: | ---: | ---: | --- |
| CNINFO | 16,226 | 16,242 | 16,226 | 2011-2025 |
| SSE | 63 | 63 | 62 | 2011, 2012, 2016 |
| SZSE | 1 | 1 | 1 | cross-year |
| Issuer official sites | 11 | 11 | 11 | cross-year |
| Official yearbooks/fact books | 4 | 4 | 4 | 2017-2019, 2024 |
| Other authoritative public sources | 7 | 7 | 7 | 2012 |
| ChinaClear | 0 | 0 | 0 | none |
| Court / restructuring administrator | 0 | 0 | 0 | none |

## Access disposition

One P2 document was already cached. A new exact filename/official-URL archive scan
found seven additional P1 CNINFO PDFs with prior HTTP-200 receipts. They were copied
with their receipts to the exact manifest destinations, leaving 16,297 net-new P1
documents. Current receipts otherwise retain 229 official HTTP-403 results and 351
DNS failures; no denial is bypassed and no unofficial mirror is accepted.

Provide original official files or an official bulk archive, or restore authorized
access to the listed official endpoints. Keep original filenames; manual renaming
is unnecessary. Place files beneath the manifest's exact `local_destination`
folders rooted at:

`/home/yuchen/data/research/manual-official-input/`

The machine manifest remains the authoritative item-by-item checklist. The bulk
collection plan is `docs/research/P1_BULK_COLLECTION_PLAN_V1.md`. No generic intake
implementation exists yet; add only the minimum matcher after P0 bytes arrive.
