import { useEffect, useRef, useState, type Ref } from "react";
import { useTranslation } from "react-i18next";
import { ApiError, requestOutcomeUncertain } from "../../api/client";
import { formatUtc } from "../../utils/format";
import { marketUpdateApi } from "./api";
import { explainUpdateCode, updateError, useUpdateCopy } from "./copy";
import { UpdateRecords } from "./UpdateRecords";
import type { UpdateJob } from "./types";
const activeStatus = (job: UpdateJob) =>
  job.status === "QUEUED" || job.status === "RUNNING";
export function UpdateTaskDetail({
  jobId,
  onOpen,
  onReturn,
  focusRef,
}: {
  jobId: string;
  onOpen: (id: string, shouldFocus: boolean) => void;
  onReturn: () => void;
  focusRef: Ref<HTMLElement>;
}) {
  const c = useUpdateCopy();
  const { i18n } = useTranslation();
  const [revision, setRevision] = useState(0);
  const [job, setJob] = useState<UpdateJob | null>(null);
  const [error, setError] = useState<unknown>(null);
  const [actionError, setActionError] = useState<{
    kind: "cancel" | "retry";
    reason: unknown;
  } | null>(null);
  const [action, setAction] = useState(false);
  const active = useRef(true);
  const locked = useRef(false);
  const focusedCommand = useRef<HTMLButtonElement | null>(null);
  const statusFocus = useRef<HTMLHeadingElement>(null);
  const errorFocus = useRef<HTMLParagraphElement>(null);
  const confirmedCancelError =
    actionError?.kind === "cancel" &&
    requestOutcomeUncertain(actionError.reason) &&
    (job?.cancel_requested || job?.status === "CANCELLED");
  const displayedError =
    error !== null
      ? error
      : job && !confirmedCancelError
        ? (actionError?.reason ?? null)
        : null;
  useEffect(() => {
    active.current = true;
    return () => {
      active.current = false;
    };
  }, []);
  useEffect(() => {
    const controller = new AbortController();
    let alive = true;
    let timer: number | undefined;
    async function load() {
      try {
        const data = await marketUpdateApi.get(jobId, controller.signal);
        if (!alive) return;
        setJob(data);
        setError(null);
        if (activeStatus(data))
          timer = window.setTimeout(() => void load(), 2500);
      } catch (reason) {
        if (alive) {
          setJob(null);
          setError(reason);
        }
      }
    }
    void load();
    return () => {
      alive = false;
      controller.abort();
      window.clearTimeout(timer);
    };
  }, [jobId, revision]);
  useEffect(() => {
    const button = focusedCommand.current;
    if (button && !button.isConnected) {
      if (document.activeElement === document.body)
        (statusFocus.current ?? errorFocus.current)?.focus();
      focusedCommand.current = null;
    }
  }, [job?.status, displayedError]);
  async function command(kind: "cancel" | "retry") {
    if (locked.current || (kind === "cancel" && job?.cancel_requested)) return;
    const trigger = document.activeElement;
    locked.current = true;
    setAction(true);
    setError(null);
    setActionError(null);
    try {
      const result =
        kind === "cancel"
          ? await marketUpdateApi.cancel(jobId)
          : await marketUpdateApi.retry(jobId);
      if (!active.current) return;
      if (kind === "retry")
        onOpen(
          result.job_id,
          trigger instanceof HTMLButtonElement &&
            document.activeElement === trigger,
        );
      else {
        setJob(result);
        setRevision((value) => value + 1);
      }
    } catch (reason) {
      if (active.current) setActionError({ kind, reason });
    } finally {
      if (active.current) {
        locked.current = false;
        setAction(false);
      }
    }
  }
  return (
    <section
      className="updateDetail"
      aria-label={`${c.task}: ${jobId}`}
      tabIndex={-1}
      ref={focusRef}
      onFocusCapture={(event) => {
        if (event.target instanceof HTMLButtonElement)
          focusedCommand.current = event.target;
      }}
      onBlurCapture={() => {
        focusedCommand.current = null;
      }}
    >
      <h3>{c.task}</h3>
      <code>{jobId}</code>
      <button
        className="button secondary"
        type="button"
        onClick={() => {
          setJob(null);
          setError(null);
          setRevision((value) => value + 1);
        }}
      >
        {c.refresh}
      </button>
      {!job && displayedError === null && <p role="status">{c.loading}</p>}
      {displayedError !== null && (
        <p ref={errorFocus} role="alert" tabIndex={-1}>
          {updateError(displayedError, i18n.language)}
        </p>
      )}
      {error !== null &&
        actionError !== null &&
        updateError(error, i18n.language) !==
          updateError(actionError.reason, i18n.language) && (
          <p role="alert">{updateError(actionError.reason, i18n.language)}</p>
        )}
      {displayedError instanceof ApiError &&
        displayedError.code === "MARKET_UPDATE_NOT_FOUND" && (
          <>
            <p>{c.missingTaskHelp}</p>
            <button
              type="button"
              className="button secondary"
              onClick={onReturn}
            >
              {c.backToRequests}
            </button>
          </>
        )}
      {job && (
        <>
          <h4 ref={statusFocus} tabIndex={-1}>
            {c.statuses[job.status]}
          </h4>
          <p>
            {job.configuration.start_date} → {job.configuration.end_date} ·
            Asia/Shanghai
          </p>
          <p>
            {c.created}: {formatUtc(job.created_at)}
          </p>
          <div role="status">
            <p>
              {c.phases[job.phase as keyof typeof c.phases] ??
                c.statuses[job.status]}
            </p>
            <p>
              {c.requests}: {job.completed_requests} /{" "}
              {job.total_requests ?? c.unknown}
            </p>
            {job.total_requests !== null && job.total_requests > 0 && (
              <progress
                aria-label={c.requests}
                value={job.completed_requests}
                max={job.total_requests}
              />
            )}
          </div>
          <p>{c.persisted}</p>
          {job.cancel_requested && activeStatus(job) && (
            <p role="status">{c.cancelPending}</p>
          )}
          {activeStatus(job) && (
            <button
              type="button"
              className="button secondary"
              aria-disabled={action || job.cancel_requested}
              onClick={() => void command("cancel")}
            >
              {action ? c.working : c.cancel}
            </button>
          )}
          {["FAILED", "CANCELLED", "INTERRUPTED"].includes(job.status) && (
            <>
              <p>{c.cancelled}</p>
              <p>{c.retryHelp}</p>
              <button
                type="button"
                className="button secondary"
                disabled={[
                  "SOURCE_ACCESS_DENIED",
                  "RECEIPT_PERSISTENCE_BLOCKED",
                ].includes(job.error_code ?? "")}
                aria-disabled={action}
                onClick={() => void command("retry")}
              >
                {action ? c.working : c.retry}
              </button>
            </>
          )}
          {job.error_code && (
            <div role="alert">
              <p>{explainUpdateCode(job.error_code, i18n.language)}</p>
              <details>
                <summary>{c.diagnostics}</summary>
                <code>{job.error_code}</code>
              </details>
            </div>
          )}
          {job.status === "SUCCEEDED" ? (
            <p>{c.completed}</p>
          ) : (
            <p>{c.notReady}</p>
          )}
          {job.summary && (
            <dl className="updateSummary">
              {[
                [c.cached, job.summary.cached_observations_skipped],
                [c.added, job.summary.new_observations],
                [c.available, job.summary.observations_available],
                [c.gap, job.summary.unresolved_date_count],
              ].map(([label, value]) => (
                <div key={label}>
                  <dt>{label}</dt>
                  <dd>{value ?? "—"}</dd>
                </div>
              ))}
            </dl>
          )}
          <UpdateRecords job={job} revision={revision} />
          <details>
            <summary>{c.technical}</summary>
            <h4>{c.snapshot}</h4>
            <pre>
              {JSON.stringify(
                {
                  master_snapshot: job.master_snapshot,
                  configuration: job.configuration,
                  configuration_sha256: job.configuration_sha256,
                  authority: job.authority,
                  summary: job.summary,
                },
                null,
                2,
              )}
            </pre>
          </details>
        </>
      )}
    </section>
  );
}
