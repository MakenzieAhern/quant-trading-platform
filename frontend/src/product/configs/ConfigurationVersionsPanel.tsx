import { useEffect, useState, type FormEvent } from "react";
import { Pagination } from "../../components/Pagination";
import { formatDecimal, formatUtc } from "../../utils/format";
import { Dialog } from "../Dialog";
import { useExperimentCopy } from "../experiments/copy";
import {
  DRAFT_RECOVERY_PREFIX,
  UNREADABLE_DRAFT_PREFIX,
  readBrowserDraftRecoveries,
  readUnreadableDraftCopies,
  type ExperimentDraft,
} from "../experiments/draft";
import { useConfigurationCopy } from "./copy";
import {
  CONFIG_VERSION_PREFIX,
  readConfigurationVersions,
  restoreConfigurationVersion,
  restoreBrowserDraft,
  saveConfigurationVersion,
  type ConfigurationVersion,
} from "./storage";
import "./configs.css";

export function ConfigurationVersionsPanel({
  current,
  disabled = false,
  restoreBlocked = false,
  onRestore,
}: {
  current: Pick<ExperimentDraft, "form" | "step" | "idempotencyKey">;
  disabled?: boolean;
  restoreBlocked?: boolean;
  onRestore: (draft: ExperimentDraft) => void;
}) {
  const c = useConfigurationCopy();
  const fields = useExperimentCopy();
  const [library, setLibrary] = useState(readConfigurationVersions);
  const [name, setName] = useState("");
  const [offset, setOffset] = useState(0);
  const [recoveries, setRecoveries] = useState(readBrowserDraftRecoveries);
  const [recoveryOffset, setRecoveryOffset] = useState(0);
  const [unreadableCopies, setUnreadableCopies] = useState(
    readUnreadableDraftCopies,
  );
  const [selected, setSelected] = useState<
    | ConfigurationVersion
    | (Omit<ConfigurationVersion, "kind"> & { kind: "browser_recovery" })
    | null
  >(null);
  const [notice, setNotice] = useState<"saved" | "restored" | null>(null);
  const [error, setError] = useState<"failed" | "conflict" | "changed" | null>(
    null,
  );
  const pageOffset = Math.min(
    offset,
    Math.max(0, Math.ceil(library.items.length / 20) - 1) * 20,
  );
  const draft = (): ExperimentDraft => ({
    ...current,
    version: 1,
    savedAt: new Date().toISOString(),
  });
  function refresh() {
    setLibrary(readConfigurationVersions());
    setRecoveries(readBrowserDraftRecoveries());
    setUnreadableCopies(readUnreadableDraftCopies());
  }
  useEffect(() => {
    const changed = (event: StorageEvent) => {
      if (
        event.key === null ||
        event.key.startsWith(CONFIG_VERSION_PREFIX) ||
        event.key.startsWith(DRAFT_RECOVERY_PREFIX) ||
        event.key.startsWith(UNREADABLE_DRAFT_PREFIX)
      )
        refresh();
    };
    window.addEventListener("storage", changed);
    return () => window.removeEventListener("storage", changed);
  }, []);
  function save(event: FormEvent) {
    event.preventDefault();
    if (disabled) return;
    setError(null);
    setNotice(null);
    try {
      saveConfigurationVersion(name, draft());
      setName("");
      setOffset(0);
      refresh();
      setNotice("saved");
    } catch {
      setError("failed");
    }
  }
  function restore() {
    if (disabled || restoreBlocked || !selected) return;
    setNotice(null);
    setError(null);
    try {
      const restored = (
        selected.kind === "browser_recovery"
          ? restoreBrowserDraft
          : restoreConfigurationVersion
      )(selected.id, draft(), c.backup, selected.draft);
      onRestore(restored);
      setSelected(null);
      setNotice("restored");
      setOffset(0);
    } catch (reason) {
      setError(
        reason instanceof Error && reason.message === "RECOVERY_DRAFT_CHANGED"
          ? "changed"
          : reason instanceof Error &&
              reason.message === "DRAFT_CHANGED_IN_ANOTHER_TAB"
            ? "conflict"
            : "failed",
      );
    }
    refresh();
  }
  const errorMessage = error && <p role="alert">{c[error]}</p>;
  return (
    <section
      className="configurationVersions experimentPanel"
      aria-label={c.title}
    >
      <h2>{c.title}</h2>
      <p>{c.localOnly}</p>
      <form className="configurationVersionSave" onSubmit={save}>
        <label>
          {c.name}
          <input
            required
            maxLength={80}
            value={name}
            disabled={disabled}
            onChange={(event) => setName(event.target.value)}
          />
        </label>
        <button
          className="button secondary"
          disabled={disabled || !name.trim()}
          type="submit"
        >
          {c.save}
        </button>
      </form>
      <p className="experimentHelp">{c.readonly}</p>
      {notice && <p role="status">{c[notice]}</p>}
      {!selected && errorMessage}
      {library.storageFailed ? (
        <p role="alert">{c.readFailed}</p>
      ) : (
        <>
          {library.unreadable > 0 && (
            <p role="alert">
              {c.corrupt} ({library.unreadable})
            </p>
          )}
          {library.items.length === 0 && library.unreadable === 0 ? (
            <p>{c.empty}</p>
          ) : (
            <>
              <p>
                {c.count}: {library.items.length}
              </p>
              <ul className="configurationVersionList">
                {library.items
                  .slice(pageOffset, pageOffset + 20)
                  .map((entry) => (
                    <li key={entry.id}>
                      <div>
                        <strong>{entry.name}</strong>
                        <span>
                          {entry.kind === "pre_restore_backup"
                            ? c.backupKind
                            : c.savedKind}{" "}
                          · {formatUtc(entry.createdAt)}
                        </span>
                        <span>
                          {entry.draft.form.start_date || "—"} →{" "}
                          {entry.draft.form.end_date || "—"} ·{" "}
                          {formatDecimal(entry.draft.form.initial_cash)} CNY
                        </span>
                      </div>
                      <button
                        type="button"
                        className="button secondary"
                        disabled={disabled}
                        aria-label={`${c.restore}: ${entry.name}`}
                        onClick={() => {
                          setError(null);
                          setSelected(entry);
                        }}
                      >
                        {c.restore}
                      </button>
                    </li>
                  ))}
              </ul>
              <Pagination
                label={c.title}
                offset={pageOffset}
                limit={20}
                total={library.items.length}
                onChange={setOffset}
              />
            </>
          )}
        </>
      )}
      <button type="button" className="button secondary" onClick={refresh}>
        {c.retry}
      </button>
      <details
        className="configurationRecovery"
        onToggle={(event) => {
          if (event.currentTarget.open)
            setRecoveries(readBrowserDraftRecoveries());
        }}
      >
        <summary>{c.recoveries}</summary>
        <p>{c.recoveryHelp}</p>
        {recoveries.storageFailed ? (
          <p role="alert">{c.readFailed}</p>
        ) : (
          <>
            {recoveries.unreadable > 0 && (
              <p role="alert">
                {c.corrupt} ({recoveries.unreadable})
              </p>
            )}
            {recoveries.items.length === 0 && recoveries.unreadable === 0 && (
              <p>{c.recoveryEmpty}</p>
            )}
            <ul className="configurationVersionList">
              {recoveries.items
                .slice(recoveryOffset, recoveryOffset + 20)
                .map((entry) => (
                  <li key={entry.id}>
                    <div>
                      <strong>{entry.draft.form.name || "—"}</strong>
                      <span>
                        {formatUtc(entry.draft.savedAt)} ·{" "}
                        {entry.id.slice(0, 8)}
                      </span>
                      <span>
                        {entry.draft.form.start_date || "—"} →{" "}
                        {entry.draft.form.end_date || "—"} ·{" "}
                        {formatDecimal(entry.draft.form.initial_cash)} CNY
                      </span>
                    </div>
                    <button
                      type="button"
                      className="button secondary"
                      disabled={disabled}
                      aria-label={`${c.recover}: ${entry.draft.form.name} ${entry.id.slice(0, 8)}`}
                      onClick={() => {
                        setError(null);
                        setSelected({
                          schema: 1,
                          id: entry.id,
                          name: entry.draft.form.name || c.recover,
                          createdAt: entry.draft.savedAt,
                          kind: "browser_recovery",
                          draft: entry.draft,
                        });
                      }}
                    >
                      {c.recover}
                    </button>
                  </li>
                ))}
            </ul>
            <Pagination
              label={c.recoveries}
              offset={recoveryOffset}
              limit={20}
              total={recoveries.items.length}
              onChange={setRecoveryOffset}
            />
          </>
        )}
      </details>
      <details
        className="configurationRecovery"
        onToggle={(event) => {
          if (event.currentTarget.open)
            setUnreadableCopies(readUnreadableDraftCopies());
        }}
      >
        <summary>{c.unreadableCopies}</summary>
        <p>{c.unreadableCopyHelp}</p>
        {unreadableCopies.storageFailed ? (
          <p role="alert">{c.readFailed}</p>
        ) : unreadableCopies.items.length === 0 ? (
          <p>{c.unreadableCopyEmpty}</p>
        ) : (
          unreadableCopies.items.map((entry) => (
            <details key={entry.id}>
              <summary>{`${c.unreadableCopy}: ${entry.id}`}</summary>
              <label>
                {c.unreadableRaw}
                <textarea
                  readOnly
                  rows={6}
                  value={entry.raw}
                  style={{ width: "100%" }}
                />
              </label>
            </details>
          ))
        )}
      </details>
      {selected && (
        <Dialog title={c.restoreTitle} onClose={() => setSelected(null)}>
          <div className="configurationVersionPreview">
            <h3>{selected.name}</h3>
            <p>{c.restoreHelp}</p>
            <p>{c.incomplete}</p>
            <dl>
              <dt>{c.created}</dt>
              <dd>{formatUtc(selected.createdAt)}</dd>
              <dt>{fields.name}</dt>
              <dd>{selected.draft.form.name || "—"}</dd>
              <dt>{fields.registered}</dt>
              <dd>{selected.draft.form.strategy_id || "—"}</dd>
              <dt>{fields.dataset}</dt>
              <dd>{selected.draft.form.dataset_id || "—"}</dd>
              <dt>{fields.period}</dt>
              <dd>
                {selected.draft.form.start_date || "—"} →{" "}
                {selected.draft.form.end_date || "—"}
              </dd>
              <dt>{fields.cash}</dt>
              <dd>{formatDecimal(selected.draft.form.initial_cash)} CNY</dd>
              <dt>{fields.universe}</dt>
              <dd>{selected.draft.form.universe}</dd>
              <dt>{fields.rebalance}</dt>
              <dd>{selected.draft.form.strategy.rebalance_sessions}</dd>
              <dt>{fields.holdings}</dt>
              <dd>{selected.draft.form.strategy.maximum_holdings}</dd>
              <dt>{fields.commission}</dt>
              <dd>
                {formatDecimal(selected.draft.form.costs.commission_rate)}
              </dd>
              <dt>{fields.minimum}</dt>
              <dd>
                {formatDecimal(selected.draft.form.costs.minimum_commission)}{" "}
                CNY
              </dd>
              <dt>{fields.drawdown}</dt>
              <dd>{formatDecimal(selected.draft.form.risk.max_drawdown)}</dd>
              <dt>{fields.position}</dt>
              <dd>
                {formatDecimal(selected.draft.form.risk.max_position_weight)}
              </dd>
            </dl>
            <details>
              <summary>{c.exact}</summary>
              <pre>{JSON.stringify(selected, null, 2)}</pre>
            </details>
            {errorMessage}
            <div className="experimentActions">
              <button
                type="button"
                className="button secondary"
                onClick={() => setSelected(null)}
              >
                {c.cancel}
              </button>
              <button
                type="button"
                className="button"
                disabled={disabled || restoreBlocked || library.storageFailed}
                onClick={restore}
              >
                {c.confirm}
              </button>
            </div>
          </div>
        </Dialog>
      )}
    </section>
  );
}
