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
      "safe positive integers",
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

  it("locks rapid duplicate submissions", async () => {
    let resolveRequest: ((response: Response) => void) | undefined;
    const fetch = vi.spyOn(globalThis, "fetch").mockImplementation(
      () =>
        new Promise<Response>((resolve) => {
          resolveRequest = resolve;
        }),
    );
    render(<CreateBacktestPage />);
    await userEvent.dblClick(
      screen.getByRole("button", { name: "Run backtest" }),
    );
    expect(fetch).toHaveBeenCalledTimes(1);
    resolveRequest?.(
      jsonResponse({ run_id: RUN_ID, status: "SUCCEEDED", links: {} }, 201),
    );
  });

  it("reuses a key for a retry and replaces it after payload edits", async () => {
    const fetch = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValue(jsonResponse({ detail: "temporary" }, 500));
    render(<CreateBacktestPage />);
    const submit = screen.getByRole("button", { name: "Run backtest" });
    await userEvent.click(submit);
    await screen.findByRole("alert");
    const firstKey = new Headers(fetch.mock.calls[0]?.[1]?.headers).get(
      "Idempotency-Key",
    );
    await userEvent.click(submit);
    await waitFor(() => expect(fetch).toHaveBeenCalledTimes(2));
    const retryKey = new Headers(fetch.mock.calls[1]?.[1]?.headers).get(
      "Idempotency-Key",
    );
    expect(retryKey).toBe(firstKey);

    fireEvent.change(screen.getByLabelText("Initial cash"), {
      target: { value: "100001" },
    });
    await userEvent.click(submit);
    await waitFor(() => expect(fetch).toHaveBeenCalledTimes(3));
    const editedKey = new Headers(fetch.mock.calls[2]?.[1]?.headers).get(
      "Idempotency-Key",
    );
    expect(editedKey).not.toBe(firstKey);
  });

  it.each(["0", "-1", "1.5", "9007199254740992", ""])(
    "rejects invalid moving-average period %j",
    async (value) => {
      const fetch = vi.spyOn(globalThis, "fetch");
      render(<CreateBacktestPage />);
      fireEvent.change(screen.getByLabelText("Short period"), {
        target: { value },
      });
      fireEvent.submit(
        screen.getByRole("button", { name: "Run backtest" }).closest("form")!,
      );
      expect(await screen.findByRole("alert")).toHaveTextContent(
        "safe positive integers",
      );
      expect(fetch).not.toHaveBeenCalled();
    },
  );

  it.each([
    ["0", "70"],
    ["30", "30"],
    ["70", "30"],
    ["30", "100"],
    ["99.999999999999999999", "99.999999999999999999"],
  ])("rejects invalid RSI thresholds %s / %s", async (low, high) => {
    const fetch = vi.spyOn(globalThis, "fetch");
    render(<CreateBacktestPage />);
    await userEvent.selectOptions(
      screen.getByLabelText("Strategy type"),
      "rsi_mean_reversion",
    );
    fireEvent.change(screen.getByLabelText("Oversold"), {
      target: { value: low },
    });
    fireEvent.change(screen.getByLabelText("Overbought"), {
      target: { value: high },
    });
    await userEvent.click(screen.getByRole("button", { name: "Run backtest" }));
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "0 < oversold < overbought < 100",
    );
    expect(fetch).not.toHaveBeenCalled();
  });

  it("exposes only registered dataset and strategy choices", () => {
    render(<CreateBacktestPage />);
    expect(screen.getByRole("combobox", { name: /Dataset/ })).toBeDisabled();
    expect(
      screen.getAllByRole("option").map((option) => option.textContent),
    ).toEqual([
      "AAPL fixture",
      "Moving average crossover",
      "RSI mean reversion",
    ]);
    expect(screen.queryByText("../")).not.toBeInTheDocument();
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
