import { describe, expect, it } from "vitest";

import { describeConnection } from "./health";

describe("describeConnection", () => {
  it("labels the active safe trading mode", () => {
    expect(
      describeConnection({
        status: "ok",
        service: "Quant Trading Platform",
        version: "0.1.0",
        environment: "development",
        broker_mode: "paper",
      }),
    ).toBe("development · paper");
  });
});
