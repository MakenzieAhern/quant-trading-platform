import { useRef, useState, type FormEvent } from "react";

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
      setError("Initial cash and quantity must be positive Decimal strings.");
      return;
    }
    let strategy: CreatePaperSessionRequest["strategy"];
    if (strategyType === "moving_average_crossover") {
      const short = parsePositiveInteger(shortPeriod);
      const long = parsePositiveInteger(longPeriod);
      if (short === null || long === null || short >= long) {
        setError(
          "Periods must be safe positive integers with short below long.",
        );
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
        setError("RSI values must satisfy 0 < oversold < overbought < 100.");
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
        reason instanceof Error
          ? reason.message
          : "Unable to create paper session.",
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
          <p className="eyebrow">NEW LOCAL REPLAY</p>
          <h1>Create paper session</h1>
        </div>
        <Link className="button" href="/paper">
          Cancel
        </Link>
      </header>
      <form
        className="formPanel"
        onSubmit={(event) => void submit(event)}
        onChange={changed}
        aria-describedby={error ? "paper-form-error" : undefined}
      >
        <fieldset disabled={pending}>
          <legend>Safe provider</legend>
          <div className="formGrid threeColumns">
            <label>
              Provider
              <select value="replay" disabled>
                <option>Replay (local)</option>
              </select>
            </label>
            <label>
              Dataset
              <select value="AAPL_fixture" disabled>
                <option>AAPL fixture</option>
              </select>
            </label>
            <label>
              Symbol
              <input value="AAPL" readOnly />
            </label>
          </div>
        </fieldset>
        <fieldset disabled={pending}>
          <legend>Capital and sizing</legend>
          <div className="formGrid">
            <label>
              Initial cash
              <input
                value={initialCash}
                onChange={(event) => setInitialCash(event.target.value)}
                required
              />
            </label>
            <label>
              Order quantity
              <input
                value={quantity}
                onChange={(event) => setQuantity(event.target.value)}
                required
              />
            </label>
          </div>
          <p className="fieldHint">
            Buying-power risk enforcement is enabled. All values remain Decimal
            strings.
          </p>
        </fieldset>
        <fieldset disabled={pending}>
          <legend>Registered strategy</legend>
          <label>
            Strategy type
            <select
              value={strategyType}
              onChange={(event) =>
                setStrategyType(event.target.value as StrategyType)
              }
            >
              <option value="moving_average_crossover">
                Moving average crossover
              </option>
              <option value="rsi_mean_reversion">RSI mean reversion</option>
            </select>
          </label>
          {strategyType === "moving_average_crossover" ? (
            <div className="formGrid">
              <label>
                Short period
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
                Long period
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
                RSI period
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
                Oversold
                <input
                  value={oversold}
                  onChange={(event) => setOversold(event.target.value)}
                  required
                />
              </label>
              <label>
                Overbought
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
            {pending ? "Creating…" : "Create paper session"}
          </button>
          <span>Creation is idempotent and does not start execution.</span>
        </div>
      </form>
    </>
  );
}
