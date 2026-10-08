import { ApiError, apiRequest, REQUEST_TIMEOUT_MS } from "../../api/client";
import { API_BASE_URL } from "../../api/config";
import { ApiContractError } from "../../api/contracts";
import { parseCurrentDatasetQuality } from "../experiments/api";
import type { Page } from "../experiments/types";
import type {
  MarketBar,
  MarketBars,
  MarketDataset,
  MarketMetadata,
  MarketRange,
  MarketSearch,
  Security,
  WatchlistItem,
} from "./types";

function record(value: unknown): Record<string, unknown> {
  if (!value || typeof value !== "object" || Array.isArray(value))
    throw new ApiContractError();
  return value as Record<string, unknown>;
}
function text(value: unknown) {
  if (typeof value !== "string") throw new ApiContractError();
}
function nullableText(value: unknown) {
  if (value !== null) text(value);
}
function integer(value: unknown) {
  if (!Number.isSafeInteger(value) || Number(value) < 0)
    throw new ApiContractError();
}
function strings(value: unknown) {
  if (!Array.isArray(value) || value.some((item) => typeof item !== "string"))
    throw new ApiContractError();
}
function decimal(value: unknown) {
  if (
    value !== null &&
    (typeof value !== "string" || !/^-?\d+(?:\.\d+)?$/.test(value))
  )
    throw new ApiContractError();
}
function dataset(value: unknown): MarketDataset {
  const item = record(value);
  for (const key of [
    "dataset_id",
    "coverage_start",
    "coverage_end",
    "default_start",
    "default_end",
    "benchmark_id",
  ])
    text(item[key]);
  for (const key of ["reason_code", "sha256", "as_of"]) nullableText(item[key]);
  if (
    !["synthetic_demo", "historical_exploration"].includes(String(item.mode)) ||
    typeof item.available !== "boolean"
  )
    throw new ApiContractError();
  integer(item.security_count);
  if (
    item.execution_available !== undefined &&
    typeof item.execution_available !== "boolean"
  )
    throw new ApiContractError();
  if (item.execution_reason_code !== undefined)
    nullableText(item.execution_reason_code);
  strings(item.universes);
  parseCurrentDatasetQuality(item.current_dataset_quality);
  return item as unknown as MarketDataset;
}
function security(value: unknown): Security {
  const item = record(value);
  for (const key of [
    "security_id",
    "symbol",
    "exchange",
    "board",
    "listed_from",
  ])
    text(item[key]);
  if (!["SSE", "SZSE"].includes(String(item.exchange)))
    throw new ApiContractError();
  for (const key of [
    "name",
    "source_observed_name",
    "name_temporal_authority",
    "source_id",
    "source_url",
    "source_sha256",
    "listed_to",
  ])
    nullableText(item[key]);
  return item as unknown as Security;
}
function metadata(value: unknown): MarketMetadata {
  const item = record(value);
  dataset(item);
  for (const key of [
    "provider",
    "provider_version",
    "market_rule_version",
    "adjustment_basis",
    "adjustment_method",
  ])
    text(item[key]);
  nullableText(item.retrieved_at_utc);
  strings(item.source_lineage);
  strings(item.limitations);
  if (
    item.trading_date_timezone !== "Asia/Shanghai" ||
    item.is_live !== false ||
    item.network_access_used !== false ||
    item.incremental_update_available !== false
  )
    throw new ApiContractError();
  if (item.partitions !== undefined) {
    if (!Array.isArray(item.partitions)) throw new ApiContractError();
    for (const entry of item.partitions) {
      const p = record(entry);
      text(p.path);
      text(p.sha256);
    }
  }
  if (item.requested_start !== undefined) text(item.requested_start);
  if (item.requested_end !== undefined) text(item.requested_end);
  if (item.status_counts !== undefined)
    for (const count of Object.values(record(item.status_counts)))
      integer(count);
  if (item.adjustment_missing_observations !== undefined)
    integer(item.adjustment_missing_observations);
  return item as unknown as MarketMetadata;
}
function page<T>(value: unknown, parse: (value: unknown) => T): Page<T> {
  const item = record(value);
  if (!Array.isArray(item.items)) throw new ApiContractError();
  integer(item.total);
  integer(item.limit);
  integer(item.offset);
  return {
    items: item.items.map(parse),
    total: item.total as number,
    limit: item.limit as number,
    offset: item.offset as number,
  };
}
function watchlist(value: unknown): WatchlistItem {
  const item = record(value);
  for (const key of ["dataset_id", "security_id", "dataset_sha256", "added_at"])
    text(item[key]);
  security(item.security);
  if (
    item.source_available !== undefined &&
    typeof item.source_available !== "boolean"
  )
    throw new ApiContractError();
  if (item.source_reason_code !== undefined)
    nullableText(item.source_reason_code);
  return item as unknown as WatchlistItem;
}
export function parseBars(value: unknown): MarketBars {
  const item = record(value);
  security(item.security);
  metadata(item.metadata);
  integer(item.total);
  if (
    !Array.isArray(item.items) ||
    item.items.length > 366 ||
    item.total !== item.items.length
  )
    throw new ApiContractError();
  for (const value of item.items) {
    const bar = record(value);
    text(bar.trading_date);
    for (const key of [
      "adjustment_factor",
      "adjustment_effective_date",
      "adjustment_lineage",
      "risk_status",
      "source_lineage",
    ])
      nullableText(bar[key]);
    decimal(bar.adjustment_factor);
    if (
      ![
        "OBSERVED",
        "SUSPENDED",
        "SUSPENSION_BOUNDARY_UNCERTAIN",
        "FEATURE_ONLY",
        "MISSING_OBSERVATION",
        "OUTSIDE_LISTING",
      ].includes(String(bar.status)) ||
      (bar.execution_open_blocked !== null &&
        typeof bar.execution_open_blocked !== "boolean")
    )
      throw new ApiContractError();
    if (bar.suspension_evidence !== undefined) {
      if (!Array.isArray(bar.suspension_evidence)) throw new ApiContractError();
      bar.suspension_evidence.forEach(record);
    }
    for (const prices of [record(bar.raw), record(bar.adjusted)])
      for (const key of ["open", "high", "low", "close"]) decimal(prices[key]);
    decimal(record(bar.raw).volume);
    decimal(record(bar.raw).amount);
  }
  return item as unknown as MarketBars;
}
const root = "/api/markets";
export const marketApi = {
  datasets: (signal?: AbortSignal) =>
    apiRequest(`${root}/datasets`, {}, signal, (value) => {
      if (!Array.isArray(value)) throw new ApiContractError();
      return value.map(dataset);
    }),
  search: (
    datasetId: string,
    q: string,
    exchange: string,
    offset = 0,
    signal?: AbortSignal,
  ) =>
    apiRequest(
      `${root}/securities?${new URLSearchParams({ dataset_id: datasetId, q, exchange, limit: "20", offset: String(offset) })}`,
      {},
      signal,
      (value): MarketSearch => ({
        ...page(value, security),
        metadata: metadata(record(value).metadata),
      }),
    ),
  bars: (
    datasetId: string,
    securityId: string,
    range: MarketRange,
    signal?: AbortSignal,
  ) =>
    apiRequest(
      `${root}/securities/${encodeURIComponent(securityId)}/bars?${new URLSearchParams({ dataset_id: datasetId, ...range })}`,
      {},
      signal,
      parseBars,
    ),
  watchlist: (offset = 0, signal?: AbortSignal, q = "") =>
    apiRequest(
      `${root}/watchlist?limit=20&offset=${offset}${q ? `&${new URLSearchParams({ q })}` : ""}`,
      {},
      signal,
      (value) => page(value, watchlist),
    ),
  add: (datasetId: string, securityId: string) =>
    apiRequest(
      `${root}/watchlist/${encodeURIComponent(securityId)}`,
      {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ dataset_id: datasetId }),
      },
      undefined,
      watchlist,
    ),
  remove: async (datasetId: string, securityId: string) => {
    const controller = new AbortController();
    const timeout = window.setTimeout(
      () => controller.abort(),
      REQUEST_TIMEOUT_MS,
    );
    try {
      const response = await fetch(
        `${API_BASE_URL}${root}/watchlist/${encodeURIComponent(securityId)}?${new URLSearchParams({ dataset_id: datasetId })}`,
        { method: "DELETE", signal: controller.signal },
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
          "The watchlist change could not be saved.",
          code,
        );
      }
    } catch (error) {
      if (controller.signal.aborted)
        throw new ApiError(408, "The watchlist request timed out.");
      throw error;
    } finally {
      window.clearTimeout(timeout);
    }
  },
};

// Calendar arithmetic only; no price or adjustment calculations happen in the UI.
export function validRange(range: MarketRange, dataset: MarketDataset) {
  const { start_date: start, end_date: end } = range;
  const validDate = (value: string) => {
    const date = new Date(`${value}T00:00:00Z`);
    return (
      /^\d{4}-\d{2}-\d{2}$/.test(value) &&
      Number.isFinite(date.getTime()) &&
      date.toISOString().slice(0, 10) === value
    );
  };
  const span =
    (Date.parse(`${end}T00:00:00Z`) - Date.parse(`${start}T00:00:00Z`)) /
    86400000;
  return (
    validDate(start) &&
    validDate(end) &&
    Number.isFinite(span) &&
    span >= 0 &&
    span < 366 &&
    start >= dataset.coverage_start &&
    end <= dataset.coverage_end
  );
}
export const securityName = (item: Security) =>
  item.name ?? item.source_observed_name ?? item.symbol;
export function closingPrice(item: MarketBar, view: "raw" | "adjusted") {
  return item[view].close;
}
