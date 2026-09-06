import { useCallback, useEffect, useState, type ReactNode } from "react";

import { backtestsApi } from "../api/backtests";
import { EmptyState, ErrorPanel, LoadingPanel } from "../components/AsyncPanel";
import { EquityChart } from "../components/EquityChart";
import { Link } from "../components/Link";
import { Pagination } from "../components/Pagination";
import { StatusBadge } from "../components/StatusBadge";
import { useApiResource } from "../hooks/useApiResource";
import type {
  Fill,
  Order,
  Page,
  RiskDecision,
  Signal,
} from "../types/backtests";
import {
  formatDecimal,
  formatPercent,
  formatUtc,
  shortId,
} from "../utils/format";

const COLLECTION_LIMIT = 25;

function Metric({
  label,
  value,
  percent = false,
}: {
  label: string;
  value: string | null;
  percent?: boolean;
}) {
  return (
    <div className="metric">
      <span>{label}</span>
      <strong title={value ?? "Not available"}>
        {percent ? formatPercent(value) : formatDecimal(value)}
      </strong>
    </div>
  );
}

function Collection<T>({
  title,
  empty,
  load,
  headings,
  row,
}: {
  title: string;
  empty: string;
  load: (
    limit: number,
    offset: number,
    signal: AbortSignal,
  ) => Promise<Page<T>>;
  headings: string[];
  row: (item: T, index: number) => ReactNode;
}) {
  const [offset, setOffset] = useState(0);
  const page = useApiResource(
    (signal) => load(COLLECTION_LIMIT, offset, signal),
    [load, offset],
  );
  return (
    <section className="panel dataPanel">
      <div className="panelHeader">
        <h2>{title}</h2>
      </div>
      {page.loading && <LoadingPanel label={title.toLowerCase()} />}
      {page.error && <ErrorPanel message={page.error} />}
      {page.data && page.data.items.length === 0 && (
        <EmptyState>{empty}</EmptyState>
      )}
      {page.data && page.data.items.length > 0 && (
        <div className="tableScroll">
          <table>
            <thead>
              <tr>
                {headings.map((heading) => (
                  <th scope="col" key={heading}>
                    {heading}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>{page.data.items.map(row)}</tbody>
          </table>
        </div>
      )}
      {page.data && (
        <Pagination
          offset={offset}
          limit={COLLECTION_LIMIT}
          total={page.data.total}
          onChange={setOffset}
        />
      )}
    </section>
  );
}

function SuccessfulResult({ runId }: { runId: string }) {
  const result = useApiResource(
    (signal) => backtestsApi.result(runId, signal),
    [runId],
  );
  const [equityOffset, setEquityOffset] = useState(0);
  const equity = useApiResource(
    (signal) => backtestsApi.equity(runId, 200, equityOffset, signal),
    [runId, equityOffset],
  );
  const signalLoader = useCallback(
    (limit: number, offset: number, signal: AbortSignal) =>
      backtestsApi.signals(runId, limit, offset, signal),
    [runId],
  );
  const riskLoader = useCallback(
    (limit: number, offset: number, signal: AbortSignal) =>
      backtestsApi.riskDecisions(runId, limit, offset, signal),
    [runId],
  );
  const orderLoader = useCallback(
    (limit: number, offset: number, signal: AbortSignal) =>
      backtestsApi.orders(runId, limit, offset, signal),
    [runId],
  );
  const fillLoader = useCallback(
    (limit: number, offset: number, signal: AbortSignal) =>
      backtestsApi.fills(runId, limit, offset, signal),
    [runId],
  );

  return (
    <>
      <section className="panel">
        <div className="panelHeader">
          <div>
            <p className="kicker">AUTHORITATIVE RESULT</p>
            <h2>Performance</h2>
          </div>
          {result.data && (
            <span className="countLabel">
              {result.data.fill_count} fills ·{" "}
              {result.data.risk_rejection_count} risk rejections
            </span>
          )}
        </div>
        {result.loading && <LoadingPanel label="performance metrics" />}
        {result.error && <ErrorPanel message={result.error} />}
        {result.data && (
          <div className="metricsGrid">
            <Metric
              label="Initial equity"
              value={result.data.metrics.initial_equity}
            />
            <Metric
              label="Final equity"
              value={result.data.metrics.final_equity}
            />
            <Metric
              label="Total return"
              value={result.data.metrics.total_return}
              percent
            />
            <Metric label="CAGR" value={result.data.metrics.cagr} percent />
            <Metric
              label="Max drawdown"
              value={result.data.metrics.max_drawdown}
              percent
            />
            <Metric label="Sharpe" value={result.data.metrics.sharpe_ratio} />
            <Metric label="Sortino" value={result.data.metrics.sortino_ratio} />
            <Metric
              label="Commission"
              value={result.data.metrics.total_commission}
            />
          </div>
        )}
      </section>
      <section className="panel">
        <div className="panelHeader">
          <div>
            <p className="kicker">PORTFOLIO</p>
            <h2>Equity curve</h2>
          </div>
          <span className="countLabel">UTC · API order</span>
        </div>
        {equity.loading && <LoadingPanel label="equity data" />}
        {equity.error && <ErrorPanel message={equity.error} />}
        {equity.data && equity.data.items.length === 0 && (
          <EmptyState>No equity snapshots were recorded.</EmptyState>
        )}
        {equity.data && equity.data.items.length > 0 && (
          <EquityChart points={equity.data.items} />
        )}
        {equity.data && (
          <Pagination
            offset={equityOffset}
            limit={200}
            total={equity.data.total}
            onChange={setEquityOffset}
          />
        )}
      </section>
      <Collection<Signal>
        title="Signals"
        empty="No signals were emitted."
        load={signalLoader}
        headings={["UTC time", "Strategy", "Symbol", "Signal"]}
        row={(item, index) => (
          <tr key={`${item.timestamp}-${index}`}>
            <td>{formatUtc(item.timestamp)}</td>
            <td>{item.strategy_id}</td>
            <td>{item.symbol}</td>
            <td>{item.signal_type}</td>
          </tr>
        )}
      />
      <Collection<RiskDecision>
        title="Risk decisions"
        empty="No proposals reached risk evaluation."
        load={riskLoader}
        headings={["Proposal", "Decision", "Reason", "Message", "UTC time"]}
        row={(item) => (
          <tr key={item.proposal_id}>
            <td className="mono" title={item.proposal_id}>
              {shortId(item.proposal_id)}
            </td>
            <td>
              <span
                className={
                  item.approved ? "decisionApproved" : "decisionRejected"
                }
              >
                {item.approved ? "APPROVED" : "RISK REJECTED"}
              </span>
            </td>
            <td>{item.reason_code}</td>
            <td>{item.message}</td>
            <td>{formatUtc(item.timestamp)}</td>
          </tr>
        )}
      />
      <Collection<Order>
        title="Orders"
        empty="No orders were created. Risk-rejected proposals do not become orders."
        load={orderLoader}
        headings={[
          "Order",
          "Strategy",
          "Symbol",
          "Side / type",
          "Quantity",
          "Status",
          "Created (UTC)",
        ]}
        row={(item) => (
          <tr key={item.order_id}>
            <td className="mono" title={item.order_id}>
              {shortId(item.order_id)}
            </td>
            <td>{item.strategy_id}</td>
            <td>{item.symbol}</td>
            <td>
              {item.side} / {item.order_type}
            </td>
            <td title={item.quantity}>{item.quantity}</td>
            <td>
              <span
                className={
                  item.status === "REJECTED"
                    ? "decisionRejected"
                    : "decisionApproved"
                }
              >
                {item.status}
              </span>
            </td>
            <td>{formatUtc(item.created_at)}</td>
          </tr>
        )}
      />
      <Collection<Fill>
        title="Fills"
        empty="No fills were recorded."
        load={fillLoader}
        headings={[
          "Order",
          "Symbol",
          "Side",
          "Quantity",
          "Price",
          "Commission",
          "UTC time",
        ]}
        row={(item, index) => (
          <tr key={`${item.order_id}-${index}`}>
            <td className="mono" title={item.order_id}>
              {shortId(item.order_id)}
            </td>
            <td>{item.symbol}</td>
            <td>{item.side}</td>
            <td title={item.quantity}>{item.quantity}</td>
            <td title={item.price}>{item.price}</td>
            <td title={item.commission}>{item.commission}</td>
            <td>{formatUtc(item.timestamp)}</td>
          </tr>
        )}
      />
    </>
  );
}

export function BacktestDetailPage({ runId }: { runId: string }) {
  const [revision, setRevision] = useState(0);
  const run = useApiResource(
    (signal) => backtestsApi.get(runId, signal),
    [runId, revision],
  );
  useEffect(() => {
    if (run.data?.status !== "RUNNING" && run.data?.status !== "CREATED")
      return;
    const timeout = window.setTimeout(
      () => setRevision((value) => value + 1),
      5000,
    );
    return () => window.clearTimeout(timeout);
  }, [run.data?.status, revision]);

  if (run.loading) return <LoadingPanel label="backtest detail" />;
  if (run.error) return <ErrorPanel message={run.error} />;
  if (!run.data) return null;
  const detail = run.data;
  return (
    <>
      <header className="detailHeader">
        <div>
          <Link className="backLink" href="/backtests">
            ← All backtests
          </Link>
          <p className="eyebrow">RUN / {shortId(detail.run_id)}</p>
          <h1>{detail.strategy_type.replaceAll("_", " ")}</h1>
          <p className="runId">{detail.run_id}</p>
        </div>
        <StatusBadge status={detail.status} />
      </header>
      <section className="runFacts" aria-label="Run details">
        <div>
          <span>Dataset</span>
          <strong>
            {detail.dataset_id} / {detail.symbol}
          </strong>
        </div>
        <div>
          <span>Created</span>
          <strong>{formatUtc(detail.created_at)}</strong>
        </div>
        <div>
          <span>Started</span>
          <strong>{formatUtc(detail.started_at)}</strong>
        </div>
        <div>
          <span>Completed</span>
          <strong>{formatUtc(detail.completed_at)}</strong>
        </div>
      </section>
      {(detail.status === "CREATED" || detail.status === "RUNNING") && (
        <section className="stateCallout runningCallout" role="status">
          <h2>Backtest in progress</h2>
          <p>
            This active run is checked every five seconds. Execution remains
            synchronous on the backend.
          </p>
        </section>
      )}
      {detail.status === "FAILED" && (
        <section className="stateCallout failedCallout" role="alert">
          <h2>Backtest failed</h2>
          <p>
            {detail.error_message ??
              "The run failed without additional safe diagnostic information."}
          </p>
          <p>
            No successful metrics or equity curve are displayed for this run.
          </p>
        </section>
      )}
      {detail.status === "SUCCEEDED" && <SuccessfulResult runId={runId} />}
    </>
  );
}
