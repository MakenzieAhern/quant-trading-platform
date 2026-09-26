import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { Link } from "../../components/Link";
import { useApiResource } from "../../hooks/useApiResource";
import { formatDecimal, formatPercent } from "../../utils/format";
import { experimentApi } from "./api";
import {
  comparisonConditions,
  comparisonUrl,
  parseComparisonIds,
} from "./comparison";
import { useComparisonCopy } from "./comparisonCopy";
import { experimentBenchmarkName, useExperimentCopy } from "./copy";
import { explainExperimentCode } from "./codes";
import { experimentError } from "./errors";
import type { Experiment, ExperimentResult } from "./types";
import "./experiments.css";

type ComparedRun = {
  id: string;
  job?: Experiment;
  result?: ExperimentResult;
  error?: unknown;
  notReady?: boolean;
};

export function ExperimentComparePage() {
  const c = useExperimentCopy();
  const u = useComparisonCopy();
  const [search, setSearch] = useState(window.location.search);
  useEffect(() => {
    const update = () => setSearch(window.location.search);
    window.addEventListener("popstate", update);
    return () => window.removeEventListener("popstate", update);
  }, []);
  const ids = parseComparisonIds(search);
  return (
    <div className="experimentWorkspace">
      <Link back className="experimentBack" href="/experiments">
        ← {c.backList}
      </Link>
      <header className="experimentHeader">
        <h1>{u.comparison}</h1>
        <p>{u.comparisonHelp}</p>
      </header>
      {ids ? (
        <Comparison key={ids.join(",")} ids={ids} />
      ) : (
        <div className="experimentNotice" role="alert">
          <p>{u.invalidIds}</p>
          <Link back href="/experiments">
            {c.backList}
          </Link>
        </div>
      )}
    </div>
  );
}

function Comparison({ ids }: { ids: string[] }) {
  const c = useExperimentCopy();
  const u = useComparisonCopy();
  const { i18n } = useTranslation();
  const [revision, setRevision] = useState(0);
  const [fullPrecision, setFullPrecision] = useState(false);
  const places = fullPrecision ? undefined : 2;
  const data = useApiResource(
    async (signal) =>
      Promise.all(
        ids.map(async (id): Promise<ComparedRun> => {
          let job: Experiment | undefined;
          try {
            job = await experimentApi.get(id, signal);
            if (job.status !== "SUCCEEDED" || !job.result_available)
              return { id, job, notReady: true };
            return { id, job, result: await experimentApi.result(id, signal) };
          } catch (error) {
            return { id, job, error };
          }
        }),
      ),
    [ids.join(","), revision],
  );
  if (data.loading) return <p role="status">{c.loading}</p>;
  const entries = data.data;
  if (!entries || entries.some((entry) => entry.error || entry.notReady))
    return (
      <div className="experimentNotice" role="alert">
        <h2>{u.incomplete}</h2>
        <ul>
          {entries?.map((entry) => (
            <li key={entry.id}>
              <Link href={`/experiments/${entry.id}`}>
                {entry.job?.name ?? entry.id}
              </Link>
              :{" "}
              {entry.notReady
                ? `${u.notReady} ${entry.job ? c.statuses[entry.job.status] : ""}`
                : entry.error
                  ? experimentError(entry.error, c)
                  : c.statuses.SUCCEEDED}
            </li>
          ))}
        </ul>
        <button
          className="button secondary"
          onClick={() => setRevision((value) => value + 1)}
        >
          {c.retryLoad}
        </button>
      </div>
    );
  const completed = entries as (ComparedRun & {
    job: Experiment;
    result: ExperimentResult;
  })[];
  const conditions = completed.map(({ job }) => comparisonConditions(job));
  const rows = [
    {
      key: "data",
      label: u.dataCondition,
      value: (job: Experiment) =>
        `${job.mode === "synthetic_demo" ? c.demo : c.historical}\n${job.dataset_id}\nSHA-256: ${job.dataset_sha256}\n${c.universe}: ${job.configuration.universe}`,
    },
    {
      key: "period",
      label: u.periodCondition,
      value: (job: Experiment) =>
        `${job.configuration.start_date} → ${job.configuration.end_date}\nAsia/Shanghai`,
    },
    {
      key: "costs",
      label: u.costCondition,
      value: (job: Experiment) =>
        `${c.commission}: ${formatDecimal(job.configuration.costs.commission_rate)}\n${c.minimum}: ${formatDecimal(job.configuration.costs.minimum_commission)}`,
    },
    {
      key: "cash",
      label: u.cashCondition,
      value: (job: Experiment) =>
        `${formatDecimal(job.configuration.initial_cash)} CNY`,
    },
    {
      key: "risk",
      label: u.riskCondition,
      value: (job: Experiment) =>
        `${c.drawdown}: ${formatDecimal(job.configuration.risk.max_drawdown)}\n${c.position}: ${formatDecimal(job.configuration.risk.max_position_weight)}`,
    },
    {
      key: "strategy",
      label: u.strategyCondition,
      value: (job: Experiment) =>
        `${job.configuration.strategy_id} · v${job.strategy_version}\n${c.rebalance}: ${job.configuration.strategy.rebalance_sessions}\n${c.holdings}: ${job.configuration.strategy.maximum_holdings}`,
    },
  ] as const;
  const differs = rows.some(
    ({ key }) => new Set(conditions.map((item) => item[key])).size > 1,
  );
  const metrics = [
    {
      label: c.return,
      value: (r: ExperimentResult) =>
        formatPercent(r.metrics.cumulative_return, places),
    },
    {
      label: c.drawdownMetric,
      value: (r: ExperimentResult) =>
        formatPercent(r.metrics.maximum_drawdown, places),
    },
    {
      label: c.cost,
      value: (r: ExperimentResult) =>
        formatDecimal(r.metrics.transaction_costs, places),
    },
    {
      label: c.benchmark,
      value: (r: ExperimentResult) =>
        `${formatPercent(r.metrics.benchmark_return, places)}\n${experimentBenchmarkName(r.benchmark_id, c)}`,
    },
    {
      label: c.excess,
      value: (r: ExperimentResult) =>
        formatPercent(r.metrics.excess_return, places),
    },
    {
      label: c.capitalEnd,
      value: (r: ExperimentResult) =>
        formatDecimal(r.metrics.final_equity, places),
    },
    {
      label: c.fills,
      value: (r: ExperimentResult) => String(r.metrics.number_of_fills),
    },
  ];
  const headers = (
    <tr>
      <th scope="col">{u.condition}</th>
      {completed.map(({ job }) => (
        <th scope="col" key={job.job_id}>
          <Link href={`/experiments/${job.job_id}`}>{job.name}</Link>
        </th>
      ))}
    </tr>
  );
  return (
    <>
      <label className="experimentShareUrl">
        {u.share}
        <input
          readOnly
          value={`${window.location.origin}${comparisonUrl(ids)}`}
          onFocus={(event) => event.currentTarget.select()}
        />
      </label>
      <section className="experimentNotice">
        <h2>{u.compatibility}</h2>
        <p>{differs ? u.differences : u.matching}</p>
        <p>{u.versionBoundary}</p>
        <p>{u.noRecommendation}</p>
      </section>
      <section className="experimentPanel">
        <h2>{u.comparisonMetrics}</h2>
        <label className="experimentCheck">
          <input
            type="checkbox"
            checked={fullPrecision}
            onChange={(event) => setFullPrecision(event.target.checked)}
          />
          {u.fullPrecision}
        </label>
        <p className="experimentHelp">{u.roundedSummary}</p>
        <p className="experimentHelp">{c.tableScroll}</p>
        <div
          className="experimentTableScroll experimentComparisonTable"
          tabIndex={0}
          aria-label={u.comparisonMetrics}
        >
          <table>
            <thead>{headers}</thead>
            <tbody>
              {metrics.map((row) => (
                <tr key={row.label}>
                  <th scope="row">{row.label}</th>
                  {completed.map(({ id, result }) => (
                    <td key={id}>{row.value(result)}</td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
      <section className="experimentPanel">
        <h2>{u.compatibility}</h2>
        <div
          className="experimentTableScroll experimentComparisonTable"
          tabIndex={0}
          aria-label={u.compatibility}
        >
          <table>
            <thead>{headers}</thead>
            <tbody>
              {rows.map((row) => (
                <tr key={row.key}>
                  <th scope="row">
                    {row.label}
                    <span
                      className={`experimentCondition ${new Set(conditions.map((item) => item[row.key])).size > 1 ? "isDifferent" : ""}`}
                    >
                      {new Set(conditions.map((item) => item[row.key])).size > 1
                        ? u.different
                        : u.same}
                    </span>
                  </th>
                  {completed.map(({ id, job }) => (
                    <td key={id}>{row.value(job)}</td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
      <section className="experimentPanel">
        <h2>{c.limits}</h2>
        <div className="experimentComparisonLimits">
          {completed.map(({ id, job, result }) => (
            <article key={id}>
              <h3>{job.name}</h3>
              <p>
                {job.mode === "synthetic_demo"
                  ? c.warningDemo
                  : c.warningHistorical}
              </p>
              <ul>
                {result.limitations.map((code) => (
                  <li key={code}>
                    {explainExperimentCode(code, i18n.language)}
                  </li>
                ))}
              </ul>
              <Link href={`/experiments/${id}`}>{c.open}</Link>
            </article>
          ))}
        </div>
      </section>
    </>
  );
}
