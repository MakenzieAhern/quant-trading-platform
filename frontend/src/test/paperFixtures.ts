import type {
  PaperCollection,
  PaperCollectionPage,
  PaperSession,
  PaperSnapshot,
  PaperState,
} from "../types/paper";

export const PAPER_ID = "34d97303-a8c9-4f71-a0fc-c4b5d156f2ee";

export function paperCalendarEvent(
  kind: "initial" | "extension" = "initial",
  sequence = 1,
) {
  const appliedAt = "2026-10-03T00:00:00.123456Z";
  return {
    sequence,
    type: "calendar.observed" as const,
    occurred_at: appliedAt,
    payload: {
      schema_version: "PAPER_CALENDAR_V1" as const,
      kind,
      calendar: {
        market: "CN_A" as const,
        sessions: [
          {
            session_date: "2010-05-26",
            is_open: true,
            source_version: "audited-calendar-fixture",
          },
          {
            session_date: "2010-05-27",
            is_open: true,
            source_version: "audited-calendar-fixture",
          },
          ...(kind === "extension"
            ? [
                {
                  session_date: "2010-05-28",
                  is_open: true,
                  source_version: "audited-calendar-fixture",
                },
              ]
            : []),
        ],
      },
      // Contract-shape placeholders, not source-authority or checksum evidence.
      before_sha256: kind === "initial" ? null : "a".repeat(64),
      after_sha256: (kind === "initial" ? "a" : "b").repeat(64),
      applied_at: appliedAt,
      after_completed_sessions: kind === "initial" ? 0 : 1,
      after_trading_date: kind === "initial" ? null : "2010-05-26",
    },
  };
}

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
    last_rebalance_plan: null,
  };
}

const COLLECTION_TYPES = {
  signals: "signal.created",
  risk_decisions: "risk.decision",
  orders: "order.updated",
  fills: "fill.created",
} as const;

export function paperState(
  snapshot: PaperSnapshot = paperSnapshot(),
): PaperState {
  return {
    ...(snapshot.current_dataset_quality === undefined
      ? {}
      : { current_dataset_quality: snapshot.current_dataset_quality }),
    session: snapshot.session,
    last_sequence: snapshot.last_sequence,
    latest_bar: snapshot.latest_bar,
    latest_session: snapshot.latest_session,
    latest_portfolio: snapshot.latest_portfolio,
    last_rebalance_plan: snapshot.last_rebalance_plan,
  };
}

export function paperCollection(
  snapshot: PaperSnapshot,
  collection: PaperCollection,
  watermark = snapshot.last_sequence,
  offset = 0,
  sequences?: readonly number[],
): PaperCollectionPage {
  const payloads = snapshot[collection];
  const kinds = Object.keys(COLLECTION_TYPES) as PaperCollection[];
  const firstSequence =
    2 +
    kinds
      .slice(0, kinds.indexOf(collection))
      .reduce((count, kind) => count + snapshot[kind].length, 0);
  const assigned =
    sequences ?? payloads.map((_, index) => firstSequence + index);
  if (
    !Number.isSafeInteger(watermark) ||
    watermark < 0 ||
    watermark > 2147483647 ||
    !Number.isSafeInteger(offset) ||
    offset < 0 ||
    offset > 2147483647 ||
    assigned.length !== payloads.length ||
    new Set(assigned).size !== assigned.length ||
    assigned.some(
      (sequence) =>
        !Number.isSafeInteger(sequence) ||
        sequence <= 0 ||
        sequence > watermark,
    )
  )
    throw new Error("Inconsistent bounded paper fixture.");
  return {
    session_id: snapshot.session.session_id,
    collection,
    as_of_sequence: watermark,
    limit: 100 as const,
    offset,
    total: payloads.length,
    items: payloads.slice(offset, offset + 100).map((payload, index) => ({
      sequence: assigned[offset + index]!,
      type: COLLECTION_TYPES[collection],
      occurred_at:
        "timestamp" in payload ? payload.timestamp : payload.created_at,
      payload: { ...payload },
    })),
  };
}
