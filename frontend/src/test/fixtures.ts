import type { BacktestRun, Metrics } from "../types/backtests";

export const RUN_ID = "8f38940a-5ee6-47da-893f-8317f891ed08";

export const metrics: Metrics = {
  initial_equity: "105.052500000000000001",
  final_equity: "105.052500000000000001",
  total_return: "0",
  cagr: null,
  max_drawdown: "0",
  sharpe_ratio: null,
  sortino_ratio: null,
  total_commission: "0.000000000000000001",
  number_of_fills: 1,
};

export function run(status: BacktestRun["status"] = "SUCCEEDED"): BacktestRun {
  const root = `/api/backtests/${RUN_ID}`;
  return {
    run_id: RUN_ID,
    status,
    strategy_id: "moving_average_crossover:AAPL",
    strategy_type: "moving_average_crossover",
    strategy_parameters: { short_period: 2, long_period: 3 },
    symbol: "AAPL",
    dataset_id: "AAPL_fixture",
    created_at: "2024-01-02T00:00:00Z",
    started_at: "2024-01-02T00:00:01Z",
    completed_at: status === "RUNNING" ? null : "2024-01-02T00:00:02Z",
    initial_cash: metrics.initial_equity,
    default_order_quantity: "10",
    risk: {},
    start: null,
    end: null,
    error_message:
      status === "FAILED" ? "RuntimeError: backtest execution failed" : null,
    metrics: status === "SUCCEEDED" ? metrics : null,
    links: {
      self: root,
      result: `${root}/result`,
      signals: `${root}/signals`,
      risk_decisions: `${root}/risk-decisions`,
      orders: `${root}/orders`,
      fills: `${root}/fills`,
      equity: `${root}/equity`,
    },
  };
}

export function jsonResponse(payload: unknown, status = 200): Response {
  return new Response(JSON.stringify(payload), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}
