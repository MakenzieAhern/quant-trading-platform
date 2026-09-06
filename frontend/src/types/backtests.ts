export type BacktestStatus = "CREATED" | "RUNNING" | "SUCCEEDED" | "FAILED";

export interface BacktestLinks {
  self: string;
  result: string;
  signals: string;
  risk_decisions: string;
  orders: string;
  fills: string;
  equity: string;
}

export interface Metrics {
  initial_equity: string;
  final_equity: string;
  total_return: string;
  cagr: string | null;
  max_drawdown: string;
  sharpe_ratio: string | null;
  sortino_ratio: string | null;
  total_commission: string;
  number_of_fills: number;
}

export interface BacktestRun {
  run_id: string;
  status: BacktestStatus;
  strategy_id: string;
  strategy_type: "moving_average_crossover" | "rsi_mean_reversion";
  strategy_parameters: Record<string, string | number>;
  symbol: string;
  dataset_id: string;
  created_at: string;
  started_at: string | null;
  completed_at: string | null;
  initial_cash: string;
  default_order_quantity: string;
  risk: Record<string, string | boolean | null>;
  start: string | null;
  end: string | null;
  error_message: string | null;
  metrics: Metrics | null;
  links: BacktestLinks;
}

export interface CreateBacktestResponse {
  run_id: string;
  status: BacktestStatus;
  links: BacktestLinks;
}

export interface MovingAverageRequest {
  type: "moving_average_crossover";
  parameters: { short_period: number; long_period: number };
}

export interface RsiRequest {
  type: "rsi_mean_reversion";
  parameters: { rsi_period: number; oversold: string; overbought: string };
}

export interface CreateBacktestRequest {
  dataset_id: "AAPL_fixture";
  symbol: "AAPL";
  strategy: MovingAverageRequest | RsiRequest;
  initial_cash: string;
  default_order_quantity: string;
  start?: string;
  end?: string;
}

export interface Page<T> {
  items: T[];
  limit: number;
  offset: number;
  total: number;
}

export interface BacktestResult {
  run_id: string;
  status: BacktestStatus;
  metrics: Metrics;
  signal_count: number;
  proposal_count: number;
  risk_decision_count: number;
  risk_rejection_count: number;
  order_count: number;
  fill_count: number;
  snapshot_count: number;
  reservation_count: number;
  start_time: string | null;
  end_time: string | null;
}

export interface Signal {
  strategy_id: string;
  symbol: string;
  timestamp: string;
  signal_type: string;
}

export interface RiskDecision {
  proposal_id: string;
  approved: boolean;
  reason_code: string;
  message: string;
  timestamp: string;
  risk_increasing: boolean;
  reference_price: string | null;
  order_notional: string | null;
  projected_position_quantity: string | null;
  projected_symbol_exposure: string | null;
  projected_gross_exposure: string | null;
  projected_net_exposure: string | null;
  projected_gross_leverage: string | null;
  projected_cash: string | null;
  estimated_transaction_cost: string | null;
}

export interface Order {
  order_id: string;
  strategy_id: string;
  symbol: string;
  side: string;
  order_type: string;
  quantity: string;
  price: string | null;
  status: string;
  created_at: string;
}

export interface Fill {
  order_id: string;
  strategy_id: string;
  symbol: string;
  side: string;
  quantity: string;
  price: string;
  commission: string;
  timestamp: string;
}

export interface EquityPoint {
  timestamp: string;
  equity: string;
  cash: string;
  market_value: string;
}
