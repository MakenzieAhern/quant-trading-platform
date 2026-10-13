import { describe, expect, it, vi } from "vitest";

import { jsonResponse } from "../test/fixtures";
import { paperCapabilities } from "../test/paperFixtures";
import { paperApi } from "./paper";

function changedProvider(change: Record<string, unknown>) {
  const value = paperCapabilities();
  return {
    ...value,
    providers: [
      { ...value.providers[0], ...change },
      ...value.providers.slice(1),
    ],
  };
}

describe("paper capability contract", () => {
  it("reads the three exact identities with no-store and keeps forward unavailable", async () => {
    const expected = paperCapabilities();
    expected.providers[2]!.available = false;
    expected.providers[2]!.reason_code = "DATASET_NOT_MOUNTED";
    const fetch = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValue(jsonResponse(expected));
    expect(await paperApi.capabilities()).toEqual(expected);
    expect(
      new URL(String(fetch.mock.calls[0]![0]), "http://test.local").pathname,
    ).toBe("/api/paper-trading/sessions/capabilities");
    expect(fetch.mock.calls[0]![1]?.cache).toBe("no-store");
    expect(fetch.mock.calls[0]![1]?.method).toBeUndefined();
  });

  it.each([
    [
      "missing provider",
      {
        ...paperCapabilities(),
        providers: paperCapabilities().providers.slice(1),
      },
    ],
    [
      "duplicate provider",
      {
        ...paperCapabilities(),
        providers: Array(3).fill(paperCapabilities().providers[0]),
      },
    ],
    ["unknown provider", changedProvider({ provider_type: "forward" })],
    ["changed dataset", changedProvider({ dataset_id: "other" })],
    ["changed symbol", changedProvider({ symbol: "CN-A" })],
    ["missing available", changedProvider({ available: undefined })],
    ["truthy available", changedProvider({ available: "true" })],
    ["unavailable without reason", changedProvider({ available: false })],
    [
      "available with reason",
      changedProvider({ reason_code: "REPLAY_DATA_INVALID" }),
    ],
    [
      "unknown reason",
      changedProvider({ available: false, reason_code: "NEW_REASON" }),
    ],
    ["missing reason", changedProvider({ reason_code: undefined })],
    ["missing forward", { ...paperCapabilities(), forward: undefined }],
    [
      "enabled forward",
      {
        ...paperCapabilities(),
        forward: { available: true, reason_code: "FORWARD_NOT_AVAILABLE" },
      },
    ],
    [
      "missing forward authority",
      {
        ...paperCapabilities(),
        forward: { reason_code: "FORWARD_NOT_AVAILABLE" },
      },
    ],
    [
      "wrong forward reason",
      {
        ...paperCapabilities(),
        forward: { available: false, reason_code: null },
      },
    ],
    [
      "reordered identities",
      {
        ...paperCapabilities(),
        providers: paperCapabilities().providers.reverse(),
      },
    ],
  ])("rejects %s rather than enabling creation", async (_name, value) => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(jsonResponse(value));
    await expect(paperApi.capabilities()).rejects.toThrow();
  });
});
