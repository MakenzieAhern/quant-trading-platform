import { useState } from "react";
import { useTranslation } from "react-i18next";
import { Link } from "../components/Link";
import { Pagination } from "../components/Pagination";
import { useApiResource } from "../hooks/useApiResource";
import { formatUtc } from "../utils/format";
import { experimentApi } from "./experiments/api";
import { useExperimentCopy } from "./experiments/copy";
import { experimentError } from "./experiments/errors";
import { marketUpdateApi } from "./marketUpdates/api";
import { updateError, useUpdateCopy } from "./marketUpdates/copy";
import { useProductCopy } from "./copy";

export function TaskCenterPage() {
  const c = useProductCopy();
  const e = useExperimentCopy();
  const u = useUpdateCopy();
  const { i18n } = useTranslation();
  const [researchOffset, setResearchOffset] = useState(0);
  const [updateOffset, setUpdateOffset] = useState(0);
  const [revision, setRevision] = useState(0);
  const research = useApiResource(
    (signal) => experimentApi.list(signal, 20, researchOffset),
    [researchOffset, revision],
  );
  const updates = useApiResource(
    (signal) => marketUpdateApi.list(updateOffset, signal),
    [updateOffset, revision],
  );
  return (
    <div className="productPage">
      <header className="pageHeader">
        <div>
          <h1>{c.tasks}</h1>
          <p>{c.tasksIntro}</p>
        </div>
        <button
          className="button secondary"
          onClick={() => setRevision((value) => value + 1)}
        >
          {e.refresh}
        </button>
      </header>
      <section className="panel" aria-label={c.researchTasks}>
        <h2>{c.researchTasks}</h2>
        {research.loading && <p role="status">{c.loading}</p>}
        {research.error && (
          <p role="alert">{experimentError(research.error, e)}</p>
        )}
        {research.data && (
          <>
            {research.data.total === 0 && <p>{c.noResearchTasks}</p>}
            <ul className="taskCenterList">
              {research.data.items.map((job) => (
                <li key={job.job_id}>
                  <div>
                    <strong>{job.name}</strong>
                    <span>
                      {e.statuses[job.status]} ·{" "}
                      {job.mode === "synthetic_demo" ? e.demo : e.historical}
                    </span>
                    <small>{formatUtc(job.created_at)}</small>
                  </div>
                  <Link
                    className="button secondary"
                    href={`/experiments/${job.job_id}`}
                    aria-label={`${e.open}: ${job.name} · ${formatUtc(job.created_at)}`}
                  >
                    {e.open}
                  </Link>
                </li>
              ))}
            </ul>
            <Pagination
              offset={researchOffset}
              limit={research.data.limit}
              total={research.data.total}
              onChange={setResearchOffset}
            />
          </>
        )}
      </section>
      <section className="panel" aria-label={c.updateTasks}>
        <h2>{c.updateTasks}</h2>
        <p>{c.candidateOnly}</p>
        {updates.loading && <p role="status">{c.loading}</p>}
        {updates.error && (
          <p role="alert">{updateError(updates.error, i18n.language)}</p>
        )}
        {updates.data && (
          <>
            {updates.data.total === 0 && <p>{c.noUpdateTasks}</p>}
            <ul className="taskCenterList">
              {updates.data.items.map((job) => (
                <li key={job.job_id}>
                  <div>
                    <strong>{job.configuration.security_ids.join(", ")}</strong>
                    <span>
                      {u.statuses[job.status]} · {job.configuration.start_date}{" "}
                      → {job.configuration.end_date} (Asia/Shanghai)
                    </span>
                    <small>{formatUtc(job.created_at)}</small>
                  </div>
                  <Link
                    className="button secondary"
                    href={`/data?updateJob=${encodeURIComponent(job.job_id)}`}
                    aria-label={`${u.open}: ${job.configuration.security_ids.join(", ")} · ${job.configuration.start_date}–${job.configuration.end_date} · ${formatUtc(job.created_at)}`}
                  >
                    {u.open}
                  </Link>
                </li>
              ))}
            </ul>
            <Pagination
              offset={updateOffset}
              limit={updates.data.limit}
              total={updates.data.total}
              onChange={setUpdateOffset}
            />
          </>
        )}
      </section>
    </div>
  );
}
