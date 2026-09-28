import { useRef, useState, type FormEvent } from "react";
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
import type { CreatePaperSessionRequest } from "../types/paper";
import {
  comparePositiveDecimals,
  isPositiveDecimal,
  parsePositiveInteger,
} from "../utils/format";
import { navigate } from "../utils/navigation";

type ReplayRequest = Extract<
  CreatePaperSessionRequest,
  { provider_type: "replay" }
>;
type StrategyType = ReplayRequest["strategy"]["type"];
type ProviderType = CreatePaperSessionRequest["provider_type"];

export function CreatePaperSessionPage() {
  const sourceId = new URLSearchParams(window.location.search).get(
    "from_experiment",
  );
  const validSourceId =
    sourceId &&
    /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(
      sourceId,
    )
      ? sourceId
      : null;
  const source = useApiResource(
    (signal) =>
      validSourceId
        ? experimentApi.get(validSourceId, signal)
        : Promise.resolve(null),
    [validSourceId],
  );
  const { t } = useTranslation("paper");
  if (sourceId && !validSourceId)
    return (
      <p role="alert">
        {t("createPage.sourceUnavailable")}{" "}
        <Link href="/experiments">{t("createPage.sourceList")}</Link>
      </p>
    );
  if (validSourceId && source.loading)
    return <LoadingPanel label={t("createPage.sourceLoading")} />;
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
  const job = source.data;
  if (validSourceId && !canUsePaperHandoff(job))
    return (
      <p role="alert">
        {t("createPage.sourceUnavailable")}{" "}
        <Link href="/experiments">{t("createPage.sourceList")}</Link>
      </p>
    );
  return <PaperSessionForm key={job?.job_id ?? "new"} sourceJob={job} />;
}

function PaperSessionForm({ sourceJob }: { sourceJob: Experiment | null }) {
  const { t } = useTranslation("paper");
  const sourceConfig = sourceJob?.configuration;
  const sourceRangeFits =
    sourceConfig &&
    Number.isFinite(Date.parse(sourceConfig.start_date)) &&
    Number.isFinite(Date.parse(sourceConfig.end_date)) &&
    Date.parse(sourceConfig.end_date) >= Date.parse(sourceConfig.start_date) &&
    Date.parse(sourceConfig.end_date) - Date.parse(sourceConfig.start_date) <=
      92 * 86_400_000;
  const [providerType, setProviderType] = useState<ProviderType>(
    sourceJob ? "historical_a_share" : "simulated_a_share",
  );
  const [strategyType, setStrategyType] = useState<StrategyType>(
    "moving_average_crossover",
  );
  const [initialCash, setInitialCash] = useState(
    sourceConfig?.initial_cash ?? "100000000",
  );
  const [quantity, setQuantity] = useState("1");
  const [shortPeriod, setShortPeriod] = useState("2");
  const [longPeriod, setLongPeriod] = useState("3");
  const [rsiPeriod, setRsiPeriod] = useState("14");
  const [oversold, setOversold] = useState("30");
  const [overbought, setOverbought] = useState("70");
  const [startDate, setStartDate] = useState(
    sourceRangeFits ? sourceConfig.start_date : sourceJob ? "" : "2011-03-01",
  );
  const [endDate, setEndDate] = useState(
    sourceConfig?.end_date ?? "2011-03-31",
  );
  const [rebalanceSessions, setRebalanceSessions] = useState(
    String(sourceConfig?.strategy.rebalance_sessions ?? 20),
  );
  const [maximumHoldings, setMaximumHoldings] = useState(
    String(sourceConfig?.strategy.maximum_holdings ?? 20),
  );
  const [maxPositionWeight, setMaxPositionWeight] = useState(
    sourceConfig?.risk.max_position_weight ?? "0.1",
  );
  const [maxDrawdown, setMaxDrawdown] = useState(
    sourceConfig?.risk.max_drawdown ?? "-0.2",
  );
  const [universe, setUniverse] = useState<"ALL" | "SSE" | "SZSE">(
    sourceConfig?.universe ?? "ALL",
  );
  const [commissionRate, setCommissionRate] = useState(
    sourceConfig?.costs.commission_rate ?? "0.0003",
  );
  const [minimumCommission, setMinimumCommission] = useState(
    sourceConfig?.costs.minimum_commission ?? "5",
  );
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const key = useRef<string | null>(null);
  const locked = useRef(false);

  const changed = () => {
    key.current = null;
    setError(null);
  };

  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (locked.current) return;
    setError(null);
    if (!isPositiveDecimal(initialCash) || !isPositiveDecimal(quantity)) {
      setError("createPage.decimalError");
      return;
    }
    if (
      providerType === "historical_a_share" &&
      comparePositiveDecimals(initialCash.trim(), "1000000000000") === 1
    ) {
      setError("createPage.historicalCashLimit");
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
      if (
        !startDate ||
        !endDate ||
        endDate < startDate ||
        !Number.isFinite(Date.parse(startDate)) ||
        !Number.isFinite(Date.parse(endDate)) ||
        Date.parse(endDate) - Date.parse(startDate) > 92 * 86_400_000 ||
        rebalance === null ||
        rebalance > 252 ||
        holdings === null ||
        holdings > 100 ||
        !isPositiveDecimal(maxPositionWeight) ||
        comparePositiveDecimals(maxPositionWeight, "1") === 1 ||
        !/^\d+(?:\.\d+)?$/.test(commissionRate) ||
        comparePositiveDecimals(commissionRate, "0.01") === 1 ||
        !/^\d+(?:\.\d+)?$/.test(minimumCommission) ||
        comparePositiveDecimals(minimumCommission, "1000") === 1 ||
        !/^-?0(?:\.\d+)?$|^-1(?:\.0+)?$/.test(maxDrawdown) ||
        (isPositiveDecimal(maxDrawdown) && maxDrawdown !== "0")
      ) {
        setError("createPage.historicalValidationError");
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
            rebalance_sessions: rebalance,
            maximum_holdings: holdings,
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
        setError("createPage.periodError");
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
        setError("createPage.rsiError");
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
    key.current ??= crypto.randomUUID();
    locked.current = true;
    setPending(true);
    try {
      const created = await paperApi.create(request, key.current);
      navigate(`/paper/${created.session_id}`);
    } catch (reason) {
      setError(
        reason instanceof ApiError &&
          (reason.status === 401 || reason.status === 403)
          ? "common:loadErrors.permission"
          : reason instanceof ApiError && reason.status === 404
            ? "createPage.datasetError"
            : reason instanceof ApiError && reason.status === 409
              ? "createPage.conflictError"
              : reason instanceof ApiError && reason.status === 422
                ? "createPage.validationError"
                : "createPage.submitError",
      );
    } finally {
      locked.current = false;
      setPending(false);
    }
  };

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
      <form
        className="formPanel"
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
                disabled={Boolean(sourceJob)}
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
                value={initialCash}
                onChange={(event) => setInitialCash(event.target.value)}
                required
              />
            </label>
            {providerType === "replay" && (
              <label>
                {t("createPage.orderQuantity")}
                <input
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
                  value={oversold}
                  onChange={(event) => setOversold(event.target.value)}
                  required
                />
              </label>
              <label>
                {t("createPage.overbought")}
                <input
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
                  type="date"
                  value={startDate}
                  onInput={(event) => setStartDate(event.currentTarget.value)}
                  required
                />
              </label>
              <label>
                {t("createPage.endDate")}
                <input
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
                    value={commissionRate}
                    onChange={(event) => setCommissionRate(event.target.value)}
                    required
                  />
                </label>
                <label>
                  {t("createPage.minimumCommission")}
                  <input
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
          <span>{t("createPage.idempotentHint")}</span>
        </div>
      </form>
    </>
  );
}
