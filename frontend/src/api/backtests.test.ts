import { describe, expect, it, vi } from "vitest";

import { backtestsApi } from "./backtests";
import { ApiError } from "./client";
import { jsonResponse, RUN_ID } from "../test/fixtures";
import { formatDecimal, formatPercent, formatUtc } from "../utils/format";

describe("typed backtest API", () => {
  it("preserves Decimal response strings exactly", async () => {
    const decimal = "105.052500000000000001";
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      jsonResponse({
        items: [{ equity: decimal }],
        limit: 1,
        offset: 0,
        total: 1,
      }),
    );
    const page = await backtestsApi.equity(RUN_ID, 1, 0);
    expect(page.items[0]?.equity).toBe(decimal);
  });

  it.each([409, 422, 500])(
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
});

describe("display formatting", () => {
  it("formats without changing stored Decimal strings", () => {
    const source = "105.052500000000000001";
    expect(formatDecimal(source)).toBe("105.0525");
    expect(source).toBe("105.052500000000000001");
    expect(formatPercent("0.000122")).toBe("0.0122%");
  });

  it("labels UTC and undefined metrics explicitly", () => {
    expect(formatUtc("2024-01-02T00:00:00Z")).toContain("(UTC)");
    expect(formatDecimal(null)).toBe("N/A");
  });
});
