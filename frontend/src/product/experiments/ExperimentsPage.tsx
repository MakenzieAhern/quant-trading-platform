import { useEffect, useState } from "react";
import { Link } from "../../components/Link";
import { Pagination } from "../../components/Pagination";
import { formatUtc } from "../../utils/format";
import { experimentApi } from "./api";
import { useExperimentCopy } from "./copy";
import { isActiveExperiment } from "./useExperiment";
import type { Experiment, Page } from "./types";
import "./experiments.css";

export function ExperimentsPage() {
  const c = useExperimentCopy();
  const [offset, setOffset] = useState(0);
  const [revision, setRevision] = useState(0);
  const [jobs, setJobs] = useState<{
    offset: number;
    data: Page<Experiment> | null;
    error: boolean;
  }>({ offset, data: null, error: false });
  if (jobs.offset !== offset) setJobs({ offset, data: null, error: false });
  useEffect(() => {
    const controller = new AbortController();
    let active = true;
    let timer: number | undefined;
    async function load() {
      try {
        const data = await experimentApi.list(controller.signal, 20, offset);
        if (!active) return;
        setJobs({ offset, data, error: false });
        if (data.items.some(isActiveExperiment))
          timer = window.setTimeout(() => void load(), 5000);
      } catch {
        if (active) setJobs((previous) => ({ ...previous, error: true }));
      }
    }
    void load();
    return () => {
      active = false;
      controller.abort();
      window.clearTimeout(timer);
    };
  }, [offset, revision]);
  return (
    <div className="experimentWorkspace">
      <header className="experimentHeader">
        <h1>{c.listTitle}</h1>
        <p>{c.listIntro}</p>
        <div className="experimentActions">
          <Link className="button" href="/research/new">
            {c.newExperiment}
          </Link>
          <Link className="button secondary" href="/research/a-share">
            {c.formalArchive}
          </Link>
          <button
            className="button secondary"
            onClick={() => setRevision((value) => value + 1)}
          >
            {c.refresh}
          </button>
        </div>
      </header>
      {!jobs.data && !jobs.error && <p role="status">{c.loading}</p>}
      {jobs.error && (
        <div className="experimentNotice" role="alert">
          <p>{c.networkError}</p>
          <button
            className="button secondary"
            onClick={() => setRevision((value) => value + 1)}
          >
            {c.retryLoad}
          </button>
        </div>
      )}
      {jobs.data && (
        <>
          {jobs.data.items.length === 0 ? (
            <div className="experimentPanel">
              <p>{c.empty}</p>
              <Link href="/research/new">{c.newExperiment}</Link>
            </div>
          ) : (
            <div className="experimentList">
              {jobs.data.items.map((job) => (
                <article
                  className="experimentPanel experimentListCard"
                  key={job.job_id}
                >
                  <div>
                    <span className="experimentMode">
                      {job.mode === "synthetic_demo" ? c.demo : c.historical}
                    </span>
                    <h2>
                      <Link href={`/experiments/${job.job_id}`}>
                        {job.name}
                      </Link>
                    </h2>
                    <p>
                      {job.configuration.start_date} →{" "}
                      {job.configuration.end_date}{" "}
                      <span className="experimentHelp">Asia/Shanghai</span>
                    </p>
                    <p className="experimentHelp">
                      {c.created}: {formatUtc(job.created_at)}
                    </p>
                  </div>
                  <div className="experimentListAction">
                    <span
                      className={`experimentStatus experimentStatus--${job.status.toLowerCase()}`}
                    >
                      {c.statuses[job.status]}
                    </span>
                    <Link
                      className="button secondary"
                      href={`/experiments/${job.job_id}`}
                    >
                      {c.open}
                    </Link>
                  </div>
                </article>
              ))}
            </div>
          )}
          <Pagination
            offset={jobs.data.offset}
            limit={jobs.data.limit}
            total={jobs.data.total}
            onChange={setOffset}
          />
        </>
      )}
    </div>
  );
}
