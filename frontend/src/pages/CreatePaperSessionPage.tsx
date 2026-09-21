import { useRef, useState, type FormEvent } from "react";
import { useTranslation } from "react-i18next";

import { ApiError } from "../api/client";
import { paperApi } from "../api/paper";
import { Link } from "../components/Link";
import { PaperSafetyBanner } from "../components/PaperSafetyBanner";
import type { CreatePaperSessionRequest } from "../types/paper";
import {
  comparePositiveDecimals,
  isPositiveDecimal,
  parsePositiveInteger,
} from "../utils/format";
import { navigate } from "../utils/navigation";

type StrategyType = CreatePaperSessionRequest["strategy"]["type"];

export function CreatePaperSessionPage() {
  const { t } = useTranslation("paper");
  const [strategyType, setStrategyType] = useState<StrategyType>(
    "moving_average_crossover",
  );
  const [initialCash, setInitialCash] = useState("100000");
  const [quantity, setQuantity] = useState("10");
  const [shortPeriod, setShortPeriod] = useState("2");
  const [longPeriod, setLongPeriod] = useState("3");
  const [rsiPeriod, setRsiPeriod] = useState("14");
  const [oversold, setOversold] = useState("30");
  const [overbought, setOverbought] = useState("70");
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
      setError(t("createPage.decimalError"));
      return;
    }
    let strategy: CreatePaperSessionRequest["strategy"];
    if (strategyType === "moving_average_crossover") {
      const short = parsePositiveInteger(shortPeriod);
      const long = parsePositiveInteger(longPeriod);
      if (short === null || long === null || short >= long) {
        setError(t("createPage.periodError"));
        return;
      }
      strategy = {
        type: strategyType,
        parameters: { short_period: short, long_period: long },
      };
    } else {
      const period = parsePositiveInteger(rsiPeriod);
      if (
        period === null ||
        !isPositiveDecimal(oversold) ||
        comparePositiveDecimals(oversold, overbought) !== -1 ||
        comparePositiveDecimals(overbought, "100") !== -1
      ) {
        setError(t("createPage.rsiError"));
        return;
      }
      strategy = {
        type: strategyType,
        parameters: { rsi_period: period, oversold, overbought },
      };
    }
    key.current ??= crypto.randomUUID();
    locked.current = true;
    setPending(true);
    try {
      const created = await paperApi.create(
        {
          provider_type: "replay",
          dataset_id: "AAPL_fixture",
          symbol: "AAPL",
          strategy,
          initial_cash: initialCash,
          default_order_quantity: quantity,
          risk: { enforce_buying_power: true },
        },
        key.current,
      );
      navigate(`/paper/${created.session_id}`);
    } catch (reason) {
      setError(
        reason instanceof ApiError && reason.status === 404
          ? t("createPage.datasetError")
          : reason instanceof ApiError && reason.status === 409
            ? t("createPage.conflictError")
            : reason instanceof ApiError && reason.status === 422
              ? t("createPage.validationError")
              : t("createPage.submitError"),
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
              <select value="replay" disabled>
                <option>{t("createPage.replayLocal")}</option>
              </select>
            </label>
            <label>
              {t("createPage.dataset")}
              <select value="AAPL_fixture" disabled>
                <option>{t("createPage.fixture")}</option>
              </select>
            </label>
            <label>
              {t("createPage.symbol")}
              <input value="AAPL" readOnly />
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
            <label>
              {t("createPage.orderQuantity")}
              <input
                value={quantity}
                onChange={(event) => setQuantity(event.target.value)}
                required
              />
            </label>
          </div>
          <p className="fieldHint">{t("createPage.buyingPowerHint")}</p>
        </fieldset>
        <fieldset disabled={pending}>
          <legend>{t("createPage.registeredStrategy")}</legend>
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
          {strategyType === "moving_average_crossover" ? (
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
          ) : (
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
          )}
        </fieldset>
        {error && (
          <div id="paper-form-error" className="formError" role="alert">
            {error}
          </div>
        )}
        <div className="formActions">
          <button className="button buttonPrimary" disabled={pending}>
            {pending ? t("createPage.creating") : t("createPage.submit")}
          </button>
          <span>{t("createPage.idempotentHint")}</span>
        </div>
      </form>
    </>
  );
}
