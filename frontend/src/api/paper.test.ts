import { describe, expect, it, vi } from "vitest";

import { paperApi, paperParsers, parseWireEvent } from "./paper";
import { applyPaperEvent } from "../hooks/usePaperStream";
import { plan } from "../product/experiments/fixtures.test-data";
import { jsonResponse } from "../test/fixtures";
import {
  PAPER_ID,
  paperCalendarEvent,
  paperCollection,
  paperSession,
  paperSnapshot,
  paperState,
} from "../test/paperFixtures";

function boundedSnapshot() {
  const snapshot = paperSnapshot("STOPPED");
  snapshot.last_sequence = 1000;
  const timestamp = "2024-01-09T00:00:00Z";
  snapshot.signals = Array.from({ length: 205 }, (_, index) => ({
    strategy_id: "exact-contract-fixture",
    symbol: `AAPL-${index}`,
    timestamp,
    signal_type: "BUY",
  }));
  snapshot.risk_decisions = snapshot.signals.map((_, index) => ({
    proposal_id: `abcdefab-cdef-4000-8000-${(index + 1).toString(16).padStart(12, "0")}`,
    approved: true,
    reason_code: "APPROVED",
    message: "Contract fixture, not market evidence.",
    timestamp,
  }));
  snapshot.orders = snapshot.risk_decisions.map((decision) => ({
    order_id: decision.proposal_id,
    strategy_id: "exact-contract-fixture",
    symbol: "AAPL",
    side: "BUY",
    order_type: "LIMIT",
    quantity: "10.000000000000000001",
    price: "9.123456789123456789",
    status: "FILLED",
    created_at: timestamp,
  }));
  snapshot.fills = [...snapshot.orders, snapshot.orders[0]!].map((order) => ({
    order_id: order.order_id,
    strategy_id: order.strategy_id,
    symbol: order.symbol,
    side: order.side,
    quantity: order.quantity,
    price: order.price!,
    commission: "0.000000000000000001",
    timestamp,
  }));
  snapshot.latest_portfolio = {
    timestamp,
    cash: "98160.852500000000000001",
    market_value: "1851.4",
    equity: "100012.252500000000000001",
    realized_pnl: "0.000000000000000001",
    unrealized_pnl: "12.2",
    cumulative_commission: "0.000000000000000001",
    drawdown: "0",
    positions: [],
    plan: null,
  };
  return snapshot;
}

describe("paper API contracts", () => {
  it("keeps read quality in the state envelope, never portfolio or plan", async () => {
    const header = {
      ...paperState(boundedSnapshot()),
      current_dataset_quality: "KNOWN_ECONOMIC_COVERAGE_GAP",
    };
    const before = JSON.stringify(header);
    const fetch = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValue(jsonResponse(header));
    expect(await paperApi.state(PAPER_ID)).toEqual(header);
    expect(JSON.stringify(header)).toBe(before);
    fetch.mockResolvedValue(
      jsonResponse({ ...header, current_dataset_quality: "PASS" }),
    );
    await expect(paperApi.state(PAPER_ID)).rejects.toThrow();
  });
  it("loads a collection-free authoritative state with exact Decimal strings", async () => {
    const snapshot = boundedSnapshot();
    const header = paperState(snapshot);
    const controller = new AbortController();
    const fetch = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValue(jsonResponse(header));
    const result = await paperApi.state(PAPER_ID, controller.signal);
    expect(result).toEqual(header);
    expect(result.latest_portfolio?.equity).toBe("100012.252500000000000001");
    for (const collection of ["signals", "risk_decisions", "orders", "fills"])
      expect(result).not.toHaveProperty(collection);
    expect(snapshot.fills).toHaveLength(206);
    expect(fetch.mock.calls[0]?.[0]).toContain(`/${PAPER_ID}/state`);
    expect(fetch.mock.calls[0]?.[1]?.method).toBeUndefined();
    expect(fetch.mock.calls[0]?.[1]?.signal).toBeInstanceOf(AbortSignal);
  });

  it("rejects invalid state money, watermarks and another account", async () => {
    const header = paperState(boundedSnapshot());
    const fetch = vi.spyOn(globalThis, "fetch");
    const invalid = [
      ...[-1, 0.5, "1000", 2147483648, Number.MAX_SAFE_INTEGER + 1].map(
        (last_sequence) => ({ ...header, last_sequence }),
      ),
      { ...header, session: { ...header.session, session_id: "other" } },
      { ...header, session: { ...header.session, initial_cash: 100000 } },
      {
        ...header,
        latest_portfolio: { ...header.latest_portfolio, cash: 98160.85 },
      },
      {
        ...header,
        latest_portfolio: { ...header.latest_portfolio, equity: "NaN" },
      },
    ];
    for (const payload of invalid) {
      fetch.mockResolvedValue(jsonResponse(payload));
      await expect(paperApi.state(PAPER_ID)).rejects.toThrow();
    }
  });

  it.each(["signals", "risk_decisions", "orders", "fills"] as const)(
    "pages all %s at fixed 100 without losing exact payloads",
    async (collection) => {
      const snapshot = boundedSnapshot();
      const fetch = vi
        .spyOn(globalThis, "fetch")
        .mockImplementation(async (request) => {
          const url = new URL(String(request), "http://localhost");
          expect(url.pathname).toBe(
            `/api/paper-trading/sessions/${PAPER_ID}/collections/${collection}`,
          );
          expect(url.searchParams.get("as_of_sequence")).toBe("1000");
          expect(url.searchParams.get("limit")).toBe("100");
          return jsonResponse(
            paperCollection(
              snapshot,
              collection,
              1000,
              Number(url.searchParams.get("offset")),
            ),
          );
        });
      const combined: Record<string, unknown>[] = [];
      for (const offset of [0, 100, 200]) {
        const result = await paperApi.collection(
          PAPER_ID,
          collection,
          1000,
          offset,
        );
        expect(result.total).toBe(snapshot[collection].length);
        expect(result.items).toHaveLength(Math.min(100, result.total - offset));
        combined.push(...result.items.map((item) => item.payload));
      }
      expect(combined).toEqual(snapshot[collection]);
      expect(fetch).toHaveBeenCalledTimes(3);
      if (collection === "fills") {
        expect(combined[0]?.quantity).toBe("10.000000000000000001");
        expect(combined[0]?.commission).toBe("0.000000000000000001");
        expect(combined[205]?.order_id).toBe(combined[0]?.order_id);
      }
    },
  );

  it("rejects mismatched collection requests, bounds and incomplete records", async () => {
    const page = paperCollection(boundedSnapshot(), "fills");
    const first = page.items[0]!;
    const fetch = vi.spyOn(globalThis, "fetch");
    const invalid = [
      { ...page, session_id: "other" },
      { ...page, collection: "orders" },
      { ...page, collection: "unknown" },
      ...[-1, 0.5, "1000", 999, 2147483648].map((as_of_sequence) => ({
        ...page,
        as_of_sequence,
      })),
      ...[0, 99, 101, "100"].map((limit) => ({ ...page, limit })),
      ...[-1, 1, 0.5, "0", 2147483648].map((offset) => ({ ...page, offset })),
      ...[-1, 0.5, "206", Number.MAX_SAFE_INTEGER + 1].map((total) => ({
        ...page,
        total,
      })),
      { ...page, items: null },
      { ...page, items: page.items.slice(0, 99) },
      { ...page, items: [...page.items, { ...first, sequence: 999 }] },
      {
        ...page,
        items: page.items.map((item, index) =>
          index === 0
            ? {
                ...item,
                type: "session.status",
                payload: { status: "CREATED" },
              }
            : item,
        ),
      },
      ...[0, -1, 0.5, "616", 1001].map((sequence) => ({
        ...page,
        items: [{ ...first, sequence }, ...page.items.slice(1)],
      })),
      {
        ...page,
        items: [
          { ...first, sequence: page.items[1]!.sequence },
          ...page.items.slice(1),
        ],
      },
      {
        ...page,
        items: [
          {
            ...first,
            payload: { order_id: first.payload.order_id, status: "CREATED" },
          },
          ...page.items.slice(1),
        ],
      },
      {
        ...page,
        items: [
          { ...first, payload: { ...first.payload, quantity: 10 } },
          ...page.items.slice(1),
        ],
      },
      {
        ...page,
        items: [
          { ...first, payload: { ...first.payload, commission: "Infinity" } },
          ...page.items.slice(1),
        ],
      },
    ];
    for (const payload of invalid) {
      fetch.mockResolvedValue(jsonResponse(payload));
      await expect(
        paperApi.collection(PAPER_ID, "fills", 1000, 0),
      ).rejects.toThrow();
    }
  });

  it.each(["signals", "risk_decisions", "fills"] as const)(
    "rejects reversed %s event order",
    async (collection) => {
      const page = paperCollection(boundedSnapshot(), collection);
      vi.spyOn(globalThis, "fetch").mockResolvedValue(
        jsonResponse({ ...page, items: [...page.items].reverse() }),
      );
      await expect(
        paperApi.collection(PAPER_ID, collection, 1000, 0),
      ).rejects.toThrow();
    },
  );

  it("accepts current orders in first-seen order, rejecting canonical duplicate IDs", async () => {
    const snapshot = boundedSnapshot();
    snapshot.signals = [];
    snapshot.risk_decisions = [];
    snapshot.fills = [];
    snapshot.orders = snapshot.orders.slice(0, 2);
    const page = paperCollection(snapshot, "orders", 1000, 0, [9, 4]);
    const fetch = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValue(jsonResponse(page));
    expect(
      (await paperApi.collection(PAPER_ID, "orders", 1000, 0)).items,
    ).toEqual(page.items);
    const orderId = page.items[0]!.payload.order_id as string;
    fetch.mockResolvedValue(
      jsonResponse({
        ...page,
        items: [
          page.items[0],
          {
            ...page.items[1],
            payload: {
              ...page.items[1]!.payload,
              order_id: orderId.toUpperCase(),
            },
          },
        ],
      }),
    );
    await expect(
      paperApi.collection(PAPER_ID, "orders", 1000, 0),
    ).rejects.toThrow();
  });

  it.each([
    ["signals", "signal_type", 1],
    ["risk_decisions", "approved", "true"],
    ["orders", "price", 9.1],
    ["fills", "commission", 0.1],
  ] as const)(
    "rejects malformed %s financial payloads",
    async (collection, field, value) => {
      const page = paperCollection(boundedSnapshot(), collection);
      const first = page.items[0]!;
      vi.spyOn(globalThis, "fetch").mockResolvedValue(
        jsonResponse({
          ...page,
          items: [
            { ...first, payload: { ...first.payload, [field]: value } },
            ...page.items.slice(1),
          ],
        }),
      );
      await expect(
        paperApi.collection(PAPER_ID, collection, 1000, 0),
      ).rejects.toThrow();
    },
  );

  it("rejects abbreviated orders even when their status is a valid session status", async () => {
    const page = paperCollection(boundedSnapshot(), "orders");
    const first = page.items[0]!;
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      jsonResponse({
        ...page,
        items: [
          {
            ...first,
            payload: { order_id: first.payload.order_id, status: "CREATED" },
          },
          ...page.items.slice(1),
        ],
      }),
    );
    await expect(
      paperApi.collection(PAPER_ID, "orders", 1000, 0),
    ).rejects.toThrow();
  });

  it("accepts zero-watermark empty pages and refuses contradictory fixtures", async () => {
    const snapshot = paperSnapshot();
    const page = paperCollection(snapshot, "fills", 0, 200);
    vi.spyOn(globalThis, "fetch").mockResolvedValue(jsonResponse(page));
    expect(await paperApi.collection(PAPER_ID, "fills", 0, 200)).toEqual(page);
    expect(() => paperCollection(boundedSnapshot(), "fills", 5)).toThrow(
      "fixture",
    );
    expect(() =>
      paperCollection(boundedSnapshot(), "orders", 1000, 0, [1]),
    ).toThrow("fixture");
  });

  it.each(["state", "collection"] as const)(
    "does not accept late %s response bodies after abort",
    async (method) => {
      const snapshot = boundedSnapshot();
      let resolveBody!: (value: unknown) => void;
      const body = new Promise<unknown>((resolve) => {
        resolveBody = resolve;
      });
      const response = jsonResponse({});
      vi.spyOn(response, "json").mockReturnValue(body);
      const fetch = vi.spyOn(globalThis, "fetch").mockResolvedValue(response);
      const controller = new AbortController();
      const pending =
        method === "state"
          ? paperApi.state(PAPER_ID, controller.signal)
          : paperApi.collection(PAPER_ID, "fills", 1000, 0, controller.signal);
      await Promise.resolve();
      controller.abort();
      resolveBody(
        method === "state"
          ? paperState(snapshot)
          : paperCollection(snapshot, "fills"),
      );
      await expect(pending).rejects.toMatchObject({ name: "AbortError" });
      expect(fetch.mock.calls[0]?.[1]?.signal?.aborted).toBe(true);
    },
  );

  it.each(["initial", "extension"] as const)(
    "accepts persisted %s calendar observations with the same UTC instant",
    (kind) => {
      const event = paperCalendarEvent(kind);
      const wire = {
        ...event,
        occurred_at: event.occurred_at.replace("Z", "+00:00"),
      };
      expect(parseWireEvent(wire)).toEqual(wire);
      expect(
        parseWireEvent({
          ...event,
          occurred_at: "2026-10-03T00:00:00.100000+00:00",
          payload: { ...event.payload, applied_at: "2026-10-03T00:00:00.1Z" },
        }).type,
      ).toBe("calendar.observed");
    },
  );

  it("retains the explicit processed-date anchor even without a financial market cursor", () => {
    const event = paperCalendarEvent("extension");
    const current = paperSnapshot("RUNNING");
    for (const after_trading_date of ["2010-05-26", "2010-05-27"]) {
      const wire = {
        ...event,
        payload: { ...event.payload, after_trading_date },
      };
      const parsed = parseWireEvent(wire);
      expect(parsed.payload.after_trading_date).toBe(after_trading_date);
      expect(applyPaperEvent(current, parsed)).toEqual({
        ...current,
        last_sequence: event.sequence,
      });
    }
    const beforeProcessing = {
      ...event,
      payload: {
        ...event.payload,
        after_completed_sessions: 0,
        after_trading_date: null,
      },
    };
    expect(parseWireEvent(beforeProcessing)).toEqual(beforeProcessing);
  });

  it("rejects malformed calendar payloads and mismatched or non-UTC envelopes", () => {
    const event = paperCalendarEvent();
    const payload = event.payload;
    const calendar = payload.calendar;
    const session = calendar.sessions[0]!;
    const extension = paperCalendarEvent("extension").payload;
    const missingDate: Record<string, unknown> = { ...payload };
    delete missingDate.after_trading_date;
    const invalid = [
      missingDate,
      { ...payload, after_trading_date: "2010-05-26" },
      { ...extension, after_trading_date: null },
      { ...extension, after_completed_sessions: 0 },
      { ...extension, after_trading_date: "2010-02-30" },
      { ...extension, after_trading_date: "2010-5-26" },
      { ...extension, after_trading_date: 20100526 },
      { ...extension, before_sha256: extension.after_sha256 },
      { ...payload, schema_version: "PAPER_CALENDAR_V2" },
      { ...payload, kind: "unknown" },
      { ...payload, extra: "not-in-contract" },
      { ...payload, calendar: undefined },
      { ...payload, before_sha256: "a".repeat(64) },
      { ...payload, kind: "extension", before_sha256: null },
      { ...payload, kind: "extension", before_sha256: "A".repeat(64) },
      { ...payload, after_sha256: "B".repeat(64) },
      { ...payload, after_sha256: "b".repeat(63) },
      { ...payload, after_completed_sessions: 1 },
      { ...payload, after_completed_sessions: -1 },
      { ...payload, after_completed_sessions: 0.5 },
      { ...payload, after_completed_sessions: "0" },
      { ...payload, after_completed_sessions: Number.MAX_SAFE_INTEGER + 1 },
      { ...payload, applied_at: "2026-10-03T00:00:00" },
      { ...payload, applied_at: "2026-10-03T08:00:00.123456+08:00" },
      { ...payload, applied_at: "2026-02-30T00:00:00.123456Z" },
      { ...payload, applied_at: "2026-10-03T24:00:00.123456Z" },
      { ...payload, applied_at: "2026-10-03T00:60:00.123456Z" },
      { ...payload, applied_at: "2026-10-03T00:00:60.123456Z" },
      { ...payload, calendar: { ...calendar, market: "US" } },
      { ...payload, calendar: { ...calendar, extra: true } },
      { ...payload, calendar: { ...calendar, sessions: [session, session] } },
      {
        ...payload,
        calendar: { ...calendar, sessions: [...calendar.sessions].reverse() },
      },
      ...[
        { ...session, session_date: "2010-02-30" },
        { ...session, session_date: "0000-01-01" },
        { ...session, session_date: "2010-5-26" },
        { ...session, session_date: 20100526 },
        { ...session, is_open: 1 },
        { ...session, source_version: "" },
        { ...session, source_version: null },
        { ...session, extra: true },
      ].map((invalidSession) => ({
        ...payload,
        calendar: { ...calendar, sessions: [invalidSession] },
      })),
    ];
    for (const invalidPayload of invalid)
      expect(() =>
        parseWireEvent({ ...event, payload: invalidPayload }),
      ).toThrow();
    for (const occurred_at of [
      "2026-10-03T00:00:00.123457Z",
      "2026-10-03T00:00:00Z",
      "2026-10-03T00:00:00.123456",
      "2026-10-03T08:00:00.123456+08:00",
    ])
      expect(() => parseWireEvent({ ...event, occurred_at })).toThrow();
    expect(() => parseWireEvent({ ...event, sequence: 0 })).toThrow();
    expect(() =>
      parseWireEvent({ ...event, type: "calendar.untrusted" }),
    ).toThrow();
  });

  it("advances calendar sequences only, preserving financial state and deduplicating", () => {
    const current = paperSnapshot("RUNNING");
    current.session.provider_type = "historical_a_share";
    current.last_sequence = 7;
    current.latest_session = {
      trading_date: "2010-05-26",
      security_count: 1,
      source: "FROZEN_HISTORICAL_A_SHARE_REPLAY_V1",
    };
    current.latest_portfolio = paperParsers.portfolio({
      timestamp: "2010-05-26T07:00:00Z",
      cash: "100000.000000000000000001",
      market_value: "0",
      equity: "100000.000000000000000001",
      realized_pnl: "0",
      unrealized_pnl: "0",
      cumulative_commission: "0",
      drawdown: "0",
      positions: [],
      plan: {
        ...plan,
        mode: "historical_exploration",
        account_mode: "HISTORICAL_PAPER_REPLAY",
        submitted_to_account: true,
        paper_session_id: PAPER_ID,
        plan_version: "PAPER_ACCOUNT_PLAN_V3",
      },
    });
    current.last_rebalance_plan = current.latest_portfolio.plan;
    current.fills = [
      paperParsers.fill({
        order_id: PAPER_ID,
        strategy_id: "cn_a_cross_sectional_momentum_low_vol_v1",
        symbol: "CN-A:SSE:600000",
        side: "BUY",
        quantity: "100",
        price: "10",
        commission: "5",
        timestamp: "2010-05-26T07:00:00Z",
      }),
    ];
    const event = parseWireEvent(paperCalendarEvent("extension", 8));
    const next = applyPaperEvent(current, event);
    expect(next).toEqual({ ...current, last_sequence: 8 });
    expect(next.session).toBe(current.session);
    expect(next.latest_session).toBe(current.latest_session);
    expect(next.latest_portfolio).toBe(current.latest_portfolio);
    expect(next.last_rebalance_plan).toBe(current.last_rebalance_plan);
    expect(next.fills).toBe(current.fills);
    expect(applyPaperEvent(next, event)).toBe(next);
    expect(
      applyPaperEvent(next, parseWireEvent(paperCalendarEvent("initial", 7))),
    ).toBe(next);
  });

  it("looks up a committed creation receipt with the original key", async () => {
    const fetch = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValue(jsonResponse(paperSession()));
    const result = await paperApi.receipt("original-key");
    expect(result.session_id).toBe(PAPER_ID);
    expect(fetch.mock.calls[0]?.[0]).toContain(
      "/api/paper-trading/sessions/receipt",
    );
    expect(fetch.mock.calls[0]?.[1]?.method).toBeUndefined();
    expect(
      new Headers(fetch.mock.calls[0]?.[1]?.headers).get("Idempotency-Key"),
    ).toBe("original-key");
  });

  it("preserves exact Decimal strings in authoritative snapshots", async () => {
    const snapshot = paperSnapshot("STOPPED");
    snapshot.orders = [
      {
        order_id: "966db07d-e61f-4ca8-aad0-e5774a63fc09",
        strategy_id: "gap-check",
        symbol: "AAPL",
        side: "BUY",
        order_type: "MARKET",
        quantity: "10",
        price: null,
        status: "CANCELLED",
        created_at: "2024-01-09T00:00:00Z",
        cancellation_reason_code: "INSUFFICIENT_BUYING_POWER",
      },
    ];
    snapshot.latest_portfolio = {
      timestamp: "2024-01-09T00:00:00Z",
      cash: "98160.852500000000000001",
      market_value: "1851.4",
      equity: "100012.252500000000000001",
      realized_pnl: "0.000000000000000001",
      unrealized_pnl: "12.2",
      cumulative_commission: "0",
      drawdown: "0",
      positions: [],
      plan: null,
    };
    vi.spyOn(globalThis, "fetch").mockResolvedValue(jsonResponse(snapshot));
    const result = await paperApi.snapshot(PAPER_ID);
    expect(result.latest_portfolio?.equity).toBe("100012.252500000000000001");
    expect(result.latest_portfolio?.realized_pnl).toBe("0.000000000000000001");
    expect(result.orders[0]?.cancellation_reason_code).toBe(
      "INSUFFICIENT_BUYING_POWER",
    );
  });

  it.each([
    "PAPER_ACCOUNT_PLAN_V1",
    "PAPER_ACCOUNT_PLAN_V2",
    "PAPER_ACCOUNT_PLAN_V3",
  ])("accepts %s only for its own account", async (version) => {
    const accountPlan = {
      ...plan,
      mode: "historical_exploration",
      account_mode: "HISTORICAL_PAPER_REPLAY",
      submitted_to_account: true,
      paper_session_id: PAPER_ID,
      plan_version: version,
    };
    const payload = {
      ...paperSnapshot("STOPPED"),
      last_rebalance_plan: accountPlan,
      session: {
        ...paperSession("STOPPED"),
        provider_type: "historical_a_share",
      },
      latest_portfolio: {
        timestamp: "2011-03-22T07:00:00Z",
        cash: "98160.852500000000000001",
        market_value: "1851.4",
        equity: "100012.252500000000000001",
        realized_pnl: "0",
        unrealized_pnl: "12.2",
        cumulative_commission: "0",
        drawdown: "0",
        positions: [],
        plan: accountPlan,
      },
    };
    const fetch = vi
      .spyOn(globalThis, "fetch")
      .mockImplementation(async () => jsonResponse(payload));
    expect(
      (await paperApi.snapshot(PAPER_ID)).latest_portfolio?.plan?.candidates[0]
        .reference_raw_close,
    ).toBe("9.123456789123456789");
    expect(
      (await paperApi.snapshot(PAPER_ID)).last_rebalance_plan?.paper_session_id,
    ).toBe(PAPER_ID);
    fetch.mockResolvedValue(
      jsonResponse({
        ...payload,
        last_rebalance_plan: { ...accountPlan, paper_session_id: "other" },
      }),
    );
    await expect(paperApi.snapshot(PAPER_ID)).rejects.toThrow(
      "does not belong",
    );
    fetch.mockResolvedValue(
      jsonResponse({
        ...payload,
        latest_portfolio: {
          ...payload.latest_portfolio,
          plan: { ...accountPlan, paper_session_id: "other" },
        },
      }),
    );
    await expect(paperApi.snapshot(PAPER_ID)).rejects.toThrow(
      "does not belong",
    );
    fetch.mockResolvedValue(
      jsonResponse({
        ...payload,
        latest_portfolio: {
          ...payload.latest_portfolio,
          plan: { ...accountPlan, estimated_cash_required: 917.3 },
        },
      }),
    );
    await expect(paperApi.snapshot(PAPER_ID)).rejects.toThrow();
    fetch.mockResolvedValue(
      jsonResponse({
        ...payload,
        last_rebalance_plan: {
          ...accountPlan,
          plan_version: "PAPER_ACCOUNT_PLAN_V4",
        },
      }),
    );
    await expect(paperApi.snapshot(PAPER_ID)).rejects.toThrow();
    fetch.mockResolvedValue(
      jsonResponse({
        ...payload,
        last_rebalance_plan: { ...accountPlan, plan_version: [version] },
      }),
    );
    await expect(paperApi.snapshot(PAPER_ID)).rejects.toThrow();
  });

  it("retains the last actual rebalance through later non-rebalance stream events", () => {
    const current = paperSnapshot("RUNNING");
    current.current_dataset_quality = "KNOWN_ECONOMIC_COVERAGE_GAP";
    current.session.provider_type = "historical_a_share";
    const accountPlan = {
      ...plan,
      mode: "historical_exploration",
      account_mode: "HISTORICAL_PAPER_REPLAY",
      submitted_to_account: true,
      paper_session_id: PAPER_ID,
      plan_version: "PAPER_ACCOUNT_PLAN_V1",
    };
    const portfolio = {
      timestamp: "2011-03-22T07:00:00Z",
      cash: "100000",
      market_value: "0",
      equity: "100000",
      realized_pnl: "0",
      unrealized_pnl: "0",
      cumulative_commission: "0",
      drawdown: "0",
      positions: [],
    };
    const event = (sequence: number, nextPlan: Record<string, unknown>) =>
      parseWireEvent({
        sequence,
        type: "portfolio.snapshot",
        occurred_at: "2011-03-22T07:00:00Z",
        payload: { ...portfolio, plan: nextPlan },
      });
    const rebalance = applyPaperEvent(current, event(1, accountPlan));
    const later = applyPaperEvent(
      rebalance,
      event(2, {
        ...accountPlan,
        status: "NOT_REBALANCE_SESSION",
        as_of_trading_date: "2011-03-23",
        candidates: [],
        submitted_to_account: false,
      }),
    );
    expect(later.latest_portfolio?.plan?.status).toBe("NOT_REBALANCE_SESSION");
    expect(later.current_dataset_quality).toBe(current.current_dataset_quality);
    expect(later.latest_portfolio?.plan).not.toHaveProperty(
      "current_dataset_quality",
    );
    expect(later.last_rebalance_plan?.as_of_trading_date).toBe(
      accountPlan.as_of_trading_date,
    );
    expect(() =>
      applyPaperEvent(
        rebalance,
        event(2, { ...accountPlan, paper_session_id: "other" }),
      ),
    ).toThrow("does not belong");
  });

  it("keeps each paper signal event while ignoring repeated sequences", () => {
    const signal = (sequence: number, symbol: string) =>
      parseWireEvent({
        sequence,
        type: "signal.created",
        occurred_at: "2011-03-22T07:00:00Z",
        payload: {
          strategy_id: "cn_a_cross_sectional_momentum_low_vol_v1",
          symbol,
          timestamp: "2011-03-22T07:00:00Z",
          signal_type: "BUY",
        },
      });
    const first = applyPaperEvent(
      paperSnapshot("RUNNING"),
      signal(1, "CN-A:SSE:600000"),
    );
    const second = applyPaperEvent(first, signal(2, "CN-A:SSE:600001"));
    const third = applyPaperEvent(second, signal(3, "CN-A:SSE:600000"));
    expect(third.signals.map((item) => item.symbol)).toEqual([
      "CN-A:SSE:600000",
      "CN-A:SSE:600001",
      "CN-A:SSE:600000",
    ]);
    expect(applyPaperEvent(third, signal(3, "CN-A:SSE:600000"))).toBe(third);
  });

  it("keeps distinct same-order fills while ignoring a repeated sequence", () => {
    const fill = (sequence: number, quantity: string, commission: string) =>
      parseWireEvent({
        sequence,
        type: "fill.created",
        occurred_at: "2011-03-22T07:00:00Z",
        payload: {
          order_id: "11111111-1111-4111-8111-111111111111",
          strategy_id: "cn_a_cross_sectional_momentum_low_vol_v1",
          symbol: "CN-A:SSE:600000",
          side: "BUY",
          quantity,
          price: "10",
          commission,
          timestamp: "2011-03-22T07:00:00Z",
        },
      });
    const first = applyPaperEvent(
      paperSnapshot("RUNNING"),
      fill(1, "10", "0.1"),
    );
    const second = applyPaperEvent(first, fill(2, "5", "0.05"));
    expect(
      second.fills.map((item) => [item.quantity, item.commission]),
    ).toEqual([
      ["10", "0.1"],
      ["5", "0.05"],
    ]);
    expect(applyPaperEvent(second, fill(2, "5", "0.05"))).toBe(second);
  });

  it("rejects malformed successful responses", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      jsonResponse({ ...paperSession(), initial_cash: 100000 }),
    );
    await expect(paperApi.get(PAPER_ID)).rejects.toThrow("expected contract");
  });

  it("validates typed stream envelopes", () => {
    expect(
      parseWireEvent({
        sequence: 3,
        type: "session.status",
        occurred_at: "2026-09-06T02:00:00Z",
        payload: { status: "RUNNING" },
      }).sequence,
    ).toBe(3);
    expect(() =>
      parseWireEvent({ sequence: "3", type: "x", payload: {} }),
    ).toThrow("sequence");
    expect(
      parseWireEvent({
        sequence: 4,
        type: "market.session",
        occurred_at: "2030-12-23T07:00:00Z",
        payload: {
          trading_date: "2030-12-23",
          security_count: 10,
          source: "SIMULATED_SCENARIO_NOT_RESEARCH_EVIDENCE_V1",
        },
      }).type,
    ).toBe("market.session");
  });
});
