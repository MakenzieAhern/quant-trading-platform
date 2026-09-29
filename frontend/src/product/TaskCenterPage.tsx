import { useEffect, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import { Link } from "../components/Link";
import { Pagination } from "../components/Pagination";
import { useApiResource } from "../hooks/useApiResource";
import { formatUtc } from "../utils/format";
import { experimentApi } from "./experiments/api";
import { useExperimentCopy } from "./experiments/copy";
import { experimentError } from "./experiments/errors";
import { isActiveExperiment } from "./experiments/useExperiment";
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
  const focusedList = useRef<"research" | "updates" | null>(null);
  const researchHeading = useRef<HTMLHeadingElement>(null);
  const updateHeading = useRef<HTMLHeadingElement>(null);
  const researchError = useRef<HTMLParagraphElement>(null);
  const updateErrorFocus = useRef<HTMLParagraphElement>(null);
  const research = useApiResource(
    (signal) => experimentApi.list(signal, 20, researchOffset),
    [researchOffset, revision],
    { intervalMs: 5000, while: (page) => page.items.some(isActiveExperiment) },
  );
  const updates = useApiResource(
    (signal) => marketUpdateApi.list(updateOffset, signal),
    [updateOffset, revision],
    {
      intervalMs: 5000,
      while: (page) =>
        page.items.some(
          (job) => job.status === "QUEUED" || job.status === "RUNNING",
        ),
    },
  );
  useEffect(() => {
    if (document.activeElement !== document.body) return;
    if (
      focusedList.current === "research" &&
      (research.error || research.data)
    ) {
      (research.error ? researchError : researchHeading).current?.focus();
      focusedList.current = null;
    } else if (
      focusedList.current === "updates" &&
      (updates.error || updates.data)
    ) {
      (updates.error ? updateErrorFocus : updateHeading).current?.focus();
      focusedList.current = null;
    }
  }, [research.data, research.error, updates.data, updates.error]);
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
        <h2 ref={researchHeading} tabIndex={-1}>
          {c.researchTasks}
        </h2>
        {research.loading && <p role="status">{c.loading}</p>}
        {research.error && (
          <p ref={researchError} role="alert" tabIndex={-1}>
            {experimentError(research.error, e)}
          </p>
        )}
        {research.data && (
          <>
            {research.data.total === 0 && <p>{c.noResearchTasks}</p>}
            <ul
              className="taskCenterList"
              onFocusCapture={() => (focusedList.current = "research")}
              onBlurCapture={() => (focusedList.current = null)}
            >
              {research.data.items.map((job) => (
                <li key={job.job_id}>
                  <div>
                    <strong>{job.name}</strong>
                    <span>
                      <span role="status">{e.statuses[job.status]}</span> ·{" "}
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
          </>
        )}
        <Pagination
          offset={researchOffset}
          limit={research.data?.limit ?? 20}
          total={research.data?.total ?? null}
          loading={research.loading}
          onChange={setResearchOffset}
        />
      </section>
      <section className="panel" aria-label={c.updateTasks}>
        <h2 ref={updateHeading} tabIndex={-1}>
          {c.updateTasks}
        </h2>
        <p>{c.candidateOnly}</p>
        {updates.loading && <p role="status">{c.loading}</p>}
        {updates.error && (
          <p ref={updateErrorFocus} role="alert" tabIndex={-1}>
            {updateError(updates.error, i18n.language)}
          </p>
        )}
        {updates.data && (
          <>
            {updates.data.total === 0 && <p>{c.noUpdateTasks}</p>}
            <ul
              className="taskCenterList"
              onFocusCapture={() => (focusedList.current = "updates")}
              onBlurCapture={() => (focusedList.current = null)}
            >
              {updates.data.items.map((job) => (
                <li key={job.job_id}>
                  <div>
                    <strong>{job.configuration.security_ids.join(", ")}</strong>
                    <span>
                      <span role="status">{u.statuses[job.status]}</span> ·{" "}
                      {job.configuration.start_date} →{" "}
                      {job.configuration.end_date} (Asia/Shanghai)
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
          </>
        )}
        <Pagination
          offset={updateOffset}
          limit={updates.data?.limit ?? 20}
          total={updates.data?.total ?? null}
          loading={updates.loading}
          onChange={setUpdateOffset}
        />
      </section>
    </div>
  );
}
