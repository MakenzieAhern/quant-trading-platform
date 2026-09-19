# R5 adjustment residual mechanics v1

## Result

The 33 factor changes previously lacking retained implementation candidates now
have checksum-bound official CNINFO coverage. This closes the source-discovery
gap, but not full adjustment authority:

- official source coverage: **33 / 33**;
- official capital/share mechanics matching the retained factor step: **25**;
- exact official gross-cash terms recovered: **7**;
- provider factor-basis semantics still unresolved: **8** (the seven cash cases
  plus the 000156 additional-issue boundary);
- input-order reproducibility: **PASS**;
- authority promotion: **NO**.

The 25 parity results describe price-normalization mechanics only. They do not
create holder entitlements. In particular, 000757 and 002506 explicitly direct
the capital increase to a restructuring/administrator account; their factor
parity cannot be reused as portfolio share credit.

## Targeted official recovery

The prior 60-day join was replaced only for the identified 33-row evidence gap
by a bounded 365-day CNINFO metadata query. It retained 3,955 metadata records,
then reduced them to 55 high-specificity official PDFs. All 55 were acquired or
reused with zero failures. One older official 000757 annual report was added to
verify the 2011 restructuring ratio and its non-holder allocation.

The shared final-distribution title parser now accepts a final `特别派息实施公告`,
which recovers 000550's exact 2018-03-27 gross cash term without a symbol-specific
exception.

## Residuals

The seven cash cases establish gross shareholder cash, record date and ex-date,
but not the historical factor provider's tax/net normalization convention.
000156 establishes the 978,090,000-share non-public issue at CNY 2 per share and
the 2012-10-19 listing/restoration boundary, but the observed factor step
`1.54062` is not admitted without a reproducible official formula.

Therefore:

`FULL_ADJUSTMENT_AUTHORITY = PARTIAL_ECONOMIC_ALIGNMENT_AND_EVENT_COMPLETENESS_NOT_ESTABLISHED`

## Immutable evidence

| Artifact | File SHA-256 | Canonical manifest SHA-256 |
|---|---|---|
| `full-adjustment-residual-metadata-v2/bounded-metadata-v2.json` | `cf08a6526cde0e3316f2f5cd77985be3d49316b90a0562ecc1e1dcfe6d350826` | `2d43f65f4f6e2933b529fc27bd894628cd3df0613defdbce797efc241436304a` |
| `full-adjustment-residual-metadata-v2/source-queue-report-v1.json` | `ad7cb2ff2e11f5975c3ce408390a5b3204b16fedfe0041a53fee8bf44243dd2a` | `688a8c73a464dc31718fd7f45dee5028a737eb5b0d994fb80a807e9392f339c7` |
| `full-adjustment-residual-sources-v1/batch-v1/source-manifest.json` | `094eacea62fb9e2d8e9fc2744c21fb9f7c90190fafc5ac80d7e1427ec31af994` | `8d9ab6f60239fcbbd8e82804a5554600d63e6f885ed527ec447cae35843fb9a9` |
| `full-adjustment-residual-supplement-v1/batch-v1/source-manifest.json` | `881434c30d6bb838d19a48f8c3b98c49b8dc0abe59a4bd3c1511878fa4d72420` | `7175e453c00057ca9dec866dc3eed3b411d7af2881ae39a8989008bdc1f9986a` |
| `full-adjustment-residual-sources-v1/official-terms-v2.json` | `b4d7809104a7dd1685dcbada153f35fbb3091aa2ed5444e612d2ab8bc17b866f` | `5b1573e5b45181a9eee522cc13a83587cf66b7153fb7de3cf07fcbec3398068a` |
| `full-adjustment-residual-sources-v1/residual-mechanics-v1.json` | `30cecf509b60cfd6ada085ff0afa7c274af4cadb94cc22352415857df915cd62` | `a38d55a2a3a5b4b6d6c0a672cac48ee4a9565efbc57fa13a2abc237916f7f35a` |

No market dataset was created, audited or frozen. No study was run.
