import {
  useEffect,
  useLayoutEffect,
  useRef,
  useState,
  type MouseEvent,
} from "react";
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

type TaskReturn = {
  url: string;
  href: string;
  scrollY: number;
  researchOffset: number;
  updateOffset: number;
};

function readTaskReturn(): TaskReturn | null {
  const value = window.history.state
    ?.taskCenterReturn as Partial<TaskReturn> | null;
  const validOffset = (offset: unknown): offset is number =>
    typeof offset === "number" &&
    Number.isSafeInteger(offset) &&
    offset >= 0 &&
    offset % 20 === 0;
  return window.location.pathname === "/tasks" &&
    value &&
    value.url === window.location.href &&
    typeof value.href === "string" &&
    typeof value.scrollY === "number" &&
    Number.isFinite(value.scrollY) &&
    value.scrollY >= 0 &&
    validOffset(value.researchOffset) &&
    validOffset(value.updateOffset)
    ? (value as TaskReturn)
    : null;
}

export function TaskCenterPage() {
  const c = useProductCopy();
  const e = useExperimentCopy();
  const u = useUpdateCopy();
  const { i18n } = useTranslation();
  const taskReturn = useRef(readTaskReturn());
  const workspace = useRef<HTMLDivElement>(null);
  const [researchOffset, setResearchOffset] = useState(
    () => readTaskReturn()?.researchOffset ?? 0,
  );
  const [updateOffset, setUpdateOffset] = useState(
    () => readTaskReturn()?.updateOffset ?? 0,
  );
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
  useLayoutEffect(() => {
    const saved = taskReturn.current;
    if (!saved || research.loading || updates.loading) return;
    taskReturn.current = null;
    window.history.replaceState(
      { ...window.history.state, taskCenterReturn: null },
      "",
    );
    if (
      document.activeElement !== document.body &&
      document.activeElement !== document.getElementById("main-content")
    )
      return;
    const trigger = Array.from(
      workspace.current?.querySelectorAll<HTMLAnchorElement>(
        ".taskCenterList a",
      ) ?? [],
    ).find((link) => link.getAttribute("href") === saved.href);
    const isResearch = saved.href.startsWith("/experiments/");
    const fallback = isResearch
      ? (research.error ? researchError : researchHeading).current
      : (updates.error ? updateErrorFocus : updateHeading).current;
    if (trigger) {
      trigger.focus({ preventScroll: true });
      window.scrollTo({ top: saved.scrollY, left: 0, behavior: "instant" });
    } else {
      fallback?.focus();
    }
  }, [research.loading, updates.loading, research.error, updates.error]);
  function rememberReturn(event: MouseEvent<HTMLAnchorElement>) {
    if (
      event.defaultPrevented ||
      event.button !== 0 ||
      event.metaKey ||
      event.ctrlKey ||
      event.shiftKey ||
      event.altKey
    )
      return;
    window.history.replaceState(
      {
        ...window.history.state,
        taskCenterReturn: {
          url: window.location.href,
          href: event.currentTarget.getAttribute("href"),
          scrollY: window.scrollY,
          researchOffset,
          updateOffset,
        },
      },
      "",
    );
  }
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
    <div ref={workspace} className="productPage">
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
      <section className="panel experimentPanel" aria-label={c.researchTasks}>
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
                    onClick={rememberReturn}
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
          label={c.researchTasks}
          offset={researchOffset}
          limit={research.data?.limit ?? 20}
          total={research.data?.total ?? null}
          loading={research.loading}
          onChange={setResearchOffset}
        />
      </section>
      <section className="panel experimentPanel" aria-label={c.updateTasks}>
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
                    onClick={rememberReturn}
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
          label={c.updateTasks}
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
