import { useEffect, useRef, useState, type FormEvent } from "react";
import { useTranslation } from "react-i18next";
import { Pagination } from "../../components/Pagination";
import { Link } from "../../components/Link";
import { useApiResource } from "../../hooks/useApiResource";
import { formatUtc } from "../../utils/format";
import { navigate } from "../../utils/navigation";
import { marketUpdateApi } from "./api";
import { explainUpdateCode, updateError, useUpdateCopy } from "./copy";
import {
  earliestUpdateDate,
  readUpdateDraft,
  requestFromDraft,
  saveUpdateDraft,
  validUpdateRequest,
  type UpdateDraft,
} from "./intent";
import { UpdateTaskDetail } from "./UpdateTaskDetail";
import type { UpdateCapabilities } from "./types";
import "./updates.css";

const selectedFromUrl = () =>
  new URLSearchParams(location.search).get("updateJob");
function openUpdateJob(id: string) {
  const url = new URL(location.href);
  url.searchParams.set("updateJob", id);
  navigate(`${url.pathname}${url.search}${url.hash}`);
}
export function MarketUpdatesPanel() {
  const c = useUpdateCopy();
  const [revision, setRevision] = useState(0);
  const [offset, setOffset] = useState(0);
  const [jobId, setJobId] = useState(selectedFromUrl);
  const caps = useApiResource(
    (signal) => marketUpdateApi.capabilities(signal),
    [revision],
  );
  const history = useApiResource(
    (signal) => marketUpdateApi.list(offset, signal),
    [offset, revision, jobId],
  );
  useEffect(() => {
    const changed = () => setJobId(selectedFromUrl());
    window.addEventListener("popstate", changed);
    return () => window.removeEventListener("popstate", changed);
  }, []);
  const refresh = () => setRevision((value) => value + 1);
  return (
    <section className="marketUpdates" aria-label={c.title}>
      <header>
        <h2>{c.title}</h2>
        <p>{c.intro}</p>
      </header>
      <aside className="updateNotice">
        <strong>{c.candidate}</strong>
        <p>{c.authority}</p>
      </aside>
      {caps.loading && <p role="status">{c.loading}</p>}
      {caps.error && <p role="alert">{c.loadFailed}</p>}
      <button type="button" className="button secondary" onClick={refresh}>
        {c.refresh}
      </button>
      {caps.data && (
        <UpdateRequestForm
          capabilities={caps.data}
          onCreated={(id) => {
            openUpdateJob(id);
            refresh();
          }}
        />
      )}
      <section aria-label={c.history}>
        <h3>{c.history}</h3>
        {history.loading && <p role="status">{c.loading}</p>}
        {history.error && <p role="alert">{c.loadFailed}</p>}
        {history.data && (
          <>
            {history.data.total === 0 && <p>{c.empty}</p>}
            <ul className="updateHistory">
              {history.data.items.map((job) => (
                <li key={job.job_id}>
                  <div>
                    <strong>{c.statuses[job.status]}</strong>
                    <span>{job.configuration.security_ids.join(", ")}</span>
                    <span>
                      {job.configuration.start_date} →{" "}
                      {job.configuration.end_date} · {formatUtc(job.created_at)}
                    </span>
                    <code>{job.job_id}</code>
                  </div>
                  <button
                    type="button"
                    className="button secondary"
                    aria-label={`${c.open}: ${job.job_id}`}
                    onClick={() => openUpdateJob(job.job_id)}
                  >
                    {c.open}
                  </button>
                </li>
              ))}
            </ul>
            <Pagination
              offset={offset}
              limit={20}
              total={history.data.total}
              onChange={setOffset}
            />
          </>
        )}
      </section>
      {jobId ? (
        /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(
          jobId,
        ) ? (
          <UpdateTaskDetail key={jobId} jobId={jobId} onOpen={openUpdateJob} />
        ) : (
          <p role="alert">{c.invalidJob}</p>
        )
      ) : (
        <p>{c.selectPrompt}</p>
      )}
    </section>
  );
}

function UpdateRequestForm({
  capabilities: caps,
  onCreated,
}: {
  capabilities: UpdateCapabilities;
  onCreated: (id: string) => void;
}) {
  const c = useUpdateCopy();
  const { i18n } = useTranslation();
  const [draft, setDraft] = useState<UpdateDraft>(
    () =>
      readUpdateDraft() ?? {
        securityText: "",
        start_date: "",
        end_date: "",
        requestKey: crypto.randomUUID(),
      },
  );
  const [accepted, setAccepted] = useState(false);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<unknown>(null);
  const [storageFailed, setStorageFailed] = useState(false);
  const lock = useRef(false);
  const active = useRef(true);
  useEffect(() => {
    active.current = true;
    return () => {
      active.current = false;
    };
  }, []);
  const archive = caps.archive.find(
    (dataset) => dataset.mode === "historical_exploration",
  );
  const unavailable =
    !caps.available || !archive?.available || caps.worker_running === false;
  function change(next: UpdateDraft) {
    const updated = {
      ...next,
      requestKey:
        JSON.stringify(requestFromDraft(next)) ===
        JSON.stringify(requestFromDraft(draft))
          ? draft.requestKey
          : next.requestKey,
    };
    setDraft(updated);
    setAccepted(false);
    setError(null);
    try {
      saveUpdateDraft(updated);
      setStorageFailed(false);
    } catch {
      setStorageFailed(true);
    }
  }
  async function submit(event: FormEvent) {
    event.preventDefault();
    if (lock.current || unavailable) return;
    const config = requestFromDraft(draft);
    if (!accepted || !validUpdateRequest(config, caps)) {
      setError("validation");
      return;
    }
    try {
      saveUpdateDraft(draft);
      setStorageFailed(false);
    } catch {
      setStorageFailed(true);
      return;
    }
    lock.current = true;
    setPending(true);
    setError(null);
    const originatingUrl = `${location.pathname}${location.search}`;
    try {
      const job = await marketUpdateApi.create(config, draft.requestKey);
      // Leave the persisted identity intact: a lost response or reopened form must
      // reconcile to this same server job, never silently create another request.
      if (
        active.current &&
        `${location.pathname}${location.search}` === originatingUrl
      )
        onCreated(job.job_id);
    } catch (reason) {
      if (active.current) setError(reason);
    } finally {
      if (active.current) {
        lock.current = false;
        setPending(false);
      }
    }
  }
  return (
    <div className="updateRequest">
      <p>
        {c.bound}: {earliestUpdateDate(caps) ?? "—"} →{" "}
        {caps.latest_publishable_date} ({caps.publication_timezone},{" "}
        {caps.publication_time})
      </p>
      <p>{c.dateHelp}</p>
      {unavailable && (
        <p role="alert">
          {c.unavailable}:{" "}
          {caps.reason_code
            ? explainUpdateCode(caps.reason_code, i18n.language)
            : !archive?.available
              ? explainUpdateCode("DATASET_NOT_MOUNTED", i18n.language)
              : explainUpdateCode("UPDATE_WORKER_UNAVAILABLE", i18n.language)}
        </p>
      )}
      <form onSubmit={(event) => void submit(event)}>
        <fieldset disabled={pending}>
          <label>
            {c.securities}
            <textarea
              rows={3}
              maxLength={500}
              required
              value={draft.securityText}
              onChange={(event) =>
                change({
                  ...draft,
                  securityText: event.target.value,
                  requestKey: crypto.randomUUID(),
                })
              }
            />
          </label>
          <p>
            {c.securitiesHelp} <Link href="/markets">{c.selectSecurity}</Link>
          </p>
          <div className="updateDateFields">
            <label>
              {c.start}
              <input
                type="date"
                required
                min={earliestUpdateDate(caps) ?? undefined}
                max={draft.end_date || caps.latest_publishable_date}
                value={draft.start_date}
                onInput={(event) =>
                  change({
                    ...draft,
                    start_date: event.currentTarget.value,
                    requestKey: crypto.randomUUID(),
                  })
                }
              />
            </label>
            <label>
              {c.end}
              <input
                type="date"
                required
                min={
                  draft.start_date || (earliestUpdateDate(caps) ?? undefined)
                }
                max={caps.latest_publishable_date}
                value={draft.end_date}
                onInput={(event) =>
                  change({
                    ...draft,
                    end_date: event.currentTarget.value,
                    requestKey: crypto.randomUUID(),
                  })
                }
              />
            </label>
          </div>
          <label className="updateCheck">
            <input
              type="checkbox"
              checked={accepted}
              onChange={(event) => setAccepted(event.target.checked)}
            />
            {c.confirm}
          </label>
          <button
            className="button"
            type="submit"
            disabled={pending || unavailable || !accepted}
          >
            {pending ? c.submitting : c.submit}
          </button>
        </fieldset>
        {error !== null && (
          <p role="alert">
            {error === "validation"
              ? c.validation
              : updateError(error, i18n.language)}
          </p>
        )}
        {storageFailed ? (
          <p role="alert">{c.storage}</p>
        ) : (
          readUpdateDraft()?.requestKey === draft.requestKey && <p>{c.saved}</p>
        )}
      </form>
      <details>
        <summary>{c.source}</summary>
        <p>
          {caps.provider} · SDK {caps.sdk_version}
        </p>
        <p>{c.termsHelp}</p>
        <SourceLink url={caps.terms.source_url} label={c.provider} />
        {" · "}
        <SourceLink url={caps.terms.terms_url} label={c.terms} />
        <p>
          {c.received}: {formatUtc(caps.terms.terms_retrieved_at_utc)}
        </p>
        <pre>{JSON.stringify(caps.terms, null, 2)}</pre>
      </details>
      <details>
        <summary>{c.limits}</summary>
        <dl>
          {[
            [c.limitSecurities, caps.max_securities],
            [c.limitDays, caps.max_days],
            [c.chunks, caps.request_chunk_days],
            [c.attempts, caps.maximum_attempts_per_request],
            [c.timeout, caps.request_timeout_seconds],
            [c.interval, caps.minimum_request_interval_seconds],
            [c.jobTimeout, caps.job_timeout_seconds],
          ].map(([label, value]) => (
            <div key={label}>
              <dt>{label}</dt>
              <dd>{value}</dd>
            </div>
          ))}
        </dl>
      </details>
    </div>
  );
}
function SourceLink({ url, label }: { url: string; label: string }) {
  let safe = false;
  try {
    safe = new URL(url).protocol === "https:";
  } catch {
    /* Invalid external references stay text, never executable URLs. */
  }
  if (safe)
    return (
      <a href={url} target="_blank" rel="noreferrer">
        {label}
      </a>
    );
  return (
    <span>
      {label}: {url}
    </span>
  );
}
