import { describe, expect, it, vi } from "vitest";

import { describeConnection, getHealth } from "./health";
import { REQUEST_TIMEOUT_MS } from "./client";

describe("describeConnection", () => {
  it.each(["headers", "body"])(
    "bounds a stalled health response at %s",
    async (stage) => {
      vi.useFakeTimers();
      vi.spyOn(globalThis, "fetch").mockImplementation((_input, init) => {
        const pending = new Promise<never>((_resolve, reject) => {
          init?.signal?.addEventListener("abort", () =>
            reject(new DOMException("Aborted", "AbortError")),
          );
        });
        return stage === "headers"
          ? pending
          : Promise.resolve({
              ok: true,
              json: () => pending,
            } as unknown as Response);
      });
      const request = getHealth();
      const assertion = expect(request).rejects.toMatchObject({ status: 408 });
      await vi.advanceTimersByTimeAsync(REQUEST_TIMEOUT_MS);
      await assertion;
    },
  );
  it("labels the active safe trading mode", () => {
    expect(
      describeConnection({
        status: "ok",
        service: "Quant Trading Platform",
        version: "1.0.0",
        environment: "development",
        broker_mode: "paper",
      }),
    ).toBe("development · paper");
  });
});
