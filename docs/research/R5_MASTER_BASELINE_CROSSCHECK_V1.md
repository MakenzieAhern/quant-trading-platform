# R5 2009 master membership cross-check

SSE: all 860 active master intervals are present in the retained 2010 yearbook's
2009 company-information table (PDF pages 208-242). The table also contains three
earlier exits, two later IPOs and ten B-only companies. They remain explicit in
the audit; they are not admitted at the 2009-12-31 boundary. The annual trading
table is not substituted for a year-end membership roster.

SZSE: the retained 2009 directory has 830 company codes. Twelve are B-only
company-code aliases, corroborated by the same yearbook's 200xxx B-share rows.
They are not ordinary A-share securities. The 818 remaining directory entries
plus 18 reviewed 2009 annual-report identities cover all 836 active master
intervals. Paused issuers are retained rather than dropped to match a directory.
No historical ST effective date or daily tradability is inferred from these names.

Targeted recovery reused the original master/yearbooks and existing CNINFO issuer
identifiers. Filtered annual-report searches produced false negatives; for example,
000038 keyword/category queries returned zero annual reports, while the unfiltered
issuer/date listing contains 2010-04-24/57864076.PDF. All original responses remain.
Bounded issuer/date queries recovered 28 documents, including annual reports for all
18 gaps and related corrections/notices. All 28 downloads succeeded with receipts.
Only the explicitly reviewed annual-report identities supplement membership.

000670 has a garbled text layer. PDFium rendering of PDF page 3 confirms the
exchange, security code and company identity. 000693 emitted a PDF structure
warning; its identity page 4 was visually verified. The original 000981 report
also emitted an EOF warning; its corrected report is the reviewed version.
These checks do not certify every financial figure or the entire PDF structure.
No raw source was rewritten, and a text-extraction failure is not missing history.

Review: FULL_MASTER_2009_SUPPLEMENT_REVIEW_V1.json (URLs, SHA-256, publication and
retrieval dates, page references). The source batch is external:
/home/yuchen/data/research/staging/full-master-szse-baseline-v2/annual2009-v1/source-manifest.json
canonical SHA-256 5f904de30336529e15c5b61866dc9e6279c00ab5d8153cbde26939b64ba3b646.

Membership audit:
/home/yuchen/data/research/staging/full-master-szse-baseline-v2/membership-crosscheck-v3.json
canonical SHA-256 95def4159b568fc8c76cc3653cd7421518b6d68943319deaee8f3898ad09efea.
The retained v1 identified a parser omission of the 001 prefix; it was corrected
and regression-tested, not treated as a source gap or a security exclusion.
The final audit preserves the existing master's inclusive effective-to convention.

Both exchanges: PASS_MEMBERSHIP_CROSSCHECK. Full master acceptance remains PARTIAL:
in-period lifecycle/instrument/board coverage and the other full-history authorities
still require their full audits. Safe start remains NOT_ESTABLISHED. This is not an
independent proof that no security is missing from every source.
576 backend tests PASS; lint/type checks PASS. No dataset or study is authorized by
this membership result. Distribution workers and the remaining R5 queues continue.
