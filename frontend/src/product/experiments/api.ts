import { ApiError, apiRequest, REQUEST_TIMEOUT_MS } from "../../api/client";
import { API_BASE_URL } from "../../api/config";
import { ApiContractError } from "../../api/contracts";
import type {
  Capabilities,
  Experiment,
  ExperimentConfiguration,
  ExperimentDecision,
  ExperimentEquity,
  ExperimentResult,
  ExperimentMode,
  ExperimentStatus,
  ExperimentTrade,
  ExperimentHolding,
  ExperimentCollection,
  DateRange,
  Page,
  SimulationPlan,
  PaperAccountPlan,
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
  if (item.simulation_plan !== undefined)
    parseSimulationPlan(item.simulation_plan);
  return item as unknown as ExperimentResult;
}
export function parseSimulationPlan(value: unknown): SimulationPlan {
  const item = record(value);
  parsePlanFields(item);
  if (
    item.submitted_to_account !== false ||
    !["EXPLORATORY_REPLAY", "SYNTHETIC_DEMO"].includes(
      String(item.account_mode),
    )
  )
    throw new ApiContractError();
  return item as unknown as SimulationPlan;
}

export function parsePaperAccountPlan(value: unknown): PaperAccountPlan {
  const item = record(value);
  parsePlanFields(item);
  text(item.paper_session_id);
  text(item.plan_version);
  if (
    item.mode !== "historical_exploration" ||
    item.account_mode !== "HISTORICAL_PAPER_REPLAY" ||
    ![
      "PAPER_ACCOUNT_PLAN_V1",
      "PAPER_ACCOUNT_PLAN_V2",
      "PAPER_ACCOUNT_PLAN_V3",
    ].includes(String(item.plan_version)) ||
    typeof item.submitted_to_account !== "boolean"
  )
    throw new ApiContractError();
  return item as unknown as PaperAccountPlan;
}

function parsePlanFields(item: Record<string, unknown>): void {
  mode(item.mode);
  if (item.account_snapshot_trading_date != null)
    text(item.account_snapshot_trading_date);
  for (const key of [
    "status",
    "as_of_trading_date",
    "dataset_sha256",
    "configuration_sha256",
    "strategy_id",
    "strategy_version",
    "price_basis",
    "account_mode",
    "data_snapshot_sha256",
  ])
    text(item[key]);
  if (item.next_accepted_session !== null) text(item.next_accepted_session);
  if (item.simulation_only !== true || item.not_today_advice !== true)
    throw new ApiContractError();
  decimal(item.estimated_cash_required, true);
  if (item.risk_rejections !== undefined) integer(item.risk_rejections);
  if (item.account !== null) {
    const account = record(item.account);
    decimal(account.cash);
    decimal(account.equity);
    text(account.snapshot_sha256);
    if (!Array.isArray(account.positions)) throw new ApiContractError();
    for (const entry of account.positions) {
      const position = record(entry);
      text(position.security_id);
      for (const key of [
        "quantity",
        "average_price",
        "market_price",
        "market_value",
      ])
        decimal(position[key]);
      decimal(position.weight, true);
    }
  }
  if (!Array.isArray(item.candidates)) throw new ApiContractError();
  for (const entry of item.candidates) {
    const candidate = record(entry);
    for (const key of ["security_id", "trigger_reason", "risk_reason_code"])
      text(candidate[key]);
    for (const key of [
      "target_weight",
      "held_quantity",
      "target_quantity",
      "desired_change_quantity",
      "proposed_quantity",
    ])
      decimal(candidate[key]);
    decimal(candidate.reference_raw_close, true);
    if (!["BUY", "SELL", "HOLD"].includes(String(candidate.side)))
      throw new ApiContractError();
    if (
      candidate.risk_approved !== null &&
      typeof candidate.risk_approved !== "boolean"
    )
      throw new ApiContractError();
  }
}
function page<T>(value: unknown, parse: (entry: unknown) => T): Page<T> {
  const item = record(value);
  if (!Array.isArray(item.items)) throw new ApiContractError();
  integer(item.total);
  integer(item.limit);
  integer(item.offset);
  if (
    item.availability !== undefined &&
    !["AVAILABLE", "NOT_RECORDED", "NOT_READY"].includes(
      String(item.availability),
    )
  )
    throw new ApiContractError();
  if (item.reason_code !== undefined && item.reason_code !== null)
    text(item.reason_code);
  return {
    items: item.items.map(parse),
    total: item.total,
    limit: item.limit,
    offset: item.offset,
    ...(item.availability === undefined
      ? {}
      : {
          availability: item.availability as Page<T>["availability"],
          reason_code: item.reason_code as string | null,
        }),
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
  if (item.trading_date !== undefined) text(item.trading_date);
  for (const key of ["order_id", "security_id", "side", "timestamp"])
    text(item[key]);
  for (const key of ["quantity", "price", "transaction_cost"])
    decimal(item[key]);
  return item as unknown as ExperimentTrade;
}
function decision(value: unknown): ExperimentDecision {
  const item = record(value);
  integer(item.sequence);
  if (item.trading_date !== undefined) text(item.trading_date);
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
function holding(value: unknown): ExperimentHolding {
  const item = record(value);
  integer(item.sequence);
  text(item.trading_date);
  text(item.timestamp);
  for (const key of ["corporate_action_realized_pnl", "total_pnl"])
    if (item[key] !== undefined) decimal(item[key], true);
  for (const key of [
    "cash",
    "equity",
    "market_value",
    "realized_pnl",
    "unrealized_pnl",
    "cumulative_commission",
    "pending_corporate_action_value",
  ])
    decimal(item[key]);
  if (!Array.isArray(item.positions)) throw new ApiContractError();
  for (const value of item.positions) {
    const position = record(value);
    text(position.security_id);
    for (const key of [
      "quantity",
      "average_price",
      "market_price",
      "market_value",
    ])
      decimal(position[key]);
    decimal(position.weight, true);
  }
  return item as unknown as ExperimentHolding;
}
export function tradingDate(item: {
  trading_date?: string;
  timestamp: string;
}) {
  if (item.trading_date) return item.trading_date;
  const date = new Date(item.timestamp);
  if (Number.isNaN(date.getTime())) return null;
  return new Intl.DateTimeFormat("en-CA", {
    timeZone: "Asia/Shanghai",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  }).format(date);
}
function dateQuery(range: DateRange = {}) {
  const query = new URLSearchParams();
  if (range.start_date) query.set("start_date", range.start_date);
  if (range.end_date) query.set("end_date", range.end_date);
  return query.size ? `&${query}` : "";
}
const path = (id: string) => `/api/experiments/${encodeURIComponent(id)}`;
function matchingJobId<T extends { job_id: string }>(job: T, id: string): T {
  if (job.job_id.toLowerCase() !== id.toLowerCase())
    throw new ApiContractError();
  return job;
}
export interface ExperimentListQuery {
  status?: ExperimentStatus;
  mode?: ExperimentMode;
  sort?: "newest" | "oldest" | "name_asc" | "name_desc";
}
export const experimentApi = {
  capabilities: (signal?: AbortSignal) =>
    apiRequest("/api/workbench/capabilities", {}, signal, parseCapabilities),
  list: (
    signal?: AbortSignal,
    limit = 20,
    offset = 0,
    q = "",
    filters: ExperimentListQuery = {},
  ) => {
    const params = new URLSearchParams({
      limit: String(limit),
      offset: String(offset),
    });
    if (q) params.set("q", q);
    if (filters.status) params.set("status", filters.status);
    if (filters.mode) params.set("mode", filters.mode);
    if (filters.sort && filters.sort !== "newest")
      params.set("sort", filters.sort);
    return apiRequest(`/api/experiments?${params}`, {}, signal, (value) =>
      page(value, parseExperiment),
    );
  },
  get: (id: string, signal?: AbortSignal) =>
    apiRequest(path(id), {}, signal, (value) =>
      matchingJobId(parseExperiment(value), id),
    ),
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
    apiRequest(`${path(id)}/result`, {}, signal, (value) =>
      matchingJobId(parseResult(value), id),
    ),
  equity: (id: string, signal?: AbortSignal, offset = 0, range?: DateRange) =>
    apiRequest(
      `${path(id)}/equity?limit=100&offset=${offset}${dateQuery(range)}`,
      {},
      signal,
      (value) => page(value, equity),
    ),
  trades: (id: string, signal?: AbortSignal, offset = 0, range?: DateRange) =>
    apiRequest(
      `${path(id)}/trades?limit=20&offset=${offset}${dateQuery(range)}`,
      {},
      signal,
      (value) => page(value, trade),
    ),
  decisions: (
    id: string,
    signal?: AbortSignal,
    offset = 0,
    range?: DateRange,
  ) =>
    apiRequest(
      `${path(id)}/decisions?limit=20&offset=${offset}${dateQuery(range)}`,
      {},
      signal,
      (value) => page(value, decision),
    ),
  holdings: (id: string, signal?: AbortSignal, offset = 0, range?: DateRange) =>
    apiRequest(
      `${path(id)}/holdings?limit=1&offset=${offset}${dateQuery(range)}`,
      {},
      signal,
      (value) => {
        const parsed = page(value, holding);
        if (!parsed.availability) throw new ApiContractError();
        return parsed;
      },
    ),
  export: async (
    id: string,
    format: "json" | "csv",
    collection: ExperimentCollection,
    range?: DateRange,
  ): Promise<Blob> => {
    const controller = new AbortController();
    const timeout = window.setTimeout(
      () => controller.abort(),
      REQUEST_TIMEOUT_MS,
    );
    try {
      const response = await fetch(
        `${API_BASE_URL}${path(id)}/export?format=${format}&collection=${collection}${dateQuery(range)}`,
        {
          signal: controller.signal,
          headers: {
            Accept: format === "json" ? "application/json" : "text/csv",
          },
        },
      );
      if (!response.ok) {
        const payload: unknown = await response.json().catch(() => null);
        const code =
          payload &&
          typeof payload === "object" &&
          "code" in payload &&
          typeof payload.code === "string"
            ? payload.code
            : null;
        throw new ApiError(
          response.status,
          "The report could not be downloaded.",
          code,
        );
      }
      return await response.blob();
    } catch (error) {
      if (controller.signal.aborted)
        throw new ApiError(408, "The report download timed out.");
      throw error;
    } finally {
      window.clearTimeout(timeout);
    }
  },
};
