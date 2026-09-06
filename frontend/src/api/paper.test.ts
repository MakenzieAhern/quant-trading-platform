import { describe, expect, it, vi } from "vitest";

import { paperApi, parseWireEvent } from "./paper";
import { jsonResponse } from "../test/fixtures";
import { PAPER_ID, paperSession, paperSnapshot } from "../test/paperFixtures";

describe("paper API contracts", () => {
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
    };
    vi.spyOn(globalThis, "fetch").mockResolvedValue(jsonResponse(snapshot));
    const result = await paperApi.snapshot(PAPER_ID);
    expect(result.latest_portfolio?.equity).toBe("100012.252500000000000001");
    expect(result.latest_portfolio?.realized_pnl).toBe("0.000000000000000001");
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
  });
});
