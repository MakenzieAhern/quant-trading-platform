import type { PaperSession, PaperSnapshot } from "../types/paper";

export const PAPER_ID = "34d97303-a8c9-4f71-a0fc-c4b5d156f2ee";

export function paperSession(
  status: PaperSession["status"] = "CREATED",
): PaperSession {
  return {
    session_id: PAPER_ID,
    status,
    provider_type: "replay",
    dataset_id: "AAPL_fixture",
    symbol: "AAPL",
    strategy_type: "moving_average_crossover",
    strategy_parameters: { short_period: 2, long_period: 3 },
    initial_cash: "100000.052500000000000001",
    default_order_quantity: "10",
    risk: { enforce_buying_power: true },
    created_at: "2026-09-06T02:00:00Z",
    started_at: null,
    stopped_at: null,
    error_message: null,
  };
}

export function paperSnapshot(
  status: PaperSession["status"] = "CREATED",
): PaperSnapshot {
  return {
    session: paperSession(status),
    last_sequence: 0,
    latest_bar: null,
    latest_session: null,
    signals: [],
    risk_decisions: [],
    orders: [],
    fills: [],
    latest_portfolio: null,
  };
}
