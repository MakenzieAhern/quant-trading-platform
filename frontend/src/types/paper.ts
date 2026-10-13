import type {
  CurrentDatasetQuality,
  CurrentSourceIntegrity,
  PaperAccountPlan,
} from "../product/experiments/types";

export type PaperSessionStatus =
  | "CREATED"
  | "STARTING"
  | "RUNNING"
  | "PAUSING"
  | "PAUSED"
  | "STOPPING"
  | "STOPPED"
  | "FAILED"
  | "INTERRUPTED";

export interface PaperSession {
  session_id: string;
  status: PaperSessionStatus;
  provider_type: "replay" | "simulated_a_share" | "historical_a_share";
  dataset_id: string;
  symbol: string;
  strategy_type:
    | "moving_average_crossover"
    | "rsi_mean_reversion"
    | "cn_a_cross_sectional_momentum_low_vol_v1";
  strategy_parameters: Record<string, unknown>;
  initial_cash: string;
  default_order_quantity: string;
  risk: Record<string, unknown>;
  created_at: string;
  started_at: string | null;
  stopped_at: string | null;
  error_message: string | null;
}

export interface MarketBar {
  symbol: string;
  timestamp: string;
  open: string;
  high: string;
  low: string;
  close: string;
  volume: string;
}

export interface MarketSession {
  trading_date: string;
  security_count: number;
  source:
    | "SIMULATED_SCENARIO_NOT_RESEARCH_EVIDENCE_V1"
    | "FROZEN_HISTORICAL_A_SHARE_REPLAY_V1";
}

export interface PaperCalendarPayload {
  schema_version: "PAPER_CALENDAR_V1";
  kind: "initial" | "extension";
  calendar: {
    market: "CN_A";
    sessions: {
      session_date: string;
      is_open: boolean;
      source_version: string;
    }[];
  };
  before_sha256: string | null;
  after_sha256: string;
  applied_at: string;
  after_completed_sessions: number;
  after_trading_date: string | null;
}

export interface PaperSignal {
  strategy_id: string;
  symbol: string;
  timestamp: string;
  signal_type: string;
}

export interface PaperRiskDecision {
  proposal_id: string;
  approved: boolean;
  reason_code: string;
  message: string;
  timestamp: string;
}

export interface PaperOrder {
  order_id: string;
  strategy_id: string;
  symbol: string;
  side: string;
  order_type: string;
  quantity: string;
  price: string | null;
  status: string;
  created_at: string;
  cancellation_reason_code?: string;
}

export interface PaperFill {
  order_id: string;
  strategy_id: string;
  symbol: string;
  side: string;
  quantity: string;
  price: string;
  commission: string;
  timestamp: string;
}

export interface PaperPosition {
  symbol: string;
  quantity: string;
  average_price: string;
  market_price: string;
  unrealized_pnl: string;
  realized_pnl: string;
}

export interface PaperPortfolio {
  timestamp: string;
  cash: string;
  market_value: string;
  equity: string;
  accounting_version?: "PNL_BREAKDOWN_V1" | null;
  corporate_action_realized_pnl?: string | null;
  total_pnl?: string | null;
  realized_pnl: string;
  unrealized_pnl: string;
  cumulative_commission: string;
  drawdown: string;
  positions: PaperPosition[];
  plan: PaperAccountPlan | null;
}

export interface PaperSnapshot {
  current_dataset_quality?: CurrentDatasetQuality;
  current_source_integrity?: CurrentSourceIntegrity;
  session: PaperSession;
  last_sequence: number;
  latest_bar: MarketBar | null;
  latest_session: MarketSession | null;
  signals: PaperSignal[];
  risk_decisions: PaperRiskDecision[];
  orders: PaperOrder[];
  fills: PaperFill[];
  latest_portfolio: PaperPortfolio | null;
  last_rebalance_plan: PaperAccountPlan | null;
}

export type PaperState = Omit<
  PaperSnapshot,
  "signals" | "risk_decisions" | "orders" | "fills"
>;

export type PaperCollection = "signals" | "risk_decisions" | "orders" | "fills";

export interface PaperCollectionPage {
  session_id: string;
  collection: PaperCollection;
  as_of_sequence: number;
  limit: number;
  offset: number;
  total: number;
  items: PaperJournalEvent[];
}

export interface PaperSessionPage {
  items: PaperSession[];
  limit: number;
  offset: number;
  total: number;
}

export type CreatePaperSessionRequest =
  | {
      provider_type: "replay";
      dataset_id: "AAPL_fixture";
      symbol: "AAPL";
      strategy:
        | {
            type: "moving_average_crossover";
            parameters: { short_period: number; long_period: number };
          }
        | {
            type: "rsi_mean_reversion";
            parameters: {
              rsi_period: number;
              oversold: string;
              overbought: string;
            };
          };
      initial_cash: string;
      default_order_quantity: string;
      risk: { enforce_buying_power: boolean };
    }
  | {
      provider_type: "simulated_a_share";
      dataset_id: "CN_A_SIMULATED_PAPER_FIXTURE_V1";
      symbol: "CN-A";
      strategy: {
        type: "cn_a_cross_sectional_momentum_low_vol_v1";
        parameters: Record<string, never>;
      };
      initial_cash: string;
      default_order_quantity: string;
      risk: { enforce_buying_power: true };
    }
  | {
      provider_type: "historical_a_share";
      dataset_id: "cn-a-research-20100101-20251231-v1";
      symbol: "CN-A";
      strategy: {
        type: "cn_a_cross_sectional_momentum_low_vol_v1";
        parameters: {
          start_date: string;
          end_date: string;
          rebalance_sessions: number;
          maximum_holdings: number;
          max_position_weight: string;
          universe: "ALL" | "SSE" | "SZSE";
          commission_rate: string;
          minimum_commission: string;
        };
      };
      initial_cash: string;
      default_order_quantity: string;
      risk: {
        enforce_buying_power: true;
        max_leverage: "1";
        max_drawdown: string;
      };
    };

export interface PaperWireEvent {
  sequence: number | null;
  type:
    | "stream.connected"
    | "stream.resync_required"
    | "session.status"
    | "market.bar"
    | "market.session"
    | "calendar.observed"
    | "signal.created"
    | "risk.decision"
    | "order.updated"
    | "fill.created"
    | "portfolio.snapshot";
  occurred_at: string | null;
  payload: Record<string, unknown>;
}

export interface PaperJournalEvent extends PaperWireEvent {
  sequence: number;
  occurred_at: string;
  type: Exclude<
    PaperWireEvent["type"],
    "stream.connected" | "stream.resync_required"
  >;
}
