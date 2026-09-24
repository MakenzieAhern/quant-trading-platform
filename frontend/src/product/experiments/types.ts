export type ExperimentMode = "historical_exploration" | "synthetic_demo";
export type ExperimentStatus =
  "QUEUED" | "RUNNING" | "SUCCEEDED" | "FAILED" | "CANCELLED" | "INTERRUPTED";
export interface ParameterRange {
  min: number;
  max: number;
  default: number;
}
export interface StrategyCapability {
  strategy_id: string;
  version: string;
  name_en: string;
  name_zh: string;
  description_en: string;
  description_zh: string;
  parameters: {
    rebalance_sessions: ParameterRange;
    maximum_holdings: ParameterRange;
  };
  limitations: string[];
}
export interface DatasetCapability {
  dataset_id: string;
  mode: ExperimentMode;
  available: boolean;
  reason_code: string | null;
  coverage_start: string;
  coverage_end: string;
  default_start: string;
  default_end: string;
  security_count: number;
  sha256: string | null;
  as_of: string | null;
  universes: string[];
  benchmark_id: string;
}
export interface Capabilities {
  strategies: StrategyCapability[];
  datasets: DatasetCapability[];
  defaults: {
    initial_cash: string;
    commission_rate: string;
    minimum_commission: string;
    max_drawdown: string;
  };
}
export interface ExperimentConfiguration {
  name: string;
  dataset_id: string;
  strategy_id: string;
  start_date: string;
  end_date: string;
  initial_cash: string;
  universe: "ALL" | "SSE" | "SZSE";
  strategy: { rebalance_sessions: number; maximum_holdings: number };
  costs: { commission_rate: string; minimum_commission: string };
  risk: { max_drawdown: string; max_position_weight: string };
}
export interface Experiment {
  job_id: string;
  name: string;
  status: ExperimentStatus;
  mode: ExperimentMode;
  dataset_id: string;
  dataset_sha256: string;
  configuration: ExperimentConfiguration;
  configuration_sha256: string;
  strategy_version: string;
  created_at: string;
  started_at: string | null;
  completed_at: string | null;
  phase: string;
  completed_sessions: number;
  total_sessions: number | null;
  cancel_requested: boolean;
  error_code: string | null;
  retry_of: string | null;
  attempt: number;
  result_available: boolean;
}
export interface ExperimentResult {
  job_id: string;
  mode: ExperimentMode;
  metrics: {
    initial_capital: string | null;
    final_equity: string | null;
    cumulative_return: string | null;
    maximum_drawdown: string | null;
    transaction_costs: string | null;
    benchmark_return: string | null;
    excess_return: string | null;
    sharpe_ratio: string | null;
    number_of_trades: number;
    number_of_fills: number;
  };
  limitations: string[];
  execution: {
    proposals: number;
    approved_decisions: number;
    orders: number;
    fills: number;
    reason_counts: Record<string, number>;
  };
  date_start: string;
  date_end: string;
  benchmark_id: string;
}
export interface ExperimentEquity {
  sequence: number;
  trading_date: string;
  equity: string;
  benchmark: string | null;
  drawdown: string | null;
}
export interface ExperimentTrade {
  sequence: number;
  order_id: string;
  security_id: string;
  side: string;
  quantity: string;
  price: string;
  transaction_cost: string;
  timestamp: string;
}
export interface ExperimentDecision {
  sequence: number;
  proposal_id: string;
  security_id: string;
  approved: boolean;
  reason_code: string;
  message: string;
  timestamp: string;
}
export interface Page<T> {
  items: T[];
  total: number;
  limit: number;
  offset: number;
}
