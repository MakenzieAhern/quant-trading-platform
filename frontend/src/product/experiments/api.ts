import { apiRequest } from "../../api/client";
import { ApiContractError } from "../../api/contracts";
import type {
  Capabilities,
  Experiment,
  ExperimentConfiguration,
  ExperimentDecision,
  ExperimentEquity,
  ExperimentResult,
  ExperimentTrade,
  Page,
} from "./types";

function record(value: unknown): Record<string, unknown> {
  if (!value || typeof value !== "object" || Array.isArray(value))
    throw new ApiContractError();
  return value as Record<string, unknown>;
}
function text(value: unknown): asserts value is string {
  if (typeof value !== "string") throw new ApiContractError();
}
function integer(value: unknown): asserts value is number {
  if (!Number.isSafeInteger(value) || Number(value) < 0)
    throw new ApiContractError();
}
function decimal(value: unknown, nullable = false) {
  if (nullable && value === null) return;
  if (typeof value !== "string" || !/^-?\d+(?:\.\d+)?$/.test(value))
    throw new ApiContractError();
}
function strings(value: unknown): asserts value is string[] {
  if (!Array.isArray(value) || value.some((item) => typeof item !== "string"))
    throw new ApiContractError();
}
function mode(value: unknown) {
  if (value !== "historical_exploration" && value !== "synthetic_demo")
    throw new ApiContractError();
}
export function parseConfiguration(value: unknown): ExperimentConfiguration {
  const item = record(value);
  for (const key of [
    "name",
    "dataset_id",
    "strategy_id",
    "start_date",
    "end_date",
  ])
    text(item[key]);
  decimal(item.initial_cash);
  if (!["ALL", "SSE", "SZSE"].includes(String(item.universe)))
    throw new ApiContractError();
  const strategy = record(item.strategy);
  integer(strategy.rebalance_sessions);
  integer(strategy.maximum_holdings);
  const costs = record(item.costs);
  decimal(costs.commission_rate);
  decimal(costs.minimum_commission);
  const risk = record(item.risk);
  decimal(risk.max_drawdown);
  decimal(risk.max_position_weight);
  return item as unknown as ExperimentConfiguration;
}
export function parseCapabilities(value: unknown): Capabilities {
  const item = record(value);
  if (!Array.isArray(item.strategies) || !Array.isArray(item.datasets))
    throw new ApiContractError();
  for (const entry of item.strategies) {
    const strategy = record(entry);
    for (const key of [
      "strategy_id",
      "version",
      "name_en",
      "name_zh",
      "description_en",
      "description_zh",
    ])
      text(strategy[key]);
    strings(strategy.limitations);
    const parameters = record(strategy.parameters);
    for (const key of ["rebalance_sessions", "maximum_holdings"]) {
      const limits = record(parameters[key]);
      integer(limits.min);
      integer(limits.max);
      integer(limits.default);
    }
  }
  for (const entry of item.datasets) {
    const dataset = record(entry);
    for (const key of [
      "dataset_id",
      "coverage_start",
      "coverage_end",
      "default_start",
      "default_end",
      "benchmark_id",
    ])
      text(dataset[key]);
    for (const key of ["sha256", "as_of"])
      if (dataset[key] !== null) text(dataset[key]);
    mode(dataset.mode);
    integer(dataset.security_count);
    strings(dataset.universes);
    if (typeof dataset.available !== "boolean") throw new ApiContractError();
    if (dataset.reason_code !== null) text(dataset.reason_code);
  }
  const defaults = record(item.defaults);
  for (const key of [
    "initial_cash",
    "commission_rate",
    "minimum_commission",
    "max_drawdown",
  ])
    decimal(defaults[key]);
  return item as unknown as Capabilities;
}
export function parseExperiment(value: unknown): Experiment {
  const item = record(value);
  for (const key of [
    "job_id",
    "name",
    "dataset_id",
    "dataset_sha256",
    "configuration_sha256",
    "strategy_version",
    "created_at",
    "phase",
  ])
    text(item[key]);
  for (const key of ["started_at", "completed_at", "error_code", "retry_of"])
    if (item[key] !== null) text(item[key]);
  mode(item.mode);
  if (
    ![
      "QUEUED",
      "RUNNING",
      "SUCCEEDED",
      "FAILED",
      "CANCELLED",
      "INTERRUPTED",
    ].includes(String(item.status))
  )
    throw new ApiContractError();
  integer(item.completed_sessions);
  integer(item.attempt);
  if (item.total_sessions !== null) integer(item.total_sessions);
  if (
    typeof item.cancel_requested !== "boolean" ||
    typeof item.result_available !== "boolean"
  )
    throw new ApiContractError();
  parseConfiguration(item.configuration);
  return item as unknown as Experiment;
}
export function parseResult(value: unknown): ExperimentResult {
  const item = record(value);
  mode(item.mode);
  strings(item.limitations);
  for (const key of ["job_id", "date_start", "date_end", "benchmark_id"])
    text(item[key]);
  const metrics = record(item.metrics);
  for (const key of [
    "initial_capital",
    "final_equity",
    "cumulative_return",
    "maximum_drawdown",
    "transaction_costs",
    "benchmark_return",
    "excess_return",
    "sharpe_ratio",
  ])
    decimal(metrics[key], true);
  integer(metrics.number_of_trades);
  integer(metrics.number_of_fills);
  const execution = record(item.execution);
  for (const key of ["proposals", "approved_decisions", "orders", "fills"])
    integer(execution[key]);
  for (const count of Object.values(record(execution.reason_counts)))
    integer(count);
  return item as unknown as ExperimentResult;
}
function page<T>(value: unknown, parse: (entry: unknown) => T): Page<T> {
  const item = record(value);
  if (!Array.isArray(item.items)) throw new ApiContractError();
  integer(item.total);
  integer(item.limit);
  integer(item.offset);
  return {
    items: item.items.map(parse),
    total: item.total,
    limit: item.limit,
    offset: item.offset,
  };
}
function equity(value: unknown): ExperimentEquity {
  const item = record(value);
  integer(item.sequence);
  text(item.trading_date);
  decimal(item.equity);
  decimal(item.benchmark, true);
  decimal(item.drawdown, true);
  return item as unknown as ExperimentEquity;
}
function trade(value: unknown): ExperimentTrade {
  const item = record(value);
  integer(item.sequence);
  for (const key of ["order_id", "security_id", "side", "timestamp"])
    text(item[key]);
  for (const key of ["quantity", "price", "transaction_cost"])
    decimal(item[key]);
  return item as unknown as ExperimentTrade;
}
function decision(value: unknown): ExperimentDecision {
  const item = record(value);
  integer(item.sequence);
  for (const key of [
    "proposal_id",
    "security_id",
    "reason_code",
    "message",
    "timestamp",
  ])
    text(item[key]);
  if (typeof item.approved !== "boolean") throw new ApiContractError();
  return item as unknown as ExperimentDecision;
}
const path = (id: string) => `/api/experiments/${encodeURIComponent(id)}`;
export const experimentApi = {
  capabilities: (signal?: AbortSignal) =>
    apiRequest("/api/workbench/capabilities", {}, signal, parseCapabilities),
  list: (signal?: AbortSignal, limit = 20, offset = 0) =>
    apiRequest(
      `/api/experiments?limit=${limit}&offset=${offset}`,
      {},
      signal,
      (value) => page(value, parseExperiment),
    ),
  get: (id: string, signal?: AbortSignal) =>
    apiRequest(path(id), {}, signal, parseExperiment),
  create: (body: ExperimentConfiguration, key: string) =>
    apiRequest(
      "/api/experiments",
      {
        method: "POST",
        headers: { "Content-Type": "application/json", "Idempotency-Key": key },
        body: JSON.stringify(body),
      },
      undefined,
      parseExperiment,
    ),
  cancel: (id: string) =>
    apiRequest(
      `${path(id)}/cancel`,
      { method: "POST" },
      undefined,
      parseExperiment,
    ),
  retry: (id: string, key: string) =>
    apiRequest(
      `${path(id)}/retry`,
      { method: "POST", headers: { "Idempotency-Key": key } },
      undefined,
      parseExperiment,
    ),
  result: (id: string, signal?: AbortSignal) =>
    apiRequest(`${path(id)}/result`, {}, signal, parseResult),
  equity: (id: string, signal?: AbortSignal, offset = 0) =>
    apiRequest(
      `${path(id)}/equity?limit=100&offset=${offset}`,
      {},
      signal,
      (value) => page(value, equity),
    ),
  trades: (id: string, signal?: AbortSignal, offset = 0) =>
    apiRequest(
      `${path(id)}/trades?limit=20&offset=${offset}`,
      {},
      signal,
      (value) => page(value, trade),
    ),
  decisions: (id: string, signal?: AbortSignal, offset = 0) =>
    apiRequest(
      `${path(id)}/decisions?limit=20&offset=${offset}`,
      {},
      signal,
      (value) => page(value, decision),
    ),
};
