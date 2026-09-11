# Controller run

RUN_ID = 20260911-R1-06
START_SHA = 9f590e7b6c36fbc6d73a42c539493858d07bcc1e
END_SHA = Resolve with git log -1 --format=%H -- docs/orchestration/RUN_REPORT.md
CURRENT_STAGE = R1
STATUS = AWAITING_HUMAN
BRANCH = feature/a-share-research-v1.1
PR = 12 OPEN / UNMERGED
CI = Verify publication HEAD after push; previous HEAD CI passed

14 official SZSE sources downloaded and inspected; all four supplied replacement
sources succeeded. No dead original URL requested. 28 rule-level claims committed
as a provenance ledger; raw HTML/PDFs remain outside Git. Full-history acceptance
is separate from Pilot. Original-PDF blocker retired.

PUBLICATION_DATE_PROVENANCE = PASS (2023-02-17; 深证上〔2023〕98号)
EFFECTIVE_DATE_PROVENANCE = PASS (2023-04-10; technical PDF p18)
FULL_HISTORY_RULE_AUTHORITY = PARTIAL
PILOT_RULE_AUTHORITY = PARTIAL
MARKET_RULE_AUTHORITY = PARTIAL
SOURCE_AUTHORITY_PREFLIGHT = FAIL

| Check | Result |
| --- | --- |
| RULE_SOURCE_PROVENANCE | PARTIAL |
| RULE_VERSION_BOUNDARY | PASS |
| BOARD_PRECEDENCE | PASS |
| MAIN_BOARD_PRICE_LIMIT | PASS |
| CHINEXT_PRICE_LIMIT | PASS |
| NEW_LISTING_EXCEPTION | PARTIAL |
| PRICE_CAGE | PARTIAL |
| INTRADAY_SUSPENSION | PARTIAL |
| ST_RULE_INTEGRATION | PASS |
| LISTING_AGE_RULES | PARTIAL |
| LOT_SIZE_RULES | FAIL |
| TICK_SIZE_RULES | FAIL |
| SUSPENSION_RULES | PARTIAL |
| ORDER_REJECTION_RULES | FAIL |
| TRANSACTION_COST_EFFECTIVE_DATES | PARTIAL |
| INPUT_ORDER_REPRODUCIBILITY | PASS |
| CHECKSUM_REPEATABILITY | PASS |

Checks distinguish matching rate metadata from actual execution. Next-open
MARKET, unchecked order caps/off-tick fills and multi-day accepted orders cannot
pass. Daily bars do not prove auction liquidity. 12 unclosed claim IDs and exact
reviews are in the JSON ledger. Settlement-fee provenance remains incomplete;
commission 0.0003 is an existing assumption, not an exchange-mandated rate.

Backend = 356 tests PASS; Ruff/format/strict mypy PASS.
Offline claim auditor verifies every source hash, pins reviewed implementation
hashes, rejects changed code/third-party URLs/later-rule behavior, and repeats
with reversed inventories. No strategy research executed.
Rule .5 versions preceding Main 2021 regime and distinguishes first IPO session,
while preserving the existing conservative no-fill treatment.

RULE_SOURCE_MANIFEST_SHA256 = 6dac2bab94829a6f726f76a185309e5ebca752c285e11d1fc31cc2ae011b81f2
NORMALIZED_RULE_SHA256 = a2910f18646d8670feeb52dcf4af7b593f6f988e880b8cc95d1959dfd4a2b625
RULE_CLAIM_AUDIT_SHA256 = a632bb7c357c5b823144359a45f662956ed057d7d08e755cf92e0f004ee17876
SOURCE_PREFLIGHT_SHA256 = 73030b9314c9ed4582c7c0526c92872bb13b39e359d725a09a58c7792933a92e

DOCKER_RECOVERY = PASS
POSTGRESQL_HEALTHY = YES
REDIS_HEALTHY = YES (PONG)
BACKEND_HEALTHY = YES (/api/health 200)
FRONTEND_HEALTHY = YES (configured 5173 HTTP200)
PILOT_DATASET_CREATED = NO
PILOT_A_SHARE_DATA_READINESS = BLOCKED
DATASET_AUDITED = NO
DATASET_FROZEN = NO
DEVELOPMENT_STUDY = NOT_RUN
VALIDATION_STUDY = NOT_RUN
OFFICIAL_OOS = NOT_RUN
HUMAN_APPROVAL_GATE = NONE (not Gate A)
HUMAN_APPROVAL_REQUIRED = YES
SINGLE_SMALLEST_BLOCKER = PILOT_EXECUTION_CONVENTION_DECISION_REQUIRED
PR_MERGED = NO

Next decision is execution convention, not another original-PDF download request.
After approval, close implementation/evidence claims and rerun the source gate
before R2/R3. Seven previously accepted data authorities unchanged.

Offline reproduction (from backend; staging root is the preserved external directory):

```sh
python -m scripts.audit_market_rule_authority \
  --ledger ../docs/research/SZSE_RULE_CLAIMS.json \
  --repository .. --staging /path/to/research/staging \
  --output /path/to/research/staging/market-rule-claims-20260911/rule-claim-audit.json
```

The manifest digest is SHA256 of the canonical normalized JSON (UTF-8, sorted
object keys, compact separators; source/claim inventories sorted by identity).
It is not the pretty-printed JSON file's physical byte digest. Semantic reviews
are explicit human-readable judgments bound to code/source bytes, not claims of
an automated legal parser. Raw snapshots are not refetched by this command.
