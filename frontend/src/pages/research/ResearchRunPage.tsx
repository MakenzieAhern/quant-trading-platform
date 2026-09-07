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
  const { t } = useTranslation(["research", "common"]);
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
      {run.data.period_kind !== "OUT_OF_SAMPLE" && (
        <div className="oosGuard">{t("research:oosNotRun")}</div>
      )}
      <section className="runFacts" aria-label={t("research:lineage")}>
        <div>
          <span>{t("common:dataset")}</span>
          <strong>{run.data.dataset_id}</strong>
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
      <ResearchTable
        title={t("research:holdings")}
        headings={["Date", "Security", "Quantity", "Weight", "Market value"]}
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
        headings={["Date", "Turnover", "Transaction cost"]}
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
        headings={["UTC time", "Security", "Side", "Quantity", "Price", "Cost"]}
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
