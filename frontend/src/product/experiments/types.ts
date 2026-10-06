export type ExperimentMode = "historical_exploration" | "synthetic_demo";
export type CurrentDatasetQuality =
  "KNOWN_ECONOMIC_COVERAGE_GAP" | "HISTORICAL_DATASET_QUALITY_UNKNOWN" | null;
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
  current_dataset_quality?: CurrentDatasetQuality;
  dataset_id: string;
  mode: ExperimentMode;
  available: boolean;
  execution_available?: boolean;
  execution_reason_code?: string | null;
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
  error_context?: {
    trading_date: string;
    security_ids: string[];
    security_count: number;
  } | null;
  retry_of: string | null;
  attempt: number;
  result_available: boolean;
}
export interface ExperimentResult {
  current_dataset_quality?: CurrentDatasetQuality;
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
  simulation_plan?: SimulationPlan;
}
export interface SimulationPlan {
  status: string;
  mode: ExperimentMode;
  as_of_trading_date: string;
  account_snapshot_trading_date?: string | null;
  next_accepted_session: string | null;
  dataset_sha256: string;
  configuration_sha256: string;
  strategy_id: string;
  strategy_version: string;
  simulation_only: true;
  submitted_to_account: false;
  price_basis: string;
  account_mode: "EXPLORATORY_REPLAY" | "SYNTHETIC_DEMO";
  not_today_advice: true;
  data_snapshot_sha256: string;
  account: {
    cash: string;
    equity: string;
    snapshot_sha256: string;
    positions: ExperimentHolding["positions"];
  } | null;
  candidates: {
    security_id: string;
    target_weight: string;
    held_quantity: string;
    target_quantity: string;
    desired_change_quantity: string;
    proposed_quantity: string;
    side: "BUY" | "SELL" | "HOLD";
    reference_raw_close: string | null;
    trigger_reason: string;
    risk_approved: boolean | null;
    risk_reason_code: string;
  }[];
  estimated_cash_required: string | null;
  risk_rejections?: number;
}

export type PaperAccountPlan = Omit<
  SimulationPlan,
  "account_mode" | "submitted_to_account"
> & {
  account_mode: "HISTORICAL_PAPER_REPLAY";
  submitted_to_account: boolean;
  paper_session_id: string;
  plan_version:
    "PAPER_ACCOUNT_PLAN_V1" | "PAPER_ACCOUNT_PLAN_V2" | "PAPER_ACCOUNT_PLAN_V3";
};
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
  trading_date?: string;
}
export interface ExperimentDecision {
  sequence: number;
  proposal_id: string;
  security_id: string;
  approved: boolean;
  reason_code: string;
  message: string;
  timestamp: string;
  trading_date?: string;
}
export interface DateRange {
  start_date?: string;
  end_date?: string;
}
export type ExperimentCollection =
  "equity" | "trades" | "holdings" | "decisions";
export interface ExperimentHolding {
  sequence: number;
  trading_date: string;
  timestamp: string;
  cash: string;
  equity: string;
  market_value: string;
  realized_pnl: string;
  unrealized_pnl: string;
  cumulative_commission: string;
  pending_corporate_action_value: string;
  corporate_action_realized_pnl?: string | null;
  total_pnl?: string | null;
  positions: {
    security_id: string;
    quantity: string;
    average_price: string;
    market_price: string;
    market_value: string;
    weight: string | null;
  }[];
}
export interface Page<T> {
  items: T[];
  total: number;
  limit: number;
  offset: number;
  availability?: "AVAILABLE" | "NOT_RECORDED" | "NOT_READY";
  reason_code?: string | null;
}
