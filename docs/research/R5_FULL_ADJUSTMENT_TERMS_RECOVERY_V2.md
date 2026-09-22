# R5 full adjustment retained-term recovery v2

## Result

Shared, fail-closed parsing fixes recovered 30 additional exact-date official
term candidates from the existing 1,421 checksum-bound CNINFO documents. No
new document was downloaded and no candidate was admitted as a CorporateAction.

- unique exact official term candidates: **1,341** (previously 1,311);
- no exact official term candidate: **42** (previously 72);
- cash-only / cash-plus-bonus / bonus-only shapes: **824 / 476 / 41**;
- differentiated ordinary-public-A cash candidates: **3**, each retaining its
  holder-class and policy identifier;
- gross cash-plus-bonus factor checks / conflicts: **476 / 476**;
- input-order reproducibility: **PASS**;
- adjustment authority promotion: **NO**.

The recovered cases cover old explicit pre-tax wording, split OCR security
codes, final revised-capital schemes, standard capital-reserve implementation
titles and deterministic date OCR artifacts. Restructuring allocations,
date-conflicting notices and the two remaining exact-date complex-holder cases
remain fail-closed.

## Immutable evidence

| Artifact | File SHA-256 | Canonical manifest SHA-256 |
|---|---|---|
| `full-adjustment-audit-v1/official-terms-candidates-v6.json` | `867a3f26fa1f17807ab75d1cd15f430ecd6eb0f30918a4b121e3f5f4999ed55e` | `fa5f479ce02574b25939bd0115b242fd1f0a2414aea5f12efe274dc6de47955c` |
| `full-adjustment-audit-v1/factor-economics-v5.json` | `c5e3c73178e5fc5f2a04d36efb71a5fff3948f13026743396ef45c6a8cfcd527` | `48de239de63c97c986e0720fff14de09e71375d2ae6d87ce2b10c3afe840993e` |

Full adjustment authority remains PARTIAL. No dataset or study was run.
