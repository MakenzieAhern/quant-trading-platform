# R5 batch source closure — progress, not a terminal gate

The identified rights queue now contains 153 events / 142 securities: all 153
map to the approved direct-subscription/no-subscription policy; 149 retain only
nonessential metadata gaps. Five official events absent from the vendor inventory
are retained for 600005, 601299, 000982, 600978 and 002089. This is **not** a full
exchange census or full-dataset authority acceptance.

The reconciler verifies source bytes, official issuer identity, record-date
language, completed subscription, stated successful ex-rights date, and a matching
pre-event issuance notice. It preserves the nine previously accepted event records.
Unverified vendor prices, ratios and dates remain in prior-row evidence, not in
new authoritative event fields. No quantities, cash or basis are changed by rights
declined under the accepted policy. There is no strategy or account-path run.

CNINFO epochs are decoded in Asia/Shanghai. The explicit document date takes
precedence over an upload date for ex-rights timing (notably 002312, 002074 and
300715). Old snapshots/manifests are immutable. H-share result notices, duplicate
ICBC notices and two JavaScript presentation links are not extra A-share events.

Two reviewed corrections change aggregate subscription/holder totals, not the
ordinary non-subscriber's quantity/cash/basis: 601377 on 2016-01-08 (PDF
9c9df39e87bf02610d2781e13402b95568dc0f312b575f4eb186ba182e992693) and 002363 on
2016-02-02 (20c2bf0091f3208c061e6e62b71cfec9c3232c268419cd91d15c4f271695e616).
Both are preserved; no aggregate amounts or adjustment factors are synthesized.
The later 600256 result references its 2018-03-28 ex-rights notice; 2018-04-10
resumption is not substituted for the earlier ex-date. A cancelled 603616 offering
notice is a source lead, not an executed rights event.

External evidence roots are `/home/yuchen/data/research/staging/`:

- `full-rights-inventory-v1/batch-v3`: 326 PDFs, two non-PDF surfaces, zero retrieval
  failures; metadata pagination retained, checksum verified. Final reconciliation:
  `inventory-batch-reconciled-v3.json`, canonical manifest
  `0b86c12f2c19106523f2ef62229257f36a86d13af35ee099fd014d6250107d08`.
- `full-merger-v1/batch-v2`: 244 retained/extracted PDFs (69 merger leads and 175
  capital-adjustment leads), not 244 accepted economic events.
- `full-code-transitions-v1`: five official code changes split without changing
  stable identities. 600849→601607 uses 2010-03-05, not March 9 resumption.
  The other changes are 601313→601360, 000022→001872, 000043→001914 and the already
  accepted 300114→302132 transition. Current names are not historical-name authority.
- `full-master-evidence`: eleven additional verified-year SZSE PDFs retrieved.
  The old file named `szse-yearbook-2024.pdf` actually contains 2008; preserved,
  never admitted as 2024 evidence. Bounded 110-second timeouts for 2017/18/19/24
  are recorded separately; other years continued without restarting acquisition.
- `full-master-sse-baseline-v1`: official 2010 yearbook contains 2009 statistics.
  Annual trading tables include companies exiting during the year and can omit
  long-suspended companies; their counts alone are not an accepted year-end master.

554 backend tests, Ruff, formatting and mypy pass in the isolated test database.
Remaining merger/restructuring execution, master baseline, ST/suspension,
historical-rule and raw/factor/calendar/benchmark queues continue. Safe start is
not established. Full Dataset created/audited/frozen = NO. No human decision is
requested at this progress checkpoint; no study, merge or release is authorized.
