import { useEffect, useRef, useState } from "react";
import { useTranslation } from "react-i18next";

import { paperApi, paperParsers } from "../api/paper";
import { ErrorPanel, LoadingPanel } from "../components/AsyncPanel";
import { Link } from "../components/Link";
import { Pagination } from "../components/Pagination";
import { PaperSafetyBanner } from "../components/PaperSafetyBanner";
import { StatusBadge } from "../components/StatusBadge";
import { ExperimentPlan } from "../product/experiments/ExperimentPlan";
import { tradingDate } from "../product/experiments/api";
import { usePaperStream } from "../hooks/usePaperStream";
import type { PaperJournalEvent, PaperSessionStatus } from "../types/paper";
import { formatDecimal, formatUtc, shortId } from "../utils/format";
import { localizeRiskMessage } from "./riskMessage";

type PaperAction = "start" | "pause" | "stop";
// ponytail: DOM-only paging; long sessions still need bounded server collections.
const PAPER_TABLE_LIMIT = 100;

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
  const [logOpen, setLogOpen] = useState(false);
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
      {(session.error_message ||
        session.status === "FAILED" ||
        session.status === "INTERRUPTED") && (
        <section className="stateCallout failedCallout" role="alert">
          <h2>{t("detail.failedTitle")}</h2>
          <p>
            {t(
              session.status === "INTERRUPTED"
                ? "detail.interruptedHelp"
                : "detail.failedHelp",
            )}
          </p>
          <Link
            className="button"
            href={`/paper/new?from_session=${encodeURIComponent(session.session_id)}`}
          >
            {t("detail.createAgain")}
          </Link>
          {session.error_message && (
            <details>
              <summary>{t("detail.auditError")}</summary>
              <code>{session.error_message}</code>
            </details>
          )}
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
          localizeRiskMessage(item.message, t),
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
          `${t(`detail.orderStatuses.${item.status}`, { defaultValue: item.status })}${item.cancellation_reason_code ? ` · ${t(`detail.fillCancellationReasons.${item.cancellation_reason_code}`, { defaultValue: item.cancellation_reason_code })}` : ""}`,
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
      <section className="panel dataPanel">
        <div className="panelHeader">
          <h2>{t("detail.eventLog")}</h2>
          <button
            type="button"
            aria-expanded={logOpen}
            aria-controls="paper-event-log"
            onClick={() => setLogOpen((open) => !open)}
          >
            {t(logOpen ? "detail.hideEventLog" : "detail.viewEventLog")}
          </button>
        </div>
        <div id="paper-event-log">
          {logOpen && (
            <PaperEventJournal
              key={sessionId}
              sessionId={sessionId}
              latestSequence={snapshot.last_sequence}
            />
          )}
        </div>
      </section>
    </>
  );
}

function PaperEventJournal({
  sessionId,
  latestSequence,
}: {
  sessionId: string;
  latestSequence: number;
}) {
  const { t } = useTranslation("paper");
  const { t: researchT } = useTranslation("research");
  const [cursors, setCursors] = useState<number[]>([]);
  const [refreshKey, setRefreshKey] = useState(0);
  const pager = useRef<HTMLDivElement>(null);
  const [result, setResult] = useState<{
    key: string;
    events: PaperJournalEvent[];
    hasOlder: boolean;
    failed: boolean;
  } | null>(null);
  const beforeSequence = cursors.at(-1);
  const requestKey = `${sessionId}:${beforeSequence ?? "latest"}:${refreshKey}`;
  const loading = result?.key !== requestKey;
  const events = loading ? [] : result.events;
  const failed = !loading && result.failed;
  const hasOlder = !loading && result.hasOlder;
  const focusPager = () => {
    if (pager.current?.contains(document.activeElement)) pager.current.focus();
  };

  useEffect(() => {
    const controller = new AbortController();
    let current = true;
    void paperApi
      .events(sessionId, beforeSequence, controller.signal)
      .then((page) => {
        if (!current) return;
        setResult({
          key: requestKey,
          events: page.slice(0, 50),
          hasOlder: page.length > 50,
          failed: false,
        });
      })
      .catch(() => {
        if (current)
          setResult({
            key: requestKey,
            events: [],
            hasOlder: false,
            failed: true,
          });
      });
    return () => {
      current = false;
      controller.abort();
    };
  }, [sessionId, beforeSequence, requestKey]);

  const description = (event: PaperJournalEvent) => {
    const payload = event.payload;
    if (event.type === "session.status")
      return t(`common:statuses.${String(payload.status)}`);
    if (event.type === "market.bar") return String(payload.symbol);
    if (event.type === "market.session") return String(payload.trading_date);
    if (event.type === "calendar.observed") {
      const observation = paperParsers.calendar(payload);
      return t(`detail.calendarSummary.${observation.kind}`, {
        count: observation.calendar.sessions.length,
        completed: observation.after_completed_sessions,
      });
    }
    if (event.type === "signal.created")
      return `${String(payload.symbol)} · ${t(`detail.directions.${String(payload.signal_type)}`, { defaultValue: String(payload.signal_type) })}`;
    if (event.type === "risk.decision")
      return `${payload.approved ? t("detail.approved") : t("detail.riskRejected")} · ${t(`detail.riskReasons.${String(payload.reason_code)}`, { defaultValue: String(payload.reason_code) })}`;
    if (event.type === "order.updated")
      return `${shortId(String(payload.order_id))} · ${t(`detail.orderStatuses.${String(payload.status)}`, { defaultValue: String(payload.status) })} · ${String(payload.symbol)}${payload.cancellation_reason_code ? ` · ${t(`detail.fillCancellationReasons.${String(payload.cancellation_reason_code)}`, { defaultValue: String(payload.cancellation_reason_code) })}` : ""}`;
    if (event.type === "fill.created")
      return `${shortId(String(payload.order_id))} · ${String(payload.quantity)} ${String(payload.symbol)} @ ${String(payload.price)}`;
    return t("detail.eventEquity", { equity: String(payload.equity) });
  };

  return (
    <div aria-busy={loading}>
      <p className="stateCallout">{t("detail.eventLogSaved")}</p>
      {loading ? (
        <LoadingPanel label={t("detail.eventLog")} />
      ) : failed ? (
        <p className="stateCallout" role="alert">
          {t("detail.eventLogError")}
        </p>
      ) : events.length === 0 ? (
        <p className="emptyState">{t("detail.noEvents")}</p>
      ) : (
        <div
          className="tableScroll"
          role="region"
          tabIndex={0}
          aria-label={`${t("detail.eventLog")} — ${researchT("scrollTable")}`}
        >
          <table aria-label={t("detail.eventLog")}>
            <thead>
              <tr>
                <th scope="col">{t("detail.eventSequence")}</th>
                <th scope="col">{t("detail.utcTime")}</th>
                <th scope="col">{t("detail.eventType")}</th>
                <th scope="col">{t("detail.eventSummary")}</th>
              </tr>
            </thead>
            <tbody>
              {events.map((event) => (
                <tr key={event.sequence}>
                  <th scope="row">{event.sequence}</th>
                  <td>{formatUtc(event.occurred_at)}</td>
                  <td>{t(`detail.eventTypes.${event.type}`)}</td>
                  <td>{description(event)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      <div
        ref={pager}
        className="pagination"
        role="group"
        tabIndex={-1}
        aria-label={t("detail.eventLog")}
        aria-busy={loading}
      >
        <span aria-live="polite">
          {loading
            ? t("detail.eventLogLoading")
            : events.length > 0
              ? t("detail.eventLogRange", {
                  newest: events[0]!.sequence,
                  oldest: events.at(-1)!.sequence,
                })
              : ""}
          {cursors.length === 0 &&
            events.length > 0 &&
            latestSequence > events[0]!.sequence &&
            ` · ${t("detail.newEventsAvailable")}`}
        </span>
        <button
          type="button"
          disabled={loading}
          onClick={() => {
            focusPager();
            setCursors([]);
            setRefreshKey((key) => key + 1);
          }}
        >
          {t("detail.refreshEvents")}
        </button>
        <button
          type="button"
          disabled={loading || cursors.length === 0}
          onClick={() => {
            focusPager();
            setCursors((current) => current.slice(0, -1));
          }}
        >
          {t("detail.newerEvents")}
        </button>
        <button
          type="button"
          disabled={loading || !hasOlder || events.length === 0}
          onClick={() => {
            focusPager();
            setCursors((current) => [...current, events.at(-1)!.sequence]);
          }}
        >
          {t("detail.olderEvents")}
        </button>
      </div>
    </div>
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
  const [offset, setOffset] = useState(0);
  const pageOffset = Math.min(
    offset,
    Math.max(
      0,
      Math.floor((rows.length - 1) / PAPER_TABLE_LIMIT) * PAPER_TABLE_LIMIT,
    ),
  );
  if (offset !== pageOffset) setOffset(pageOffset);
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
              {rows
                .slice(pageOffset, pageOffset + PAPER_TABLE_LIMIT)
                .map((row, rowIndex) => (
                  <tr key={`${row.join(":")}:${pageOffset + rowIndex}`}>
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
                        <td
                          key={`${headings[index]}-${rowIndex}`}
                          title={value}
                        >
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
      <Pagination
        label={title}
        offset={pageOffset}
        limit={PAPER_TABLE_LIMIT}
        total={rows.length}
        onChange={setOffset}
      />
    </section>
  );
}
