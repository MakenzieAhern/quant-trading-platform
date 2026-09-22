# Approved partial-surrender boundary and fractional convention

The exact account-level CSDC book-entry date and fractional allocation rule for the 600462 restructuring are not publicly evidenced in the retained sources. Because the security was non-trading through the relevant transition, the research engine applies the corporate action immediately before the first post-event tradable Bar. Fractional surrender is conservatively rounded upward at the surrendered-share level.

CN_A_MANDATORY_PARTIAL_SHARE_SURRENDER_POLICY_V1 remains unchanged. This approval
adds CEIL_SURRENDER_FLOOR_RETAINED_V1 and FIRST_POST_EVENT_TRADING_BOUNDARY_V1.
Approval attachment SHA2566f14546633e87d4a3dfec3564d92e03de07b6778b0636e4f86193994772f03b1.

Compute theoreticalQ*S; ceiling (cappedQ) becomes actual research surrender;
retainedQ=Q-ceiling. Retained basis B*retainedQ/Q, surrendered basis the difference.
If retainedQ0, retained basis/average0 and full B becomes corporate-action loss.
Cash, orders, fills, trading realizations and external capital do not change.
Audit-only floor difference uses only the already observed pre-event mark.
Research date and historical date are distinct fields; boundary sources and approval
checksum required. The existing deterministic engine opening phase is an ordering
marker, not a fabricated CSDC timestamp. The event is applied before resumed bar
execution, valuation and strategy/risk/target processing. Missing/nontradable boundary
data fail closed. Unknown or tradable intraperiod events cannot use this convention
without establishing the nontrading boundary conditions.

Source-level exact historical admission remains PARTIAL in the evidence receipt;
research accounting acceptance is PASS_UNDER_APPROVED_CONVENTION. These are not
contradictory. Aggregate share counts PASS; unresolved exact holder registry rules
are disclosed, not silently converted into facts.

## Reachability audit

See600462_APPROVED_CONVENTION_REVIEW_V1.json for the complete induction and18 source
receipts. Retained2010/2011 annual reports confirm no stock/rights quantity changes;
2010 unlocking changes tradability only.2012 share changes reconcile to surrender
and separate issuer issuance. Startingflat under existing all-or-nothing100-share
cash-account execution and no external transfers, pre-surrender holdings belong
to100*n. Every reachable subset constrained by capital/liquidity is also divisible5.
Thus FRACTIONAL_SURRENDER_CASES=0, ZERO_RETAINED_CASES=0 for positive holdings,
MAX_EXTRA_SHARE_SURRENDERED_VS_FLOOR=0 and MAX_ESTIMATED_ECONOMIC_DIFFERENCE=0.
INTEGER_SURRENDER_CASES=all reachable positive states, not an observed strategy count.
No strategy was run to obtain these results. Actual trade counts/maximum capital-
feasible quantity are not inferred. If historical incoming conversions or an altered
fill/lot/imported-holding pipeline is introduced, invalidate and rerun this certificate.

Generic stress cases1/6/101 exercise fractional/zero outcomes with maximum1 extra
whole share versus floor; value uncertainty equals one already-observed pre-event
share price. This is distinct from600462's verified quantity lattice. Source order
reversal, resumed-price perturbation, no-bar/invalid-boundary guards and database
roundtrip checks PASS.528 full backend tests/Ruff/format/mypy PASS.

Lineage/event checksum cdcaa9586d930eaeac52edc23c7f099221925f63759d70ee981b53a7ed6ae14b.
Evidence manifest a4d49ac37c9bff57485be7087122707ad0e03b788cfc39d776e509fdb00fd83a.
Prior immutable receipts and unapproved historical fixture preserved.
R5 resumes existing census/authority queues; no full freeze or formal study authorized.
