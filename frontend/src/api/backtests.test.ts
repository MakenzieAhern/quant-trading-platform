import { describe, expect, it, vi } from "vitest";

import { backtestsApi } from "./backtests";
import { ApiError, REQUEST_TIMEOUT_MS } from "./client";
import { ApiContractError } from "./contracts";
import { jsonResponse, RUN_ID } from "../test/fixtures";
import { formatDecimal, formatPercent, formatUtc } from "../utils/format";

describe("typed backtest API", () => {
  it("preserves Decimal response strings exactly", async () => {
    const decimal = "105.052500000000000001";
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      jsonResponse({
        items: [
          {
            timestamp: "2024-01-02T00:00:00Z",
            equity: decimal,
            cash: decimal,
            market_value: "0",
          },
        ],
        limit: 1,
        offset: 0,
        total: 1,
      }),
    );
    const page = await backtestsApi.equity(RUN_ID, 1, 0);
    expect(page.items[0]?.equity).toBe(decimal);
  });

  it.each([400, 404, 409, 422, 500])(
    "returns a safe typed HTTP %s error",
    async (status) => {
      vi.spyOn(globalThis, "fetch").mockResolvedValue(
        jsonResponse({ detail: "safe public message" }, status),
      );
      await expect(backtestsApi.get(RUN_ID)).rejects.toEqual(
        expect.objectContaining<ApiError>({
          status,
          name: "ApiError",
          message: "safe public message",
        }),
      );
    },
  );

  it("rejects malformed successful payloads without crashing renderers", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      jsonResponse({ items: [] }),
    );
    await expect(backtestsApi.list()).rejects.toBeInstanceOf(ApiContractError);
  });

  it("rejects invalid JSON with a stable safe error", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response("not-json", { status: 200 }),
    );
    await expect(backtestsApi.get(RUN_ID)).rejects.toEqual(
      expect.objectContaining<ApiError>({
        status: 502,
        name: "ApiError",
        message: "The API returned an invalid JSON response.",
      }),
    );
  });

  it("times out a request that never completes", async () => {
    vi.useFakeTimers();
    vi.spyOn(globalThis, "fetch").mockImplementation(
      (_input, init) =>
        new Promise((_resolve, reject) => {
          init?.signal?.addEventListener("abort", () =>
            reject(new DOMException("Aborted", "AbortError")),
          );
        }),
    );
    const request = backtestsApi.get(RUN_ID);
    const rejection = expect(request).rejects.toEqual(
      expect.objectContaining<ApiError>({
        status: 408,
        name: "ApiError",
        message: "The API request timed out.",
      }),
    );
    await vi.advanceTimersByTimeAsync(REQUEST_TIMEOUT_MS);
    await rejection;
  });
});

describe("display formatting", () => {
  it("formats without changing stored Decimal strings", () => {
    const source = "105.052500000000000001";
    expect(formatDecimal(source)).toBe("105.052500000000000001");
    expect(source).toBe("105.052500000000000001");
    expect(formatPercent("0.000122")).toBe("0.0122%");
    expect(formatDecimal("0.000000000000000001")).toBe("0.000000000000000001");
    expect(formatDecimal("999999999999999999.123456789012345678")).toBe(
      "999,999,999,999,999,999.123456789012345678",
    );
    expect(formatPercent("0.000000000000000001")).toBe("0.0000000000000001%");
  });

  it("labels UTC and undefined metrics explicitly", () => {
    expect(formatUtc("2024-01-02T00:00:00Z")).toContain("(UTC)");
    expect(formatDecimal(null)).toBe("N/A");
  });
});
