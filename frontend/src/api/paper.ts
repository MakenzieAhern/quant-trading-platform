import { apiRequest } from "./client";
import { API_BASE_URL } from "./config";
import {
  parseCurrentDatasetQuality,
  parseCurrentSourceIntegrity,
  parsePaperAccountPlan,
} from "../product/experiments/api";
import type {
  CreatePaperSessionRequest,
  MarketBar,
  MarketSession,
  PaperCalendarPayload,
  PaperCollection,
  PaperCollectionPage,
  PaperFill,
  PaperJournalEvent,
  PaperOrder,
  PaperPortfolio,
  PaperRiskDecision,
  PaperSession,
  PaperSessionPage,
  PaperSessionStatus,
  PaperSignal,
  PaperSnapshot,
  PaperState,
  PaperWireEvent,
} from "../types/paper";

const DECIMAL = /^-?\d+(?:\.\d+)?$/;
const MAX_SEQUENCE = 2147483647;
const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
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
  "calendar.observed",
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

function calendarFields(item: Record<string, unknown>, keys: string[]) {
  if (
    Object.keys(item).length !== keys.length ||
    keys.some((key) => !Object.hasOwn(item, key))
  )
    throw new Error("Invalid paper calendar fields.");
}

function calendarDate(value: unknown): string {
  const text = requiredString(value);
  const date = new Date(`${text}T00:00:00Z`);
  if (
    !/^\d{4}-\d{2}-\d{2}$/.test(text) ||
    text.startsWith("0000") ||
    !Number.isFinite(date.getTime()) ||
    date.toISOString().slice(0, 10) !== text
  )
    throw new Error("Invalid paper calendar date.");
  return text;
}

function calendarUtc(value: unknown): string {
  const text = requiredString(value);
  const match =
    /^(\d{4}-\d{2}-\d{2})T(\d{2}):(\d{2}):(\d{2})(?:\.(\d{1,6}))?(?:Z|\+00:00)$/.exec(
      text,
    );
  if (
    !match ||
    Number(match[2]) > 23 ||
    Number(match[3]) > 59 ||
    Number(match[4]) > 59
  )
    throw new Error("Invalid paper calendar UTC timestamp.");
  calendarDate(match[1]);
  // Preserve microseconds: Date.parse alone would equate different instants.
  return `${match[1]}T${match[2]}:${match[3]}:${match[4]}.${(match[5] ?? "").padEnd(6, "0")}Z`;
}

function calendarObservation(value: unknown): PaperCalendarPayload {
  const item = record(value);
  calendarFields(item, [
    "schema_version",
    "kind",
    "calendar",
    "before_sha256",
    "after_sha256",
    "applied_at",
    "after_completed_sessions",
    "after_trading_date",
  ]);
  const kind = requiredString(item.kind);
  const before = item.before_sha256;
  const after = requiredString(item.after_sha256);
  const count = item.after_completed_sessions;
  const completedDate =
    item.after_trading_date === null
      ? null
      : calendarDate(item.after_trading_date);
  if (
    item.schema_version !== "PAPER_CALENDAR_V1" ||
    (kind !== "initial" && kind !== "extension") ||
    !/^[a-f0-9]{64}$/.test(after) ||
    !Number.isSafeInteger(count) ||
    Number(count) < 0 ||
    (count === 0 && completedDate !== null) ||
    (Number(count) > 0 && completedDate === null) ||
    (kind === "initial" && (before !== null || count !== 0)) ||
    (kind === "extension" &&
      (typeof before !== "string" ||
        !/^[a-f0-9]{64}$/.test(before) ||
        before === after))
  )
    throw new Error("Invalid paper calendar observation.");
  const calendar = record(item.calendar);
  calendarFields(calendar, ["market", "sessions"]);
  if (calendar.market !== "CN_A")
    throw new Error("Invalid paper calendar market.");
  const sessions = array(calendar.sessions, (value) => {
    const session = record(value);
    calendarFields(session, ["session_date", "is_open", "source_version"]);
    const source = requiredString(session.source_version);
    if (typeof session.is_open !== "boolean" || source.length === 0)
      throw new Error("Invalid paper calendar session.");
    return {
      session_date: calendarDate(session.session_date),
      is_open: session.is_open,
      source_version: source,
    };
  });
  if (
    sessions.some(
      (session, index) =>
        index > 0 && session.session_date <= sessions[index - 1]!.session_date,
    )
  )
    throw new Error("Invalid paper calendar order.");
  calendarUtc(item.applied_at);
  return {
    schema_version: "PAPER_CALENDAR_V1",
    kind,
    calendar: { market: "CN_A", sessions },
    before_sha256: before as string | null,
    after_sha256: after,
    applied_at: requiredString(item.applied_at),
    after_completed_sessions: count as number,
    after_trading_date: completedDate,
  };
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
    ...(item.cancellation_reason_code == null
      ? {}
      : {
          cancellation_reason_code: requiredString(
            item.cancellation_reason_code,
          ),
        }),
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

function state(value: unknown): PaperState {
  const item = record(value);
  if (
    !Number.isSafeInteger(item.last_sequence) ||
    Number(item.last_sequence) < 0 ||
    Number(item.last_sequence) > MAX_SEQUENCE
  )
    throw new Error("Invalid sequence.");
  const result: PaperState = {
    ...(item.current_source_integrity === undefined
      ? {}
      : {
          current_source_integrity: parseCurrentSourceIntegrity(
            item.current_source_integrity,
          ),
        }),
    ...(item.current_dataset_quality === undefined
      ? {}
      : {
          current_dataset_quality: parseCurrentDatasetQuality(
            item.current_dataset_quality,
          ),
        }),
    session: session(item.session),
    last_sequence: item.last_sequence as number,
    latest_bar: item.latest_bar === null ? null : marketBar(item.latest_bar),
    latest_session:
      item.latest_session == null ? null : marketSession(item.latest_session),
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

function snapshot(value: unknown): PaperSnapshot {
  const item = record(value);
  return {
    ...state(item),
    signals: array(item.signals, signal),
    risk_decisions: array(item.risk_decisions, decision),
    orders: array(item.orders, order),
    fills: array(item.fills, fill),
  };
}

const COLLECTION_EVENT_TYPES = {
  signals: "signal.created",
  risk_decisions: "risk.decision",
  orders: "order.updated",
  fills: "fill.created",
} as const;

function collectionPage(value: unknown): PaperCollectionPage {
  const item = record(value);
  const collection = requiredString(item.collection) as PaperCollection;
  if (
    !Object.hasOwn(COLLECTION_EVENT_TYPES, collection) ||
    !Number.isSafeInteger(item.as_of_sequence) ||
    Number(item.as_of_sequence) < 0 ||
    Number(item.as_of_sequence) > MAX_SEQUENCE ||
    !Number.isSafeInteger(item.limit) ||
    Number(item.limit) < 1 ||
    Number(item.limit) > 100 ||
    !Number.isSafeInteger(item.offset) ||
    Number(item.offset) < 0 ||
    Number(item.offset) > MAX_SEQUENCE ||
    !Number.isSafeInteger(item.total) ||
    Number(item.total) < 0 ||
    Number(item.total) > Number(item.as_of_sequence)
  )
    throw new Error("Invalid paper collection page.");
  const count = Math.min(
    Number(item.limit),
    Math.max(0, Number(item.total) - Number(item.offset)),
  );
  if (!Array.isArray(item.items) || item.items.length !== count)
    throw new Error("Invalid paper collection records.");
  const items = item.items.map(journalEvent);
  if (
    items.some(
      (event) =>
        event.type !== COLLECTION_EVENT_TYPES[collection] ||
        event.sequence > Number(item.as_of_sequence),
    ) ||
    new Set(items.map((event) => event.sequence)).size !== items.length
  )
    throw new Error("Invalid paper collection records.");
  if (collection === "orders") {
    const ids = items.map((event) => requiredString(event.payload.order_id));
    if (
      ids.some((id) => !UUID.test(id)) ||
      new Set(ids.map((id) => id.toLowerCase())).size !== ids.length
    )
      throw new Error("Invalid current paper orders.");
  } else if (
    items.some(
      (event, index) =>
        index > 0 && event.sequence <= items[index - 1]!.sequence,
    )
  ) {
    throw new Error("Invalid paper collection order.");
  }
  return {
    session_id: requiredString(item.session_id),
    collection,
    as_of_sequence: item.as_of_sequence as number,
    limit: item.limit as number,
    offset: item.offset as number,
    total: item.total as number,
    items,
  };
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
  receipt: (key: string, signal?: AbortSignal) =>
    apiRequest(
      "/api/paper-trading/sessions/receipt",
      { headers: { "Idempotency-Key": key } },
      signal,
      session,
    ),
  snapshot: (sessionId: string, signal?: AbortSignal) =>
    apiRequest(
      `/api/paper-trading/sessions/${sessionId}/snapshot`,
      {},
      signal,
      snapshot,
    ),
  state: (sessionId: string, signal?: AbortSignal) =>
    apiRequest(
      `/api/paper-trading/sessions/${sessionId}/state`,
      {},
      signal,
      (value) => {
        signal?.throwIfAborted();
        const result = state(value);
        if (result.session.session_id !== sessionId)
          throw new Error("Paper state does not belong to this account.");
        return result;
      },
    ),
  collection: (
    sessionId: string,
    collection: PaperCollection,
    asOfSequence: number,
    offset = 0,
    signal?: AbortSignal,
  ) =>
    apiRequest(
      `/api/paper-trading/sessions/${sessionId}/collections/${collection}?as_of_sequence=${asOfSequence}&limit=100&offset=${offset}`,
      {},
      signal,
      (value) => {
        signal?.throwIfAborted();
        const result = collectionPage(value);
        if (
          result.session_id !== sessionId ||
          result.collection !== collection ||
          result.as_of_sequence !== asOfSequence ||
          result.limit !== 100 ||
          result.offset !== offset
        )
          throw new Error("Paper collection does not match this request.");
        return result;
      },
    ),
  events: (sessionId: string, beforeSequence?: number, signal?: AbortSignal) =>
    apiRequest(
      `/api/paper-trading/sessions/${sessionId}/events?limit=51${beforeSequence === undefined ? "" : `&before_sequence=${beforeSequence}`}`,
      {},
      signal,
      journalPage,
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
  state,
  collection: collectionPage,
  marketBar,
  marketSession,
  calendar: calendarObservation,
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
    else if (type === "calendar.observed") {
      const observation = calendarObservation(payload);
      if (
        Number(item.sequence) <= 0 ||
        calendarUtc(item.occurred_at) !== calendarUtc(observation.applied_at)
      )
        throw new Error("Invalid paper calendar event envelope.");
    } else if (type === "signal.created") signal(payload);
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

function journalEvent(value: unknown): PaperJournalEvent {
  const event = parseWireEvent(value);
  const type = event.type;
  if (
    event.sequence === null ||
    event.sequence <= 0 ||
    event.occurred_at === null ||
    type === "stream.connected" ||
    type === "stream.resync_required"
  )
    throw new Error("Invalid persisted paper event.");
  return {
    ...event,
    type,
    sequence: event.sequence,
    occurred_at: event.occurred_at,
  };
}

function journalPage(value: unknown): PaperJournalEvent[] {
  if (!Array.isArray(value) || value.length > 51)
    throw new Error("Invalid paper event page.");
  const events = value.map(journalEvent);
  if (
    events.some(
      (event, index) =>
        index > 0 && event.sequence >= events[index - 1]!.sequence,
    )
  )
    throw new Error("Invalid paper event order.");
  return events;
}
