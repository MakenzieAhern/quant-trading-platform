import { backtestsApi } from "../api/backtests";
import { ErrorPanel, EmptyState, LoadingPanel } from "../components/AsyncPanel";
import { Link } from "../components/Link";
import { Pagination } from "../components/Pagination";
import { StatusBadge } from "../components/StatusBadge";
import { useApiResource } from "../hooks/useApiResource";
import { formatUtc, shortId } from "../utils/format";
import { useState } from "react";

const LIMIT = 20;

export function BacktestHistoryPage() {
  const [offset, setOffset] = useState(0);
  const runs = useApiResource(
    (signal) => backtestsApi.list(LIMIT, offset, signal),
    [offset],
  );

  return (
    <>
      <header className="pageHeader">
        <div>
          <p className="eyebrow">RESEARCH LEDGER</p>
          <h1>Backtests</h1>
          <p>Durable, deterministic runs from the Phase 7 API.</p>
        </div>
        <Link className="button buttonPrimary" href="/backtests/new">
          Create backtest
        </Link>
      </header>
      <section className="panel" aria-labelledby="history-title">
        <div className="panelHeader">
          <div>
            <p className="kicker">RUN HISTORY</p>
            <h2 id="history-title">Persisted executions</h2>
          </div>
        </div>
        {runs.loading && <LoadingPanel label="backtest history" />}
        {runs.error && <ErrorPanel message={runs.error} />}
        {runs.data && runs.data.items.length === 0 && (
          <EmptyState>
            No backtests yet. Create a deterministic research run to begin.
          </EmptyState>
        )}
        {runs.data && runs.data.items.length > 0 && (
          <div className="tableScroll">
            <table>
              <thead>
                <tr>
                  <th scope="col">Run</th>
                  <th scope="col">Strategy</th>
                  <th scope="col">Dataset</th>
                  <th scope="col">Status</th>
                  <th scope="col">Created</th>
                  <th scope="col">Started</th>
                  <th scope="col">Completed</th>
                </tr>
              </thead>
              <tbody>
                {runs.data.items.map((run) => (
                  <tr key={run.run_id}>
                    <td>
                      <Link
                        className="monoLink"
                        href={`/backtests/${run.run_id}`}
                        title={run.run_id}
                      >
                        {shortId(run.run_id)}
                      </Link>
                    </td>
                    <td>{run.strategy_type.replaceAll("_", " ")}</td>
                    <td>{run.dataset_id}</td>
                    <td>
                      <StatusBadge status={run.status} />
                    </td>
                    <td>{formatUtc(run.created_at)}</td>
                    <td>{formatUtc(run.started_at)}</td>
                    <td>{formatUtc(run.completed_at)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
        {runs.data && (
          <Pagination
            offset={offset}
            limit={LIMIT}
            total={runs.data.total}
            onChange={setOffset}
          />
        )}
      </section>
    </>
  );
}
