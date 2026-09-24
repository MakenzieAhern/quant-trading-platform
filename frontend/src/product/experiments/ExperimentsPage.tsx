import { useEffect, useState } from "react";
import { Link } from "../../components/Link";
import { Pagination } from "../../components/Pagination";
import { formatUtc } from "../../utils/format";
import { navigate } from "../../utils/navigation";
import { experimentApi } from "./api";
import { useExperimentCopy } from "./copy";
import { experimentError } from "./errors";
import { comparisonUrl } from "./comparison";
import { useComparisonCopy } from "./comparisonCopy";
import { isActiveExperiment } from "./useExperiment";
import type { Experiment, ExperimentMode, ExperimentStatus, Page } from "./types";
import "./experiments.css";

export const EXPERIMENT_VIEW_KEY = "quant.product.experiment-view.v1";
type Sort = "newest" | "oldest" | "name_asc" | "name_desc";
type View = {
  q: string;
  status: ExperimentStatus | "";
  mode: ExperimentMode | "";
  sort: Sort;
  columns: { mode: boolean; period: boolean; created: boolean };
};
const statuses: ExperimentStatus[] = [
  "QUEUED", "RUNNING", "SUCCEEDED", "FAILED", "CANCELLED", "INTERRUPTED",
];
const defaultView: View = {
  q: "", status: "", mode: "", sort: "newest",
  columns: { mode: true, period: true, created: true },
};
function validView(value: unknown): value is View {
  if (!value || typeof value !== "object") return false;
  const view = value as View;
  return !(
    typeof view.q !== "string" || view.q.length > 80 ||
    !["", ...statuses].includes(view.status) ||
    !["", "synthetic_demo", "historical_exploration"].includes(view.mode) ||
    !["newest", "oldest", "name_asc", "name_desc"].includes(view.sort) ||
    !view.columns ||
    Object.values(view.columns).some((entry) => typeof entry !== "boolean") ||
    !["mode", "period", "created"].every((key) => typeof view.columns[key as keyof View["columns"]] === "boolean")
  );
}
function readSavedView(): View {
  try {
    const current: unknown = window.history.state?.experimentView;
    if (window.location.pathname === "/experiments" && validView(current)) return current;
    const raw = window.localStorage.getItem(EXPERIMENT_VIEW_KEY);
    if (!raw) return defaultView;
    const saved: unknown = JSON.parse(raw);
    return validView(saved) ? saved : defaultView;
  } catch {
    return defaultView;
  }
}
function readOffset(): number {
  const offset: unknown = window.history.state?.experimentOffset;
  return window.location.pathname === "/experiments" &&
    typeof offset === "number" && Number.isSafeInteger(offset) &&
    offset >= 0 && offset % 20 === 0 ? offset : 0;
}

export function ExperimentsPage() {
  const c = useExperimentCopy();
  const u = useComparisonCopy();
  const [selected, setSelected] = useState<{ id: string; name: string; createdAt: string }[]>([]);
  const [offset, setOffset] = useState(readOffset);
  const [view, setView] = useState(readSavedView);
  const [saveStatus, setSaveStatus] = useState<"saved" | "error" | null>(null);
  const [revision, setRevision] = useState(0);
  const queryKey = JSON.stringify([offset, view.q, view.status, view.mode, view.sort]);
  const [jobs, setJobs] = useState<{
    key: string;
    data: Page<Experiment> | null;
    error: unknown;
  }>({ key: queryKey, data: null, error: null });
  if (jobs.key !== queryKey) setJobs({ key: queryKey, data: null, error: null });
  useEffect(() => {
    if (window.location.pathname === "/experiments")
      window.history.replaceState(
        { ...window.history.state, experimentView: view, experimentOffset: offset },
        "",
      );
  }, [view, offset]);
  function updateView(patch: Partial<View>, queryChanged = true) {
    setView((current) => ({ ...current, ...patch }));
    setSaveStatus(null);
    if (queryChanged) setOffset(0);
  }
  function resetView() {
    updateView(defaultView);
    try { window.localStorage.removeItem(EXPERIMENT_VIEW_KEY); }
    catch { setSaveStatus("error"); }
  }
  useEffect(() => {
    const controller = new AbortController();
    let active = true;
    let timer: number | undefined;
    async function load() {
      try {
        const data = await experimentApi.list(controller.signal, 20, offset, view.q, {
          status: view.status || undefined,
          mode: view.mode || undefined,
          sort: view.sort,
        });
        if (!active) return;
        setJobs({ key: queryKey, data, error: null });
        if (data.items.some(isActiveExperiment))
          timer = window.setTimeout(() => void load(), 5000);
      } catch (reason) {
        if (active) setJobs({ key: queryKey, data: null, error: reason });
      }
    }
    void load();
    return () => {
      active = false;
      controller.abort();
      window.clearTimeout(timer);
    };
  }, [queryKey, revision, offset, view.q, view.status, view.mode, view.sort]);
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
      <section className="experimentPanel experimentView" aria-label={c.viewSettings}>
        <div className="experimentViewControls">
          <label>
            {c.searchStudies}
            <input type="search" maxLength={80} value={view.q}
              onChange={(event) => updateView({ q: event.target.value })} />
          </label>
          <label>
            {c.status}
            <select value={view.status}
              onChange={(event) => updateView({ status: event.target.value as View["status"] })}>
              <option value="">{c.allStatuses}</option>
              {statuses.map((status) => <option key={status} value={status}>{c.statuses[status]}</option>)}
            </select>
          </label>
          <label>
            {c.mode}
            <select value={view.mode}
              onChange={(event) => updateView({ mode: event.target.value as View["mode"] })}>
              <option value="">{c.allModes}</option>
              <option value="historical_exploration">{c.historical}</option>
              <option value="synthetic_demo">{c.demo}</option>
            </select>
          </label>
          <label>
            {c.sort}
            <select value={view.sort}
              onChange={(event) => updateView({ sort: event.target.value as Sort })}>
              <option value="newest">{c.newest}</option>
              <option value="oldest">{c.oldest}</option>
              <option value="name_asc">{c.nameAsc}</option>
              <option value="name_desc">{c.nameDesc}</option>
            </select>
          </label>
        </div>
        <div className="experimentViewActions">
          <details>
            <summary>{c.columns}</summary>
            <div className="experimentColumnOptions">
              {(["mode", "period", "created"] as const).map((key) => (
                <label key={key}>
                  <input type="checkbox" checked={view.columns[key]}
                    onChange={(event) => updateView({ columns: { ...view.columns, [key]: event.target.checked } }, false)} />
                  {c[key]}
                </label>
              ))}
            </div>
          </details>
          <button className="button secondary" onClick={() => {
            try {
              window.localStorage.setItem(EXPERIMENT_VIEW_KEY, JSON.stringify(view));
              setSaveStatus("saved");
            } catch { setSaveStatus("error"); }
          }}>{c.saveView}</button>
          <button className="button secondary" onClick={resetView}>{c.clearView}</button>
        </div>
        {saveStatus && <p role={saveStatus === "error" ? "alert" : "status"}>
          {saveStatus === "error" ? c.viewSaveFailed : c.viewSaved}
        </p>}
        {(view.q || view.status || view.mode) && <div className="experimentFilterChips">
          {view.q && <button onClick={() => updateView({ q: "" })}
            aria-label={`${c.removeFilter}: ${c.searchStudies}`}>
            {c.searchStudies}: {view.q} ×
          </button>}
          {view.status && <button onClick={() => updateView({ status: "" })}
            aria-label={`${c.removeFilter}: ${c.status}`}>
            {c.status}: {c.statuses[view.status]} ×
          </button>}
          {view.mode && <button onClick={() => updateView({ mode: "" })}
            aria-label={`${c.removeFilter}: ${c.mode}`}>
            {c.mode}: {view.mode === "synthetic_demo" ? c.demo : c.historical} ×
          </button>}
        </div>}
      </section>
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
              aria-label={`${u.remove} ${item.name} · ${formatUtc(item.createdAt)}`}
              onClick={() =>
                setSelected((items) =>
                  items.filter((entry) => entry.id !== item.id),
                )
              }
            >
              {item.name} · {formatUtc(item.createdAt)} ×
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
      {!jobs.data && jobs.error === null && <p role="status">{c.loading}</p>}
      {jobs.error !== null && (
        <div className="experimentNotice" role="alert">
          <p>{experimentError(jobs.error, c)}</p>
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
              <p>{view.q || view.status || view.mode ? c.noMatches : c.empty}</p>
              {view.q || view.status || view.mode ? (
                <button className="button secondary" onClick={resetView}>{c.clearView}</button>
              ) : <Link href="/research/new">{c.newExperiment}</Link>}
            </div>
          ) : (
            <div className="experimentTableScroll" role="region" tabIndex={0} aria-label={c.listTitle}>
              <p className="experimentHelp">{c.tableScroll}</p>
              <table className="experimentTable">
                <thead><tr>
                  <th scope="col">{u.select}</th>
                  <th scope="col">{c.task}</th>
                  {view.columns.mode && <th scope="col">{c.mode}</th>}
                  {view.columns.period && <th scope="col">{c.period}</th>}
                  {view.columns.created && <th scope="col">{c.created}</th>}
                  <th scope="col">{c.status}</th>
                  <th scope="col">{c.open}</th>
                </tr></thead>
                <tbody>{jobs.data.items.map((job) => (
                  <tr key={job.job_id}>
                    <td><label className="experimentTableSelect">
                      <input type="checkbox" aria-label={`${u.select}: ${job.name} · ${c.statuses[job.status]} · ${formatUtc(job.created_at)}`}
                        checked={selected.some((item) => item.id === job.job_id)}
                        disabled={job.status !== "SUCCEEDED" || !job.result_available ||
                          (selected.length === 3 && !selected.some((item) => item.id === job.job_id))}
                        onChange={(event) => setSelected((items) => event.target.checked
                          ? [...items, { id: job.job_id, name: job.name, createdAt: job.created_at }]
                          : items.filter((item) => item.id !== job.job_id))} />
                    </label></td>
                    <th scope="row"><Link href={`/experiments/${job.job_id}`}
                      aria-label={`${job.name} · ${c.statuses[job.status]} · ${formatUtc(job.created_at)}`}>{job.name}</Link></th>
                    {view.columns.mode && <td>{job.mode === "synthetic_demo" ? c.demo : c.historical}</td>}
                    {view.columns.period && <td>{job.configuration.start_date} → {job.configuration.end_date}</td>}
                    {view.columns.created && <td>{formatUtc(job.created_at)}</td>}
                    <td><span className={`experimentStatus experimentStatus--${job.status.toLowerCase()}`}>
                      {c.statuses[job.status]}
                    </span></td>
                    <td><Link className="button secondary" href={`/experiments/${job.job_id}`}
                      aria-label={`${c.open}: ${job.name} · ${formatUtc(job.created_at)}`}>{c.open}</Link></td>
                  </tr>
                ))}</tbody>
              </table>
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
