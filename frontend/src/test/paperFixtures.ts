import type { PaperSession, PaperSnapshot } from "../types/paper";

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
