import { useRef, useState, type FormEvent } from "react";

import { backtestsApi } from "../api/backtests";
import { ApiError } from "../api/client";
import { Link } from "../components/Link";
import type { CreateBacktestRequest } from "../types/backtests";
import { isPositiveDecimal } from "../utils/format";
import { navigate } from "../utils/navigation";

type StrategyType = CreateBacktestRequest["strategy"]["type"];

export function CreateBacktestPage() {
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
  const requestKey = useRef<string | null>(null);
  const submissionLocked = useRef(false);

  const changed = () => {
    requestKey.current = null;
    setError(null);
  };

  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (submissionLocked.current) return;
    setError(null);
    if (!isPositiveDecimal(initialCash) || !isPositiveDecimal(quantity)) {
      setError(
        "Initial cash and order quantity must be positive decimal strings.",
      );
      return;
    }
    const payload: CreateBacktestRequest = {
      dataset_id: "AAPL_fixture",
      symbol: "AAPL",
      initial_cash: initialCash,
      default_order_quantity: quantity,
      strategy:
        strategyType === "moving_average_crossover"
          ? {
              type: strategyType,
              parameters: {
                short_period: Number(shortPeriod),
                long_period: Number(longPeriod),
              },
            }
          : {
              type: strategyType,
              parameters: {
                rsi_period: Number(rsiPeriod),
                oversold,
                overbought,
              },
            },
    };
    if (
      strategyType === "moving_average_crossover" &&
      Number(shortPeriod) >= Number(longPeriod)
    ) {
      setError("Short period must be less than long period.");
      return;
    }
    if (
      strategyType === "rsi_mean_reversion" &&
      (!isPositiveDecimal(oversold) ||
        !isPositiveDecimal(overbought) ||
        Number(oversold) >= Number(overbought))
    ) {
      setError("RSI oversold must be a positive value below overbought.");
      return;
    }

    requestKey.current ??= crypto.randomUUID();
    submissionLocked.current = true;
    setPending(true);
    try {
      const created = await backtestsApi.create(payload, requestKey.current);
      navigate(`/backtests/${created.run_id}`);
    } catch (reason) {
      if (reason instanceof ApiError && reason.status === 409) {
        setError(`Duplicate request conflict: ${reason.message}`);
      } else if (reason instanceof ApiError && reason.status === 422) {
        setError(`Validation failed: ${reason.message}`);
      } else if (reason instanceof ApiError && reason.status >= 500) {
        setError(
          "Backtest execution failed safely. Check run history for a failed run.",
        );
      } else {
        setError(
          reason instanceof Error
            ? reason.message
            : "Unable to submit the backtest.",
        );
      }
    } finally {
      submissionLocked.current = false;
      setPending(false);
    }
  };

  return (
    <>
      <header className="pageHeader compactHeader">
        <div>
          <p className="eyebrow">NEW RESEARCH RUN</p>
          <h1>Create backtest</h1>
          <p>
            Inputs map directly to the approved Phase 7 dataset and strategy
            contracts.
          </p>
        </div>
        <Link className="button" href="/backtests">
          Cancel
        </Link>
      </header>
      <form
        className="formPanel"
        onSubmit={(event) => void submit(event)}
        onChange={changed}
      >
        <fieldset disabled={pending}>
          <legend>Dataset</legend>
          <div className="formGrid">
            <label>
              Dataset
              <select name="dataset" value="AAPL_fixture" disabled>
                <option value="AAPL_fixture">AAPL fixture</option>
              </select>
              <small>Registry ID: AAPL_fixture</small>
            </label>
            <label>
              Symbol
              <input name="symbol" value="AAPL" readOnly />
            </label>
          </div>
        </fieldset>
        <fieldset disabled={pending}>
          <legend>Capital &amp; sizing</legend>
          <div className="formGrid">
            <label>
              Initial cash
              <input
                name="initial_cash"
                inputMode="decimal"
                value={initialCash}
                onChange={(event) => setInitialCash(event.target.value)}
                required
              />
            </label>
            <label>
              Default order quantity
              <input
                name="default_order_quantity"
                inputMode="decimal"
                value={quantity}
                onChange={(event) => setQuantity(event.target.value)}
                required
              />
            </label>
          </div>
          <p className="fieldHint">
            Exact Decimal strings are sent to the API; browser-visible values
            are never used for portfolio calculations.
          </p>
        </fieldset>
        <fieldset disabled={pending}>
          <legend>Strategy</legend>
          <label>
            Strategy type
            <select
              name="strategy_type"
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
                Long period
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
                RSI period
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
                Oversold
                <input
                  name="oversold"
                  inputMode="decimal"
                  value={oversold}
                  onChange={(event) => setOversold(event.target.value)}
                  required
                />
              </label>
              <label>
                Overbought
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
        {error && (
          <div className="formError" role="alert">
            {error}
          </div>
        )}
        <div className="formActions">
          <button
            className="button buttonPrimary"
            type="submit"
            disabled={pending}
          >
            {pending ? "Running backtest…" : "Run backtest"}
          </button>
          <span>
            Submission uses an Idempotency-Key to prevent duplicate runs.
          </span>
        </div>
      </form>
    </>
  );
}
