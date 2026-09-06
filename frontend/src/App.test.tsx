import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { App } from "./App";
import { jsonResponse, RUN_ID } from "./test/fixtures";

const health = {
  status: "ok",
  service: "Quant Trading Platform",
  version: "0.1.0",
  environment: "development",
  broker_mode: "paper",
};

describe("routing", () => {
  it.each(["/unknown", "/backtests/not-a-uuid", "/backtests/1234"])(
    "fails safely for %s",
    async (pathname) => {
      window.history.replaceState({}, "", pathname);
      vi.spyOn(globalThis, "fetch").mockResolvedValue(jsonResponse(health));
      render(<App />);
      expect(
        screen.getByRole("heading", { name: "Page not found" }),
      ).toBeInTheDocument();
      expect(
        await screen.findByText("development · paper"),
      ).toBeInTheDocument();
    },
  );

  it("supports a direct detail URL and shows a safe 404 state", async () => {
    window.history.replaceState({}, "", `/backtests/${RUN_ID}`);
    vi.spyOn(globalThis, "fetch").mockImplementation((input) =>
      String(input).endsWith("/api/health")
        ? Promise.resolve(jsonResponse(health))
        : Promise.resolve(jsonResponse({ detail: "Run not found" }, 404)),
    );
    render(<App />);
    expect(await screen.findByText("Run not found")).toBeInTheDocument();
    expect(screen.queryByText("Page not found")).not.toBeInTheDocument();
  });
});
