import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { jsonResponse, run } from "../test/fixtures";
import { BacktestHistoryPage } from "./BacktestHistoryPage";

describe("backtest history", () => {
  it("renders persisted run identity, strategy, status, and UTC timestamps", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      jsonResponse({ items: [run()], limit: 20, offset: 0, total: 1 }),
    );
    render(<BacktestHistoryPage />);
    expect(await screen.findByText("SUCCEEDED")).toBeInTheDocument();
    expect(screen.getByText("moving average crossover")).toBeInTheDocument();
    expect(screen.getAllByText(/2024-01-02 00:00:0\dZ \(UTC\)/)).toHaveLength(
      3,
    );
  });

  it("renders an explicit empty state", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      jsonResponse({ items: [], limit: 20, offset: 0, total: 0 }),
    );
    render(<BacktestHistoryPage />);
    expect(await screen.findByText(/No backtests yet/)).toBeInTheDocument();
  });
});
