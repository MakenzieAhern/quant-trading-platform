import { useTranslation } from "react-i18next";

import { researchApi } from "../../api/research";
import {
  EmptyState,
  ErrorPanel,
  LoadingPanel,
} from "../../components/AsyncPanel";
import { Link } from "../../components/Link";
import { BenchmarkChart } from "../../components/research/BenchmarkChart";
import { DrawdownChart } from "../../components/research/DrawdownChart";
import { MonthlyReturnHeatmap } from "../../components/research/MonthlyReturnHeatmap";
import { ResearchMetricGrid } from "../../components/research/ResearchMetricGrid";
import { SplitBadge } from "../../components/research/SplitBadge";
import { useApiResource } from "../../hooks/useApiResource";
import {
  formatDecimal,
  formatPercent,
  formatUtc,
  shortId,
} from "../../utils/format";

export function ResearchRunPage({ runId }: { runId: string }) {
  const { t } = useTranslation([
    "research",
    "common",
    "metrics",
    "accessibility",
  ]);
  const run = useApiResource(
    (signal) => researchApi.run(runId, signal),
    [runId],
  );
  const metrics = useApiResource(
    (signal) => researchApi.metrics(runId, signal),
    [runId],
  );
  const equity = useApiResource(
    (signal) => researchApi.points(runId, "equity", signal),
    [runId],
  );
  const benchmark = useApiResource(
    (signal) => researchApi.points(runId, "benchmark", signal),
    [runId],
  );
  const drawdown = useApiResource(
    (signal) => researchApi.points(runId, "drawdown", signal),
    [runId],
  );
  const monthly = useApiResource(
    (signal) => researchApi.monthlyReturns(runId, signal),
    [runId],
  );
  const rolling = useApiResource(
    (signal) => researchApi.rollingMetrics(runId, signal),
    [runId],
  );
  const holdings = useApiResource(
    (signal) => researchApi.holdings(runId, signal),
    [runId],
  );
  const rebalances = useApiResource(
    (signal) => researchApi.rebalances(runId, signal),
    [runId],
  );
  const trades = useApiResource(
    (signal) => researchApi.trades(runId, signal),
    [runId],
  );
  if (run.loading) return <LoadingPanel label={t("research:runDetail")} />;
  if (run.error) return <ErrorPanel message={run.error} />;
  if (!run.data) return null;
  const emptyCharts =
    !equity.data?.items.length && !benchmark.data?.items.length;
  const rollingByDate = new Map<string, Record<string, string>>();
  for (const item of rolling.data?.items ?? []) {
    if (item.value === null) continue;
    const values = rollingByDate.get(item.trading_date) ?? {};
    values[item.metric_name] = item.value;
    rollingByDate.set(item.trading_date, values);
  }
  const completeRolling = [...rollingByDate].filter(
    ([, values]) =>
      values.sharpe !== undefined && values.drawdown !== undefined,
  );
  const rollingPoints = (metricName: "sharpe" | "drawdown") =>
    completeRolling.map(([trading_date, values], sequence) => ({
      sequence,
      trading_date,
      value: values[metricName],
    }));
  const rollingSharpe = rollingPoints("sharpe");
  const rollingDrawdown = rollingPoints("drawdown");
  return (
    <>
      <Link className="backLink" href="/research/a-share">
        {t("research:back")}
      </Link>
      <header className="detailHeader">
        <div>
          <p className="eyebrow">
            {t("research:runDetail")} / {shortId(runId)}
          </p>
          <h1>{run.data.strategy_id}</h1>
          <p className="runId">{runId}</p>
        </div>
        <SplitBadge period={run.data.period_kind} />
      </header>
      {run.data.period_kind !== "PILOT_SMOKE" && (
        <div className="oosGuard" role="note">
          {run.data.period_kind === "OUT_OF_SAMPLE"
            ? t("research:oosResultCaution")
            : t("research:preOosEvidence")}
        </div>
      )}
      {Boolean(run.data.diagnostics.dataset_acceptance_warning) && (
        <div className="oosGuard" role="alert">
          {String(run.data.diagnostics.dataset_acceptance_warning)}
        </div>
      )}
      {run.data.period_kind === "PILOT_SMOKE" && (
        <div className="oosGuard" role="note">
          PILOT_ENGINEERING_SMOKE_ONLY — 仅工程验证；非 Development / Validation
          / OOS 证据。 Unknown executable liquidity = NO FILL.
          未知可成交状态不得假定成交。
        </div>
      )}
      <section className="runFacts" aria-label={t("research:lineage")}>
        <div>
          <span>{t("common:dataset")}</span>
          <strong>
            <Link
              className="monoLink"
              href={`/research/a-share/datasets/${encodeURIComponent(run.data.dataset_id)}`}
            >
              {run.data.dataset_id}
            </Link>
          </strong>
        </div>
        <div>
          <span>{t("research:provider")}</span>
          <strong>
            {run.data.provider} / {run.data.provider_version}
          </strong>
        </div>
        <div>
          <span>{t("research:checksum")}</span>
          <strong className="mono" title={run.data.dataset_checksum}>
            {shortId(run.data.dataset_checksum)}
          </strong>
        </div>
        <div>
          <span>{t("research:ruleVersion")}</span>
          <strong>{run.data.market_rule_version}</strong>
        </div>
        <div>
          <span>{t("research:benchmark")}</span>
          <strong>{run.data.benchmark_id}</strong>
        </div>
        <div>
          <span>{t("common:created")}</span>
          <strong>{formatUtc(run.data.created_at)}</strong>
        </div>
        <div>
          <span>{t("research:gitCommit")}</span>
          <strong className="mono" title={run.data.git_commit}>
            {shortId(run.data.git_commit)}
          </strong>
        </div>
        <div>
          <span>{t("research:strategyConfig")}</span>
          <strong className="mono" title={run.data.strategy_config_hash}>
            {shortId(run.data.strategy_config_hash)}
          </strong>
        </div>
      </section>
      <section className="panel">
        <div className="panelHeader">
          <h2>{t("research:methodology")}</h2>
        </div>
        {metrics.loading && <LoadingPanel label={t("research:methodology")} />}
        {metrics.error && <ErrorPanel message={metrics.error} />}
        {metrics.data && <ResearchMetricGrid metrics={metrics.data.items} />}
      </section>
      <section className="panel">
        <div className="panelHeader">
          <h2>
            {t("research:equity")} / {t("research:benchmarkCurve")}
          </h2>
        </div>
        {emptyCharts ? (
          <EmptyState>{t("common:noData")}</EmptyState>
        ) : (
          <BenchmarkChart
            strategy={equity.data?.items ?? []}
            benchmark={benchmark.data?.items ?? []}
          />
        )}
      </section>
      <section className="panel">
        <div className="panelHeader">
          <h2>{t("research:drawdown")}</h2>
        </div>
        {drawdown.data?.items.length ? (
          <DrawdownChart points={drawdown.data.items} />
        ) : (
          <EmptyState>{t("common:noData")}</EmptyState>
        )}
      </section>
      <section className="panel">
        <div className="panelHeader">
          <h2>{t("research:monthlyReturns")}</h2>
        </div>
        {monthly.data?.items.length ? (
          <MonthlyReturnHeatmap values={monthly.data.items} />
        ) : (
          <EmptyState>{t("common:noData")}</EmptyState>
        )}
      </section>
      <section className="panel">
        <div className="panelHeader">
          <h2>{t("research:rollingMetrics")}</h2>
        </div>
        {rolling.loading && (
          <LoadingPanel label={t("research:rollingMetrics")} />
        )}
        {rolling.error && <ErrorPanel message={rolling.error} />}
        {rollingSharpe.length || rollingDrawdown.length ? (
          <BenchmarkChart
            strategy={rollingSharpe}
            benchmark={rollingDrawdown}
            strategyLabel={t("metrics:sharpe_ratio")}
            benchmarkLabel={t("research:rollingDrawdown")}
            ariaLabel={t("accessibility:rollingChart")}
          />
        ) : (
          !rolling.loading && <EmptyState>{t("common:noData")}</EmptyState>
        )}
      </section>
      <ResearchTable
        title={t("research:holdings")}
        headings={[
          t("research:columns.date"),
          t("research:columns.security"),
          t("research:columns.quantity"),
          t("research:columns.weight"),
          t("research:columns.marketValue"),
        ]}
        rows={
          holdings.data?.items.map((item) => [
            item.trading_date,
            item.security_id,
            formatDecimal(item.quantity),
            formatPercent(item.weight),
            formatDecimal(item.market_value),
          ]) ?? []
        }
      />
      <ResearchTable
        title={t("research:rebalances")}
        headings={[
          t("research:columns.date"),
          t("research:columns.turnover"),
          t("research:columns.transactionCost"),
        ]}
        rows={
          rebalances.data?.items.map((item) => [
            item.trading_date,
            formatPercent(item.turnover),
            formatDecimal(item.transaction_cost),
          ]) ?? []
        }
      />
      <ResearchTable
        title={t("research:trades")}
        headings={[
          t("research:columns.utcTime"),
          t("research:columns.security"),
          t("research:columns.side"),
          t("research:columns.quantity"),
          t("research:columns.price"),
          t("research:columns.cost"),
        ]}
        rows={
          trades.data?.items.map((item) => [
            formatUtc(item.timestamp),
            item.security_id,
            item.side,
            formatDecimal(item.quantity),
            formatDecimal(item.price),
            formatDecimal(item.transaction_cost),
          ]) ?? []
        }
      />
      <section className="researchNotes">
        <article>
          <h2>{t("research:knownLimitations")}</h2>
          <p>
            {run.data.diagnostics.known_limitations
              ? String(run.data.diagnostics.known_limitations)
              : t("common:noData")}
          </p>
        </article>
        <article>
          <h2>{t("research:reproducibility")}</h2>
          <p>{t("research:reproduceCommand")}</p>
          <code>
            python backend/scripts/reproduce_research.py --run-id {runId}
          </code>
        </article>
      </section>
    </>
  );
}

function ResearchTable({
  title,
  headings,
  rows,
}: {
  title: string;
  headings: string[];
  rows: string[][];
}) {
  const { t } = useTranslation("common");
  return (
    <section className="panel">
      <div className="panelHeader">
        <h2>{title}</h2>
      </div>
      {rows.length === 0 ? (
        <EmptyState>{t("noData")}</EmptyState>
      ) : (
        <div className="tableScroll">
          <table>
            <thead>
              <tr>
                {headings.map((heading) => (
                  <th key={heading}>{heading}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {rows.map((row, index) => (
                <tr key={index}>
                  {row.map((value, column) => (
                    <td key={`${column}-${value}`}>{value}</td>
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
