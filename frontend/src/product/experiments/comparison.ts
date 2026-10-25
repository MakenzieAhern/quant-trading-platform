import type { Experiment, ExperimentResult } from "./types";

export const comparisonUrl = (ids: string[]) =>
  `/experiments/compare?ids=${ids.join(",")}`;

export function parseComparisonIds(search: string): string[] | null {
  const ids = new URLSearchParams(search)
    .get("ids")
    ?.split(",")
    .map((id) => id.trim().toLowerCase());
  return ids &&
    ids.length >= 2 &&
    ids.length <= 3 &&
    new Set(ids).size === ids.length &&
    ids.every((id) =>
      /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/.test(id),
    )
    ? ids
    : null;
}

// Equality only: spelling differences such as 100.0/100 never use floating point.
export function comparableDecimal(value: string): string {
  const negative = value.startsWith("-");
  const [integer, fraction = ""] = value.replace(/^-/, "").split(".");
  const whole = integer.replace(/^0+(?=\d)/, "");
  const tail = fraction.replace(/0+$/, "");
  const zero = !/[1-9]/.test(whole + tail);
  return `${negative && !zero ? "-" : ""}${whole}${tail ? `.${tail}` : ""}`;
}

export function comparisonConditions(
  job: Experiment,
  result: Pick<ExperimentResult, "date_start" | "date_end">,
): Record<"data" | "period" | "costs" | "cash" | "risk" | "strategy", string> {
  const { configuration: c } = job;
  return {
    data: JSON.stringify([
      job.mode,
      job.dataset_id,
      job.dataset_sha256,
      c.universe,
    ]),
    period: JSON.stringify([
      c.start_date,
      c.end_date,
      result.date_start,
      result.date_end,
    ]),
    costs: JSON.stringify([
      comparableDecimal(c.costs.commission_rate),
      comparableDecimal(c.costs.minimum_commission),
    ]),
    cash: comparableDecimal(c.initial_cash),
    risk: JSON.stringify([
      comparableDecimal(c.risk.max_drawdown),
      comparableDecimal(c.risk.max_position_weight),
    ]),
    strategy: JSON.stringify([
      c.strategy_id,
      job.strategy_version,
      c.strategy.rebalance_sessions,
      c.strategy.maximum_holdings,
    ]),
  };
}
