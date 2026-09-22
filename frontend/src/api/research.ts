import type {
  MonthlyReturn,
  ResearchDataset,
  ResearchHolding,
  ResearchMetric,
  ResearchPage,
  ResearchPoint,
  ResearchRebalance,
  ResearchRun,
  ResearchStrategy,
  ResearchTrade,
  RollingMetric,
} from "../types/research";
import { ApiContractError } from "./contracts";
import { apiRequest } from "./client";

const DECIMAL = /^-?\d+(?:\.\d+)?$/;

function record(value: unknown): Record<string, unknown> {
  if (typeof value !== "object" || value === null || Array.isArray(value))
    throw new ApiContractError();
  return value as Record<string, unknown>;
}

function text(value: unknown): asserts value is string {
  if (typeof value !== "string") throw new ApiContractError();
}

function decimal(value: unknown, nullable = false): void {
  if (nullable && value === null) return;
  if (typeof value !== "string" || !DECIMAL.test(value))
    throw new ApiContractError();
}

function page<T>(value: unknown, parse: (item: unknown) => T): ResearchPage<T> {
  const payload = record(value);
  if (!Array.isArray(payload.items)) throw new ApiContractError();
  for (const key of ["limit", "offset", "total"])
    if (!Number.isSafeInteger(payload[key])) throw new ApiContractError();
  return {
    items: payload.items.map(parse),
    limit: payload.limit as number,
    offset: payload.offset as number,
    total: payload.total as number,
  };
}

function dataset(value: unknown): ResearchDataset {
  const item = record(value);
  for (const key of [
    "dataset_id",
    "provider",
    "provider_version",
    "retrieval_timestamp",
    "coverage_start",
    "coverage_end",
    "canonical_sha256",
    "rule_version",
    "adjustment_method",
    "readiness_status",
  ])
    text(item[key]);
  if (
    !Number.isSafeInteger(item.security_count) ||
    typeof item.frozen !== "boolean"
  )
    throw new ApiContractError();
  if (item.manifest !== null) record(item.manifest);
  return item as unknown as ResearchDataset;
}

function strategy(value: unknown): ResearchStrategy {
  const item = record(value);
  for (const key of [
    "strategy_id",
    "version",
    "name_en",
    "name_zh",
    "configuration_hash",
  ])
    text(item[key]);
  if (
    !Array.isArray(item.factor_formulas) ||
    !item.factor_formulas.every((value) => typeof value === "string")
  )
    throw new ApiContractError();
  record(item.frozen_configuration);
  return item as unknown as ResearchStrategy;
}

function run(value: unknown): ResearchRun {
  const item = record(value);
  for (const key of [
    "run_id",
    "status",
    "period_kind",
    "git_commit",
    "dataset_id",
    "dataset_checksum",
    "provider",
    "provider_version",
    "market_rule_version",
    "strategy_id",
    "strategy_config_hash",
    "benchmark_id",
    "benchmark_version",
    "temporal_split_hash",
    "created_at",
  ])
    text(item[key]);
  record(item.transaction_cost_config);
  record(item.diagnostics);
  return item as unknown as ResearchRun;
}

const metric = (value: unknown): ResearchMetric => {
  const item = record(value);
  text(item.period_kind);
  text(item.metric_name);
  decimal(item.value, true);
  return item as unknown as ResearchMetric;
};

const point = (value: unknown): ResearchPoint => {
  const item = record(value);
  text(item.trading_date);
  decimal(item.value);
  return item as unknown as ResearchPoint;
};

const rollingMetric = (value: unknown): RollingMetric => {
  const item = record(value);
  text(item.trading_date);
  text(item.metric_name);
  decimal(item.value, true);
  return item as unknown as RollingMetric;
};

async function completePage<T>(
  path: string,
  parse: (item: unknown) => T,
  signal?: AbortSignal,
): Promise<ResearchPage<T>> {
  const items: T[] = [];
  let total: number | undefined;
  do {
    const result = await apiRequest(
      `${path}?limit=200&offset=${items.length}`,
      {},
      signal,
      (value) => page(value, parse),
    );
    if (
      result.total < 0 ||
      result.total > 100_000 ||
      (total !== undefined && total !== result.total) ||
      result.offset !== items.length ||
      (result.items.length === 0 && result.total > items.length)
    )
      throw new ApiContractError();
    total = result.total;
    items.push(...result.items);
    if (items.length > total) throw new ApiContractError();
  } while (items.length < total);
  return { items, total, offset: 0, limit: items.length };
}

export const researchApi = {
  datasets: (signal?: AbortSignal) =>
    apiRequest("/api/research/datasets", {}, signal, (value) =>
      page(value, dataset),
    ),
  dataset: (datasetId: string, signal?: AbortSignal) =>
    apiRequest(
      `/api/research/datasets/${encodeURIComponent(datasetId)}`,
      {},
      signal,
      dataset,
    ),
  strategies: (signal?: AbortSignal) =>
    apiRequest<ResearchStrategy[]>(
      "/api/research/strategies",
      {},
      signal,
      (value) => {
        if (!Array.isArray(value)) throw new ApiContractError();
        return value.map(strategy);
      },
    ),
  strategy: (strategyId: string, signal?: AbortSignal) =>
    apiRequest(
      `/api/research/strategies/${encodeURIComponent(strategyId)}`,
      {},
      signal,
      strategy,
    ),
  runs: (signal?: AbortSignal) =>
    apiRequest("/api/research/runs", {}, signal, (value) => page(value, run)),
  run: (runId: string, signal?: AbortSignal) =>
    apiRequest(
      `/api/research/runs/${encodeURIComponent(runId)}`,
      {},
      signal,
      run,
    ),
  metrics: (runId: string, signal?: AbortSignal) =>
    apiRequest(
      `/api/research/runs/${encodeURIComponent(runId)}/metrics`,
      {},
      signal,
      (value) => page(value, metric),
    ),
  points: (
    runId: string,
    kind: "equity" | "benchmark" | "drawdown",
    signal?: AbortSignal,
  ) =>
    completePage(
      `/api/research/runs/${encodeURIComponent(runId)}/${kind}`,
      point,
      signal,
    ),
  monthlyReturns: (runId: string, signal?: AbortSignal) =>
    apiRequest(
      `/api/research/runs/${encodeURIComponent(runId)}/monthly-returns`,
      {},
      signal,
      (value) => page(value, (item) => item as MonthlyReturn),
    ),
  rollingMetrics: (runId: string, signal?: AbortSignal) =>
    completePage(
      `/api/research/runs/${encodeURIComponent(runId)}/rolling-metrics`,
      rollingMetric,
      signal,
    ),
  holdings: (runId: string, signal?: AbortSignal) =>
    completePage(
      `/api/research/runs/${encodeURIComponent(runId)}/holdings`,
      (item) => item as ResearchHolding,
      signal,
    ),
  rebalances: (runId: string, signal?: AbortSignal) =>
    apiRequest(
      `/api/research/runs/${encodeURIComponent(runId)}/rebalances`,
      {},
      signal,
      (value) => page(value, (item) => item as ResearchRebalance),
    ),
  trades: (runId: string, signal?: AbortSignal) =>
    apiRequest(
      `/api/research/runs/${encodeURIComponent(runId)}/trades`,
      {},
      signal,
      (value) => page(value, (item) => item as ResearchTrade),
    ),
};
