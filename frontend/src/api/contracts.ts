import type {
  BacktestResult,
  BacktestRun,
  BacktestStatus,
  CreateBacktestResponse,
  EquityPoint,
  Fill,
  Metrics,
  Order,
  Page,
  RiskDecision,
  Signal,
} from "../types/backtests";

const DECIMAL = /^-?\d+(?:\.\d+)?$/;
const STATUSES = new Set<BacktestStatus>([
  "CREATED",
  "RUNNING",
  "SUCCEEDED",
  "FAILED",
]);

export class ApiContractError extends Error {
  constructor() {
    super("The API response did not match the expected contract.");
    this.name = "ApiContractError";
  }
}

function record(value: unknown): Record<string, unknown> {
  if (typeof value !== "object" || value === null || Array.isArray(value))
    throw new ApiContractError();
  return value as Record<string, unknown>;
}

function string(value: unknown): asserts value is string {
  if (typeof value !== "string") throw new ApiContractError();
}

function nullableString(value: unknown): asserts value is string | null {
  if (value !== null) string(value);
}

function decimal(value: unknown): asserts value is string {
  string(value);
  if (!DECIMAL.test(value)) throw new ApiContractError();
}

function nullableDecimal(value: unknown): asserts value is string | null {
  if (value !== null) decimal(value);
}

function utc(value: unknown): asserts value is string {
  string(value);
  if (!/(?:Z|[+-]\d{2}:\d{2})$/.test(value) || Number.isNaN(Date.parse(value)))
    throw new ApiContractError();
}

function nullableUtc(value: unknown): asserts value is string | null {
  if (value !== null) utc(value);
}

function integer(value: unknown): asserts value is number {
  if (!Number.isSafeInteger(value) || (value as number) < 0)
    throw new ApiContractError();
}

function status(value: unknown): asserts value is BacktestStatus {
  if (typeof value !== "string" || !STATUSES.has(value as BacktestStatus))
    throw new ApiContractError();
}

export function parseMetrics(value: unknown): Metrics {
  const item = record(value);
  for (const key of [
    "initial_equity",
    "final_equity",
    "total_return",
    "max_drawdown",
    "total_commission",
  ] as const)
    decimal(item[key]);
  for (const key of ["cagr", "sharpe_ratio", "sortino_ratio"] as const)
    nullableDecimal(item[key]);
  integer(item.number_of_fills);
  return item as unknown as Metrics;
}

export function parseRun(value: unknown): BacktestRun {
  const item = record(value);
  for (const key of ["run_id", "strategy_id", "symbol", "dataset_id"] as const)
    string(item[key]);
  status(item.status);
  if (
    item.strategy_type !== "moving_average_crossover" &&
    item.strategy_type !== "rsi_mean_reversion"
  )
    throw new ApiContractError();
  record(item.strategy_parameters);
  record(item.risk);
  record(item.links);
  decimal(item.initial_cash);
  decimal(item.default_order_quantity);
  utc(item.created_at);
  for (const key of ["started_at", "completed_at", "start", "end"] as const)
    nullableUtc(item[key]);
  nullableString(item.error_message);
  if (item.metrics !== null) parseMetrics(item.metrics);
  return item as unknown as BacktestRun;
}

export function parseCreate(value: unknown): CreateBacktestResponse {
  const item = record(value);
  string(item.run_id);
  status(item.status);
  record(item.links);
  return item as unknown as CreateBacktestResponse;
}

export function parseResult(value: unknown): BacktestResult {
  const item = record(value);
  string(item.run_id);
  status(item.status);
  parseMetrics(item.metrics);
  for (const key of [
    "signal_count",
    "proposal_count",
    "risk_decision_count",
    "risk_rejection_count",
    "order_count",
    "fill_count",
    "snapshot_count",
    "reservation_count",
  ] as const)
    integer(item[key]);
  nullableUtc(item.start_time);
  nullableUtc(item.end_time);
  return item as unknown as BacktestResult;
}

function parseSignal(value: unknown): Signal {
  const item = record(value);
  for (const key of ["strategy_id", "symbol", "signal_type"] as const)
    string(item[key]);
  utc(item.timestamp);
  return item as unknown as Signal;
}

function parseRiskDecision(value: unknown): RiskDecision {
  const item = record(value);
  for (const key of ["proposal_id", "reason_code", "message"] as const)
    string(item[key]);
  if (
    typeof item.approved !== "boolean" ||
    typeof item.risk_increasing !== "boolean"
  )
    throw new ApiContractError();
  utc(item.timestamp);
  for (const key of [
    "reference_price",
    "order_notional",
    "projected_position_quantity",
    "projected_symbol_exposure",
    "projected_gross_exposure",
    "projected_net_exposure",
    "projected_gross_leverage",
    "projected_cash",
    "estimated_transaction_cost",
  ] as const)
    nullableDecimal(item[key]);
  return item as unknown as RiskDecision;
}

function parseOrder(value: unknown): Order {
  const item = record(value);
  for (const key of [
    "order_id",
    "strategy_id",
    "symbol",
    "side",
    "order_type",
    "status",
  ] as const)
    string(item[key]);
  decimal(item.quantity);
  nullableDecimal(item.price);
  utc(item.created_at);
  return item as unknown as Order;
}

function parseFill(value: unknown): Fill {
  const item = record(value);
  for (const key of ["order_id", "strategy_id", "symbol", "side"] as const)
    string(item[key]);
  for (const key of ["quantity", "price", "commission"] as const)
    decimal(item[key]);
  utc(item.timestamp);
  return item as unknown as Fill;
}

function parseEquity(value: unknown): EquityPoint {
  const item = record(value);
  utc(item.timestamp);
  for (const key of ["equity", "cash", "market_value"] as const)
    decimal(item[key]);
  return item as unknown as EquityPoint;
}

function page<T>(value: unknown, parseItem: (item: unknown) => T): Page<T> {
  const result = record(value);
  if (!Array.isArray(result.items)) throw new ApiContractError();
  integer(result.limit);
  integer(result.offset);
  integer(result.total);
  return {
    items: result.items.map(parseItem),
    limit: result.limit,
    offset: result.offset,
    total: result.total,
  };
}

export const parseRunPage = (value: unknown) => page(value, parseRun);
export const parseSignalPage = (value: unknown) => page(value, parseSignal);
export const parseRiskDecisionPage = (value: unknown) =>
  page(value, parseRiskDecision);
export const parseOrderPage = (value: unknown) => page(value, parseOrder);
export const parseFillPage = (value: unknown) => page(value, parseFill);
export const parseEquityPage = (value: unknown) => page(value, parseEquity);
