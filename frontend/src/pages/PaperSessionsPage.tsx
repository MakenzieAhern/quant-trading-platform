import { useState } from "react";

import { paperApi } from "../api/paper";
import { EmptyState, ErrorPanel, LoadingPanel } from "../components/AsyncPanel";
import { Link } from "../components/Link";
import { Pagination } from "../components/Pagination";
import { PaperSafetyBanner } from "../components/PaperSafetyBanner";
import { StatusBadge } from "../components/StatusBadge";
import { useApiResource } from "../hooks/useApiResource";
import { formatUtc, shortId } from "../utils/format";

const LIMIT = 20;

export function PaperSessionsPage() {
  const [offset, setOffset] = useState(0);
  const sessions = useApiResource(
    (signal) => paperApi.list(LIMIT, offset, signal),
    [offset],
  );
  return (
    <>
      <PaperSafetyBanner />
      <header className="pageHeader">
        <div>
          <p className="eyebrow">SIMULATED EXECUTION LEDGER</p>
          <h1>Paper trading sessions</h1>
          <p>
            Local deterministic replay sessions. No external broker is
            connected.
          </p>
        </div>
        <Link className="button buttonPrimary" href="/paper/new">
          Create paper session
        </Link>
      </header>
      <section className="panel" aria-labelledby="paper-sessions-title">
        <div className="panelHeader">
          <h2 id="paper-sessions-title">Persisted sessions</h2>
        </div>
        {sessions.loading && <LoadingPanel label="paper trading sessions" />}
        {sessions.error && <ErrorPanel message={sessions.error} />}
        {sessions.data?.items.length === 0 && (
          <EmptyState>
            No paper sessions yet. Create a safe replay session to begin.
          </EmptyState>
        )}
        {sessions.data && sessions.data.items.length > 0 && (
          <div className="tableScroll">
            <table>
              <thead>
                <tr>
                  <th scope="col">Session</th>
                  <th scope="col">Strategy</th>
                  <th scope="col">Provider</th>
                  <th scope="col">Status</th>
                  <th scope="col">Created</th>
                </tr>
              </thead>
              <tbody>
                {sessions.data.items.map((item) => (
                  <tr key={item.session_id}>
                    <td>
                      <Link
                        className="monoLink"
                        href={`/paper/${item.session_id}`}
                        title={item.session_id}
                      >
                        {shortId(item.session_id)}
                      </Link>
                    </td>
                    <td>{item.strategy_type.replaceAll("_", " ")}</td>
                    <td>
                      {item.provider_type} / {item.dataset_id}
                    </td>
                    <td>
                      <StatusBadge status={item.status} />
                    </td>
                    <td>{formatUtc(item.created_at)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
        {sessions.data && (
          <Pagination
            offset={offset}
            limit={LIMIT}
            total={sessions.data.total}
            onChange={setOffset}
          />
        )}
      </section>
    </>
  );
}
