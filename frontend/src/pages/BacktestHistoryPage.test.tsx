import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { jsonResponse, run } from "../test/fixtures";
import { BacktestHistoryPage } from "./BacktestHistoryPage";

describe("backtest history", () => {
  it("renders persisted run identity, strategy, status, and UTC timestamps", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      jsonResponse({ items: [run()], limit: 20, offset: 0, total: 1 }),
    );
    render(<BacktestHistoryPage />);
    expect(
      await screen.findByText("Completed", { selector: ".statusBadge" }),
    ).toBeInTheDocument();
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

  it("renders each backend lifecycle status distinctly", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      jsonResponse({
        items: ["CREATED", "RUNNING", "SUCCEEDED", "FAILED"].map(
          (status, index) => ({
            ...run(status as ReturnType<typeof run>["status"]),
            run_id: `0000000${index}-0000-4000-8000-00000000000${index}`,
          }),
        ),
        limit: 20,
        offset: 0,
        total: 4,
      }),
    );
    render(<BacktestHistoryPage />);
    for (const label of ["Created", "Running", "Completed", "Failed"])
      expect(
        await screen.findByText(label, { selector: ".statusBadge" }),
      ).toBeInTheDocument();
  });

  it("loads the limit-plus-one boundary without duplicate rows", async () => {
    const firstIds = Array.from(
      { length: 20 },
      (_, index) => `1000000${index.toString(16)}-0000-4000-8000-000000000000`,
    );
    const finalId = "20000000-0000-4000-8000-000000000000";
    const fetch = vi.spyOn(globalThis, "fetch").mockImplementation((input) => {
      const secondPage = String(input).includes("offset=20");
      const ids = secondPage ? [finalId] : firstIds;
      return Promise.resolve(
        jsonResponse({
          items: ids.map((runId) => ({ ...run(), run_id: runId })),
          limit: 20,
          offset: secondPage ? 20 : 0,
          total: 21,
        }),
      );
    });
    render(<BacktestHistoryPage />);
    expect(await screen.findByTitle(firstIds[0]!)).toBeInTheDocument();
    expect(screen.getAllByRole("row")).toHaveLength(21);
    await userEvent.click(screen.getByRole("button", { name: "Next" }));
    expect(await screen.findByTitle(finalId)).toBeInTheDocument();
    expect(screen.queryByTitle(firstIds[0]!)).not.toBeInTheDocument();
    expect(screen.getAllByRole("row")).toHaveLength(2);
    expect(fetch).toHaveBeenCalledTimes(2);
  });

  it("shows malformed successful responses as a safe section error", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      jsonResponse({ items: "not-an-array", limit: 20, offset: 0, total: 0 }),
    );
    render(<BacktestHistoryPage />);
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "expected contract",
    );
  });
});
