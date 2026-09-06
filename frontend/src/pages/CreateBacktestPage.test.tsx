import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { jsonResponse, RUN_ID } from "../test/fixtures";
import { CreateBacktestPage } from "./CreateBacktestPage";

describe("create backtest", () => {
  it("validates strategy periods before submission", async () => {
    const fetch = vi.spyOn(globalThis, "fetch");
    render(<CreateBacktestPage />);
    fireEvent.change(screen.getByLabelText("Short period"), {
      target: { value: "4" },
    });
    fireEvent.change(screen.getByLabelText("Long period"), {
      target: { value: "3" },
    });
    await userEvent.click(screen.getByRole("button", { name: "Run backtest" }));
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Short period must be less",
    );
    expect(fetch).not.toHaveBeenCalled();
  });

  it("submits exact strings once with an Idempotency-Key and navigates", async () => {
    const fetch = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValue(
        jsonResponse({ run_id: RUN_ID, status: "SUCCEEDED", links: {} }, 201),
      );
    render(<CreateBacktestPage />);
    await userEvent.click(screen.getByRole("button", { name: "Run backtest" }));
    await waitFor(() =>
      expect(window.location.pathname).toBe(`/backtests/${RUN_ID}`),
    );
    expect(fetch).toHaveBeenCalledTimes(1);
    const request = fetch.mock.calls[0];
    const init = request?.[1];
    expect(new Headers(init?.headers).get("Idempotency-Key")).toBeTruthy();
    expect(JSON.parse(String(init?.body))).toMatchObject({
      initial_cash: "100000",
      default_order_quantity: "10",
    });
  });

  it.each([
    [409, "Duplicate request conflict"],
    [422, "Validation failed"],
    [500, "execution failed safely"],
  ])("shows a safe HTTP %s submission error", async (status, expected) => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      jsonResponse({ detail: "safe detail" }, status),
    );
    render(<CreateBacktestPage />);
    await userEvent.click(screen.getByRole("button", { name: "Run backtest" }));
    expect(await screen.findByRole("alert")).toHaveTextContent(expected);
  });
});
