export type ResearchPeriod =
  | "DEVELOPMENT"
  | "VALIDATION"
  | "OUT_OF_SAMPLE"
  | "FULL_PERIOD"
  | "PILOT_SMOKE";

export interface ResearchPage<T> {
  items: T[];
  limit: number;
  offset: number;
  total: number;
}

export interface ResearchDataset {
  dataset_id: string;
  provider: string;
  provider_version: string;
  retrieval_timestamp: string;
  coverage_start: string;
  coverage_end: string;
  security_count: number;
  canonical_sha256: string;
  rule_version: string;
  adjustment_method: string;
  readiness_status: string;
  frozen: boolean;
  manifest: Record<string, unknown> | null;
}

export interface ResearchStrategy {
  strategy_id: string;
  version: string;
  name_en: string;
  name_zh: string;
  factor_formulas: string[];
  frozen_configuration: Record<string, unknown>;
  configuration_hash: string;
}

export interface ResearchRun {
  run_id: string;
  status: string;
  period_kind: ResearchPeriod;
  git_commit: string;
  dataset_id: string;
  dataset_checksum: string;
  provider: string;
  provider_version: string;
  market_rule_version: string;
  strategy_id: string;
  strategy_config_hash: string;
  transaction_cost_config: Record<string, unknown>;
  benchmark_id: string;
  benchmark_version: string;
  temporal_split_hash: string;
  random_seed: number;
  created_at: string;
  started_at: string | null;
  completed_at: string | null;
  failure_code: string | null;
  diagnostics: Record<string, unknown>;
}

export interface ResearchMetric {
  period_kind: ResearchPeriod;
  metric_name: string;
  value: string | null;
}

export interface ResearchPoint {
  sequence: number;
  trading_date: string;
  value: string;
}

export type NullableResearchPoint = Omit<ResearchPoint, "value"> & {
  value: string | null;
};

export interface MonthlyReturn {
  month: string;
  value: string | null;
}

export interface RollingMetric {
  trading_date: string;
  metric_name: string;
  value: string | null;
}

export interface ResearchHolding {
  sequence: number;
  trading_date: string;
  security_id: string;
  quantity: string;
  weight: string;
  market_value: string;
}

export interface ResearchRebalance {
  sequence: number;
  trading_date: string;
  turnover: string;
  transaction_cost: string;
}

export interface ResearchTrade {
  sequence: number;
  order_id: string;
  security_id: string;
  side: string;
  quantity: string;
  price: string;
  transaction_cost: string;
  timestamp: string;
}
