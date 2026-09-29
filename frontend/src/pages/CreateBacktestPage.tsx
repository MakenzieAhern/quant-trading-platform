import { useEffect, useRef, useState, type FormEvent } from "react";
import { useTranslation } from "react-i18next";

import { backtestsApi } from "../api/backtests";
import { ApiError } from "../api/client";
import { Link } from "../components/Link";
import type { CreateBacktestRequest } from "../types/backtests";
import {
  comparePositiveDecimals,
  isPositiveDecimal,
  parsePositiveInteger,
} from "../utils/format";
import { navigate } from "../utils/navigation";

type StrategyType = CreateBacktestRequest["strategy"]["type"];

export function CreateBacktestPage() {
  const { t } = useTranslation("backtests");
  const [strategyType, setStrategyType] = useState<StrategyType>(
    "moving_average_crossover",
  );
  const [initialCash, setInitialCash] = useState("100000");
  const [quantity, setQuantity] = useState("10");
  const [buyingPower, setBuyingPower] = useState(false);
  const [maxNotional, setMaxNotional] = useState("");
  const [shortPeriod, setShortPeriod] = useState("2");
  const [longPeriod, setLongPeriod] = useState("3");
  const [rsiPeriod, setRsiPeriod] = useState("14");
  const [oversold, setOversold] = useState("30");
  const [overbought, setOverbought] = useState("70");
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | Error | null>(null);
  const requestKey = useRef<string | null>(null);
  const submissionLocked = useRef(false);
  const active = useRef(true);

  useEffect(() => {
    active.current = true;
    return () => {
      active.current = false;
    };
  }, []);

  const changed = () => {
    requestKey.current = null;
    setError(null);
  };

  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (submissionLocked.current) return;
    setError(null);
    if (maxNotional && !isPositiveDecimal(maxNotional)) {
      setError("createPage.maxNotionalError");
      return;
    }
    if (!isPositiveDecimal(initialCash) || !isPositiveDecimal(quantity)) {
      setError("createPage.decimalError");
      return;
    }
    let strategy: CreateBacktestRequest["strategy"];
    if (strategyType === "moving_average_crossover") {
      const short = parsePositiveInteger(shortPeriod);
      const long = parsePositiveInteger(longPeriod);
      if (short === null || long === null || short >= long) {
        setError("createPage.periodError");
        return;
      }
      strategy = {
        type: strategyType,
        parameters: { short_period: short, long_period: long },
      };
    } else {
      const period = parsePositiveInteger(rsiPeriod);
      const thresholdOrder = comparePositiveDecimals(oversold, overbought);
      const upperBound = comparePositiveDecimals(overbought, "100");
      if (
        period === null ||
        !isPositiveDecimal(oversold) ||
        !isPositiveDecimal(overbought) ||
        thresholdOrder !== -1 ||
        upperBound !== -1
      ) {
        setError("createPage.rsiError");
        return;
      }
      strategy = {
        type: strategyType,
        parameters: { rsi_period: period, oversold, overbought },
      };
    }
    const payload: CreateBacktestRequest = {
      dataset_id: "AAPL_fixture",
      symbol: "AAPL",
      initial_cash: initialCash,
      default_order_quantity: quantity,
      strategy,
      ...(buyingPower || maxNotional
        ? {
            risk: {
              enforce_buying_power: buyingPower,
              ...(maxNotional ? { max_order_notional: maxNotional } : {}),
            },
          }
        : {}),
    };

    requestKey.current ??= crypto.randomUUID();
    submissionLocked.current = true;
    setPending(true);
    const originatingUrl = window.location.href;
    try {
      const created = await backtestsApi.create(payload, requestKey.current);
      if (active.current && window.location.href === originatingUrl)
        navigate(`/backtests/${created.run_id}`);
    } catch (reason) {
      if (active.current)
        setError(reason instanceof Error ? reason : "createPage.submitError");
    } finally {
      submissionLocked.current = false;
      if (active.current) setPending(false);
    }
  };

  const errorKey =
    typeof error === "string"
      ? error
      : error instanceof ApiError && error.status === 409
        ? "createPage.conflictError"
        : error instanceof ApiError && error.status === 422
          ? "createPage.validationError"
          : error instanceof ApiError && error.status >= 500
            ? "createPage.executionError"
            : error instanceof ApiError &&
                (error.status === 401 || error.status === 403)
              ? "common:loadErrors.permission"
              : error instanceof ApiError && error.status === 404
                ? "createPage.unavailableError"
                : error instanceof ApiError && error.status === 408
                  ? "createPage.timeoutError"
                  : error instanceof TypeError
                    ? "createPage.offlineError"
                    : "createPage.submitError";

  return (
    <>
      <header className="pageHeader compactHeader">
        <div>
          <p className="eyebrow">{t("createPage.eyebrow")}</p>
          <h1>{t("createPage.title")}</h1>
          <p>{t("createPage.description")}</p>
        </div>
        <Link className="button" href="/backtests">
          {t("createPage.cancel")}
        </Link>
      </header>
      <form
        className="formPanel"
        onSubmit={(event) => void submit(event)}
        onChange={changed}
        aria-describedby={error ? "form-error" : undefined}
      >
        <fieldset disabled={pending}>
          <legend>{t("createPage.dataset")}</legend>
          <div className="formGrid">
            <label>
              {t("createPage.dataset")}
              <select name="dataset" value="AAPL_fixture" disabled>
                <option value="AAPL_fixture">{t("createPage.fixture")}</option>
              </select>
              <small>{t("createPage.registryId")}: AAPL_fixture</small>
            </label>
            <label>
              {t("createPage.symbol")}
              <input name="symbol" value="AAPL" readOnly tabIndex={-1} />
            </label>
          </div>
        </fieldset>
        <fieldset disabled={pending}>
          <legend>{t("createPage.capitalSizing")}</legend>
          <div className="formGrid">
            <label>
              {t("createPage.initialCash")}
              <input
                name="initial_cash"
                inputMode="decimal"
                value={initialCash}
                onChange={(event) => setInitialCash(event.target.value)}
                required
              />
            </label>
            <label>
              {t("createPage.quantity")}
              <input
                name="default_order_quantity"
                inputMode="decimal"
                value={quantity}
                onChange={(event) => setQuantity(event.target.value)}
                required
              />
            </label>
          </div>
          <p className="fieldHint">{t("createPage.decimalHint")}</p>
        </fieldset>
        <fieldset disabled={pending}>
          <legend>{t("createPage.strategy")}</legend>
          <label>
            {t("createPage.strategyType")}
            <select
              name="strategy_type"
              value={strategyType}
              onChange={(event) =>
                setStrategyType(event.target.value as StrategyType)
              }
            >
              <option value="moving_average_crossover">
                {t("createPage.movingAverage")}
              </option>
              <option value="rsi_mean_reversion">
                {t("createPage.rsiMean")}
              </option>
            </select>
          </label>
          {strategyType === "moving_average_crossover" ? (
            <div className="formGrid">
              <label>
                {t("createPage.shortPeriod")}
                <input
                  name="short_period"
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
                  name="long_period"
                  type="number"
                  min="2"
                  step="1"
                  value={longPeriod}
                  onChange={(event) => setLongPeriod(event.target.value)}
                  required
                />
              </label>
            </div>
          ) : (
            <div className="formGrid threeColumns">
              <label>
                {t("createPage.rsiPeriod")}
                <input
                  name="rsi_period"
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
                  name="oversold"
                  inputMode="decimal"
                  value={oversold}
                  onChange={(event) => setOversold(event.target.value)}
                  required
                />
              </label>
              <label>
                {t("createPage.overbought")}
                <input
                  name="overbought"
                  inputMode="decimal"
                  value={overbought}
                  onChange={(event) => setOverbought(event.target.value)}
                  required
                />
              </label>
            </div>
          )}
        </fieldset>
        <fieldset disabled={pending}>
          <legend>{t("createPage.riskControls")}</legend>
          <label>
            <input
              type="checkbox"
              checked={buyingPower}
              onChange={(event) => setBuyingPower(event.target.checked)}
            />
            {t("createPage.buyingPower")}
          </label>
          <label>
            {t("createPage.maxNotional")}
            <input
              inputMode="decimal"
              value={maxNotional}
              onChange={(event) => setMaxNotional(event.target.value)}
            />
          </label>
          <p className="fieldHint">{t("createPage.riskHint")}</p>
        </fieldset>
        {error && (
          <div id="form-error" className="formError" role="alert">
            <p>
              {t(errorKey, {
                message: error instanceof Error ? error.message : "",
              })}
            </p>
            {error instanceof Error && (
              <>
                <p>{t("createPage.recoveryHint")}</p>
                <details>
                  <summary>{t("common:loadErrors.diagnostic")}</summary>
                  <code>{error.message}</code>
                </details>
              </>
            )}
          </div>
        )}
        <div className="formActions">
          <button
            className="button buttonPrimary"
            type="submit"
            aria-disabled={pending}
          >
            {pending ? t("createPage.running") : t("createPage.run")}
          </button>
          <span>{t("createPage.idempotencyHint")}</span>
        </div>
      </form>
    </>
  );
}
