import { useState } from "react";

import { paperApi } from "../api/paper";
import { ErrorPanel, LoadingPanel } from "../components/AsyncPanel";
import { Link } from "../components/Link";
import { PaperSafetyBanner } from "../components/PaperSafetyBanner";
import { StatusBadge } from "../components/StatusBadge";
import { usePaperStream } from "../hooks/usePaperStream";
import { formatDecimal, formatUtc, shortId } from "../utils/format";

export function PaperSessionDetailPage({ sessionId }: { sessionId: string }) {
  const { snapshot, connection, error } = usePaperStream(sessionId);
  const [commandPending, setCommandPending] = useState(false);
  const [commandError, setCommandError] = useState<string | null>(null);

  const command = async (action: "start" | "stop") => {
    if (commandPending) return;
    setCommandPending(true);
    setCommandError(null);
    try {
      await paperApi[action](sessionId);
    } catch (reason) {
      setCommandError(
        reason instanceof Error ? reason.message : `Unable to ${action}.`,
      );
    } finally {
      setCommandPending(false);
    }
  };

  if (!snapshot && !error)
    return <LoadingPanel label="paper session snapshot" />;
  if (!snapshot && error) return <ErrorPanel message={error} />;
  if (!snapshot) return null;
  const { session, latest_bar: bar, latest_portfolio: portfolio } = snapshot;
  const active = session.status === "STARTING" || session.status === "RUNNING";

  return (
    <>
      <PaperSafetyBanner />
      <header className="detailHeader">
        <div>
          <Link className="backLink" href="/paper">
            ← All paper sessions
          </Link>
          <p className="eyebrow">
            PAPER SESSION / {shortId(session.session_id)}
          </p>
          <h1>{session.strategy_type.replaceAll("_", " ")}</h1>
          <p className="runId">{session.session_id}</p>
        </div>
        <div className="paperControls">
          <span className={`streamState stream-${connection}`}>
            WebSocket: {connection}
          </span>
          <StatusBadge status={session.status} />
          {session.status === "CREATED" && (
            <button
              className="button buttonPrimary"
              disabled={commandPending}
              onClick={() => void command("start")}
            >
              Start replay
            </button>
          )}
          {active && (
            <button
              className="button"
              disabled={commandPending}
              onClick={() => void command("stop")}
            >
              Stop replay
            </button>
          )}
        </div>
      </header>
      {(error || commandError) && (
        <ErrorPanel message={commandError ?? error ?? "Unknown error"} />
      )}
      <section className="runFacts" aria-label="Paper session details">
        <div>
          <span>Provider</span>
          <strong>
            {session.provider_type} / {session.dataset_id}
          </strong>
        </div>
        <div>
          <span>Created</span>
          <strong>{formatUtc(session.created_at)}</strong>
        </div>
        <div>
          <span>Started</span>
          <strong>{formatUtc(session.started_at)}</strong>
        </div>
        <div>
          <span>Stopped</span>
          <strong>{formatUtc(session.stopped_at)}</strong>
        </div>
      </section>
      {session.error_message && (
        <section className="stateCallout failedCallout" role="alert">
          <h2>Paper session ended safely</h2>
          <p>{session.error_message}</p>
        </section>
      )}
      <section className="panel">
        <div className="panelHeader">
          <div>
            <p className="kicker">LATEST COMPLETED BAR</p>
            <h2>Market data</h2>
          </div>
        </div>
        {bar ? (
          <div className="metricsGrid">
            <Metric label="Open" value={bar.open} />
            <Metric label="High" value={bar.high} />
            <Metric label="Low" value={bar.low} />
            <Metric label="Close" value={bar.close} />
            <Metric label="Volume" value={bar.volume} />
            <Metric label="UTC time" value={formatUtc(bar.timestamp)} raw />
          </div>
        ) : (
          <p className="emptyState">No completed replay Bars received yet.</p>
        )}
      </section>
      <section className="panel">
        <div className="panelHeader">
          <div>
            <p className="kicker">AUTHORITATIVE PORTFOLIO</p>
            <h2>Paper portfolio</h2>
          </div>
        </div>
        {portfolio ? (
          <div className="metricsGrid">
            <Metric label="Cash" value={portfolio.cash} />
            <Metric label="Market value" value={portfolio.market_value} />
            <Metric label="Equity" value={portfolio.equity} />
            <Metric label="Realized PnL" value={portfolio.realized_pnl} />
            <Metric label="Unrealized PnL" value={portfolio.unrealized_pnl} />
            <Metric
              label="Commission"
              value={portfolio.cumulative_commission}
            />
          </div>
        ) : (
          <p className="emptyState">
            Portfolio initializes on the first completed Bar.
          </p>
        )}
      </section>
      <PaperTable
        title="Signals"
        empty="No signals emitted."
        headings={["UTC time", "Strategy", "Symbol", "Signal"]}
        rows={snapshot.signals.map((item) => [
          formatUtc(item.timestamp),
          item.strategy_id,
          item.symbol,
          item.signal_type,
        ])}
      />
      <PaperTable
        title="Risk decisions"
        empty="No risk decisions recorded."
        headings={["Proposal", "Decision", "Reason", "Message"]}
        rows={snapshot.risk_decisions.map((item) => [
          shortId(item.proposal_id),
          item.approved ? "APPROVED" : "RISK REJECTED",
          item.reason_code,
          item.message,
        ])}
      />
      <PaperTable
        title="Paper orders"
        empty="No simulated orders recorded."
        headings={["Order", "Side / type", "Quantity", "Status", "UTC time"]}
        rows={snapshot.orders.map((item) => [
          shortId(item.order_id),
          `${item.side} / ${item.order_type}`,
          item.quantity,
          item.status,
          formatUtc(item.created_at),
        ])}
      />
      <PaperTable
        title="Paper fills"
        empty="No simulated fills recorded."
        headings={[
          "Order",
          "Side",
          "Quantity",
          "Price",
          "Commission",
          "UTC time",
        ]}
        rows={snapshot.fills.map((item) => [
          shortId(item.order_id),
          item.side,
          item.quantity,
          item.price,
          item.commission,
          formatUtc(item.timestamp),
        ])}
      />
    </>
  );
}

function Metric({
  label,
  value,
  raw = false,
}: {
  label: string;
  value: string;
  raw?: boolean;
}) {
  return (
    <div className="metric">
      <span>{label}</span>
      <strong title={value}>{raw ? value : formatDecimal(value)}</strong>
    </div>
  );
}

function PaperTable({
  title,
  empty,
  headings,
  rows,
}: {
  title: string;
  empty: string;
  headings: string[];
  rows: string[][];
}) {
  return (
    <section className="panel dataPanel">
      <div className="panelHeader">
        <h2>{title}</h2>
      </div>
      {rows.length === 0 ? (
        <p className="emptyState">{empty}</p>
      ) : (
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
            <tbody>
              {rows.map((row, rowIndex) => (
                <tr key={row.join(":")}>
                  {row.map((value, index) => (
                    <td key={`${headings[index]}-${rowIndex}`} title={value}>
                      {value}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}
