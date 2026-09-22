# R5 full adjustment retained-term recovery v3

## Result

Two additional deterministic PDF-text artifacts were removed from date parsing:
an embedded board-guarantee line and an issuer-template page header. Together
with v2, this recovers 32 exact-date official term candidates from the existing
retained corpus without downloading a document.

- unique exact official term candidates: **1,343**;
- no exact official term candidate: **40**;
- cash-only / cash-plus-bonus / bonus-only shapes: **825 / 477 / 41**;
- gross cash-plus-bonus factor checks / conflicts: **477 / 477**;
- differentiated ordinary-public-A candidates: **3**;
- input-order reproducibility: **PASS**;
- adjustment authority promotion: **NO**.

The 40 residuals are fully source-covered and are no longer represented as an
opaque missing-document queue:

- restructuring or directed-capital mechanics: **27**;
- official distribution date mismatch or unreadable/OCR date boundary: **12**;
- complex holder-class terms: **1**.

These classifications do not establish holder entitlement, correction
precedence or the historical factor provider's normalization convention.

## Immutable evidence

| Artifact | File SHA-256 | Canonical manifest SHA-256 |
|---|---|---|
| `full-adjustment-audit-v1/official-terms-candidates-v7.json` | `22da493a9e1ea0bec3baf0e9e175c129fbfbdec63a07401e0e3795c806e8f1e5` | `f934e27f416ebf1fe760cd69070e8a12b571b8d200afa04b5baf36a498427c68` |
| `full-adjustment-audit-v1/factor-economics-v6.json` | `1c7d9c5d8d7ae3994521ebd7992958e6dc7f223a853a2a91087a7c71839a21f9` | `e34d1bd6758942e7f107079c007812ec2681ac39aec02a361754765b616b560e` |
| `full-adjustment-audit-v1/retained-term-residual-classification-v1.json` | `318cba8fd5617adb2aab708a7c6302139f9518fb7a15dca57cdc277d65f64cad` | `083bc89bb456580a838c1f752ea23950379cc7bc9044f230fa94a68c0cb85628` |

Full adjustment authority remains PARTIAL. No dataset or study was run.
