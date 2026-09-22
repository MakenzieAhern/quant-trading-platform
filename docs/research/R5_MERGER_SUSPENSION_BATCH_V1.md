# R5 merger suspension-boundary batch

The three prior reviewed-candidate chronology gaps are closed using policy-matrix
class 14, not invented registry timestamps or additional human methodology.
The reviewed inventory now has nine supported candidates and zero unresolved
within that set. The full-market merger census remains NOT_ESTABLISHED.

| Parent | Successor | Ratio | Record | Daily boundary |
| --- | --- | --- | --- | --- |
| 600553 | 601992 | 1.2 | 2011-02-01 | 2011-03-01 |
| 600991 | 601238 | 1.6 | 2012-03-06 | 2012-03-29 |
| 601299 | 601766 | 1.10 | 2015-05-20 | 2015-06-08 |

600553 and 600991: retained implementation notices establish automatic conversion
for non-electing ordinary holders, global fractional allocation and continuous
suspension through delisting. Retained successor listing notices establish the
unrestricted converted shares' first trading date. Targeted unadjusted observations
corroborate the boundaries; they do not establish full raw-data authority.

601299: three targeted official PDFs close the exact identified source gaps:

- 2015-05-18/1201027137.PDF: ratio, record date, May 7 halt, global fractions.
- 2015-06-01/1201085316.PDF: A-share registration completed May 28; new shares
  listed June 4; the notice explicitly says listing is not trading resumption.
- 2015-06-03/1201096263.PDF: successor resumes June 8.

All URLs are under https://static.cninfo.com.cn/finalpage/; exact SHA-256,
retrieval UTC, publication dates and reviewed pages are in the fixture below.
The retained completion report also confirms the cash-election offering. Default
non-participation is unchanged. H-share conversion May 26 is NOT the A-share date.
June disclosures are not applied retrospectively to May 28. The research mutation
uses the approved first tradable boundary June 8; registry completion remains a
separate factual field. No synthetic trade or cash election is introduced.

Fixture: backend/tests/fixtures/merger_suspension_boundary_batch_v2.json.
Source audit: /home/yuchen/data/research/staging/full-merger-v1/reviewed-suspension-boundary-batch-v3.json.
Canonical manifest: 62f5d5a3068cb1ee02e9d36523e08f58e1d5aa5e4454507d7db8fc028009b676.
Inventory: MERGER_INVENTORY_V4.json; prior versions remain intact.

Final parser-byte revalidation (same events, after lint-only cleanup):
reviewed-suspension-boundary-batch-v4.json, canonical
3af6a715e86b0c91e930cdfb6d706b9c9713faa9f855e4c4f6849dc2753a63ef.
575 backend tests PASS; lint and formatting PASS.

The shared reconciler re-parses retained raw rows, rejects duplicate/unsorted dates,
checks source bytes and master dates, and rejects unknown boundary policies.
Existing accounting fixtures exercise floor/zero-whole, full basis transfer,
unchanged cash, no order/fill, no trading PnL and persistence roundtrip.
Full account-path materiality is not established; no strategy was run.

Acquisition continues independently. Dataset CREATED/AUDITED/FROZEN remain NO.
