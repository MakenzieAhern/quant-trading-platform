import { apiRequest } from "./client";
import { API_BASE_URL } from "./config";
import { parsePaperAccountPlan } from "../product/experiments/api";
import type {
  CreatePaperSessionRequest,
  MarketBar,
  MarketSession,
  PaperFill,
  PaperOrder,
  PaperPortfolio,
  PaperRiskDecision,
  PaperSession,
  PaperSessionPage,
  PaperSessionStatus,
  PaperSignal,
  PaperSnapshot,
  PaperWireEvent,
} from "../types/paper";

const DECIMAL = /^-?\d+(?:\.\d+)?$/;
const STATUSES = new Set<PaperSessionStatus>([
  "CREATED",
  "STARTING",
  "RUNNING",
  "PAUSING",
  "PAUSED",
  "STOPPING",
  "STOPPED",
  "FAILED",
  "INTERRUPTED",
]);
const EVENT_TYPES = new Set<PaperWireEvent["type"]>([
  "stream.connected",
  "stream.resync_required",
  "session.status",
  "market.bar",
  "market.session",
  "signal.created",
  "risk.decision",
  "order.updated",
  "fill.created",
  "portfolio.snapshot",
]);

function record(value: unknown): Record<string, unknown> {
  if (typeof value !== "object" || value === null || Array.isArray(value))
    throw new Error(
      "The paper API response did not match the expected contract.",
    );
  return value as Record<string, unknown>;
}

function requiredString(value: unknown): string {
  if (typeof value !== "string")
    throw new Error(
      "The paper API response did not match the expected contract.",
    );
  return value;
}

function decimal(value: unknown): string {
  const result = requiredString(value);
  if (!DECIMAL.test(result))
    throw new Error(
      "The paper API response did not match the expected contract.",
    );
  return result;
}

function nullableString(value: unknown): string | null {
  return value === null ? null : requiredString(value);
}

function session(value: unknown): PaperSession {
  const item = record(value);
  const status = requiredString(item.status) as PaperSessionStatus;
  if (!STATUSES.has(status)) throw new Error("Invalid paper session status.");
  const provider = requiredString(
    item.provider_type,
  ) as PaperSession["provider_type"];
  if (
    provider !== "replay" &&
    provider !== "simulated_a_share" &&
    provider !== "historical_a_share"
  )
    throw new Error("Invalid paper provider.");
  const strategy = requiredString(
    item.strategy_type,
  ) as PaperSession["strategy_type"];
  if (
    strategy !== "moving_average_crossover" &&
    strategy !== "rsi_mean_reversion" &&
    strategy !== "cn_a_cross_sectional_momentum_low_vol_v1"
  )
    throw new Error("Invalid paper strategy.");
  return {
    session_id: requiredString(item.session_id),
    status,
    provider_type: provider,
    dataset_id: requiredString(item.dataset_id),
    symbol: requiredString(item.symbol),
    strategy_type: strategy,
    strategy_parameters: record(item.strategy_parameters),
    initial_cash: decimal(item.initial_cash),
    default_order_quantity: decimal(item.default_order_quantity),
    risk: record(item.risk),
    created_at: requiredString(item.created_at),
    started_at: nullableString(item.started_at),
    stopped_at: nullableString(item.stopped_at),
    error_message: nullableString(item.error_message),
  };
}

function array<T>(value: unknown, parse: (item: unknown) => T): T[] {
  if (!Array.isArray(value)) throw new Error("Invalid paper collection.");
  return value.map(parse);
}

const marketBar = (value: unknown): MarketBar => {
  const item = record(value);
  return {
    symbol: requiredString(item.symbol),
    timestamp: requiredString(item.timestamp),
    open: decimal(item.open),
    high: decimal(item.high),
    low: decimal(item.low),
    close: decimal(item.close),
    volume: decimal(item.volume),
  };
};

const marketSession = (value: unknown): MarketSession => {
  const item = record(value);
  if (
    !Number.isSafeInteger(item.security_count) ||
    Number(item.security_count) < 0
  )
    throw new Error("Invalid A-share market session.");
  if (
    item.source !== "SIMULATED_SCENARIO_NOT_RESEARCH_EVIDENCE_V1" &&
    item.source !== "FROZEN_HISTORICAL_A_SHARE_REPLAY_V1"
  )
    throw new Error("Invalid A-share simulation source.");
  return {
    trading_date: requiredString(item.trading_date),
    security_count: item.security_count as number,
    source: item.source,
  };
};

const signal = (value: unknown): PaperSignal => {
  const item = record(value);
  return {
    strategy_id: requiredString(item.strategy_id),
    symbol: requiredString(item.symbol),
    timestamp: requiredString(item.timestamp),
    signal_type: requiredString(item.signal_type),
  };
};

const decision = (value: unknown): PaperRiskDecision => {
  const item = record(value);
  if (typeof item.approved !== "boolean") throw new Error("Invalid decision.");
  return {
    proposal_id: requiredString(item.proposal_id),
    approved: item.approved,
    reason_code: requiredString(item.reason_code),
    message: requiredString(item.message),
    timestamp: requiredString(item.timestamp),
  };
};

const order = (value: unknown): PaperOrder => {
  const item = record(value);
  return {
    order_id: requiredString(item.order_id),
    strategy_id: requiredString(item.strategy_id),
    symbol: requiredString(item.symbol),
    side: requiredString(item.side),
    order_type: requiredString(item.order_type),
    quantity: decimal(item.quantity),
    price: item.price === null ? null : decimal(item.price),
    status: requiredString(item.status),
    created_at: requiredString(item.created_at),
  };
};

const fill = (value: unknown): PaperFill => {
  const item = record(value);
  return {
    order_id: requiredString(item.order_id),
    strategy_id: requiredString(item.strategy_id),
    symbol: requiredString(item.symbol),
    side: requiredString(item.side),
    quantity: decimal(item.quantity),
    price: decimal(item.price),
    commission: decimal(item.commission),
    timestamp: requiredString(item.timestamp),
  };
};

const portfolio = (value: unknown): PaperPortfolio => {
  const item = record(value);
  return {
    timestamp: requiredString(item.timestamp),
    cash: decimal(item.cash),
    market_value: decimal(item.market_value),
    equity: decimal(item.equity),
    realized_pnl: decimal(item.realized_pnl),
    unrealized_pnl: decimal(item.unrealized_pnl),
    cumulative_commission: decimal(item.cumulative_commission),
    drawdown: decimal(item.drawdown),
    positions: array(item.positions, (positionValue) => {
      const position = record(positionValue);
      return {
        symbol: requiredString(position.symbol),
        quantity: decimal(position.quantity),
        average_price: decimal(position.average_price),
        market_price: decimal(position.market_price),
        unrealized_pnl: decimal(position.unrealized_pnl),
        realized_pnl: decimal(position.realized_pnl),
      };
    }),
    plan: item.plan == null ? null : parsePaperAccountPlan(item.plan),
  };
};

function snapshot(value: unknown): PaperSnapshot {
  const item = record(value);
  if (!Number.isSafeInteger(item.last_sequence))
    throw new Error("Invalid sequence.");
  const result: PaperSnapshot = {
    session: session(item.session),
    last_sequence: item.last_sequence as number,
    latest_bar: item.latest_bar === null ? null : marketBar(item.latest_bar),
    latest_session:
      item.latest_session == null ? null : marketSession(item.latest_session),
    signals: array(item.signals, signal),
    risk_decisions: array(item.risk_decisions, decision),
    orders: array(item.orders, order),
    fills: array(item.fills, fill),
    latest_portfolio:
      item.latest_portfolio === null ? null : portfolio(item.latest_portfolio),
    last_rebalance_plan:
      item.last_rebalance_plan == null
        ? null
        : parsePaperAccountPlan(item.last_rebalance_plan),
  };
  if (
    (result.latest_portfolio?.plan || result.last_rebalance_plan) &&
    (result.session.provider_type !== "historical_a_share" ||
      [result.latest_portfolio?.plan, result.last_rebalance_plan].some(
        (plan) => plan && plan.paper_session_id !== result.session.session_id,
      ))
  )
    throw new Error("Paper plan does not belong to this account.");
  return result;
}

function page(value: unknown): PaperSessionPage {
  const item = record(value);
  if (
    !Number.isSafeInteger(item.limit) ||
    !Number.isSafeInteger(item.offset) ||
    !Number.isSafeInteger(item.total)
  )
    throw new Error("Invalid paper pagination.");
  return {
    items: array(item.items, session),
    limit: item.limit as number,
    offset: item.offset as number,
    total: item.total as number,
  };
}

export const PAPER_WS_BASE_URL = API_BASE_URL.replace(/^http/, "ws");

export const paperApi = {
  list: (limit = 20, offset = 0, signal?: AbortSignal) =>
    apiRequest(
      `/api/paper-trading/sessions?limit=${limit}&offset=${offset}`,
      {},
      signal,
      page,
    ),
  get: (sessionId: string, signal?: AbortSignal) =>
    apiRequest(`/api/paper-trading/sessions/${sessionId}`, {}, signal, session),
  snapshot: (sessionId: string, signal?: AbortSignal) =>
    apiRequest(
      `/api/paper-trading/sessions/${sessionId}/snapshot`,
      {},
      signal,
      snapshot,
    ),
  create: (
    request: CreatePaperSessionRequest,
    key: string,
    signal?: AbortSignal,
  ) =>
    apiRequest(
      "/api/paper-trading/sessions",
      {
        method: "POST",
        headers: { "Content-Type": "application/json", "Idempotency-Key": key },
        body: JSON.stringify(request),
      },
      signal,
      session,
    ),
  start: (sessionId: string, signal?: AbortSignal) =>
    apiRequest(
      `/api/paper-trading/sessions/${sessionId}/start`,
      { method: "POST" },
      signal,
      session,
    ),
  pause: (sessionId: string, signal?: AbortSignal) =>
    apiRequest(
      `/api/paper-trading/sessions/${sessionId}/pause`,
      { method: "POST" },
      signal,
      session,
    ),
  stop: (sessionId: string, signal?: AbortSignal) =>
    apiRequest(
      `/api/paper-trading/sessions/${sessionId}/stop`,
      { method: "POST" },
      signal,
      session,
    ),
};

export const paperParsers = {
  session,
  snapshot,
  marketBar,
  marketSession,
  signal,
  decision,
  order,
  fill,
  portfolio,
};

export function parseWireEvent(value: unknown): PaperWireEvent {
  const item = record(value);
  if (item.sequence !== null && !Number.isSafeInteger(item.sequence))
    throw new Error("Invalid paper stream sequence.");
  const type = requiredString(item.type) as PaperWireEvent["type"];
  if (!EVENT_TYPES.has(type))
    throw new Error("Invalid paper stream event type.");
  const payload = record(item.payload);
  if (type === "stream.connected" || type === "stream.resync_required") {
    if (item.sequence !== null)
      throw new Error("Invalid paper control event sequence.");
  } else {
    if (
      !Number.isSafeInteger(item.sequence) ||
      typeof item.occurred_at !== "string"
    )
      throw new Error("Invalid persisted paper event envelope.");
    if (type === "session.status") {
      const status = requiredString(payload.status) as PaperSessionStatus;
      if (!STATUSES.has(status))
        throw new Error("Invalid paper session status.");
    } else if (type === "market.bar") marketBar(payload);
    else if (type === "market.session") marketSession(payload);
    else if (type === "signal.created") signal(payload);
    else if (type === "risk.decision") decision(payload);
    else if (type === "order.updated") order(payload);
    else if (type === "fill.created") fill(payload);
    else if (type === "portfolio.snapshot") portfolio(payload);
  }
  return {
    sequence: item.sequence as number | null,
    type,
    occurred_at:
      item.occurred_at === null ? null : requiredString(item.occurred_at),
    payload,
  };
}
