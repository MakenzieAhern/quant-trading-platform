# Approved Pilot freeze and engineering smoke

Gate A approval is recorded in `.research/approvals/gate-a-pilot-v1.json`.
The immutable freeze receipt is `.research/freezes/cn-a-pilot-akshare-20230101-20240731-v1.json`.
Its canonical SHA256 is74870e7d64a9197bd75a6ee32e7bf019aecaf5159d7ed9d1023078df7ce0ad31.
The dataset manifest remains0696a5c7454f044a3f0ea8886b1c08fbe2228b19598894ddb44ac54498978490.
The read-only final check verified the pinned R3 audit/publication receipts,22
audits,exact partition set/bytes,counts and accepted source pins. No source was
reacquired or methodology changed. Group component hashes are canonical ordered
manifest-partition records, not a claim of concatenated vendor-byte hashes.

The frozen catalog has a matching `.freeze.json` marker. Shared CSV/Parquet and
manifest writers reject any frozen ancestor, including new nested partitions.
Control records publish atomically without replacement; identical restart is safe.
The file and receipt content are immutable through project writers, not an OS
administrator-proof WORM claim. Corrections require a new dataset version/hash
and renewed freeze review. The original manifest's publication-stage not-frozen
note remains unchanged; the separate later freeze record supplies current status.

## Smoke scope

R4 uses `cn_a_cross_sectional_momentum_low_vol_v1` with unchanged configuration,
weights,rebalance interval,history and amount thresholds. Initial cash1M CNY is
an engineering test input, not return-based tuning. Every result is
PILOT_ENGINEERING_SMOKE_ONLY, never Development/Validation/OOS or profitability
evidence. Intended full research splits remain2010-2017/2018-2021/2022-2025; this
explicitly approved Pilot smoke does not count as official OOS execution.

Frozen PIT ordinary-A-share rows feed the existing factor/winsorization/z-score/
ranking/portfolio construction code and the existing RiskEngine/OMS/broker/
Portfolio/analytics path. H(t) is selected only from effective factors dated<=t.
Feature levels P(t)*H(t) omit the common H(T) denominator which cancels from all
three predeclared scale-invariant factors; raw prices are never adjusted for fills.
The full result is compared with reversed partition input and a truncated prefix.
Factor/score hashes and proposal/decision/order/rebalance traces are preserved.

Official daily suspension/tradeability stays null, not false. Unknown suspension
makes rule execution false; the execution convention requires positively known
unsuspended/tradeable states. Candidate scoring is not certification of executable
liquidity. Missing pre_close is not manufactured. On this Pilot the expected
result is NO FILL, zero holdings/costs/turnover; the smoke rejects unexpected fills.
This does not prove complete corporate-action accounting or available auction
liquidity. Synthetic regression tests separately exercise positive-fill accounting.
No empty or unexercised proposal/ranking pipeline can be labeled smoke PASS.

Run from `backend` with existing dependencies and Git available:

```sh
python -m scripts.freeze_pilot --staging "$STAGING" --dataset "$DATASET" --repository "$REPOSITORY"
python -m scripts.run_pilot_smoke --dataset "$DATASET" --repository "$REPOSITORY" --output "$RESULT_ROOT"
python -m scripts.run_pilot_smoke --dataset "$DATASET" --repository "$REPOSITORY" --output "$RESULT_ROOT" --persist-existing --git-commit "$VERIFIED_COMMIT"
```

The first command is read-only; `--freeze` is only for an explicitly approved
freeze. Freeze writes need access to both the research-control receipt and catalog
marker, possibly using the same container owner that published the catalog.
The persistent result uses existing research tables/API,period_kind=PILOT_SMOKE
and the full label in diagnostics/UI. Formal Pilot POST runs remain blocked.
Curve pagination loads all sessions rather than silently showing the first page.
Results and large dataset manifests remain outside Git; only control metadata is
committed. API/UI parity must be checked against the real persisted result before
R4 acceptance. R5 follows only after R4 acceptance; formal research remains locked
until GATE_FULL_RESEARCH_DATASET_FREEZE approval.
