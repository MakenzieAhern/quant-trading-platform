import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { App } from "./App";
import { jsonResponse, RUN_ID } from "./test/fixtures";

const health = {
  status: "ok",
  service: "Quant Trading Platform",
  version: "1.0.0",
  environment: "development",
  broker_mode: "paper",
};

describe("routing", () => {
  it("names icon-only search and restores mobile navigation focus", () => {
    window.history.replaceState({}, "", "/unknown");
    vi.spyOn(globalThis, "fetch").mockResolvedValue(jsonResponse(health));
    render(<App />);
    expect(
      screen.getByRole("button", {
        name: "Search pages, strategies and research",
      }),
    ).toBeInTheDocument();
    const menu = screen.getByRole("button", { name: "Open navigation" });
    fireEvent.click(menu);
    expect(
      screen.getByRole("link", { name: /QUANT Research workspace/ }),
    ).toHaveFocus();
    fireEvent.keyDown(window, { key: "Escape" });
    expect(menu).toHaveFocus();
    expect(menu).toHaveAttribute("aria-expanded", "false");
  });

  it.each(["/unknown", "/backtests/not-a-uuid", "/backtests/1234"])(
    "fails safely for %s",
    async (pathname) => {
      window.history.replaceState({}, "", pathname);
      vi.spyOn(globalThis, "fetch").mockResolvedValue(jsonResponse(health));
      render(<App />);
      expect(
        screen.getByRole("heading", { name: "Page not found" }),
      ).toBeInTheDocument();
      expect(await screen.findByText("Service online")).toBeInTheDocument();
      expect(screen.getByTitle("development · paper")).toBeInTheDocument();
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

  it("supports a direct research dataset lineage URL", async () => {
    const datasetId = "cn-a-research-20100101-20251231-v1";
    window.history.replaceState(
      {},
      "",
      `/research/a-share/datasets/${datasetId}`,
    );
    vi.spyOn(globalThis, "fetch").mockImplementation((input) =>
      String(input).endsWith("/api/health")
        ? Promise.resolve(jsonResponse(health))
        : Promise.resolve(
            jsonResponse({
              dataset_id: datasetId,
              provider: "official-public-reconstruction",
              provider_version: "v1",
              retrieval_timestamp: "2026-09-21T00:00:00Z",
              coverage_start: "2010-01-01",
              coverage_end: "2025-12-31",
              security_count: 5431,
              canonical_sha256: "a".repeat(64),
              rule_version: "cn-a-v1",
              adjustment_method: "separate factors",
              readiness_status: "PASSED",
              frozen: true,
              manifest: { schema_version: "1" },
            }),
          ),
    );
    render(<App />);
    expect(
      await screen.findByRole("heading", { name: datasetId }),
    ).toBeInTheDocument();
    expect(screen.queryByText("Page not found")).not.toBeInTheDocument();
  });
});
