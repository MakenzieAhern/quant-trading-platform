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

type ReplayRequest = Extract<
  CreatePaperSessionRequest,
  { provider_type: "replay" }
>;
type StrategyType = ReplayRequest["strategy"]["type"];
type ProviderType = CreatePaperSessionRequest["provider_type"];

export function CreatePaperSessionPage() {
  const { t } = useTranslation("paper");
  const [providerType, setProviderType] = useState<ProviderType>("replay");
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
    } else if (strategyType === "moving_average_crossover") {
      const short = parsePositiveInteger(shortPeriod);
      const long = parsePositiveInteger(longPeriod);
      if (short === null || long === null || short >= long) {
        setError(t("createPage.periodError"));
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
        setError(t("createPage.rsiError"));
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
              <select
                value={providerType}
                onChange={(event) => {
                  const value = event.target.value as ProviderType;
                  setProviderType(value);
                  setInitialCash(
                    value === "simulated_a_share" ? "100000000" : "100000",
                  );
                  setQuantity(value === "simulated_a_share" ? "1" : "10");
                }}
              >
                <option value="simulated_a_share">
                  {t("createPage.aShareSimulation")}
                </option>
                <option value="replay">{t("createPage.replayLocal")}</option>
              </select>
            </label>
            <label>
              {t("createPage.dataset")}
              <input
                value={
                  providerType === "simulated_a_share"
                    ? "CN_A_SIMULATED_PAPER_FIXTURE_V1"
                    : "AAPL_fixture"
                }
                readOnly
              />
            </label>
            <label>
              {t("createPage.symbol")}
              <input
                value={providerType === "simulated_a_share" ? "CN-A" : "AAPL"}
                readOnly
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
              : t("createPage.buyingPowerHint")}
          </p>
        </fieldset>
        <fieldset disabled={pending}>
          <legend>{t("createPage.registeredStrategy")}</legend>
          {providerType === "simulated_a_share" ? (
            <label>
              {t("createPage.strategyType")}
              <input
                value={t("strategies.cn_a_cross_sectional_momentum_low_vol_v1")}
                readOnly
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
