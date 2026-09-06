# Synthetic performance baseline

Measured 2026-09-06 in Linux x86_64 containers under WSL2/Docker Desktop, Python 3.12.14,
PostgreSQL 16, on the development PC. These are single observations, not guarantees or
cross-machine claims. No GPU is used. First-call import/cache effects are included.

| Bars | Strategies | Fills | Backtest seconds | Persist seconds | History seconds | Detail seconds |
| --- | --- | --- | --- | --- | --- | --- |
| 1,000 | 1 | 98 | 0.050219 | 0.110041 | 0.013025 | 0.014561 |
| 10,000 | 1 | 998 | 2.214350 | 1.020590 | 0.003987 | 0.010637 |
| 10,000 | 2 | 1,996 | 4.682204 | 1.529576 | 0.003183 | 0.009684 |

`backend/scripts/benchmark.py` creates deterministic sawtooth Bars in memory, then measures
engine execution, atomic result persistence and ASGI history/detail requests. API timings
include database work and serialization but exclude network/browser latency. Dataset
construction is outside the engine timer. History contains up to three benchmark runs.
Run only in the disposable test project:

```bash
docker compose -f compose.test.yml run --rm backend sh -c 'alembic upgrade head && python scripts/benchmark.py'
docker compose -f compose.test.yml down --volumes
```

The 10x input increase costs more than 10x engine time: strategies recompute indicators
from observed history, and result collections retain finite-run history. This is an explicit
baseline bottleneck, not an invitation to change numerical semantics during release.
Current public replay is six registered Bars. History/detail reads are bounded queries;
equity/audit pages are limited to 200 items. There is no per-row lazy ORM relationship loop.

Future comparisons should repeat several times on the same environment and dataset, record
medians and memory, and investigate large differences before setting CI timing thresholds.

## Frontend rendering

`frontend/scripts/benchmark.mjs` renders the actual equity chart and its accessible text
alternative with 200 points (the API page maximum). Node 24 React server-side rendering:
10 measured samples after one warmup, median **19.194 ms** on the same development PC.
This measures React rendering only, not Chrome layout/paint, networking or interaction latency.
It is a repeatable regression baseline, not a browser frame-rate claim.

```bash
docker compose -f compose.test.yml run --rm --no-deps frontend node scripts/benchmark.mjs
```
