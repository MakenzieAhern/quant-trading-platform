import { useEffect, useRef, useState, type FormEvent } from "react";
import { useTranslation } from "react-i18next";
import { Link } from "../../components/Link";
import { useApiResource } from "../../hooks/useApiResource";
import {
  comparePositiveDecimals,
  formatDecimal,
  isPositiveDecimal,
} from "../../utils/format";
import { navigate, useNavigationGuard } from "../../utils/navigation";
import { usePageDataContext } from "../dataContext";
import { ConfigurationVersionsPanel } from "../configs";
import { experimentApi } from "./api";
import { useExperimentCopy } from "./copy";
import {
  EXPERIMENT_DRAFT_KEY,
  readExperimentDraft,
  saveExperimentDraft,
} from "./draft";
import { experimentError } from "./errors";
import type { Capabilities, ExperimentConfiguration } from "./types";
import "./experiments.css";

export function CreateExperimentPage() {
  const c = useExperimentCopy();
  const [revision, setRevision] = useState(0);
  const capabilities = useApiResource(
    (signal) => experimentApi.capabilities(signal),
    [revision],
  );
  return (
    <div className="experimentWorkspace">
      <header className="experimentHeader">
        <p className="experimentEyebrow">{c.steps[0]}</p>
        <h1>{c.title}</h1>
        <p>{c.intro}</p>
      </header>
      {capabilities.loading && <p role="status">{c.loading}</p>}
      {capabilities.error && (
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
      {capabilities.data &&
        (capabilities.data.strategies.length ? (
          <ExperimentWizard capabilities={capabilities.data} />
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
      (item) => item.available && item.mode === "historical_exploration",
    ) ??
    capabilities.datasets.find((item) => item.available) ??
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

function validConfiguration(
  form: ExperimentConfiguration,
  capabilities: Capabilities,
  step: number,
): boolean {
  const strategy = capabilities.strategies.find(
    (item) => item.strategy_id === form.strategy_id,
  );
  if (!strategy) return false;
  if (step === 0) return true;
  const dataset = capabilities.datasets.find(
    (item) => item.dataset_id === form.dataset_id,
  );
  if (
    !dataset?.available ||
    !form.name.trim() ||
    !isPositiveDecimal(form.initial_cash) ||
    comparePositiveDecimals(form.initial_cash, "1000000000000") === 1 ||
    !form.start_date ||
    !form.end_date ||
    form.start_date > form.end_date ||
    form.start_date < dataset.coverage_start ||
    form.end_date > dataset.coverage_end ||
    !dataset.universes.includes(form.universe)
  )
    return false;
  for (const key of ["rebalance_sessions", "maximum_holdings"] as const) {
    const value = form.strategy[key],
      range = strategy.parameters[key];
    if (!Number.isSafeInteger(value) || value < range.min || value > range.max)
      return false;
  }
  if (step === 1) return true;
  for (const [value, max] of [
    [form.costs.commission_rate, "0.01"],
    [form.costs.minimum_commission, "1000"],
  ]) {
    const comparison = comparePositiveDecimals(value, max);
    if (comparison === null || comparison === 1) return false;
  }
  const magnitude = form.risk.max_drawdown.replace(/^-/, "");
  if (
    !/^-?0(?:\.\d+)?$|^-1(?:\.0+)?$/.test(form.risk.max_drawdown) ||
    comparePositiveDecimals(magnitude, "1") === 1 ||
    (isPositiveDecimal(form.risk.max_drawdown) &&
      form.risk.max_drawdown !== "0")
  )
    return false;
  return (
    isPositiveDecimal(form.risk.max_position_weight) &&
    comparePositiveDecimals(form.risk.max_position_weight, "1") !== 1
  );
}

function ExperimentWizard({ capabilities }: { capabilities: Capabilities }) {
  const c = useExperimentCopy();
  const { i18n } = useTranslation();
  const [restored] = useState(readExperimentDraft);
  const [form, setForm] = useState(
    () => restored?.form ?? initialForm(capabilities, c.defaultName),
  );
  const [step, setStep] = useState(restored?.step ?? 0);
  const [requestKey, setRequestKey] = useState(
    () => restored?.idempotencyKey ?? crypto.randomUUID(),
  );
  const [saved, setSaved] = useState(Boolean(restored));
  const savedRef = useRef(Boolean(restored));
  const [storageError, setStorageError] = useState(false);
  const [error, setError] = useState<unknown>(null);
  const [pending, setPending] = useState(false);
  const [acknowledged, setAcknowledged] = useState(false);
  const locked = useRef(false);
  const active = useRef(true);
  const heading = useRef<HTMLHeadingElement>(null);
  const strategy = capabilities.strategies.find(
    (item) => item.strategy_id === form.strategy_id,
  );
  const dataset = capabilities.datasets.find(
    (item) => item.dataset_id === form.dataset_id,
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
  useNavigationGuard(() => savedRef.current || window.confirm(c.exitConfirm));

  useEffect(() => {
    active.current = true;
    return () => {
      active.current = false;
    };
  }, []);
  useEffect(() => {
    heading.current?.focus();
  }, [step]);
  useEffect(() => {
    const save = () => {
      try {
        saveExperimentDraft(form, step, requestKey);
        return true;
      } catch {
        return false;
      }
    };
    save();
    const unload = (event: BeforeUnloadEvent) => {
      if (!savedRef.current || !save()) {
        event.preventDefault();
        event.returnValue = "";
      }
    };
    window.addEventListener("beforeunload", unload);
    return () => {
      window.removeEventListener("beforeunload", unload);
    };
  }, [form, step, requestKey, saved, c.exitConfirm]);

  function update(next: ExperimentConfiguration) {
    setForm(next);
    setRequestKey(crypto.randomUUID());
    setError(null);
    setSaved(false);
    savedRef.current = false;
    setAcknowledged(false);
  }
  function persist() {
    try {
      saveExperimentDraft(form, step, requestKey);
      setSaved(true);
      savedRef.current = true;
      setStorageError(false);
      return true;
    } catch {
      setStorageError(true);
      return false;
    }
  }
  function move(next: number) {
    if (next > step && !validConfiguration(form, capabilities, step)) {
      setError("validation");
      return;
    }
    setError(null);
    setStep(next);
  }
  async function submit(event: FormEvent) {
    event.preventDefault();
    if (step < 3) {
      move(step + 1);
      return;
    }
    if (locked.current) return;
    if (!acknowledged || !validConfiguration(form, capabilities, 3)) {
      setError("validation");
      return;
    }
    locked.current = true;
    setPending(true);
    setError(null);
    persist();
    try {
      const job = await experimentApi.create(form, requestKey);
      try {
        if (readExperimentDraft()?.idempotencyKey === requestKey)
          window.localStorage.removeItem(EXPERIMENT_DRAFT_KEY);
      } catch {
        /* The durable server job is authoritative after creation. */
      }
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
      {restored && (
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
          className="experimentPanel experimentForm"
          onSubmit={(event) => void submit(event)}
        >
          <h2 ref={heading} tabIndex={-1}>
            {c.steps[step]}
          </h2>
          <fieldset disabled={pending}>
            {step === 0 && (
              <div className="experimentStrategyChoices">
                {capabilities.strategies.map((entry) => (
                  <label
                    key={entry.strategy_id}
                    className={`experimentChoice ${entry.strategy_id === form.strategy_id ? "isSelected" : ""}`}
                  >
                    <input
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
                        disabled={!entry.available}
                      >
                        {entry.mode === "synthetic_demo"
                          ? c.demo
                          : c.historical}
                        {!entry.available ? ` · ${c.unavailable}` : ""}
                      </option>
                    ))}
                  </select>
                </label>
                {dataset && (
                  <p className="experimentHelp">
                    {c.coverage}: {dataset.coverage_start} —{" "}
                    {dataset.coverage_end} · {dataset.security_count}{" "}
                    {c.securities}
                  </p>
                )}
                {!dataset?.available && (
                  <p role="alert">
                    {c.dataUnavailable} <Link href="/data">{c.dataset}</Link>
                  </p>
                )}
                <label>
                  {c.cash}
                  <input
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
                      type="date"
                      required
                      min={dataset?.coverage_start}
                      max={form.end_date || dataset?.coverage_end}
                      value={form.start_date}
                      onInput={(event) =>
                        update({ ...form, start_date: event.currentTarget.value })
                      }
                    />
                  </label>
                  <label>
                    {c.end}
                    <input
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
            <div className="experimentError" role="alert">
              {error === "validation"
                ? c.validation
                : experimentError(error, c)}
            </div>
          )}
          {storageError && <p role="alert">{c.storageError}</p>}
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
              disabled={pending || (step === 3 && !acknowledged)}
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
                if (persist() && window.confirm(c.exitConfirm)) navigate("/");
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
        onRestore={(draft) => {
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
    </>
  );
}
