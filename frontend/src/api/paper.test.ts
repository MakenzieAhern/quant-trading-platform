import { describe, expect, it, vi } from "vitest";

import { paperApi, parseWireEvent } from "./paper";
import { applyPaperEvent } from "../hooks/usePaperStream";
import { plan } from "../product/experiments/fixtures.test-data";
import { jsonResponse } from "../test/fixtures";
import { PAPER_ID, paperSession, paperSnapshot } from "../test/paperFixtures";

describe("paper API contracts", () => {
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
