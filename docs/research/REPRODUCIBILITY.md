# Reproducibility

Verify a frozen dataset with:

```bash
PYTHONPATH=backend python backend/scripts/verify_dataset.py <dataset-id>
```

Development and validation runs accept only registered strategy IDs and immutable dataset IDs.
They remain blocked while the readiness report is not fully `YES`. Official OOS is deliberately
absent from the command choices and requires a separately reviewed, explicit approval workflow.

Completed runs must persist their Git SHA, canonical manifest checksum, provider/version,
rule version, strategy configuration SHA-256, transaction costs, CSI300 benchmark lineage,
temporal split, random seed and sanitized failure information. Reproduction then uses only the
persisted run ID; provider APIs are never called during calculation.
