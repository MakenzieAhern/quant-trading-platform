# Restructuring bonus pass-through V1

Human approval SHA-256: b42ec74db5f29f3a1434b96bdc04f9833dcb572a20198ee5b6fe69e3fe7293d6.
Policy: CN_A_RESTRUCTURING_BONUS_PASS_THROUGH_POLICY_V1.
Accounting: NET_PASS_THROUGH_NO_BASIS_ALLOCATION, a research convention, not a legal fact.

## Accepted 600817 evidence

Five official issuer PDFs are reconciled in 600817_APPROVED_PASS_THROUGH_REVIEW_V1.json.
Pre-event shares128,728,066; new shares32,182,016; ratio25%; post-total160,910,082.
The February2013 resumption notice explicitly confirms registration2012-07-31 and
transfer2012-08-01. The August2012 completion notice independently confirms transfer.
Original shares remain unchanged. The original notice's conflicting July26/July30
record dates remain visible; neither is substituted for actual registration.

The pre-effective implementation mandates automatic CSDC credit/transfer. The company
was suspended from2010-04-09, with resumption2013-02-08. There was no ordinary trading
opportunity in the temporary interval. Issuer-level asset receipt is not holder consideration.
The reference5.65 derives from prior7.06 and25% capitalization, but is never a Fill or mark.
Subsequent Portfolio valuation uses actual raw observations only.

## Accounting and lineage

The immutable generic event enters ResearchSession and central PortfolioEngine.
Q/B/average/cash/realized PnL remain unchanged; only a typed snapshot audit is appended.
Q*ratio is theoretical metadata, explicitly not a reconstructed CSDC fractional allocation.
No temporary asset, basis, order or fill exists. Metadata persists through an additive,
reversible JSONB migration20260913_0010. Prior snapshots default to an empty audit list.
Later confirmation sources stay in lineage and are removed from strategy inputs.
Pre-effective terms are required. Compensated, tradable, monetizable and unknown variants
fail closed; ordinary retained bonuses and original-share surrender are separate.
Same-session conflicting corporate-action legs are rejected before mutation.

Source replay command (from backend; external staging/output arguments are required):

```text
python -m scripts.audit_pass_through_evidence --review ../docs/research/600817_APPROVED_PASS_THROUGH_REVIEW_V1.json --event tests/fixtures/600817_pass_through_v1.json --staging EXTERNAL_STAGING --output EXTERNAL_RECEIPT
```

Event SHA-256:87906998560350451581d053659cca0bd43ee7223759e779928a2bda216d039a.
Evidence manifest:0e100b6ec0a586daa97b7bd599ce2669ab88cae22a83da72365dd5396b3ff2f2.
Receipt verifies five original PDFs and input-order repeatability, not full census completeness.

## Preserved R5 continuation

Prior600462, rights, merger, demerger, Pilotv2 and authority decisions are unchanged.
Capital-adjustment metadata175 documents are leads, not175 events. Chronological review
has additionally inspected twenty-one2010-2015 plan documents. Proposals are not execution
evidence. Identified analogous leads000818 (mixed retained/pass-through bonus),000757
(original surrender plus administrator capitalization),000035 (ordinary-holder all-new-share
pass-through) require final-plan/registration/eligibility reconciliation; none is silently admitted.
Ordinary original-surrender leads000034/000587/600699/000030/600757/000787/000557/600678/
000820 remain in source work.002145 revised proposal affects controlling shareholder only.
No full census total or historical Portfolio quantity total is claimed.
Full dataset2010-2025 remains uncreated, unaudited and unfrozen. No formal studies authorized.
Latest continuation and new600381 consolidation gate: PASS_THROUGH_R5_CHECKPOINT.md.
