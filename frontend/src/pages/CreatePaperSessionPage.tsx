import {
  useEffect,
  useLayoutEffect,
  useRef,
  useState,
  type FormEvent,
} from "react";
import { useTranslation } from "react-i18next";

import { ApiError } from "../api/client";
import { paperApi } from "../api/paper";
import { ErrorPanel, LoadingPanel } from "../components/AsyncPanel";
import { Link } from "../components/Link";
import { PaperSafetyBanner } from "../components/PaperSafetyBanner";
import { useApiResource } from "../hooks/useApiResource";
import { experimentApi } from "../product/experiments/api";
import { canUsePaperHandoff } from "../product/experiments/paperHandoff";
import type { Experiment } from "../product/experiments/types";
import type { CreatePaperSessionRequest, PaperSession } from "../types/paper";
import {
  comparePositiveDecimals,
  isPositiveDecimal,
  parsePositiveInteger,
} from "../utils/format";
import { navigate } from "../utils/navigation";
import {
  confirmPaperCreate,
  discardRejectedPaperCreate,
  PAPER_CREATE_PENDING_PREFIX,
  paperRequestFromBody,
  PendingPaperCreateError,
  preparePaperCreate,
  readPendingPaperCreates,
  type PendingPaperCreate,
  withPaperCreateLock,
} from "./paperCreateRecovery";

type ReplayRequest = Extract<
  CreatePaperSessionRequest,
  { provider_type: "replay" }
>;
type StrategyType = ReplayRequest["strategy"]["type"];
type ProviderType = CreatePaperSessionRequest["provider_type"];

const uuidPattern =
  /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
const decimalPattern = /^\d+(?:\.\d+)?$/;

function copiedPaperRequest(
  source: PaperSession,
): CreatePaperSessionRequest | null {
  if (
    !["STOPPED", "FAILED", "INTERRUPTED"].includes(source.status) ||
    !isPositiveDecimal(source.initial_cash) ||
    !isPositiveDecimal(source.default_order_quantity)
  )
    return null;
  const risk = source.risk;
  const supportedRisk = new Set([
    "max_order_notional",
    "max_position_quantity",
    "max_symbol_exposure",
    "max_gross_exposure",
    "max_leverage",
    "enforce_buying_power",
    "max_drawdown",
    "allow_limit_orders",
  ]);
  if (
    Object.keys(risk).some((key) => !supportedRisk.has(key)) ||
    [
      risk.max_order_notional,
      risk.max_position_quantity,
      risk.max_symbol_exposure,
      risk.max_gross_exposure,
    ].some((value) => value != null) ||
    risk.enforce_buying_power !== true ||
    (risk.allow_limit_orders !== undefined && risk.allow_limit_orders !== false)
  )
    return null;

  const parameters = source.strategy_parameters;
  if (source.provider_type === "historical_a_share") {
    const supported = new Set([
      "start_date",
      "end_date",
      "rebalance_sessions",
      "maximum_holdings",
      "max_position_weight",
      "universe",
      "commission_rate",
      "minimum_commission",
      "dataset_sha256", // Server provenance is resolved again for the new account.
      "plan_version",
    ]);
    if (
      source.dataset_id !== "cn-a-research-20100101-20251231-v1" ||
      source.symbol !== "CN-A" ||
      source.strategy_type !== "cn_a_cross_sectional_momentum_low_vol_v1" ||
      source.default_order_quantity !== "1" ||
      risk.max_leverage !== "1" ||
      typeof risk.max_drawdown !== "string" ||
      Object.keys(parameters).some((key) => !supported.has(key)) ||
      typeof parameters.start_date !== "string" ||
      typeof parameters.end_date !== "string" ||
      !/^\d{4}-\d{2}-\d{2}$/.test(parameters.start_date) ||
      !/^\d{4}-\d{2}-\d{2}$/.test(parameters.end_date) ||
      !Number.isFinite(Date.parse(parameters.start_date)) ||
      !Number.isFinite(Date.parse(parameters.end_date)) ||
      !Number.isSafeInteger(parameters.rebalance_sessions) ||
      !Number.isSafeInteger(parameters.maximum_holdings) ||
      typeof parameters.max_position_weight !== "string" ||
      !isPositiveDecimal(parameters.max_position_weight) ||
      !["ALL", "SSE", "SZSE"].includes(String(parameters.universe)) ||
      typeof parameters.commission_rate !== "string" ||
      !decimalPattern.test(parameters.commission_rate) ||
      typeof parameters.minimum_commission !== "string" ||
      !decimalPattern.test(parameters.minimum_commission)
    )
      return null;
    return {
      provider_type: "historical_a_share",
      dataset_id: "cn-a-research-20100101-20251231-v1",
      symbol: "CN-A",
      strategy: {
        type: "cn_a_cross_sectional_momentum_low_vol_v1",
        parameters: {
          start_date: parameters.start_date,
          end_date: parameters.end_date,
          rebalance_sessions: parameters.rebalance_sessions as number,
          maximum_holdings: parameters.maximum_holdings as number,
          max_position_weight: parameters.max_position_weight,
          universe: parameters.universe as "ALL" | "SSE" | "SZSE",
          commission_rate: parameters.commission_rate,
          minimum_commission: parameters.minimum_commission,
        },
      },
      initial_cash: source.initial_cash,
      default_order_quantity: "1",
      risk: {
        enforce_buying_power: true,
        max_leverage: "1",
        max_drawdown: risk.max_drawdown,
      },
    };
  }
  if (risk.max_leverage != null || risk.max_drawdown != null) return null;
  if (source.provider_type === "simulated_a_share") {
    if (
      source.dataset_id !== "CN_A_SIMULATED_PAPER_FIXTURE_V1" ||
      source.symbol !== "CN-A" ||
      source.strategy_type !== "cn_a_cross_sectional_momentum_low_vol_v1" ||
      source.default_order_quantity !== "1" ||
      Object.keys(parameters).length !== 0
    )
      return null;
    return {
      provider_type: "simulated_a_share",
      dataset_id: "CN_A_SIMULATED_PAPER_FIXTURE_V1",
      symbol: "CN-A",
      strategy: {
        type: "cn_a_cross_sectional_momentum_low_vol_v1",
        parameters: {},
      },
      initial_cash: source.initial_cash,
      default_order_quantity: "1",
      risk: { enforce_buying_power: true },
    };
  }
  if (source.dataset_id !== "AAPL_fixture" || source.symbol !== "AAPL")
    return null;
  if (source.strategy_type === "moving_average_crossover") {
    if (
      Object.keys(parameters).some(
        (key) => key !== "short_period" && key !== "long_period",
      ) ||
      !Number.isSafeInteger(parameters.short_period) ||
      !Number.isSafeInteger(parameters.long_period)
    )
      return null;
    return {
      provider_type: "replay",
      dataset_id: "AAPL_fixture",
      symbol: "AAPL",
      strategy: {
        type: "moving_average_crossover",
        parameters: {
          short_period: parameters.short_period as number,
          long_period: parameters.long_period as number,
        },
      },
      initial_cash: source.initial_cash,
      default_order_quantity: source.default_order_quantity,
      risk: { enforce_buying_power: true },
    };
  }
  if (
    source.strategy_type !== "rsi_mean_reversion" ||
    Object.keys(parameters).some(
      (key) => !["rsi_period", "oversold", "overbought"].includes(key),
    ) ||
    !Number.isSafeInteger(parameters.rsi_period) ||
    typeof parameters.oversold !== "string" ||
    typeof parameters.overbought !== "string" ||
    !decimalPattern.test(parameters.oversold) ||
    !decimalPattern.test(parameters.overbought)
  )
    return null;
  return {
    provider_type: "replay",
    dataset_id: "AAPL_fixture",
    symbol: "AAPL",
    strategy: {
      type: "rsi_mean_reversion",
      parameters: {
        rsi_period: parameters.rsi_period as number,
        oversold: parameters.oversold,
        overbought: parameters.overbought,
      },
    },
    initial_cash: source.initial_cash,
    default_order_quantity: source.default_order_quantity,
    risk: { enforce_buying_power: true },
  };
}

export function CreatePaperSessionPage() {
  const { t } = useTranslation("paper");
  const [saved, setSaved] = useState<PendingPaperCreate[] | null>(loadSaved);
  const refreshSaved = () => setSaved(loadSaved());
  useEffect(() => {
    const onStorage = (event: StorageEvent) => {
      if (
        event.key === null ||
        event.key.startsWith(PAPER_CREATE_PENDING_PREFIX)
      )
        refreshSaved();
    };
    window.addEventListener("storage", onStorage);
    return () => window.removeEventListener("storage", onStorage);
  }, []);
  return (
    <>
      <PaperSafetyBanner />
      <header className="pageHeader compactHeader">
        <div>
          <p className="eyebrow">{t("createPage.eyebrow")}</p>
          <h1>{t("createPage.title")}</h1>
        </div>
        <Link className="button" href="/paper">
          {t("createPage.cancel")}
        </Link>
      </header>
      <PaperCreateRecoveryPanel saved={saved} onSavedChange={refreshSaved} />
      <PaperSessionCreationContent
        onSavedChange={refreshSaved}
        canCreateAnother={Boolean(
          saved?.length && saved.every((item) => item.confirmedSessionId),
        )}
      />
    </>
  );
}

function loadSaved(): PendingPaperCreate[] | null {
  try {
    return readPendingPaperCreates();
  } catch {
    return null;
  }
}

function definitelyNotCreated(reason: unknown): boolean {
  return (
    reason instanceof ApiError &&
    [400, 401, 403, 404, 422].includes(reason.status)
  );
}

function paperCreateError(reason: unknown): string {
  return reason instanceof ApiError &&
    (reason.status === 401 || reason.status === 403)
    ? "common:loadErrors.permission"
    : reason instanceof ApiError && reason.status === 404
      ? "createPage.datasetError"
      : reason instanceof ApiError && reason.status === 409
        ? "createPage.conflictError"
        : reason instanceof ApiError && reason.status === 422
          ? "createPage.validationError"
          : "createPage.submitError";
}

async function createOrRecoverPaper(
  request: CreatePaperSessionRequest,
  key: string,
  priorAttempt: boolean,
) {
  try {
    return await paperApi.create(request, key);
  } catch (reason) {
    if (
      priorAttempt &&
      reason instanceof ApiError &&
      [400, 404, 422].includes(reason.status)
    ) {
      try {
        return await paperApi.receipt(key);
      } catch {
        // A missing receipt is not proof that an in-flight POST cannot commit.
      }
    }
    throw reason;
  }
}

async function verifiedPaperSessionId(
  saved: PendingPaperCreate,
): Promise<string> {
  if (!saved.confirmedSessionId)
    throw new Error("Paper receipt is unconfirmed");
  const current = await paperApi.receipt(saved.key);
  if (current.session_id !== saved.confirmedSessionId)
    throw new Error("Saved paper receipt does not match server");
  return current.session_id;
}

function PaperCreateRecoveryPanel({
  saved,
  onSavedChange,
}: {
  saved: PendingPaperCreate[] | null;
  onSavedChange: () => void;
}) {
  const { t } = useTranslation("paper");
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const locked = useRef(false);
  const active = useRef(true);
  useEffect(() => {
    active.current = true;
    return () => {
      active.current = false;
    };
  }, []);

  const retry = async (intent: PendingPaperCreate) => {
    if (locked.current) return;
    locked.current = true;
    setBusy(intent.key);
    setError(null);
    const originatingUrl = window.location.href;
    let sent = false;
    let verifyingReceipt = false;
    try {
      const sessionId = await withPaperCreateLock(async () => {
        if (!active.current || window.location.href !== originatingUrl)
          throw new Error("Paper creation page was left before retry");
        const saved = readPendingPaperCreates().find(
          (item) => item.body === intent.body && item.key === intent.key,
        );
        if (!saved) throw new Error("Saved paper request changed");
        if (saved.confirmedSessionId) {
          verifyingReceipt = true;
          return verifiedPaperSessionId(saved);
        }
        // A prior attempt may have committed even if this retry is rejected.
        sent = true;
        const created = await createOrRecoverPaper(
          paperRequestFromBody(saved.body),
          saved.key,
          true,
        );
        try {
          confirmPaperCreate(saved, created.session_id);
        } catch {
          // Keep the exact key for another recovery if receipt storage fails.
        }
        return created.session_id;
      });
      if (active.current && window.location.href === originatingUrl)
        navigate(`/paper/${sessionId}`);
    } catch (reason) {
      if (active.current)
        setError(
          verifyingReceipt
            ? "createPage.receiptUnverified"
            : sent
              ? paperCreateError(reason)
              : "createPage.recoveryError",
        );
    } finally {
      locked.current = false;
      if (active.current) {
        setBusy(null);
        onSavedChange();
      }
    }
  };

  const verifyAndOpen = async (intent: PendingPaperCreate) => {
    if (locked.current) return;
    locked.current = true;
    setBusy(intent.key);
    setError(null);
    const originatingUrl = window.location.href;
    try {
      const sessionId = await withPaperCreateLock(async () => {
        if (!active.current || window.location.href !== originatingUrl)
          throw new Error("Paper creation page was left before verification");
        const saved = readPendingPaperCreates().find(
          (item) => item.key === intent.key && item.body === intent.body,
        );
        if (
          !saved?.confirmedSessionId ||
          saved.confirmedSessionId !== intent.confirmedSessionId
        )
          throw new Error("Saved paper receipt changed");
        return verifiedPaperSessionId(saved);
      });
      if (active.current && window.location.href === originatingUrl)
        navigate(`/paper/${sessionId}`);
    } catch {
      if (active.current) setError("createPage.receiptUnverified");
    } finally {
      locked.current = false;
      if (active.current) {
        setBusy(null);
        onSavedChange();
      }
    }
  };

  if (saved === null)
    return <p role="alert">{t("createPage.recoveryError")}</p>;
  if (!saved.length) return null;
  return (
    <section
      className="experimentNotice"
      aria-labelledby="paper-recovery-title"
    >
      <h2 id="paper-recovery-title">{t("createPage.pendingTitle")}</h2>
      <p>{t("createPage.pendingHelp")}</p>
      <ul>
        {saved.map((intent, index) => {
          const request = paperRequestFromBody(intent.body);
          const mode = t(
            request.provider_type === "replay"
              ? "createPage.replayLocal"
              : request.provider_type === "historical_a_share"
                ? "createPage.historicalAShare"
                : "createPage.aShareSimulation",
          );
          return (
            <li key={intent.key}>
              <p>
                {mode} · {t("createPage.initialCash")}: {request.initial_cash}
              </p>
              <details>
                <summary>{t("createPage.pendingDetails")}</summary>
                <pre style={{ overflowX: "auto" }}>
                  {JSON.stringify(request, null, 2)}
                </pre>
              </details>
              {intent.confirmedSessionId ? (
                <button
                  type="button"
                  aria-disabled={busy !== null}
                  onClick={() => void verifyAndOpen(intent)}
                >
                  {t("createPage.openSaved")}
                </button>
              ) : (
                <button
                  type="button"
                  aria-disabled={busy !== null}
                  onClick={() => void retry(intent)}
                >
                  {t("createPage.retrySaved", { number: index + 1 })}
                </button>
              )}
            </li>
          );
        })}
      </ul>
      {error && <p role="alert">{t(error)}</p>}
    </section>
  );
}

function PaperSessionCreationContent({
  onSavedChange,
  canCreateAnother,
}: {
  onSavedChange: () => void;
  canCreateAnother: boolean;
}) {
  const sourceId = new URLSearchParams(window.location.search).get(
    "from_experiment",
  );
  const sessionId = new URLSearchParams(window.location.search).get(
    "from_session",
  );
  const validSourceId =
    sourceId && uuidPattern.test(sourceId) ? sourceId : null;
  const validSessionId =
    sessionId && uuidPattern.test(sessionId) ? sessionId.toLowerCase() : null;
  const source = useApiResource(
    (signal) =>
      validSourceId && !sessionId
        ? experimentApi.get(validSourceId, signal)
        : Promise.resolve(null),
    [validSourceId, sessionId],
  );
  const paperSource = useApiResource(
    (signal) =>
      validSessionId && !sourceId
        ? paperApi.get(validSessionId, signal)
        : Promise.resolve(null),
    [validSessionId, sourceId],
  );
  const { t } = useTranslation("paper");
  if (sessionId && (sourceId || !validSessionId))
    return (
      <p role="alert">
        {t("createPage.sessionSourceUnavailable")}{" "}
        <Link href="/paper">{t("createPage.sessionSourceList")}</Link>
      </p>
    );
  if (sourceId && !validSourceId)
    return (
      <p role="alert">
        {t("createPage.sourceUnavailable")}{" "}
        <Link href="/experiments">{t("createPage.sourceList")}</Link>
      </p>
    );
  if (validSourceId && source.loading)
    return <LoadingPanel label={t("createPage.sourceLoading")} />;
  if (validSessionId && paperSource.loading)
    return <LoadingPanel label={t("createPage.sessionSourceLoading")} />;
  if (validSourceId && source.error)
    return (
      <ErrorPanel
        message={source.error}
        notFoundReturn={{
          href: "/experiments",
          label: t("createPage.sourceList"),
        }}
      />
    );
  if (validSessionId && paperSource.error)
    return (
      <ErrorPanel
        message={paperSource.error}
        notFoundReturn={{
          href: "/paper",
          label: t("createPage.sessionSourceList"),
        }}
      />
    );
  const job = source.data;
  if (validSourceId && !canUsePaperHandoff(job))
    return (
      <p role="alert">
        {t("createPage.sourceUnavailable")}{" "}
        <Link href="/experiments">{t("createPage.sourceList")}</Link>
      </p>
    );
  const original = paperSource.data;
  const sourceDraft = original ? copiedPaperRequest(original) : null;
  if (
    validSessionId &&
    (!original || original.session_id !== validSessionId || !sourceDraft)
  )
    return (
      <p role="alert">
        {t("createPage.sessionSourceUnavailable")}{" "}
        <Link href="/paper">{t("createPage.sessionSourceList")}</Link>
      </p>
    );
  return (
    <PaperSessionForm
      key={job?.job_id ?? original?.session_id ?? "new"}
      sourceJob={job}
      sourceSession={original}
      sourceDraft={sourceDraft}
      onSavedChange={onSavedChange}
      canCreateAnother={canCreateAnother}
    />
  );
}

function PaperSessionForm({
  sourceJob,
  sourceSession,
  sourceDraft,
  onSavedChange,
  canCreateAnother,
}: {
  sourceJob: Experiment | null;
  sourceSession: PaperSession | null;
  sourceDraft: CreatePaperSessionRequest | null;
  onSavedChange: () => void;
  canCreateAnother: boolean;
}) {
  const { t } = useTranslation("paper");
  const sourceConfig = sourceJob?.configuration;
  const historicalDraft =
    sourceDraft?.provider_type === "historical_a_share" ? sourceDraft : null;
  const replayDraft =
    sourceDraft?.provider_type === "replay" ? sourceDraft : null;
  const movingAverageDraft =
    replayDraft?.strategy.type === "moving_average_crossover"
      ? replayDraft.strategy.parameters
      : null;
  const rsiDraft =
    replayDraft?.strategy.type === "rsi_mean_reversion"
      ? replayDraft.strategy.parameters
      : null;
  const sourceRangeFits =
    sourceConfig &&
    Number.isFinite(Date.parse(sourceConfig.start_date)) &&
    Number.isFinite(Date.parse(sourceConfig.end_date)) &&
    Date.parse(sourceConfig.end_date) >= Date.parse(sourceConfig.start_date) &&
    Date.parse(sourceConfig.end_date) - Date.parse(sourceConfig.start_date) <=
      92 * 86_400_000;
  const [providerType, setProviderType] = useState<ProviderType>(
    sourceDraft?.provider_type ??
      (sourceJob ? "historical_a_share" : "simulated_a_share"),
  );
  const [strategyType, setStrategyType] = useState<StrategyType>(
    replayDraft?.strategy.type ?? "moving_average_crossover",
  );
  const [initialCash, setInitialCash] = useState(
    sourceDraft?.initial_cash ?? sourceConfig?.initial_cash ?? "100000000",
  );
  const [quantity, setQuantity] = useState(
    sourceDraft?.default_order_quantity ?? "1",
  );
  const [shortPeriod, setShortPeriod] = useState(
    String(movingAverageDraft?.short_period ?? 2),
  );
  const [longPeriod, setLongPeriod] = useState(
    String(movingAverageDraft?.long_period ?? 3),
  );
  const [rsiPeriod, setRsiPeriod] = useState(
    String(rsiDraft?.rsi_period ?? 14),
  );
  const [oversold, setOversold] = useState(rsiDraft?.oversold ?? "30");
  const [overbought, setOverbought] = useState(rsiDraft?.overbought ?? "70");
  const [startDate, setStartDate] = useState(
    historicalDraft?.strategy.parameters.start_date ??
      (sourceRangeFits
        ? sourceConfig.start_date
        : sourceJob
          ? ""
          : "2011-03-01"),
  );
  const [endDate, setEndDate] = useState(
    historicalDraft?.strategy.parameters.end_date ??
      sourceConfig?.end_date ??
      "2011-03-31",
  );
  const [rebalanceSessions, setRebalanceSessions] = useState(
    String(
      historicalDraft?.strategy.parameters.rebalance_sessions ??
        sourceConfig?.strategy.rebalance_sessions ??
        20,
    ),
  );
  const [maximumHoldings, setMaximumHoldings] = useState(
    String(
      historicalDraft?.strategy.parameters.maximum_holdings ??
        sourceConfig?.strategy.maximum_holdings ??
        20,
    ),
  );
  const [maxPositionWeight, setMaxPositionWeight] = useState(
    historicalDraft?.strategy.parameters.max_position_weight ??
      sourceConfig?.risk.max_position_weight ??
      "0.1",
  );
  const [maxDrawdown, setMaxDrawdown] = useState(
    historicalDraft?.risk.max_drawdown ??
      sourceConfig?.risk.max_drawdown ??
      "-0.2",
  );
  const [universe, setUniverse] = useState<"ALL" | "SSE" | "SZSE">(
    historicalDraft?.strategy.parameters.universe ??
      sourceConfig?.universe ??
      "ALL",
  );
  const [commissionRate, setCommissionRate] = useState(
    historicalDraft?.strategy.parameters.commission_rate ??
      sourceConfig?.costs.commission_rate ??
      "0.0003",
  );
  const [minimumCommission, setMinimumCommission] = useState(
    historicalDraft?.strategy.parameters.minimum_commission ??
      sourceConfig?.costs.minimum_commission ??
      "5",
  );
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [invalidField, setInvalidField] = useState<string | null>(null);
  const [validationAttempt, setValidationAttempt] = useState(0);
  const locked = useRef(false);
  const active = useRef(true);
  const formElement = useRef<HTMLFormElement>(null);

  useEffect(() => {
    active.current = true;
    return () => {
      active.current = false;
    };
  }, []);
  useLayoutEffect(() => {
    if (!invalidField) return;
    const input = formElement.current?.elements.namedItem(invalidField);
    if (input instanceof HTMLElement) {
      const details = input.closest("details");
      if (details) details.open = true;
      input.focus();
    }
  }, [invalidField, validationAttempt]);

  const changed = () => {
    setError(null);
    setInvalidField(null);
  };

  const fieldAccessibility = (field: string) => ({
    name: field,
    "aria-invalid": invalidField === field || undefined,
    "aria-describedby": invalidField === field ? "paper-form-error" : undefined,
  });
  const reportInvalid = (message: string, field: string) => {
    setInvalidField(field);
    setError(message);
    setValidationAttempt((attempt) => attempt + 1);
  };

  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (locked.current) return;
    const submitter = (event.nativeEvent as SubmitEvent).submitter;
    const createAnother =
      Boolean(sourceSession) ||
      (submitter instanceof HTMLButtonElement && submitter.value === "another");
    setError(null);
    setInvalidField(null);
    if (!isPositiveDecimal(initialCash)) {
      reportInvalid("createPage.decimalError", "initialCash");
      return;
    }
    if (!isPositiveDecimal(quantity)) {
      reportInvalid("createPage.decimalError", "orderQuantity");
      return;
    }
    if (
      providerType === "historical_a_share" &&
      comparePositiveDecimals(initialCash.trim(), "1000000000000") === 1
    ) {
      reportInvalid("createPage.historicalCashLimit", "initialCash");
      return;
    }
    let request: CreatePaperSessionRequest;
    if (providerType === "simulated_a_share") {
      request = {
        provider_type: providerType,
        dataset_id: "CN_A_SIMULATED_PAPER_FIXTURE_V1",
        symbol: "CN-A",
        strategy: {
          type: "cn_a_cross_sectional_momentum_low_vol_v1",
          parameters: {},
        },
        initial_cash: initialCash,
        default_order_quantity: quantity,
        risk: { enforce_buying_power: true },
      };
    } else if (providerType === "historical_a_share") {
      const rebalance = parsePositiveInteger(rebalanceSessions);
      const holdings = parsePositiveInteger(maximumHoldings);
      const invalid =
        !startDate || !Number.isFinite(Date.parse(startDate))
          ? "startDate"
          : !endDate ||
              endDate < startDate ||
              !Number.isFinite(Date.parse(endDate)) ||
              Date.parse(endDate) - Date.parse(startDate) > 92 * 86_400_000
            ? "endDate"
            : rebalance === null || rebalance > 252
              ? "rebalanceSessions"
              : holdings === null || holdings > 100
                ? "maximumHoldings"
                : !isPositiveDecimal(maxPositionWeight) ||
                    comparePositiveDecimals(maxPositionWeight, "1") === 1
                  ? "maxPositionWeight"
                  : !/^\d+(?:\.\d+)?$/.test(commissionRate) ||
                      comparePositiveDecimals(commissionRate, "0.01") === 1
                    ? "commissionRate"
                    : !/^\d+(?:\.\d+)?$/.test(minimumCommission) ||
                        comparePositiveDecimals(minimumCommission, "1000") === 1
                      ? "minimumCommission"
                      : !/^-?0(?:\.\d+)?$|^-1(?:\.0+)?$/.test(maxDrawdown) ||
                          (isPositiveDecimal(maxDrawdown) &&
                            maxDrawdown !== "0")
                        ? "maxDrawdown"
                        : null;
      if (invalid) {
        reportInvalid("createPage.historicalValidationError", invalid);
        return;
      }
      request = {
        provider_type: "historical_a_share",
        dataset_id: "cn-a-research-20100101-20251231-v1",
        symbol: "CN-A",
        strategy: {
          type: "cn_a_cross_sectional_momentum_low_vol_v1",
          parameters: {
            start_date: startDate,
            end_date: endDate,
            rebalance_sessions: rebalance!,
            maximum_holdings: holdings!,
            max_position_weight: maxPositionWeight,
            universe,
            commission_rate: commissionRate,
            minimum_commission: minimumCommission,
          },
        },
        initial_cash: initialCash,
        default_order_quantity: "1",
        risk: {
          enforce_buying_power: true,
          max_leverage: "1",
          max_drawdown: maxDrawdown,
        },
      };
    } else if (strategyType === "moving_average_crossover") {
      const short = parsePositiveInteger(shortPeriod);
      const long = parsePositiveInteger(longPeriod);
      if (short === null || long === null || short >= long) {
        reportInvalid(
          "createPage.periodError",
          short === null ? "shortPeriod" : "longPeriod",
        );
        return;
      }
      request = {
        provider_type: providerType,
        dataset_id: "AAPL_fixture",
        symbol: "AAPL",
        strategy: {
          type: strategyType,
          parameters: { short_period: short, long_period: long },
        },
        initial_cash: initialCash,
        default_order_quantity: quantity,
        risk: { enforce_buying_power: true },
      };
    } else {
      const period = parsePositiveInteger(rsiPeriod);
      if (
        period === null ||
        !isPositiveDecimal(oversold) ||
        comparePositiveDecimals(oversold, overbought) !== -1 ||
        comparePositiveDecimals(overbought, "100") !== -1
      ) {
        reportInvalid(
          "createPage.rsiError",
          period === null
            ? "rsiPeriod"
            : !isPositiveDecimal(oversold) ||
                comparePositiveDecimals(oversold, "100") !== -1
              ? "oversold"
              : "overbought",
        );
        return;
      }
      request = {
        provider_type: providerType,
        dataset_id: "AAPL_fixture",
        symbol: "AAPL",
        strategy: {
          type: strategyType,
          parameters: { rsi_period: period, oversold, overbought },
        },
        initial_cash: initialCash,
        default_order_quantity: quantity,
        risk: { enforce_buying_power: true },
      };
    }
    locked.current = true;
    setPending(true);
    const originatingUrl = window.location.href;
    let intent: PendingPaperCreate | null = null;
    let sent = false;
    let verifyingReceipts = false;
    try {
      const created = await withPaperCreateLock(async () => {
        if (!active.current || window.location.href !== originatingUrl)
          throw new Error("Paper creation page was left before submission");
        if (createAnother) {
          const previous = readPendingPaperCreates();
          if (previous.some((item) => !item.confirmedSessionId))
            throw new PendingPaperCreateError(
              "Resolve saved paper request first",
            );
          verifyingReceipts = true;
          for (const item of previous) await verifiedPaperSessionId(item);
          verifyingReceipts = false;
        }
        const priorKeys = new Set(
          readPendingPaperCreates().map((item) => item.key),
        );
        intent = preparePaperCreate(request, createAnother);
        const fresh = !priorKeys.has(intent.key);
        let result;
        try {
          sent = true;
          result = await createOrRecoverPaper(request, intent.key, !fresh);
        } catch (reason) {
          if (fresh && definitelyNotCreated(reason)) {
            try {
              discardRejectedPaperCreate(intent);
            } catch {
              // A storage failure leaves the original key for reconciliation.
            }
          }
          throw reason;
        }
        try {
          confirmPaperCreate(intent, result.session_id);
        } catch {
          // The original key remains recoverable if receipt storage fails.
        }
        return result;
      });
      if (active.current && window.location.href === originatingUrl)
        navigate(`/paper/${created.session_id}`);
    } catch (reason) {
      if (active.current)
        setError(
          reason instanceof PendingPaperCreateError
            ? "createPage.resolvePendingFirst"
            : verifyingReceipts
              ? "createPage.receiptUnverified"
              : sent
                ? paperCreateError(reason)
                : "createPage.storageError",
        );
    } finally {
      locked.current = false;
      if (active.current) {
        setPending(false);
        onSavedChange();
      }
    }
  };

  return (
    <>
      {sourceJob && (
        <section className="experimentNotice" role="note">
          <p>{t("createPage.sourceReview", { name: sourceJob.name })}</p>
          <p>
            {sourceConfig?.start_date} — {sourceConfig?.end_date}
            {!sourceRangeFits && ` · ${t("createPage.sourceChooseDates")}`}
          </p>
          <Link href="/paper/new">{t("createPage.sourceIndependent")}</Link>
        </section>
      )}
      {sourceSession && (
        <section className="experimentNotice" role="note">
          <p>{t("createPage.sessionSourceReview")}</p>
          <Link href={`/paper/${sourceSession.session_id}`}>
            {t("createPage.sessionSourceOriginal")}
          </Link>{" "}
          · <Link href="/paper/new">{t("createPage.sourceIndependent")}</Link>
        </section>
      )}
      <form
        ref={formElement}
        className="formPanel"
        noValidate
        onSubmit={(event) => void submit(event)}
        onChange={changed}
        aria-describedby={error ? "paper-form-error" : undefined}
      >
        <fieldset disabled={pending}>
          <legend>{t("createPage.safeProvider")}</legend>
          <div className="formGrid threeColumns">
            <label>
              {t("createPage.provider")}
              <select
                value={providerType}
                disabled={Boolean(sourceJob || sourceSession)}
                onChange={(event) => {
                  const value = event.target.value as ProviderType;
                  setProviderType(value);
                  setInitialCash(
                    value === "simulated_a_share" ? "100000000" : "100000",
                  );
                  setQuantity(value === "replay" ? "10" : "1");
                }}
              >
                <option value="simulated_a_share">
                  {t("createPage.aShareSimulation")}
                </option>
                <option value="replay">{t("createPage.replayLocal")}</option>
                <option value="historical_a_share">
                  {t("createPage.historicalAShare")}
                </option>
              </select>
            </label>
            <label>
              {t("createPage.dataset")}
              <input
                value={
                  providerType === "simulated_a_share"
                    ? "CN_A_SIMULATED_PAPER_FIXTURE_V1"
                    : providerType === "historical_a_share"
                      ? "cn-a-research-20100101-20251231-v1"
                      : "AAPL_fixture"
                }
                readOnly
                tabIndex={-1}
              />
            </label>
            <label>
              {t("createPage.symbol")}
              <input
                value={providerType === "replay" ? "AAPL" : "CN-A"}
                readOnly
                tabIndex={-1}
              />
            </label>
          </div>
        </fieldset>
        <fieldset disabled={pending}>
          <legend>{t("createPage.capitalSizing")}</legend>
          <div className="formGrid">
            <label>
              {t("createPage.initialCash")}
              <input
                {...fieldAccessibility("initialCash")}
                value={initialCash}
                onChange={(event) => setInitialCash(event.target.value)}
                required
              />
            </label>
            {providerType === "replay" && (
              <label>
                {t("createPage.orderQuantity")}
                <input
                  {...fieldAccessibility("orderQuantity")}
                  value={quantity}
                  onChange={(event) => setQuantity(event.target.value)}
                  required
                />
              </label>
            )}
          </div>
          <p className="fieldHint">
            {providerType === "simulated_a_share"
              ? t("createPage.aShareScenarioHint")
              : providerType === "historical_a_share"
                ? t("createPage.historicalHint")
                : t("createPage.buyingPowerHint")}
          </p>
          {providerType === "historical_a_share" && (
            <p className="fieldHint">{t("createPage.historicalCashLimit")}</p>
          )}
        </fieldset>
        <fieldset disabled={pending}>
          <legend>{t("createPage.registeredStrategy")}</legend>
          {providerType !== "replay" ? (
            <label>
              {t("createPage.strategyType")}
              <input
                value={t("strategies.cn_a_cross_sectional_momentum_low_vol_v1")}
                readOnly
                tabIndex={-1}
              />
            </label>
          ) : (
            <label>
              {t("createPage.strategyType")}
              <select
                value={strategyType}
                onChange={(event) =>
                  setStrategyType(event.target.value as StrategyType)
                }
              >
                <option value="moving_average_crossover">
                  {t("strategies.moving_average_crossover")}
                </option>
                <option value="rsi_mean_reversion">
                  {t("strategies.rsi_mean_reversion")}
                </option>
              </select>
            </label>
          )}
          {providerType === "replay" &&
          strategyType === "moving_average_crossover" ? (
            <div className="formGrid">
              <label>
                {t("createPage.shortPeriod")}
                <input
                  {...fieldAccessibility("shortPeriod")}
                  type="number"
                  min="1"
                  step="1"
                  value={shortPeriod}
                  onChange={(event) => setShortPeriod(event.target.value)}
                  required
                />
              </label>
              <label>
                {t("createPage.longPeriod")}
                <input
                  {...fieldAccessibility("longPeriod")}
                  type="number"
                  min="2"
                  step="1"
                  value={longPeriod}
                  onChange={(event) => setLongPeriod(event.target.value)}
                  required
                />
              </label>
            </div>
          ) : providerType === "replay" ? (
            <div className="formGrid threeColumns">
              <label>
                {t("createPage.rsiPeriod")}
                <input
                  {...fieldAccessibility("rsiPeriod")}
                  type="number"
                  min="1"
                  step="1"
                  value={rsiPeriod}
                  onChange={(event) => setRsiPeriod(event.target.value)}
                  required
                />
              </label>
              <label>
                {t("createPage.oversold")}
                <input
                  {...fieldAccessibility("oversold")}
                  value={oversold}
                  onChange={(event) => setOversold(event.target.value)}
                  required
                />
              </label>
              <label>
                {t("createPage.overbought")}
                <input
                  {...fieldAccessibility("overbought")}
                  value={overbought}
                  onChange={(event) => setOverbought(event.target.value)}
                  required
                />
              </label>
            </div>
          ) : null}
        </fieldset>
        {providerType === "historical_a_share" && (
          <fieldset disabled={pending}>
            <legend>{t("createPage.historicalRange")}</legend>
            <div className="formGrid">
              <label>
                {t("createPage.startDate")}
                <input
                  {...fieldAccessibility("startDate")}
                  type="date"
                  value={startDate}
                  onInput={(event) => setStartDate(event.currentTarget.value)}
                  required
                />
              </label>
              <label>
                {t("createPage.endDate")}
                <input
                  {...fieldAccessibility("endDate")}
                  type="date"
                  value={endDate}
                  onInput={(event) => setEndDate(event.currentTarget.value)}
                  required
                />
              </label>
            </div>
            <details>
              <summary>{t("createPage.historicalAdvanced")}</summary>
              <div className="formGrid threeColumns">
                <label>
                  {t("createPage.rebalanceSessions")}
                  <input
                    {...fieldAccessibility("rebalanceSessions")}
                    type="number"
                    min="1"
                    max="252"
                    value={rebalanceSessions}
                    onChange={(event) =>
                      setRebalanceSessions(event.target.value)
                    }
                    required
                  />
                </label>
                <label>
                  {t("createPage.maximumHoldings")}
                  <input
                    {...fieldAccessibility("maximumHoldings")}
                    type="number"
                    min="1"
                    max="100"
                    value={maximumHoldings}
                    onChange={(event) => setMaximumHoldings(event.target.value)}
                    required
                  />
                </label>
                <label>
                  {t("createPage.maxPositionWeight")}
                  <input
                    {...fieldAccessibility("maxPositionWeight")}
                    value={maxPositionWeight}
                    onChange={(event) =>
                      setMaxPositionWeight(event.target.value)
                    }
                    required
                  />
                </label>
                <label>
                  {t("createPage.maxDrawdown")}
                  <input
                    {...fieldAccessibility("maxDrawdown")}
                    value={maxDrawdown}
                    onChange={(event) => setMaxDrawdown(event.target.value)}
                    required
                  />
                </label>
                <label>
                  {t("createPage.universe")}
                  <select
                    value={universe}
                    onChange={(event) =>
                      setUniverse(event.target.value as typeof universe)
                    }
                  >
                    <option value="ALL">{t("createPage.allShares")}</option>
                    <option value="SSE">SSE</option>
                    <option value="SZSE">SZSE</option>
                  </select>
                </label>
                <label>
                  {t("createPage.commissionRate")}
                  <input
                    {...fieldAccessibility("commissionRate")}
                    value={commissionRate}
                    onChange={(event) => setCommissionRate(event.target.value)}
                    required
                  />
                </label>
                <label>
                  {t("createPage.minimumCommission")}
                  <input
                    {...fieldAccessibility("minimumCommission")}
                    value={minimumCommission}
                    onChange={(event) =>
                      setMinimumCommission(event.target.value)
                    }
                    required
                  />
                </label>
              </div>
              <p className="fieldHint">
                {t("createPage.commissionAssumption")}
              </p>
            </details>
          </fieldset>
        )}
        {error && (
          <div id="paper-form-error" className="formError" role="alert">
            {t(error)}
          </div>
        )}
        <div className="formActions">
          <button className="button buttonPrimary" aria-disabled={pending}>
            {pending ? t("createPage.creating") : t("createPage.submit")}
          </button>
          {canCreateAnother && !sourceSession && (
            <button type="submit" value="another" aria-disabled={pending}>
              {t("createPage.createAnother")}
            </button>
          )}
          <span>{t("createPage.idempotentHint")}</span>
        </div>
      </form>
    </>
  );
}
