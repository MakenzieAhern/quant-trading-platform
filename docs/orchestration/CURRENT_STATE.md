# Current state

R1 AWAITING_HUMAN for push-identity clarification, not Gate A.
Latest attachment requires MackenzieAhern; actual Git/GitHub identity is
MakenzieAhern. No identity change or push performed. Branch
feature/a-share-research-v1.1, PR #12 open/unmerged; starting HEAD
5e4903a14005019d7058a4b5ff18bee170ae09ae.

Master/SSE/SZSE/calendar acceptance preserved without reacquisition.
Sina adjustment route PASS under frozen sina-multiplicative-asof-v1:
P(t)*H(t)/H(T), t<=T, immutable vintage, raw execution. Five securities,
21 SDK price dates and six raw control dates checked. Historical nonuniform
vendor corrections remain a disclosed versioning risk, not permission to refresh.
This is not an archived publication-time dataset. See
docs/research/SINA_ADJUSTMENT_ACCEPTANCE.md.

Raw OHLCV route PASS at sample/route scope, not full-universe completeness.
Four ordinary samples each have 382 bars. Exited control 000732 has 100 bars;
the other 282 calendar sessions are NOT automatically missing observations
or suspensions. CSI300 price-index route PASS: 382 sessions exactly aligned.

External staging acceptance manifests (canonical SHA-256):

- Sina: 711ba1895a8952cfebcac25f85446d5cc35963f729b0695ca7684e9dfcb23403
- OHLCV: 1899343e4ea40727875e6f2058f05794d586918033938b341146dae24258265b
- CSI300: 97a465b961d6310afeae8cd4f6bedcd998bd07cee1cccecd3bdb383f1159ec4d
- Preflight: 541f7eb754d92c27b094f077ab23e37ff1506947330d59afe368136864ae2b19

SOURCE_AUTHORITY_PREFLIGHT = FAIL: MARKET_RULE remains UNVERIFIED.
Main-board registration effective date corrected to 2023-04-10, version
cn-a-2010-2025.2, with regression coverage. Remaining audit found that
DailySecurityStatus cannot represent the first delisting-period session.
300336 issuer notice 2023-044 specifies 2023-06-12 as that first session,
without a price limit; current ChiNext resolver returns 20% for either is_st
value. Existing SZSE audit retains 384 DELISTING_PERIOD lifecycle security-days,
not a count of traded bars. Do not collapse these into NORMAL/ST or exclude
whole securities to force acceptance. Complete effective-dated mapping and
regression checks before promoting market rules.

Dataset not created/audited/frozen; no studies/OOS. Gate A NOT reached.
After identity clarification publish checkpoint and continue R1 -> R2 -> R3.
Legacy BaoStock recovery is not required. Machine authority:
.research/project_state.json; read-only controller returns STOP for this pause.
