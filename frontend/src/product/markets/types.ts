import type { DatasetCapability, Page } from "../experiments/types";
export type MarketDataset = DatasetCapability;
export interface Security {
  security_id: string;
  symbol: string;
  exchange: "SSE" | "SZSE";
  board: string;
  name: string | null;
  source_observed_name: string | null;
  name_temporal_authority: string | null;
  source_id: string | null;
  source_url: string | null;
  source_sha256: string | null;
  listed_from: string;
  listed_to: string | null;
}
export interface MarketMetadata extends MarketDataset {
  provider: string;
  provider_version: string;
  retrieved_at_utc: string | null;
  market_rule_version: string;
  source_lineage: string[];
  trading_date_timezone: "Asia/Shanghai";
  is_live: false;
  network_access_used: false;
  incremental_update_available: false;
  adjustment_basis: string;
  adjustment_method: string;
  limitations: string[];
  partitions?: { path: string; sha256: string }[];
  requested_start?: string;
  requested_end?: string;
  status_counts?: Record<string, number>;
  adjustment_missing_observations?: number;
}
export interface MarketSearch extends Page<Security> {
  metadata: MarketMetadata;
}
export interface WatchlistItem {
  dataset_id: string;
  security_id: string;
  dataset_sha256: string;
  security: Security;
  added_at: string;
  source_available?: boolean;
  source_reason_code?: string | null;
}
export type BarStatus =
  | "OBSERVED"
  | "SUSPENDED"
  | "SUSPENSION_BOUNDARY_UNCERTAIN"
  | "FEATURE_ONLY"
  | "MISSING_OBSERVATION"
  | "OUTSIDE_LISTING";
export interface MarketBar {
  trading_date: string;
  raw: {
    open: string | null;
    high: string | null;
    low: string | null;
    close: string | null;
    volume: string | null;
    amount: string | null;
  };
  adjusted: {
    open: string | null;
    high: string | null;
    low: string | null;
    close: string | null;
  };
  adjustment_factor: string | null;
  adjustment_effective_date: string | null;
  adjustment_lineage: string | null;
  status: BarStatus;
  risk_status: string | null;
  execution_open_blocked: boolean | null;
  suspension_evidence?: Record<string, unknown>[];
  source_lineage: string | null;
}
export interface MarketBars {
  security: Security;
  metadata: MarketMetadata;
  items: MarketBar[];
  total: number;
}
export type MarketRange = { start_date: string; end_date: string };
