import { apiRequest } from "../../api/client";
import { ApiContractError } from "../../api/contracts";
import type {
  CandidateObservations,
  UpdateCapabilities,
  UpdateConfiguration,
  UpdateJob,
  UpdatePage,
  UpdateReceipt,
} from "./types";

function record(value: unknown): Record<string, unknown> {
  if (!value || typeof value !== "object" || Array.isArray(value))
    throw new ApiContractError();
  return value as Record<string, unknown>;
}
function text(value: unknown): asserts value is string {
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
  if (!Array.isArray(value)) throw new ApiContractError();
  value.forEach(text);
}
function authority(value: unknown) {
  const item = record(value);
  if (
    item.raw_ohlcv !== "CANDIDATE_ONLY" ||
    item.execution_eligible !== false ||
    item.forward_acceptance !== false
  )
    throw new ApiContractError();
}
function terms(value: unknown) {
  const item = record(value);
  for (const key of [
    "source_url",
    "source_snapshot_sha256",
    "terms_url",
    "terms_version",
    "terms_snapshot_sha256",
    "terms_retrieved_at_utc",
    "permitted_scope",
    "redistribution_commercial_rights",
    "software_license",
  ])
    text(item[key]);
}
function configuration(value: unknown) {
  const item = record(value);
  strings(item.security_ids);
  if (
    (item.security_ids as string[]).length < 1 ||
    (item.security_ids as string[]).length > 20
  )
    throw new ApiContractError();
  text(item.start_date);
  text(item.end_date);
}
export function parseCapabilities(value: unknown): UpdateCapabilities {
  const item = record(value);
  authority(item.authority);
  terms(item.terms);
  for (const key of [
    "provider",
    "sdk_version",
    "latest_publishable_date",
    "publication_timezone",
    "publication_time",
    "scope",
  ])
    text(item[key]);
  nullableText(item.reason_code);
  if (
    item.mode !== "raw_only_candidate" ||
    typeof item.available !== "boolean" ||
    !Array.isArray(item.archive)
  )
    throw new ApiContractError();
  for (const key of [
    "max_securities",
    "max_days",
    "request_chunk_days",
    "maximum_attempts_per_request",
    "request_timeout_seconds",
    "minimum_request_interval_seconds",
    "job_timeout_seconds",
  ])
    integer(item[key]);
  for (const dataset of item.archive) {
    const row = record(dataset);
    for (const key of ["dataset_id", "coverage_start", "coverage_end"])
      text(row[key]);
    if (
      typeof row.available !== "boolean" ||
      !["historical_exploration", "synthetic_demo"].includes(String(row.mode))
    )
      throw new ApiContractError();
  }
  return item as unknown as UpdateCapabilities;
}
export function parseJob(value: unknown): UpdateJob {
  const item = record(value);
  authority(item.authority);
  configuration(item.configuration);
  if (
    item.mode !== "raw_only_candidate" ||
    ![
      "QUEUED",
      "RUNNING",
      "SUCCEEDED",
      "FAILED",
      "CANCELLED",
      "INTERRUPTED",
    ].includes(String(item.status)) ||
    typeof item.cancel_requested !== "boolean"
  )
    throw new ApiContractError();
  for (const key of ["job_id", "phase", "configuration_sha256", "created_at"])
    text(item[key]);
  for (const key of ["started_at", "completed_at", "error_code", "retry_of"])
    nullableText(item[key]);
  integer(item.completed_requests);
  integer(item.attempt);
  if (item.total_requests !== null) integer(item.total_requests);
  const master = record(item.master_snapshot);
  for (const key of ["dataset_id", "sha256", "as_of", "current_authority"])
    text(master[key]);
  if (!Array.isArray(master.securities)) throw new ApiContractError();
  if (item.summary !== null) {
    const summary = record(item.summary);
    for (const key of [
      "cached_observations_skipped",
      "observations_available",
      "new_observations",
      "unresolved_date_count",
    ])
      if (summary[key] !== undefined) integer(summary[key]);
    if (summary.unresolved_dates !== undefined)
      Object.values(record(summary.unresolved_dates)).forEach(strings);
  }
  return item as unknown as UpdateJob;
}
function receipt(value: unknown): UpdateReceipt {
  const item = record(value);
  authority(item.authority);
  terms(item.terms);
  for (const key of [
    "receipt_id",
    "manifest_sha256",
    "provider",
    "sdk_version",
    "parser_version",
    "security_id",
    "requested_at_utc",
    "received_at_utc",
    "response_completed_at_utc",
    "first_received_at_utc",
    "raw_response_representation",
    "raw_response_sha256",
    "logical_rows_sha256",
  ])
    text(item[key]);
  integer(item.attempt);
  integer(item.row_count);
  Object.values(record(item.parameters)).forEach(text);
  return item as unknown as UpdateReceipt;
}
function page<T>(value: unknown, parse: (value: unknown) => T): UpdatePage<T> {
  const item = record(value);
  if (!Array.isArray(item.items) || item.items.length > 100)
    throw new ApiContractError();
  for (const key of ["total", "limit", "offset"]) integer(item[key]);
  return {
    items: item.items.map(parse),
    total: item.total as number,
    limit: item.limit as number,
    offset: item.offset as number,
  };
}
export function parseObservations(value: unknown): CandidateObservations {
  const item = record(value);
  authority(item.authority);
  integer(item.total);
  if (
    item.mode !== "raw_only_candidate" ||
    item.trading_date_timezone !== "Asia/Shanghai" ||
    !Array.isArray(item.items) ||
    item.items.length > 366 ||
    item.total !== item.items.length
  )
    throw new ApiContractError();
  for (const value of item.items) {
    const row = record(value);
    for (const key of ["security_id", "trading_date", "receipt_id"])
      text(row[key]);
    for (const key of ["provider_trade_status", "provider_is_st"])
      if (
        !["0", "1"].includes(String(row[key])) ||
        typeof row[key] !== "string"
      )
        throw new ApiContractError();
    if (
      row.execution_eligible !== false ||
      !["VENDOR_SUSPENDED", "RAW_CANDIDATE"].includes(String(row.status))
    )
      throw new ApiContractError();
    const raw = record(row.raw);
    for (const key of [
      "open",
      "high",
      "low",
      "close",
      "preclose",
      "volume",
      "amount",
    ]) {
      text(raw[key]);
      if (!/^-?\d+(?:\.\d+)?$/.test(raw[key])) throw new ApiContractError();
    }
  }
  return item as unknown as CandidateObservations;
}
const root = "/api/market-updates";
const path = (id: string) => `${root}/${encodeURIComponent(id)}`;
const post = (key?: string, body?: UpdateConfiguration): RequestInit => ({
  method: "POST",
  headers: {
    ...(key ? { "Idempotency-Key": key } : {}),
    ...(body ? { "Content-Type": "application/json" } : {}),
  },
  ...(body ? { body: JSON.stringify(body) } : {}),
});
export const marketUpdateApi = {
  capabilities: (signal?: AbortSignal) =>
    apiRequest(`${root}/capabilities`, {}, signal, parseCapabilities),
  list: (offset = 0, signal?: AbortSignal) =>
    apiRequest(`${root}?limit=20&offset=${offset}`, {}, signal, (value) =>
      page(value, parseJob),
    ),
  get: (id: string, signal?: AbortSignal) =>
    apiRequest(path(id), {}, signal, (value) => {
      const parsed = parseJob(value);
      if (parsed.job_id.toLowerCase() !== id.toLowerCase())
        throw new ApiContractError();
      return parsed;
    }),
  create: (config: UpdateConfiguration, key: string) =>
    apiRequest(root, post(key, config), undefined, parseJob),
  cancel: (id: string) =>
    apiRequest(`${path(id)}/cancel`, post(), undefined, parseJob),
  retry: (id: string) =>
    apiRequest(
      `${path(id)}/retry`,
      post(`market-update-retry-v1:${id}`),
      undefined,
      parseJob,
    ),
  receipts: (id: string, offset = 0, signal?: AbortSignal) =>
    apiRequest(
      `${path(id)}/receipts?limit=20&offset=${offset}`,
      {},
      signal,
      (value) => page(value, receipt),
    ),
  observations: (
    securityId: string,
    range: Pick<UpdateConfiguration, "start_date" | "end_date">,
    signal?: AbortSignal,
  ) =>
    apiRequest(
      `${root}/observations?${new URLSearchParams({ security_id: securityId, ...range })}`,
      {},
      signal,
      parseObservations,
    ),
};
