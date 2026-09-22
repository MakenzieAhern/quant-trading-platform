import { useEffect, useState } from "react";
import { Link } from "../../components/Link";
import { Pagination } from "../../components/Pagination";
import { formatUtc } from "../../utils/format";
import { navigate } from "../../utils/navigation";
import { experimentApi } from "./api";
import { useExperimentCopy } from "./copy";
import { comparisonUrl } from "./comparison";
import { useComparisonCopy } from "./comparisonCopy";
import { isActiveExperiment } from "./useExperiment";
import type { Experiment, Page } from "./types";
import "./experiments.css";

export function ExperimentsPage() {
  const c = useExperimentCopy();
  const u = useComparisonCopy();
  const [selected, setSelected] = useState<{ id: string; name: string }[]>([]);
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
      <section
        className="experimentPanel experimentCompareSelection"
        aria-label={u.compare}
      >
        <div>
          <h2>{u.compare}</h2>
          <p className="experimentHelp">{u.selectHelp}</p>
          <p role="status">
            {u.selected}: {selected.length} / 3
          </p>
        </div>
        <div className="experimentActions">
          {selected.map((item) => (
            <button
              className="button secondary"
              key={item.id}
              aria-label={`${u.remove} ${item.name}`}
              onClick={() =>
                setSelected((items) =>
                  items.filter((entry) => entry.id !== item.id),
                )
              }
            >
              {item.name} ×
            </button>
          ))}
          <button
            className="button"
            disabled={selected.length < 2}
            onClick={() =>
              navigate(comparisonUrl(selected.map((item) => item.id)))
            }
          >
            {u.compare}
          </button>
        </div>
      </section>
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
                    <label className="experimentCheck">
                      <input
                        type="checkbox"
                        aria-label={`${u.select}: ${job.name}`}
                        checked={selected.some(
                          (item) => item.id === job.job_id,
                        )}
                        disabled={
                          job.status !== "SUCCEEDED" ||
                          !job.result_available ||
                          (selected.length === 3 &&
                            !selected.some((item) => item.id === job.job_id))
                        }
                        onChange={(event) =>
                          setSelected((items) =>
                            event.target.checked
                              ? [...items, { id: job.job_id, name: job.name }]
                              : items.filter((item) => item.id !== job.job_id),
                          )
                        }
                      />
                      {u.select}
                    </label>
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
