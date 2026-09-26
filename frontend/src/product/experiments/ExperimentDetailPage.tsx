import { useEffect, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import { Link } from "../../components/Link";
import { useApiResource } from "../../hooks/useApiResource";
import { formatDecimal, formatPercent, formatUtc } from "../../utils/format";
import { navigate } from "../../utils/navigation";
import { usePageDataContext } from "../dataContext";
import { experimentApi } from "./api";
import { experimentBenchmarkName, useExperimentCopy } from "./copy";
import { useComparisonCopy } from "./comparisonCopy";
import { explainExperimentCode } from "./codes";
import { experimentError } from "./errors";
import { ExperimentCollections } from "./ExperimentCollections";
import { ExperimentPlan } from "./ExperimentPlan";
import { canUsePaperHandoff } from "./paperHandoff";
import { isActiveExperiment, useExperiment } from "./useExperiment";
import type { Experiment } from "./types";
import "./experiments.css";

export function ExperimentDetailPage({ jobId }: { jobId: string }) {
  return <ExperimentDetail key={jobId} jobId={jobId} />;
}

function ExperimentDetail({ jobId }: { jobId: string }) {
  const c = useExperimentCopy();
  const { i18n } = useTranslation();
  const job = useExperiment(jobId);
  const [observedEnd, setObservedEnd] = useState<string | null>(null);
  usePageDataContext(
    job.data?.mode ?? null,
    observedEnd ?? job.data?.configuration.end_date ?? null,
    observedEnd ? "observed" : "requested",
  );
  const [action, setAction] = useState<"cancel" | "retry" | null>(null);
  const [actionError, setActionError] = useState<unknown>(null);
  const locked = useRef(false);
  const activeJob = useRef<string | null>(jobId);
  useEffect(() => {
    activeJob.current = jobId;
    locked.current = false;
    return () => {
      activeJob.current = null;
    };
  }, [jobId]);
  async function command(kind: "cancel" | "retry") {
    if (locked.current) return;
    locked.current = true;
    setAction(kind);
    setActionError(null);
    try {
      const updated =
        kind === "cancel"
          ? await experimentApi.cancel(jobId)
          : // One logical child per immutable parent. Its server-persisted key survives
            // refresh, a lost response and another tab; further retries use the child.
            await experimentApi.retry(jobId, `experiment-retry-v1:${jobId}`);
      if (activeJob.current !== jobId) return;
      if (kind === "retry") navigate(`/experiments/${updated.job_id}`);
      else job.refresh();
    } catch (reason) {
      if (activeJob.current === jobId) setActionError(reason);
    } finally {
      if (activeJob.current === jobId) {
        locked.current = false;
        setAction(null);
      }
    }
  }
  const data = job.data;
  return (
    <div className="experimentWorkspace">
      <Link back className="experimentBack" href="/experiments">
        ← {c.backList}
      </Link>
      {!data && !job.error && <p role="status">{c.loading}</p>}
      {Boolean(job.error) && (
        <div className="experimentNotice" role="alert">
          <p>{experimentError(job.error, c)}</p>
          <button className="button secondary" onClick={job.refresh}>
            {c.refresh}
          </button>
        </div>
      )}
      {data && (
        <>
          <header className="experimentHeader">
            <span className="experimentMode">
              {data.mode === "synthetic_demo" ? c.demo : c.historical}
            </span>
            <h1>{data.name}</h1>
            <p>
              {data.configuration.start_date} → {data.configuration.end_date} ·
              Asia/Shanghai
            </p>
            <div className="experimentActions">
              <span
                className={`experimentStatus experimentStatus--${data.status.toLowerCase()}`}
              >
                {c.statuses[data.status]}
              </span>
              <button className="button secondary" onClick={job.refresh}>
                {c.refresh}
              </button>
              {isActiveExperiment(data) && (
                <button
                  className="button secondary"
                  disabled={action !== null || data.cancel_requested}
                  onClick={() => void command("cancel")}
                >
                  {action === "cancel" ? c.cancelling : c.cancel}
                </button>
              )}
              {["FAILED", "INTERRUPTED", "CANCELLED"].includes(data.status) && (
                <button
                  className="button"
                  disabled={action !== null}
                  onClick={() => void command("retry")}
                >
                  {action === "retry" ? c.retrying : c.retry}
                </button>
              )}
            </div>
          </header>
          {Boolean(actionError) && (
            <p className="experimentError" role="alert">
              {experimentError(actionError, c)}
            </p>
          )}
          {isActiveExperiment(data) && <JobProgress job={data} />}
          {data.status === "FAILED" && (
            <p className="experimentNotice" role="alert">
              {c.failureHelp}
            </p>
          )}
          {data.status === "CANCELLED" && (
            <p className="experimentNotice">{c.cancelledHelp}</p>
          )}
          {data.status === "INTERRUPTED" && (
            <p className="experimentNotice">{c.interruptedHelp}</p>
          )}
          {["FAILED", "INTERRUPTED", "CANCELLED"].includes(data.status) && (
            <p className="experimentHelp">{c.retryHelp}</p>
          )}
          {data.error_code && (
            <div>
              <p>{explainExperimentCode(data.error_code, i18n.language)}</p>
              <details className="experimentTechnical">
                <summary>{c.technical}</summary>
                <code>{data.error_code}</code>
              </details>
            </div>
          )}
          {data.result_available ? (
            <ExperimentResults job={data} onObservedEnd={setObservedEnd} />
          ) : (
            <p className="experimentHelp">{c.resultPending}</p>
          )}
          <details className="experimentPanel experimentAudit">
            <summary>{c.audit}</summary>
            <dl>
              <dt>{c.task}</dt>
              <dd>{data.job_id}</dd>
              <dt>{c.dataset}</dt>
              <dd>{data.dataset_id}</dd>
              <dt>{c.datasetHash}</dt>
              <dd>{data.dataset_sha256}</dd>
              <dt>{c.configHash}</dt>
              <dd>{data.configuration_sha256}</dd>
              <dt>{c.strategyVersion}</dt>
              <dd>{data.strategy_version}</dd>
              <dt>{c.created}</dt>
              <dd>{formatUtc(data.created_at)}</dd>
              <dt>{c.attempt}</dt>
              <dd>{data.attempt}</dd>
              {data.retry_of && (
                <>
                  <dt>{c.retryOf}</dt>
                  <dd>
                    <Link href={`/experiments/${data.retry_of}`}>
                      {data.retry_of}
                    </Link>
                  </dd>
                </>
              )}
            </dl>
            <h3>{c.configuration}</h3>
            <pre>{JSON.stringify(data.configuration, null, 2)}</pre>
          </details>
        </>
      )}
    </div>
  );
}

function JobProgress({ job }: { job: Experiment }) {
  const c = useExperimentCopy();
  const [now, setNow] = useState(Date.now);
  useEffect(() => {
    const timer = window.setInterval(() => setNow(Date.now()), 1000);
    return () => window.clearInterval(timer);
  }, []);
  const elapsed = Math.max(
    0,
    Math.floor((now - Date.parse(job.started_at ?? job.created_at)) / 1000),
  );
  return (
    <section className="experimentPanel" aria-label={c.status}>
      <div role="status" aria-live="polite">
        <h2>
          {c.phases[job.phase as keyof typeof c.phases] ??
            c.statuses[job.status]}
        </h2>
        <p>{job.cancel_requested ? c.cancelRequested : c.persisted}</p>
        <p>
          {c.sessions}: {job.completed_sessions}
          {job.total_sessions === null ? "" : ` / ${job.total_sessions}`}
        </p>
      </div>
      {job.total_sessions !== null && job.total_sessions > 0 ? (
        <progress
          aria-label={c.sessions}
          value={job.completed_sessions}
          max={job.total_sessions}
        />
      ) : (
        <p className="experimentHelp">{c.progressUnknown}</p>
      )}
      <p className="experimentHelp">
        {c.elapsed}: {elapsed} {c.seconds}
      </p>
      <p className="experimentTaskId">
        {c.task}: {job.job_id}
      </p>
    </section>
  );
}

function ExperimentResults({
  job,
  onObservedEnd,
}: {
  job: Experiment;
  onObservedEnd: (value: string | null) => void;
}) {
  const c = useExperimentCopy();
  const u = useComparisonCopy();
  const [fullPrecision, setFullPrecision] = useState(false);
  const places = fullPrecision ? undefined : 2;
  const { i18n } = useTranslation();
  const [revision, setRevision] = useState(0);
  const result = useApiResource(
    (signal) => experimentApi.result(job.job_id, signal),
    [job.job_id, revision],
  );
  useEffect(() => {
    onObservedEnd(result.data?.date_end ?? null);
  }, [onObservedEnd, result.data?.date_end]);
  if (result.loading) return <p role="status">{c.loading}</p>;
  if (result.error)
    return (
      <div role="alert">
        <p>{experimentError(result.error, c)}</p>
        <button
          className="button secondary"
          onClick={() => setRevision((value) => value + 1)}
        >
          {c.retryLoad}
        </button>
      </div>
    );
  if (!result.data) return null;
  const data = result.data;
  const signedPercent = (value: string | null) =>
    value !== null && !value.startsWith("-") && /[1-9]/.test(value)
      ? `+${formatPercent(value, places)}`
      : formatPercent(value, places);
  return (
    <>
      <section aria-label={c.resultTitle}>
        <h2>{c.resultTitle}</h2>
        <label className="experimentCheck">
          <input
            type="checkbox"
            checked={fullPrecision}
            onChange={(event) => setFullPrecision(event.target.checked)}
          />
          {u.fullPrecision}
        </label>
        <p className="experimentHelp">{u.roundedSummary}</p>
        <dl className="experimentMetrics">
          {[
            [c.return, signedPercent(data.metrics.cumulative_return)],
            [
              c.drawdownMetric,
              formatPercent(data.metrics.maximum_drawdown, places),
            ],
            [c.cost, formatDecimal(data.metrics.transaction_costs, places)],
            [c.benchmark, signedPercent(data.metrics.benchmark_return)],
          ].map(([label, value]) => (
            <div className="experimentPanel" key={label}>
              <dt>{label}</dt>
              <dd>{value}</dd>
            </div>
          ))}
        </dl>
        <p className="experimentHelp">
          {c.capitalEnd}: {formatDecimal(data.metrics.final_equity, places)} ·{" "}
          {c.excess}: {signedPercent(data.metrics.excess_return)} ·{" "}
          {experimentBenchmarkName(data.benchmark_id, c)}
        </p>
      </section>
      <section className="experimentNotice" aria-label={c.limits}>
        <h3>{c.limits}</h3>
        <p>
          {data.mode === "synthetic_demo" ? c.warningDemo : c.warningHistorical}
        </p>
        <p>{c.noGuarantee}</p>
        {data.limitations.length > 0 && (
          <ul>
            {data.limitations.map((limitation) => (
              <li key={limitation}>
                {explainExperimentCode(limitation, i18n.language)}
              </li>
            ))}
          </ul>
        )}
        <details>
          <summary>{c.technical}</summary>
          {data.limitations.map((code) => (
            <p key={code}>
              <code>{code}</code>
            </p>
          ))}
        </details>
      </section>
      <ExperimentPlan plan={data.simulation_plan ?? null} />
      {canUsePaperHandoff(job) && (
        <div className="experimentPanel">
          <Link
            className="button secondary"
            href={`/paper/new?from_experiment=${encodeURIComponent(job.job_id)}`}
          >
            {c.paperHandoff}
          </Link>
          <p className="experimentHelp">{c.paperHandoffHelp}</p>
        </div>
      )}
      <ExperimentCollections jobId={job.job_id} />
      <section className="experimentPanel">
        <h2>{c.execution}</h2>
        <dl className="experimentExecution">
          <div>
            <dt>{c.proposals}</dt>
            <dd>{data.execution.proposals}</dd>
          </div>
          <div>
            <dt>{c.approved}</dt>
            <dd>{data.execution.approved_decisions}</dd>
          </div>
          <div>
            <dt>{c.fills}</dt>
            <dd>{data.execution.fills}</dd>
          </div>
        </dl>
        <div
          className="experimentTableScroll"
          tabIndex={0}
          aria-label={c.tableScroll}
        >
          <table>
            <thead>
              <tr>
                <th scope="col">{c.reason}</th>
                <th scope="col">{c.count}</th>
              </tr>
            </thead>
            <tbody>
              {Object.entries(data.execution.reason_counts).map(
                ([reason, count]) => (
                  <tr key={reason}>
                    <td>
                      {explainExperimentCode(reason, i18n.language)}
                      <details>
                        <summary aria-label={`${c.technical}: ${reason}`}>
                          {c.technical}
                        </summary>
                        <code>{reason}</code>
                      </details>
                    </td>
                    <td>{count}</td>
                  </tr>
                ),
              )}
            </tbody>
          </table>
        </div>
      </section>
    </>
  );
}
