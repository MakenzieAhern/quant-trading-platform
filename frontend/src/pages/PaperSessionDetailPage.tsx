import { useEffect, useRef, useState } from "react";
import { useTranslation } from "react-i18next";

import { paperApi } from "../api/paper";
import { ErrorPanel, LoadingPanel } from "../components/AsyncPanel";
import { Link } from "../components/Link";
import { PaperSafetyBanner } from "../components/PaperSafetyBanner";
import { StatusBadge } from "../components/StatusBadge";
import { ExperimentPlan } from "../product/experiments/ExperimentPlan";
import { tradingDate } from "../product/experiments/api";
import { usePaperStream } from "../hooks/usePaperStream";
import type { PaperSessionStatus } from "../types/paper";
import { formatDecimal, formatUtc, shortId } from "../utils/format";

type PaperAction = "start" | "pause" | "stop";

function commandConfirmed(
  action: PaperAction,
  status: PaperSessionStatus | undefined,
) {
  if (action === "start") return status === "STARTING" || status === "RUNNING";
  if (action === "pause") return status === "PAUSING" || status === "PAUSED";
  return status === "STOPPING" || status === "STOPPED";
}

export function PaperSessionDetailPage({ sessionId }: { sessionId: string }) {
  const { t } = useTranslation("paper");
  const {
    snapshot,
    fillAnnouncement,
    connection,
    error,
    acknowledge,
    refresh,
  } = usePaperStream(sessionId);
  const [contractErrorId, setContractErrorId] = useState<string | null>(null);
  const [commandPending, setCommandPending] = useState(false);
  const [commandError, setCommandError] = useState<PaperAction | null>(null);
  const commandLock = useRef(false);
  const pendingAction = useRef<PaperAction | null>(null);
  const pendingCommandConfirmed = useRef(false);
  const focusedCommand = useRef<HTMLButtonElement | null>(null);
  const statusFocus = useRef<HTMLSpanElement>(null);

  useEffect(() => {
    const button = focusedCommand.current;
    if (button && !button.isConnected) {
      if (document.activeElement === document.body)
        statusFocus.current?.focus();
      focusedCommand.current = null;
    }
  }, [snapshot?.session.status]);

  const status = snapshot?.session.status;
  useEffect(() => {
    if (
      pendingAction.current &&
      commandConfirmed(pendingAction.current, status)
    )
      pendingCommandConfirmed.current = true;
  }, [status]);
  const commandErrorIsStale =
    commandError !== null && commandConfirmed(commandError, status);
  if (commandErrorIsStale) setCommandError(null);

  const command = async (action: PaperAction) => {
    if (commandLock.current) return;
    const before = snapshot?.session.status;
    if (!before) return;
    commandLock.current = true;
    pendingAction.current = action;
    pendingCommandConfirmed.current = false;
    setCommandPending(true);
    setCommandError(null);
    let accepted = false;
    try {
      const response = await paperApi[action](sessionId);
      if (response.session_id !== sessionId) {
        setContractErrorId(sessionId);
        return;
      }
      accepted = true;
      acknowledge(before, response);
      await refresh();
    } catch {
      if (!accepted && !pendingCommandConfirmed.current)
        setCommandError(action);
    } finally {
      pendingAction.current = null;
      commandLock.current = false;
      setCommandPending(false);
    }
  };

  const liveFillStatus = (
    <span
      id="paper-fill-announcement"
      className="srOnly"
      role="status"
      aria-atomic="true"
    >
      {fillAnnouncement && (
        <span key={fillAnnouncement.sequence} lang={fillAnnouncement.language}>
          {fillAnnouncement.text}
        </span>
      )}
    </span>
  );

  if (contractErrorId === sessionId)
    return (
      <>
        {liveFillStatus}
        <div className="panelState errorPanel" role="alert">
          <p>{t("detail.commandAccountMismatch")}</p>
          <a className="button" href={window.location.href}>
            {t("common:loadErrors.reload")}
          </a>
        </div>
      </>
    );
  if (!snapshot && !error)
    return (
      <>
        {liveFillStatus}
        <LoadingPanel label={t("detail.loading")} />
      </>
    );
  if (!snapshot && error)
    return (
      <>
        {liveFillStatus}
        <ErrorPanel
          message={error}
          notFoundReturn={{ href: "/paper", label: t("detail.back") }}
        />
      </>
    );
  if (!snapshot) return <>{liveFillStatus}</>;
  const {
    session,
    latest_bar: bar,
    latest_session: marketSession,
    latest_portfolio: portfolio,
  } = snapshot;
  const active = session.status === "STARTING" || session.status === "RUNNING";
  const aShare =
    session.provider_type === "simulated_a_share" ||
    session.provider_type === "historical_a_share";
  const moneyUnit =
    session.provider_type === "historical_a_share" ? t("detail.cnySuffix") : "";
  const portfolioDate = portfolio ? tradingDate(portfolio) : null;
  const stalePortfolio = Boolean(
    aShare &&
    marketSession &&
    portfolio &&
    portfolioDate !== marketSession.trading_date,
  );
  const riskMessage = (message: string) => {
    const reserved = /^reserved quantity for (.+) must be finite$/.exec(
      message,
    );
    if (reserved)
      return t("detail.riskMessages.reservedQuantityFinite", {
        symbol: reserved[1],
      });
    const mark = /^a positive observed mark is required for (.+)$/.exec(
      message,
    );
    if (mark)
      return t("detail.riskMessages.positiveMarkRequired", { symbol: mark[1] });
    return t(`detail.riskMessages.${message}`, { defaultValue: message });
  };

  return (
    <>
      {liveFillStatus}
      <PaperSafetyBanner />
      <header className="detailHeader">
        <div>
          <Link className="backLink" href="/paper">
            {t("detail.back")}
          </Link>
          <p className="eyebrow">
            {t("detail.eyebrow")} / {shortId(session.session_id)}
          </p>
          <h1>{t(`strategies.${session.strategy_type}`)}</h1>
        </div>
        <div
          className="paperControls"
          onFocusCapture={(event) => {
            if (event.target instanceof HTMLButtonElement)
              focusedCommand.current = event.target;
          }}
          onBlurCapture={() => {
            focusedCommand.current = null;
          }}
        >
          <span className={`streamState stream-${connection}`} role="status">
            {t("detail.websocket")}: {t(`detail.connection.${connection}`)}
          </span>
          <span role="status" ref={statusFocus} tabIndex={-1}>
            <StatusBadge status={session.status} />
          </span>
          {(session.status === "CREATED" || session.status === "PAUSED") && (
            <button
              className="button buttonPrimary"
              aria-disabled={commandPending}
              onClick={() => void command("start")}
            >
              {t(
                session.status === "PAUSED" ? "detail.resume" : "detail.start",
              )}
            </button>
          )}
          {active && (
            <button
              className="button"
              aria-disabled={commandPending}
              onClick={() => void command("pause")}
            >
              {t("detail.pause")}
            </button>
          )}
          {(session.status === "CREATED" ||
            active ||
            session.status === "PAUSING" ||
            session.status === "PAUSED") && (
            <button
              className="button"
              aria-disabled={commandPending}
              onClick={() => void command("stop")}
            >
              {t("detail.stop")}
            </button>
          )}
        </div>
      </header>
      {connection === "reconnecting" && (
        <p className="stateCallout" role="status">
          {t("detail.lastVerifiedWarning")}
        </p>
      )}
      {commandError && !commandErrorIsStale && (
        <p className="stateCallout" role="alert">
          {t(`detail.${commandError}Error`)}
        </p>
      )}
      {error && <ErrorPanel message={error} />}
      <section className="runFacts" aria-label={t("detail.detailsLabel")}>
        <div>
          <span>{t("detail.provider")}</span>
          <strong>{t(`providers.${session.provider_type}`)}</strong>
          <details>
            <summary>{t("detail.auditIdentity")}</summary>
            <span>{t("detail.sessionId")}</span>
            <code>{session.session_id}</code>
            <span>{t("detail.datasetId")}</span>
            <code>{session.dataset_id}</code>
          </details>
        </div>
        <div>
          <span>{t("detail.created")}</span>
          <strong>{formatUtc(session.created_at)}</strong>
        </div>
        <div>
          <span>{t("detail.started")}</span>
          <strong>{formatUtc(session.started_at)}</strong>
        </div>
        <div>
          <span>{t("detail.stopped")}</span>
          <strong>{formatUtc(session.stopped_at)}</strong>
        </div>
      </section>
      {session.error_message && (
        <section className="stateCallout failedCallout" role="alert">
          <h2>{t("detail.failedTitle")}</h2>
          <p>
            {t(
              session.status === "INTERRUPTED"
                ? "detail.interruptedHelp"
                : "detail.failedHelp",
            )}
          </p>
          <Link className="button" href="/paper/new">
            {t("detail.createAgain")}
          </Link>
          <details>
            <summary>{t("detail.auditError")}</summary>
            <code>{session.error_message}</code>
          </details>
        </section>
      )}
      <section className="panel">
        <div className="panelHeader">
          <div>
            <p className="kicker">
              {aShare ? t("detail.latestSession") : t("detail.latestBar")}
            </p>
            <h2>
              {aShare ? t("detail.marketSession") : t("detail.marketData")}
            </h2>
          </div>
        </div>
        {marketSession ? (
          <div className="metricsGrid">
            <Metric
              label={t("detail.sessionDate")}
              value={marketSession.trading_date}
              raw
            />
            <Metric
              label={t("detail.securities")}
              value={String(marketSession.security_count)}
            />
            <Metric
              label={t("detail.source")}
              value={t(`detail.marketSources.${marketSession.source}`)}
              raw
            />
          </div>
        ) : bar ? (
          <div className="metricsGrid">
            <Metric label={t("detail.open")} value={bar.open} />
            <Metric label={t("detail.high")} value={bar.high} />
            <Metric label={t("detail.low")} value={bar.low} />
            <Metric label={t("detail.close")} value={bar.close} />
            <Metric label={t("detail.volume")} value={bar.volume} />
            <Metric
              label={t("detail.utcTime")}
              value={formatUtc(bar.timestamp)}
              raw
            />
          </div>
        ) : (
          <p className="emptyState">
            {t(aShare ? "detail.noSessions" : "detail.noBars")}
          </p>
        )}
      </section>
      <section className="panel">
        <div className="panelHeader">
          <div>
            <p className="kicker">
              {t(
                connection === "reconnecting" || stalePortfolio
                  ? "detail.lastVerifiedPortfolioKicker"
                  : "detail.portfolioKicker",
              )}
            </p>
            <h2>{t("detail.portfolio")}</h2>
          </div>
        </div>
        {stalePortfolio && (
          <p className="stateCallout" role="alert">
            {t("detail.stalePortfolioWarning", {
              portfolioDate: portfolioDate ?? t("detail.unknownDate"),
              sessionDate: marketSession?.trading_date,
            })}
          </p>
        )}
        {portfolio ? (
          <div className="metricsGrid">
            <Metric
              label={`${t("detail.cash")}${moneyUnit}`}
              value={portfolio.cash}
            />
            <Metric
              label={`${t("detail.marketValue")}${moneyUnit}`}
              value={portfolio.market_value}
            />
            <Metric
              label={`${t("detail.equity")}${moneyUnit}`}
              value={portfolio.equity}
            />
            <Metric
              label={`${t("detail.realizedPnl")}${moneyUnit}`}
              value={portfolio.realized_pnl}
            />
            <Metric
              label={`${t("detail.unrealizedPnl")}${moneyUnit}`}
              value={portfolio.unrealized_pnl}
            />
            <Metric
              label={`${t("detail.commission")}${moneyUnit}`}
              value={portfolio.cumulative_commission}
            />
          </div>
        ) : (
          <p className="emptyState">
            {t(aShare ? "detail.noSessionPortfolio" : "detail.noPortfolio")}
          </p>
        )}
      </section>
      {session.provider_type === "historical_a_share" && portfolio && (
        <ExperimentPlan
          plan={snapshot.last_rebalance_plan ?? portfolio.plan}
          account
        />
      )}
      <PaperTable
        title={t("detail.positions")}
        empty={t("detail.noPositions")}
        headings={[
          t("createPage.symbol"),
          t("detail.quantity"),
          `${t("detail.averagePrice")}${moneyUnit}`,
          `${t("detail.price")}${moneyUnit}`,
          `${t("detail.unrealizedPnlShort")}${moneyUnit}`,
          `${t("detail.realizedPnlShort")}${moneyUnit}`,
        ]}
        rows={(portfolio?.positions ?? []).map((item) => [
          item.symbol,
          item.quantity,
          item.average_price,
          item.market_price,
          item.unrealized_pnl,
          item.realized_pnl,
        ])}
      />
      <PaperTable
        title={t("detail.signals")}
        empty={t("detail.noSignals")}
        headings={[
          t("detail.utcTime"),
          t("detail.strategy"),
          t("createPage.symbol"),
          t("detail.signal"),
        ]}
        rows={snapshot.signals.map((item) => [
          formatUtc(item.timestamp),
          t(`strategies.${item.strategy_id}`, {
            defaultValue: item.strategy_id,
          }),
          item.symbol,
          t(`detail.directions.${item.signal_type}`, {
            defaultValue: item.signal_type,
          }),
        ])}
      />
      <PaperTable
        title={t("detail.riskDecisions")}
        empty={t("detail.noRiskDecisions")}
        headings={[
          t("detail.proposal"),
          t("detail.decision"),
          t("detail.reason"),
          t("detail.message"),
        ]}
        rows={snapshot.risk_decisions.map((item) => [
          shortId(item.proposal_id),
          item.approved ? t("detail.approved") : t("detail.riskRejected"),
          t(`detail.riskReasons.${item.reason_code}`, {
            defaultValue: item.reason_code,
          }),
          riskMessage(item.message),
        ])}
      />
      <PaperTable
        title={t("detail.orders")}
        empty={t("detail.noOrders")}
        headings={[
          t("detail.order"),
          t("detail.sideType"),
          t("detail.quantity"),
          t("detail.status"),
          t("detail.utcTime"),
        ]}
        rows={snapshot.orders.map((item) => [
          shortId(item.order_id),
          `${t(`detail.directions.${item.side}`, { defaultValue: item.side })} / ${t(`detail.orderTypes.${item.order_type}`, { defaultValue: item.order_type })}`,
          item.quantity,
          t(`detail.orderStatuses.${item.status}`, {
            defaultValue: item.status,
          }),
          formatUtc(item.created_at),
        ])}
      />
      <PaperTable
        title={t("detail.fills")}
        empty={t("detail.noFills")}
        headings={[
          t("detail.order"),
          t("detail.side"),
          t("detail.quantity"),
          `${t("detail.price")}${moneyUnit}`,
          `${t("detail.commission")}${moneyUnit}`,
          t("detail.utcTime"),
        ]}
        rows={snapshot.fills.map((item) => [
          shortId(item.order_id),
          t(`detail.directions.${item.side}`, { defaultValue: item.side }),
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
  const { t } = useTranslation("research");
  return (
    <section className="panel dataPanel">
      <div className="panelHeader">
        <h2>{title}</h2>
      </div>
      {rows.length === 0 ? (
        <p className="emptyState">{empty}</p>
      ) : (
        <div
          className="tableScroll"
          role="region"
          tabIndex={0}
          aria-label={`${title} — ${t("scrollTable")}`}
        >
          <table aria-label={title}>
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
                <tr key={`${row.join(":")}:${rowIndex}`}>
                  {row.map((value, index) =>
                    index === 0 ? (
                      <th
                        scope="row"
                        key={`${headings[index]}-${rowIndex}`}
                        title={value}
                      >
                        {value}
                      </th>
                    ) : (
                      <td key={`${headings[index]}-${rowIndex}`} title={value}>
                        {value}
                      </td>
                    ),
                  )}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}
