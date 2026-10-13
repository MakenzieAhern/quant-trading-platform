import type {
  DatasetCapability,
  ExperimentStatus,
  Page,
} from "../experiments/types";

export interface UpdateConfiguration {
  security_ids: string[];
  start_date: string;
  end_date: string;
}
export interface UpdateAuthority {
  raw_ohlcv: "CANDIDATE_ONLY";
  execution_eligible: false;
  forward_acceptance: false;
  [key: string]: string | boolean;
}
export interface UpdateTerms {
  source_url: string;
  source_snapshot_sha256: string;
  terms_url: string;
  terms_version: string;
  terms_snapshot_sha256: string;
  terms_retrieved_at_utc: string;
  permitted_scope: string;
  redistribution_commercial_rights: string;
  software_license: string;
}
export interface UpdateCapabilities {
  provider: string;
  sdk_version: string;
  available: boolean;
  reason_code: string | null;
  mode: "raw_only_candidate";
  authority: UpdateAuthority;
  terms: UpdateTerms;
  max_securities: number;
  max_days: number;
  request_chunk_days: number;
  latest_publishable_date: string;
  publication_timezone: string;
  publication_time: string;
  maximum_attempts_per_request: number;
  request_timeout_seconds: number;
  minimum_request_interval_seconds: number;
  job_timeout_seconds: number;
  scope: string;
  archive: DatasetCapability[];
  provider_available?: boolean;
  archive_available?: boolean;
  worker_running?: boolean;
}
export interface UpdateSummary {
  cached_observations_skipped?: number;
  observations_available?: number;
  new_observations?: number;
  unresolved_dates?: Record<string, string[]>;
  unresolved_date_count?: number;
  active_request?: unknown;
  [key: string]: unknown;
}
export interface UpdateJob {
  job_id: string;
  status: ExperimentStatus;
  phase: string;
  configuration: UpdateConfiguration;
  configuration_sha256: string;
  master_snapshot: {
    dataset_id: string;
    sha256: string;
    as_of: string;
    current_authority: string;
    securities: unknown[];
  };
  created_at: string;
  started_at: string | null;
  completed_at: string | null;
  completed_requests: number;
  total_requests: number | null;
  cancel_requested: boolean;
  error_code: string | null;
  retry_of: string | null;
  attempt: number;
  summary: UpdateSummary | null;
  authority: UpdateAuthority;
  mode: "raw_only_candidate";
}
export interface UpdateReceipt {
  reader_diagnostics?: "PARSER_LABEL_MISMATCH_READ_ONLY"[];
  receipt_id: string;
  manifest_sha256: string;
  provider: string;
  sdk_version: string;
  parser_version: string;
  security_id: string;
  parameters: Record<string, string>;
  requested_at_utc: string;
  received_at_utc: string;
  response_completed_at_utc: string;
  first_received_at_utc: string;
  attempt: number;
  raw_response_representation: string;
  raw_response_sha256: string;
  logical_rows_sha256: string;
  row_count: number;
  terms: UpdateTerms;
  authority: UpdateAuthority;
}
export interface CandidateObservation {
  security_id: string;
  trading_date: string;
  raw: Record<
    "open" | "high" | "low" | "close" | "preclose" | "volume" | "amount",
    string
  >;
  provider_trade_status: "0" | "1";
  provider_is_st: "0" | "1";
  status: "VENDOR_SUSPENDED" | "RAW_CANDIDATE";
  execution_eligible: false;
  receipt_id: string;
}
export interface CandidateObservations {
  items: CandidateObservation[];
  total: number;
  authority: UpdateAuthority;
  mode: "raw_only_candidate";
  trading_date_timezone: "Asia/Shanghai";
}
export type UpdatePage<T> = Page<T>;
