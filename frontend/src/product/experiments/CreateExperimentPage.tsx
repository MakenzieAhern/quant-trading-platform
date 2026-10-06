import {
  useCallback,
  useEffect,
  useRef,
  useState,
  type FormEvent,
} from "react";
import { useTranslation } from "react-i18next";
import { ApiError } from "../../api/client";
import { Link } from "../../components/Link";
import { useApiResource } from "../../hooks/useApiResource";
import {
  comparePositiveDecimals,
  formatDecimal,
  isPositiveDecimal,
} from "../../utils/format";
import {
  navigate,
  replaceUrl,
  useNavigationGuard,
} from "../../utils/navigation";
import { usePageDataContext } from "../dataContext";
import { Dialog } from "../Dialog";
import { ProductError } from "../ProductPages";
import { ConfigurationVersionsPanel } from "../configs";
import { useConfigurationCopy } from "../configs/copy";
import { startNewExperimentDraft } from "../configs/storage";
import { experimentApi } from "./api";
import { useExperimentCopy, type ExperimentCopy } from "./copy";
import {
  EXPERIMENT_DRAFT_KEY,
  beginExperimentDraftPage,
  clearCompletedExperimentDraft,
  parseExperimentDraft,
  saveExperimentDraft,
} from "./draft";
import { experimentError } from "./errors";
import { explainExperimentCode } from "./codes";
import type {
  Capabilities,
  DatasetCapability,
  ExperimentConfiguration,
} from "./types";
import "./experiments.css";

function executable(dataset: DatasetCapability | undefined) {
  return !!dataset?.available && dataset.execution_available !== false;
}

function finishNewIntent() {
  const url = new URL(window.location.href);
  url.searchParams.delete("new");
  replaceUrl(url.pathname + url.search);
}

function existingDraft() {
  try {
    const raw = window.localStorage.getItem(EXPERIMENT_DRAFT_KEY);
    let draft = null;
    try {
      draft = raw === null ? null : parseExperimentDraft(JSON.parse(raw));
    } catch {
      // A malformed value remains available as exact text for recovery.
    }
    return { draft, raw, unreadable: raw !== null && !draft };
  } catch {
    return { draft: null, raw: null, unreadable: true };
  }
}

export function CreateExperimentPage() {
  const c = useExperimentCopy();
  const versions = useConfigurationCopy();
  const newIntent =
    new URLSearchParams(window.location.search).get("new") === "1";
  const [choice, setChoice] = useState<"pending" | "resume" | "started">(
    "pending",
  );
  const original =
    choice === "pending"
      ? existingDraft()
      : { draft: null, raw: null, unreadable: false };
  const [choiceError, setChoiceError] = useState<"failed" | "conflict" | null>(
    null,
  );
  const [revision, setRevision] = useState(0);
  const capabilities = useApiResource(
    (signal) => experimentApi.capabilities(signal),
    [revision],
  );
  useEffect(() => {
    if (
      newIntent &&
      capabilities.data &&
      !original.draft &&
      !original.unreadable
    ) {
      finishNewIntent();
    }
  }, [newIntent, capabilities.data, original.draft, original.unreadable]);
  return (
    <div className="experimentWorkspace">
      <header className="experimentHeader">
        <p className="experimentEyebrow">{c.steps[0]}</p>
        <h1>{c.title}</h1>
        <p>{c.intro}</p>
      </header>
      {capabilities.loading && <p role="status">{c.loading}</p>}
      {capabilities.error && (
        <ProductError
          error={capabilities.error}
          retry={() => setRevision((value) => value + 1)}
        />
      )}
      {choice === "pending" &&
        original.unreadable &&
        (original.raw === null ? (
          <p role="alert">{versions.readFailed}</p>
        ) : (
          <section
            className="experimentPanel"
            aria-labelledby="unreadable-draft-title"
          >
            <h2 id="unreadable-draft-title">{c.unreadableDraftTitle}</h2>
            <p>{c.unreadableDraftHint}</p>
            <details>
              <summary>{c.unreadableDraftText}</summary>
              <textarea
                className="experimentUnreadableDraft"
                aria-label={c.unreadableDraftText}
                readOnly
                rows={5}
                value={original.raw}
              />
            </details>
            {choiceError && <p role="alert">{versions[choiceError]}</p>}
            <button
              className="button"
              disabled={!capabilities.data?.strategies.length}
              onClick={() => {
                try {
                  saveExperimentDraft(
                    initialForm(capabilities.data!, c.defaultName),
                    0,
                    crypto.randomUUID(),
                    {
                      expectedRaw: original.raw,
                      replaceUnreadable: true,
                      newIntent: true,
                    },
                  );
                  finishNewIntent();
                  setChoice("started");
                } catch (reason) {
                  setChoiceError(
                    reason instanceof Error &&
                      reason.message === "DRAFT_CHANGED_IN_ANOTHER_TAB"
                      ? "conflict"
                      : "failed",
                  );
                }
              }}
            >
              {c.unreadableDraftStart}
            </button>
          </section>
        ))}
      {capabilities.data &&
        (capabilities.data.strategies.length ? (
          choice === "pending" && original.unreadable ? null : newIntent &&
            choice === "pending" &&
            original.draft ? (
            <section
              className="experimentPanel"
              aria-labelledby="new-draft-title"
            >
              <h2 id="new-draft-title">{c.newDraftTitle}</h2>
              <p>{c.newDraftHint}</p>
              {choiceError && <p role="alert">{versions[choiceError]}</p>}
              <div className="experimentActions">
                <button
                  className="button secondary"
                  onClick={() => {
                    finishNewIntent();
                    setChoice("resume");
                  }}
                >
                  {c.newDraftResume}
                </button>
                <button
                  className="button"
                  onClick={() => {
                    try {
                      startNewExperimentDraft(
                        original.draft!,
                        initialForm(capabilities.data!, c.defaultName),
                        versions.backup,
                      );
                      finishNewIntent();
                      setChoice("started");
                    } catch (reason) {
                      setChoiceError(
                        reason instanceof Error &&
                          reason.message === "DRAFT_CHANGED_IN_ANOTHER_TAB"
                          ? "conflict"
                          : "failed",
                      );
                    }
                  }}
                >
                  {c.newDraftStart}
                </button>
              </div>
            </section>
          ) : (
            <ExperimentWizard
              capabilities={capabilities.data}
              showRestored={choice !== "started"}
              focusOnMount={choice !== "pending"}
            />
          )
        ) : (
          <p role="alert">{c.noStrategies}</p>
        ))}
    </div>
  );
}

function initialForm(
  capabilities: Capabilities,
  name: string,
): ExperimentConfiguration {
  const dataset =
    capabilities.datasets.find(
      (item) => executable(item) && item.mode === "historical_exploration",
    ) ??
    capabilities.datasets.find(executable) ??
    capabilities.datasets[0];
  const requested = new URLSearchParams(window.location.search).get("strategy");
  const strategy =
    capabilities.strategies.find((item) => item.strategy_id === requested) ??
    capabilities.strategies[0];
  return {
    name,
    dataset_id: dataset?.dataset_id ?? "",
    strategy_id: strategy.strategy_id,
    initial_cash: capabilities.defaults.initial_cash,
    start_date: dataset?.default_start ?? "",
    end_date: dataset?.default_end ?? "",
    universe: "ALL",
    strategy: {
      rebalance_sessions: strategy.parameters.rebalance_sessions.default,
      maximum_holdings: strategy.parameters.maximum_holdings.default,
    },
    costs: {
      commission_rate: capabilities.defaults.commission_rate,
      minimum_commission: capabilities.defaults.minimum_commission,
    },
    risk: {
      max_drawdown: capabilities.defaults.max_drawdown,
      max_position_weight: "0.1",
    },
  };
}

type ConfigurationField = keyof ExperimentCopy["fieldErrors"];

function validTradingDate(value: string) {
  const date = new Date(`${value}T00:00:00Z`);
  return (
    /^\d{4}-\d{2}-\d{2}$/.test(value) &&
    !Number.isNaN(date.getTime()) &&
    date.toISOString().slice(0, 10) === value
  );
}

function invalidConfigurationField(
  form: ExperimentConfiguration,
  capabilities: Capabilities,
  step: number,
): ConfigurationField | null {
  const strategy = capabilities.strategies.find(
    (item) => item.strategy_id === form.strategy_id,
  );
  if (!strategy) return "strategy";
  if (step === 0) return null;
  const dataset = capabilities.datasets.find(
    (item) => item.dataset_id === form.dataset_id,
  );
  if (!dataset || !executable(dataset)) return "dataset";
  if (!form.name.trim() || form.name.length > 120) return "name";
  if (
    !isPositiveDecimal(form.initial_cash) ||
    comparePositiveDecimals(form.initial_cash, "1000000000000") === 1
  )
    return "cash";
  if (
    !validTradingDate(form.start_date) ||
    form.start_date < dataset.coverage_start ||
    form.start_date > dataset.coverage_end
  )
    return "start";
  if (
    !validTradingDate(form.end_date) ||
    form.end_date < form.start_date ||
    form.end_date > dataset.coverage_end
  )
    return "end";
  if (!dataset.universes.includes(form.universe)) return "universe";
  for (const key of ["rebalance_sessions", "maximum_holdings"] as const) {
    const value = form.strategy[key],
      range = strategy.parameters[key];
    if (!Number.isSafeInteger(value) || value < range.min || value > range.max)
      return key === "rebalance_sessions" ? "rebalance" : "holdings";
  }
  if (step === 1) return null;
  for (const [field, value, max] of [
    ["commission", form.costs.commission_rate, "0.01"],
    ["minimum", form.costs.minimum_commission, "1000"],
  ] as const) {
    const comparison = comparePositiveDecimals(value, max);
    if (comparison === null || comparison === 1) return field;
  }
  const magnitude = form.risk.max_drawdown.replace(/^-/, "");
  if (
    !/^-?0(?:\.\d+)?$|^-1(?:\.0+)?$/.test(form.risk.max_drawdown) ||
    comparePositiveDecimals(magnitude, "1") === 1 ||
    (isPositiveDecimal(form.risk.max_drawdown) &&
      form.risk.max_drawdown !== "0")
  )
    return "drawdown";
  return isPositiveDecimal(form.risk.max_position_weight) &&
    comparePositiveDecimals(form.risk.max_position_weight, "1") !== 1
    ? null
    : "position";
}

function focusInvalidField(form: HTMLFormElement | null) {
  const field = form?.querySelector<HTMLElement>('[aria-invalid="true"]');
  const details = field?.closest("details");
  if (details) details.open = true;
  field?.focus();
}

function ExperimentWizard({
  capabilities,
  showRestored,
  focusOnMount,
}: {
  capabilities: Capabilities;
  showRestored: boolean;
  focusOnMount: boolean;
}) {
  const c = useExperimentCopy();
  const { i18n } = useTranslation();
  const [atMount] = useState(() => {
    beginExperimentDraftPage();
    return existingDraft();
  });
  const restored = atMount.draft;
  const expectedRaw = useRef(atMount.raw);
  const [form, setForm] = useState(
    () => restored?.form ?? initialForm(capabilities, c.defaultName),
  );
  const [step, setStep] = useState(restored?.step ?? 0);
  const previousStep = useRef(step);
  const [requestKey, setRequestKey] = useState(
    () => restored?.idempotencyKey ?? crypto.randomUUID(),
  );
  const [saved, setSaved] = useState(Boolean(restored));
  const savedRef = useRef(Boolean(restored));
  const [storageError, setStorageError] = useState(false);
  const [draftConflict, setDraftConflict] = useState(false);
  const draftConflictRef = useRef(false);
  const [exitOpen, setExitOpen] = useState(false);
  const [error, setError] = useState<unknown>(null);
  const [pending, setPending] = useState(false);
  const [acknowledged, setAcknowledged] = useState(false);
  const locked = useRef(false);
  const active = useRef(true);
  const heading = useRef<HTMLHeadingElement>(null);
  const formElement = useRef<HTMLFormElement>(null);
  const errorElement = useRef<HTMLDivElement>(null);
  const invalidField =
    error === "validation"
      ? invalidConfigurationField(form, capabilities, 3)
      : null;
  const dataset = capabilities.datasets.find(
    (item) => item.dataset_id === form.dataset_id,
  );
  const fieldAccessibility = (field: ConfigurationField) => ({
    "aria-invalid": invalidField === field || undefined,
    "aria-describedby":
      [
        invalidField === field ? "experiment-validation-error" : null,
        field === "dataset" ? "experiment-dataset-version" : null,
        field === "dataset" && dataset?.current_dataset_quality
          ? "experiment-dataset-quality"
          : null,
      ]
        .filter(Boolean)
        .join(" ") || undefined,
  });
  const strategy = capabilities.strategies.find(
    (item) => item.strategy_id === form.strategy_id,
  );
  const chinese = i18n.language.startsWith("zh");
  usePageDataContext(
    dataset?.mode ?? null,
    form.end_date || dataset?.coverage_end || null,
  );
  const nameOfStrategy = strategy
    ? chinese
      ? strategy.name_zh
      : strategy.name_en
    : form.strategy_id;
  useNavigationGuard(
    () => savedRef.current || window.confirm(c.unsavedLeaveConfirm),
  );

  const save = useCallback(() => {
    try {
      const raw = saveExperimentDraft(form, step, requestKey, {
        expectedRaw: expectedRaw.current,
        recoveryOnly: draftConflictRef.current,
      });
      if (draftConflictRef.current) return false;
      expectedRaw.current = raw;
      setStorageError(false);
      return true;
    } catch (reason) {
      savedRef.current = false;
      setSaved(false);
      if (
        reason instanceof Error &&
        reason.message === "DRAFT_CHANGED_IN_ANOTHER_TAB"
      ) {
        draftConflictRef.current = true;
        setDraftConflict(true);
      } else setStorageError(true);
      return false;
    }
  }, [form, step, requestKey]);

  useEffect(() => {
    active.current = true;
    return () => {
      active.current = false;
    };
  }, []);
  useEffect(() => {
    if (focusOnMount) heading.current?.focus();
  }, [focusOnMount]);
  useEffect(() => {
    if (previousStep.current === step) return;
    previousStep.current = step;
    heading.current?.focus();
  }, [step]);
  useEffect(() => {
    if (!error) return;
    if (formElement.current?.querySelector('[aria-invalid="true"]'))
      focusInvalidField(formElement.current);
    else errorElement.current?.focus();
  }, [error, step]);
  useEffect(() => {
    const changed = (event: StorageEvent) => {
      if (event.key === EXPERIMENT_DRAFT_KEY) {
        try {
          if (
            window.localStorage.getItem(EXPERIMENT_DRAFT_KEY) ===
            expectedRaw.current
          )
            return;
        } catch {
          // Fail closed when the shared draft cannot be checked.
        }
        draftConflictRef.current = true;
        setDraftConflict(true);
        savedRef.current = false;
        setSaved(false);
      }
    };
    window.addEventListener("storage", changed);
    return () => window.removeEventListener("storage", changed);
  }, []);
  useEffect(() => {
    let cancelled = false;
    queueMicrotask(() => {
      if (!cancelled) save();
    });
    const unload = (event: BeforeUnloadEvent) => {
      let recovered = false;
      let sharedUnchanged = false;
      try {
        saveExperimentDraft(form, step, requestKey, { recoveryOnly: true });
        recovered = true;
        sharedUnchanged =
          window.localStorage.getItem(EXPERIMENT_DRAFT_KEY) ===
          expectedRaw.current;
      } catch {
        // A failed page recovery must not be described as saved.
      }
      if (!savedRef.current || !recovered || !sharedUnchanged) {
        event.preventDefault();
        event.returnValue = "";
      }
    };
    window.addEventListener("beforeunload", unload);
    return () => {
      cancelled = true;
      window.removeEventListener("beforeunload", unload);
    };
  }, [save, form, step, requestKey]);

  function update(next: ExperimentConfiguration) {
    setForm(next);
    setRequestKey(crypto.randomUUID());
    setError(null);
    setSaved(false);
    savedRef.current = false;
    setAcknowledged(false);
  }
  function persist() {
    if (save()) {
      setSaved(true);
      savedRef.current = true;
      return true;
    }
    return false;
  }
  function move(next: number) {
    const invalid = invalidConfigurationField(form, capabilities, step);
    if (next > step && invalid) {
      rejectConfiguration(invalid);
      return;
    }
    setError(null);
    setStep(next);
  }
  function rejectConfiguration(field: ConfigurationField) {
    setStep(
      field === "strategy"
        ? 0
        : ["commission", "minimum", "drawdown", "position"].includes(field)
          ? 2
          : 1,
    );
    if (error === "validation") focusInvalidField(formElement.current);
    setError("validation");
  }
  async function submit(event: FormEvent) {
    event.preventDefault();
    if (step < 3) {
      move(step + 1);
      return;
    }
    if (locked.current) return;
    const invalid = invalidConfigurationField(form, capabilities, 3);
    if (invalid) {
      rejectConfiguration(invalid);
      return;
    }
    if (!acknowledged) {
      setError("validation");
      return;
    }
    setError(null);
    if (!persist()) return;
    locked.current = true;
    setPending(true);
    try {
      const job = await experimentApi.create(form, requestKey);
      clearCompletedExperimentDraft(form, requestKey);
      if (active.current && window.location.pathname === "/research/new")
        navigate(`/experiments/${job.job_id}`);
    } catch (reason) {
      if (active.current) setError(reason);
    } finally {
      locked.current = false;
      if (active.current) setPending(false);
    }
  }

  const universeName = (universe: string) =>
    universe === "ALL" ? c.all : universe === "SSE" ? c.sse : c.szse;
  return (
    <>
      {showRestored && restored && (
        <p className="experimentRestored" role="status">
          {c.restored}
        </p>
      )}
      <ol className="experimentSteps" aria-label={c.title}>
        {c.steps.map((label, index) => (
          <li key={label} aria-current={step === index ? "step" : undefined}>
            <span>{index + 1}</span>
            {label}
          </li>
        ))}
      </ol>
      <div className="experimentWizardLayout">
        <form
          ref={formElement}
          noValidate
          className="experimentPanel experimentForm"
          onSubmit={(event) => void submit(event)}
        >
          <h2 ref={heading} tabIndex={-1}>
            {c.steps[step]}
          </h2>
          {(step === 1 || step === 3) && dataset?.current_dataset_quality && (
            <p
              id="experiment-dataset-quality"
              className="experimentNotice"
              role="note"
            >
              {explainExperimentCode(
                dataset.current_dataset_quality,
                i18n.language,
              )}
            </p>
          )}
          <fieldset disabled={pending}>
            {step === 0 && (
              <div className="experimentStrategyChoices">
                {capabilities.strategies.map((entry) => (
                  <label
                    key={entry.strategy_id}
                    className={`experimentChoice ${entry.strategy_id === form.strategy_id ? "isSelected" : ""}`}
                  >
                    <input
                      {...fieldAccessibility("strategy")}
                      type="radio"
                      name="strategy"
                      value={entry.strategy_id}
                      checked={entry.strategy_id === form.strategy_id}
                      onChange={() =>
                        update({
                          ...form,
                          strategy_id: entry.strategy_id,
                          strategy: {
                            rebalance_sessions:
                              entry.parameters.rebalance_sessions.default,
                            maximum_holdings:
                              entry.parameters.maximum_holdings.default,
                          },
                        })
                      }
                    />
                    <span>
                      <strong>{chinese ? entry.name_zh : entry.name_en}</strong>
                      <span>
                        {chinese ? entry.description_zh : entry.description_en}
                      </span>
                      <small>
                        {c.registered} · v{entry.version}
                      </small>
                    </span>
                  </label>
                ))}
              </div>
            )}
            {step === 1 && (
              <>
                <label>
                  {c.name}
                  <input
                    {...fieldAccessibility("name")}
                    required
                    maxLength={120}
                    value={form.name}
                    onChange={(event) =>
                      update({ ...form, name: event.target.value })
                    }
                  />
                </label>
                <label>
                  {c.dataset}
                  <select
                    {...fieldAccessibility("dataset")}
                    value={form.dataset_id}
                    onChange={(event) => {
                      const chosen = capabilities.datasets.find(
                        (item) => item.dataset_id === event.target.value,
                      );
                      if (chosen)
                        update({
                          ...form,
                          dataset_id: chosen.dataset_id,
                          start_date: chosen.default_start,
                          end_date: chosen.default_end,
                          universe: chosen.universes.includes(form.universe)
                            ? form.universe
                            : (chosen
                                .universes[0] as ExperimentConfiguration["universe"]),
                        });
                    }}
                  >
                    {capabilities.datasets.map((entry) => (
                      <option
                        key={entry.dataset_id}
                        value={entry.dataset_id}
                        disabled={!executable(entry)}
                      >
                        {entry.mode === "synthetic_demo"
                          ? c.demo
                          : c.historical}
                        {` · ${entry.dataset_id}`}
                        {!executable(entry) ? ` · ${c.unavailable}` : ""}
                      </option>
                    ))}
                  </select>
                </label>
                <p
                  id="experiment-dataset-version"
                  className="experimentTechnical"
                >
                  {c.dataset}: {form.dataset_id}
                </p>
                {dataset && (
                  <p className="experimentHelp">
                    {c.coverage}: {dataset.coverage_start} —{" "}
                    {dataset.coverage_end} · {dataset.security_count}{" "}
                    {c.securities}
                  </p>
                )}
                {!executable(dataset) && (
                  <p role="alert">
                    {dataset?.execution_reason_code
                      ? explainExperimentCode(
                          dataset.execution_reason_code,
                          i18n.language,
                        )
                      : c.dataUnavailable}{" "}
                    <Link href="/data">{c.dataset}</Link>
                  </p>
                )}
                <label>
                  {c.cash}
                  <input
                    {...fieldAccessibility("cash")}
                    required
                    inputMode="decimal"
                    value={form.initial_cash}
                    onChange={(event) =>
                      update({ ...form, initial_cash: event.target.value })
                    }
                  />
                </label>
                <div className="experimentFields">
                  <label>
                    {c.start}
                    <input
                      {...fieldAccessibility("start")}
                      type="date"
                      required
                      min={dataset?.coverage_start}
                      max={form.end_date || dataset?.coverage_end}
                      value={form.start_date}
                      onInput={(event) =>
                        update({
                          ...form,
                          start_date: event.currentTarget.value,
                        })
                      }
                    />
                  </label>
                  <label>
                    {c.end}
                    <input
                      {...fieldAccessibility("end")}
                      type="date"
                      required
                      min={form.start_date || dataset?.coverage_start}
                      max={dataset?.coverage_end}
                      value={form.end_date}
                      onInput={(event) =>
                        update({ ...form, end_date: event.currentTarget.value })
                      }
                    />
                  </label>
                </div>
                <p className="experimentHelp">{c.datesHint}</p>
                <label>
                  {c.universe}
                  <select
                    {...fieldAccessibility("universe")}
                    value={form.universe}
                    onChange={(event) =>
                      update({
                        ...form,
                        universe: event.target
                          .value as ExperimentConfiguration["universe"],
                      })
                    }
                  >
                    {dataset?.universes.map((value) => (
                      <option key={value} value={value}>
                        {universeName(value)}
                      </option>
                    ))}
                  </select>
                </label>
                <details>
                  <summary>{c.advanced}</summary>
                  <p className="experimentHelp">{c.fixedStrategy}</p>
                  <div className="experimentFields">
                    <label>
                      {c.rebalance}
                      <input
                        {...fieldAccessibility("rebalance")}
                        type="number"
                        required
                        min={strategy?.parameters.rebalance_sessions.min}
                        max={strategy?.parameters.rebalance_sessions.max}
                        value={form.strategy.rebalance_sessions || ""}
                        onChange={(event) =>
                          update({
                            ...form,
                            strategy: {
                              ...form.strategy,
                              rebalance_sessions: Number(event.target.value),
                            },
                          })
                        }
                      />
                    </label>
                    <label>
                      {c.holdings}
                      <input
                        {...fieldAccessibility("holdings")}
                        type="number"
                        required
                        min={strategy?.parameters.maximum_holdings.min}
                        max={strategy?.parameters.maximum_holdings.max}
                        value={form.strategy.maximum_holdings || ""}
                        onChange={(event) =>
                          update({
                            ...form,
                            strategy: {
                              ...form.strategy,
                              maximum_holdings: Number(event.target.value),
                            },
                          })
                        }
                      />
                    </label>
                  </div>
                </details>
              </>
            )}
            {step === 2 && (
              <>
                <label>
                  {c.commission}
                  <input
                    {...fieldAccessibility("commission")}
                    inputMode="decimal"
                    required
                    value={form.costs.commission_rate}
                    onChange={(event) =>
                      update({
                        ...form,
                        costs: {
                          ...form.costs,
                          commission_rate: event.target.value,
                        },
                      })
                    }
                  />
                </label>
                <p className="experimentHelp">{c.commissionHint}</p>
                <label>
                  {c.minimum}
                  <input
                    {...fieldAccessibility("minimum")}
                    inputMode="decimal"
                    required
                    value={form.costs.minimum_commission}
                    onChange={(event) =>
                      update({
                        ...form,
                        costs: {
                          ...form.costs,
                          minimum_commission: event.target.value,
                        },
                      })
                    }
                  />
                </label>
                <label>
                  {c.drawdown}
                  <input
                    {...fieldAccessibility("drawdown")}
                    inputMode="decimal"
                    required
                    value={form.risk.max_drawdown}
                    onChange={(event) =>
                      update({
                        ...form,
                        risk: {
                          ...form.risk,
                          max_drawdown: event.target.value,
                        },
                      })
                    }
                  />
                </label>
                <p className="experimentHelp">{c.drawdownHint}</p>
                <label>
                  {c.position}
                  <input
                    {...fieldAccessibility("position")}
                    inputMode="decimal"
                    required
                    value={form.risk.max_position_weight}
                    onChange={(event) =>
                      update({
                        ...form,
                        risk: {
                          ...form.risk,
                          max_position_weight: event.target.value,
                        },
                      })
                    }
                  />
                </label>
                <p className="experimentHelp">{c.positionHint}</p>
              </>
            )}
            {step === 3 && (
              <>
                <p>{c.submitInfo}</p>
                <div className="experimentNotice">
                  <strong>
                    {dataset?.mode === "synthetic_demo" ? c.demo : c.historical}
                  </strong>
                  <p>
                    {dataset?.mode === "synthetic_demo"
                      ? c.warningDemo
                      : c.warningHistorical}
                  </p>
                  <p>{c.noGuarantee}</p>
                </div>
                <label className="experimentCheck">
                  <input
                    type="checkbox"
                    checked={acknowledged}
                    onChange={(event) => setAcknowledged(event.target.checked)}
                  />
                  {c.acknowledge}
                </label>
              </>
            )}
          </fieldset>
          {Boolean(error) && (
            <div
              ref={errorElement}
              id="experiment-validation-error"
              className="experimentError"
              role="alert"
              tabIndex={-1}
            >
              {error === "validation"
                ? c.validation
                : experimentError(error, c)}
              {error !== "validation" &&
                (!(error instanceof ApiError) ||
                  error.status === 408 ||
                  error.status >= 500) && (
                  <p>
                    {c.uncertainSubmission}{" "}
                    <Link href="/tasks">{c.checkTaskCenter}</Link>
                  </p>
                )}
              {invalidField && (
                <p>
                  {c.fieldErrors[invalidField]}
                  {invalidField === "rebalance" &&
                    strategy &&
                    ` (${strategy.parameters.rebalance_sessions.min}–${strategy.parameters.rebalance_sessions.max})`}
                  {invalidField === "holdings" &&
                    strategy &&
                    ` (${strategy.parameters.maximum_holdings.min}–${strategy.parameters.maximum_holdings.max})`}
                </p>
              )}
            </div>
          )}
          {storageError && <p role="alert">{c.storageError}</p>}
          {draftConflict && (
            <p role="alert">
              {storageError ? c.draftConflictStorageFailed : c.draftConflict}
            </p>
          )}
          <div className="experimentActions">
            {step > 0 && (
              <button
                type="button"
                className="button secondary"
                disabled={pending}
                onClick={() => move(step - 1)}
              >
                {c.back}
              </button>
            )}
            <button
              className="button"
              type="submit"
              disabled={step === 3 && !acknowledged}
              aria-disabled={pending || (step === 3 && !acknowledged)}
            >
              {pending ? c.submitting : step === 3 ? c.confirm : c.next}
            </button>
          </div>
          <div className="experimentDraftActions">
            <button
              type="button"
              className="button secondary"
              disabled={pending}
              onClick={persist}
            >
              {c.save}
            </button>
            <button
              type="button"
              className="button secondary"
              disabled={pending}
              onClick={() => {
                if (persist()) setExitOpen(true);
              }}
            >
              {c.exit}
            </button>
            <span role="status">{saved ? c.saved : ""}</span>
          </div>
        </form>
        <aside
          className="experimentPanel experimentSummary"
          aria-label={c.summary}
        >
          <h2>{c.summary}</h2>
          <dl>
            <dt>{c.registered}</dt>
            <dd>{nameOfStrategy}</dd>
            <dt>{c.mode}</dt>
            <dd>
              {dataset?.mode === "synthetic_demo" ? c.demo : c.historical}
            </dd>
            <dt>{c.cash}</dt>
            <dd>{formatDecimal(form.initial_cash)}</dd>
            <dt>{c.period}</dt>
            <dd>
              {form.start_date || "—"} → {form.end_date || "—"}
            </dd>
            <dt>{c.universe}</dt>
            <dd>{universeName(form.universe)}</dd>
            <dt>{c.rebalance}</dt>
            <dd>{form.strategy.rebalance_sessions}</dd>
            <dt>{c.holdings}</dt>
            <dd>{form.strategy.maximum_holdings}</dd>
            <dt>{c.commission}</dt>
            <dd>{formatDecimal(form.costs.commission_rate)}</dd>
            <dt>{c.minimum}</dt>
            <dd>{formatDecimal(form.costs.minimum_commission)}</dd>
            <dt>{c.drawdown}</dt>
            <dd>{formatDecimal(form.risk.max_drawdown)}</dd>
            <dt>{c.position}</dt>
            <dd>{formatDecimal(form.risk.max_position_weight)}</dd>
          </dl>
        </aside>
      </div>
      <ConfigurationVersionsPanel
        current={{ form, step, idempotencyKey: requestKey }}
        disabled={pending}
        restoreBlocked={draftConflict}
        onRestore={(draft) => {
          expectedRaw.current = JSON.stringify(draft);
          draftConflictRef.current = false;
          setDraftConflict(false);
          setForm(draft.form);
          setStep(0);
          setRequestKey(draft.idempotencyKey);
          setSaved(true);
          savedRef.current = true;
          setStorageError(false);
          setError(null);
          setAcknowledged(false);
        }}
      />
      {exitOpen && (
        <Dialog title={c.exit} onClose={() => setExitOpen(false)}>
          <p>{c.exitConfirm}</p>
          <div className="experimentDraftActions">
            <button
              type="button"
              className="button secondary"
              onClick={() => setExitOpen(false)}
            >
              {c.back}
            </button>
            <button
              type="button"
              className="button"
              onClick={() => navigate("/")}
            >
              {c.exit}
            </button>
          </div>
        </Dialog>
      )}
    </>
  );
}
