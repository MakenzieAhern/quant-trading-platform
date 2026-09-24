import { useCallback, useEffect, useState, type ReactNode } from "react";
import { useTranslation } from "react-i18next";

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
  const { t } = useTranslation("backtests");
  return (
    <div className="metric">
      <span>{label}</span>
      <strong title={value ?? t("detail.notAvailable")}>
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
  const { t } = useTranslation("research");
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
        <div
          className="tableScroll"
          role="region"
          tabIndex={0}
          aria-label={t("scrollTable")}
        >
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
  const { t } = useTranslation("backtests");
  const { t: paperT } = useTranslation("paper");
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
            <p className="kicker">{t("detail.authoritative")}</p>
            <h2>{t("detail.performance")}</h2>
          </div>
          {result.data && (
            <span className="countLabel">
              {t("detail.counts", {
                fills: result.data.fill_count,
                rejections: result.data.risk_rejection_count,
              })}
            </span>
          )}
        </div>
        {result.loading && <LoadingPanel label={t("detail.metricsLoading")} />}
        {result.error && <ErrorPanel message={result.error} />}
        {result.data && (
          <div className="metricsGrid">
            <Metric
              label={t("detail.initialEquity")}
              value={result.data.metrics.initial_equity}
            />
            <Metric
              label={t("detail.finalEquity")}
              value={result.data.metrics.final_equity}
            />
            <Metric
              label={t("detail.totalReturn")}
              value={result.data.metrics.total_return}
              percent
            />
            <Metric
              label={t("detail.cagr")}
              value={result.data.metrics.cagr}
              percent
            />
            <Metric
              label={t("detail.maxDrawdown")}
              value={result.data.metrics.max_drawdown}
              percent
            />
            <Metric
              label={t("detail.sharpe")}
              value={result.data.metrics.sharpe_ratio}
            />
            <Metric
              label={t("detail.sortino")}
              value={result.data.metrics.sortino_ratio}
            />
            <Metric
              label={t("detail.commission")}
              value={result.data.metrics.total_commission}
            />
          </div>
        )}
      </section>
      <section className="panel">
        <div className="panelHeader">
          <div>
            <p className="kicker">{t("detail.portfolio")}</p>
            <h2>{t("detail.equityCurve")}</h2>
          </div>
          <span className="countLabel">{t("detail.apiOrder")}</span>
        </div>
        {equity.loading && <LoadingPanel label={t("detail.equityData")} />}
        {equity.error && <ErrorPanel message={equity.error} />}
        {equity.data && equity.data.items.length === 0 && (
          <EmptyState>{t("detail.noEquity")}</EmptyState>
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
        title={t("detail.signals")}
        empty={t("detail.noSignals")}
        load={signalLoader}
        headings={[
          t("detail.utcTime"),
          t("detail.strategy"),
          t("detail.symbol"),
          t("detail.signal"),
        ]}
        row={(item, index) => (
          <tr key={`${item.timestamp}-${index}`}>
            <td>{formatUtc(item.timestamp)}</td>
            <td>{item.strategy_id}</td>
            <td>{item.symbol}</td>
            <td>
              {paperT(`detail.directions.${item.signal_type}`, {
                defaultValue: item.signal_type,
              })}
            </td>
          </tr>
        )}
      />
      <Collection<RiskDecision>
        title={t("detail.riskDecisions")}
        empty={t("detail.noRisk")}
        load={riskLoader}
        headings={[
          t("detail.proposal"),
          t("detail.decision"),
          t("detail.reason"),
          t("detail.message"),
          t("detail.utcTime"),
        ]}
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
                {t(item.approved ? "detail.approved" : "detail.riskRejected")}
              </span>
            </td>
            <td>
              {paperT(`detail.riskReasons.${item.reason_code}`, {
                defaultValue: item.reason_code,
              })}
            </td>
            <td>
              {paperT(`detail.riskMessages.${item.message}`, {
                defaultValue: item.message,
              })}
            </td>
            <td>{formatUtc(item.timestamp)}</td>
          </tr>
        )}
      />
      <Collection<Order>
        title={t("detail.orders")}
        empty={t("detail.noOrders")}
        load={orderLoader}
        headings={[
          t("detail.order"),
          t("detail.strategy"),
          t("detail.symbol"),
          t("detail.sideType"),
          t("detail.quantity"),
          t("detail.status"),
          t("detail.createdUtc"),
        ]}
        row={(item) => (
          <tr key={item.order_id}>
            <td className="mono" title={item.order_id}>
              {shortId(item.order_id)}
            </td>
            <td>{item.strategy_id}</td>
            <td>{item.symbol}</td>
            <td>
              {paperT(`detail.directions.${item.side}`, {
                defaultValue: item.side,
              })}{" "}
              /{" "}
              {paperT(`detail.orderTypes.${item.order_type}`, {
                defaultValue: item.order_type,
              })}
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
                {paperT(`detail.orderStatuses.${item.status}`, {
                  defaultValue: item.status,
                })}
              </span>
            </td>
            <td>{formatUtc(item.created_at)}</td>
          </tr>
        )}
      />
      <Collection<Fill>
        title={t("detail.fills")}
        empty={t("detail.noFills")}
        load={fillLoader}
        headings={[
          t("detail.order"),
          t("detail.symbol"),
          t("detail.side"),
          t("detail.quantity"),
          t("detail.price"),
          t("detail.commission"),
          t("detail.utcTime"),
        ]}
        row={(item, index) => (
          <tr key={`${item.order_id}-${index}`}>
            <td className="mono" title={item.order_id}>
              {shortId(item.order_id)}
            </td>
            <td>{item.symbol}</td>
            <td>
              {paperT(`detail.directions.${item.side}`, {
                defaultValue: item.side,
              })}
            </td>
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
  const { t } = useTranslation("backtests");
  const { t: paperT } = useTranslation("paper");
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

  if (run.loading) return <LoadingPanel label={t("detail.facts")} />;
  if (run.error) return <ErrorPanel message={run.error} />;
  if (!run.data) return null;
  const detail = run.data;
  return (
    <>
      <header className="detailHeader">
        <div>
          <Link className="backLink" href="/backtests">
            {t("detail.back")}
          </Link>
          <p className="eyebrow">
            {t("detail.eyebrow")} / {shortId(detail.run_id)}
          </p>
          <h1>
            {paperT(`strategies.${detail.strategy_type}`, {
              defaultValue: detail.strategy_type.replaceAll("_", " "),
            })}
          </h1>
          <p className="runId">{detail.run_id}</p>
        </div>
        <StatusBadge status={detail.status} />
      </header>
      <section className="runFacts" aria-label={t("detail.facts")}>
        <div>
          <span>{t("detail.dataset")}</span>
          <strong>
            {detail.dataset_id} / {detail.symbol}
          </strong>
        </div>
        <div>
          <span>{t("detail.created")}</span>
          <strong>{formatUtc(detail.created_at)}</strong>
        </div>
        <div>
          <span>{t("detail.started")}</span>
          <strong>{formatUtc(detail.started_at)}</strong>
        </div>
        <div>
          <span>{t("detail.completed")}</span>
          <strong>{formatUtc(detail.completed_at)}</strong>
        </div>
      </section>
      {(detail.status === "CREATED" || detail.status === "RUNNING") && (
        <section className="stateCallout runningCallout" role="status">
          <h2>{t("detail.inProgress")}</h2>
          <p>{t("detail.progressHelp")}</p>
        </section>
      )}
      {detail.status === "FAILED" && (
        <section className="stateCallout failedCallout" role="alert">
          <h2>{t("detail.failed")}</h2>
          <p>{detail.error_message ?? t("detail.failedDefault")}</p>
          <p>{t("detail.failedNoMetrics")}</p>
        </section>
      )}
      {detail.status === "SUCCEEDED" && <SuccessfulResult runId={runId} />}
    </>
  );
}
