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
import {
  parseCurrentDatasetQuality,
  parseCurrentSourceIntegrity,
} from "../product/experiments/api";
import type { DateRange } from "../product/experiments/types";

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
  parseCurrentDatasetQuality(item.current_dataset_quality);
  parseCurrentSourceIntegrity(item.current_source_integrity);
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
  parseCurrentDatasetQuality(item.current_dataset_quality);
  parseCurrentSourceIntegrity(item.current_source_integrity);
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
  if (!Number.isSafeInteger(item.sequence) || (item.sequence as number) < 0)
    throw new ApiContractError();
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

function boundedPage<T>(
  path: string,
  parse: (item: unknown) => T,
  offset: number,
  signal?: AbortSignal,
  range: DateRange = {},
): Promise<ResearchPage<T>> {
  if (!Number.isSafeInteger(offset) || offset < 0 || offset % 200 !== 0)
    throw new ApiContractError();
  const query = new URLSearchParams({ limit: "200", offset: String(offset) });
  if (range.start_date) query.set("start_date", range.start_date);
  if (range.end_date) query.set("end_date", range.end_date);
  return apiRequest(`${path}?${query}`, {}, signal, (value) => {
    const result = page(value, parse);
    if (
      result.limit !== 200 ||
      result.offset !== offset ||
      result.total < 0 ||
      result.items.length !== Math.min(200, Math.max(0, result.total - offset))
    )
      throw new ApiContractError();
    return result;
  });
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
    offset = 0,
    signal?: AbortSignal,
    range: DateRange = {},
  ) =>
    boundedPage(
      `/api/research/runs/${encodeURIComponent(runId)}/${kind}`,
      point,
      offset,
      signal,
      range,
    ),
  monthlyReturns: (runId: string, signal?: AbortSignal) =>
    apiRequest(
      `/api/research/runs/${encodeURIComponent(runId)}/monthly-returns`,
      {},
      signal,
      (value) => page(value, (item) => item as MonthlyReturn),
    ),
  rollingMetrics: (
    runId: string,
    offset = 0,
    signal?: AbortSignal,
    range: DateRange = {},
  ) =>
    boundedPage(
      `/api/research/runs/${encodeURIComponent(runId)}/rolling-metrics`,
      rollingMetric,
      offset,
      signal,
      range,
    ),
  holdings: (
    runId: string,
    offset = 0,
    signal?: AbortSignal,
    range: DateRange = {},
  ) =>
    boundedPage(
      `/api/research/runs/${encodeURIComponent(runId)}/holdings`,
      (item) => item as ResearchHolding,
      offset,
      signal,
      range,
    ),
  rebalances: (
    runId: string,
    offset = 0,
    signal?: AbortSignal,
    range: DateRange = {},
  ) =>
    boundedPage(
      `/api/research/runs/${encodeURIComponent(runId)}/rebalances`,
      (item) => item as ResearchRebalance,
      offset,
      signal,
      range,
    ),
  trades: (
    runId: string,
    offset = 0,
    signal?: AbortSignal,
    range: DateRange = {},
  ) =>
    boundedPage(
      `/api/research/runs/${encodeURIComponent(runId)}/trades`,
      (item) => item as ResearchTrade,
      offset,
      signal,
      range,
    ),
};
