# Reproducibility

Verify a frozen dataset with:

```bash
PYTHONPATH=backend python backend/scripts/verify_dataset.py <dataset-id>
```

Development and validation ran only against the immutable full dataset. The Development replay
and a separate-process S0/S1 check passed. Candidate configurations were frozen before Validation.
Gate C froze S4 before OOS, and the exactly-once Official OOS claim is consumed. Do not rerun OOS.

Completed runs must persist their Git SHA, canonical manifest checksum, provider/version,
rule version, strategy configuration SHA-256, transaction costs, CSI300 benchmark lineage,
temporal split, random seed and sanitized failure information. Reproduction then uses only the
persisted run ID; provider APIs are never called during calculation.

To register the three immutable formal artifacts in a local PostgreSQL ledger:

```bash
PYTHONPATH=backend python backend/scripts/publish_formal_research.py \
  --dataset /data/research/cn-a-research-20100101-20251231-v1 \
  --development /data/research/runs/r6-development-v5 \
  --validation /data/research/runs/r7-validation-v1 \
  --oos /data/research/runs/r8-official-oos-v1
```

The deterministic UUIDs and checksum checks make publication idempotent. Reproduction means
verifying the frozen bytes and persisted result lineage—not consuming a second OOS run.
