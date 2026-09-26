import {
  act,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { i18n } from "../i18n";
import { jsonResponse, RUN_ID } from "../test/fixtures";
import { CreateBacktestPage } from "./CreateBacktestPage";

describe("create backtest", () => {
  it("translates the legacy form without resetting entered capital", async () => {
    const fetch = vi.spyOn(globalThis, "fetch");
    await act(async () => i18n.changeLanguage("en-US"));
    try {
      render(<CreateBacktestPage />);
      fireEvent.change(screen.getByLabelText("Initial cash"), {
        target: { value: "123456.789" },
      });
      await act(async () => i18n.changeLanguage("zh-CN"));
      expect(screen.getByRole("heading", { name: "创建回测" })).toBeVisible();
      expect(screen.getByLabelText("初始资金")).toHaveValue("123456.789");
      fireEvent.change(screen.getByLabelText("短周期"), {
        target: { value: "4" },
      });
      await userEvent.click(screen.getByRole("button", { name: "运行回测" }));
      expect(await screen.findByRole("alert")).toHaveTextContent(
        "短周期小于长周期",
      );
      await act(async () => i18n.changeLanguage("en-US"));
      expect(screen.getByRole("alert")).toHaveTextContent(
        "short period below long period",
      );
      expect(screen.getByLabelText("Initial cash")).toHaveValue("123456.789");
      expect(fetch).not.toHaveBeenCalled();
    } finally {
      await act(async () => i18n.changeLanguage("en-US"));
    }
  });
  it("submits configured risk without rounding the Decimal limit", async () => {
    const fetch = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValue(
        jsonResponse({ run_id: RUN_ID, status: "SUCCEEDED", links: {} }, 201),
      );
    render(<CreateBacktestPage />);
    await userEvent.click(screen.getByLabelText("Enforce buying power"));
    fireEvent.change(
      screen.getByLabelText("Maximum order notional (optional)"),
      {
        target: { value: "1000.000000000000000001" },
      },
    );
    await userEvent.click(screen.getByRole("button", { name: "Run backtest" }));
    expect(JSON.parse(String(fetch.mock.calls[0]?.[1]?.body)).risk).toEqual({
      enforce_buying_power: true,
      max_order_notional: "1000.000000000000000001",
    });
  });
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

  it.each([500, 408, "offline"])(
    "reuses a key after %s and replaces it only after payload edits",
    async (failure) => {
      const fetch = vi
        .spyOn(globalThis, "fetch")
        .mockImplementation(() =>
          failure === "offline"
            ? Promise.reject(new TypeError("Failed to fetch"))
            : Promise.resolve(
                jsonResponse({ detail: "temporary" }, Number(failure)),
              ),
        );
      render(<CreateBacktestPage />);
      fireEvent.change(screen.getByLabelText("Initial cash"), {
        target: { value: "100000.000000000000000001" },
      });
      const submit = screen.getByRole("button", { name: "Run backtest" });
      await userEvent.click(submit);
      await screen.findByRole("alert");
      expect(
        screen.queryByRole("link", { name: "Reload page" }),
      ).not.toBeInTheDocument();
      expect(
        screen.queryByRole("link", { name: "Return to workbench" }),
      ).not.toBeInTheDocument();
      expect(screen.getByLabelText("Initial cash")).toHaveValue(
        "100000.000000000000000001",
      );
      const firstKey = new Headers(fetch.mock.calls[0]?.[1]?.headers).get(
        "Idempotency-Key",
      );
      await userEvent.click(submit);
      await waitFor(() => expect(fetch).toHaveBeenCalledTimes(2));
      const retryKey = new Headers(fetch.mock.calls[1]?.[1]?.headers).get(
        "Idempotency-Key",
      );
      expect(retryKey).toBe(firstKey);
      expect(fetch.mock.calls[1]?.[1]?.body).toBe(
        fetch.mock.calls[0]?.[1]?.body,
      );

      fireEvent.change(screen.getByLabelText("Initial cash"), {
        target: { value: "100001" },
      });
      await userEvent.click(submit);
      await waitFor(() => expect(fetch).toHaveBeenCalledTimes(3));
      const editedKey = new Headers(fetch.mock.calls[2]?.[1]?.headers).get(
        "Idempotency-Key",
      );
      expect(editedKey).not.toBe(firstKey);
    },
  );

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

  it("skips the immutable symbol during keyboard setup", async () => {
    render(<CreateBacktestPage />);
    screen.getByRole("link", { name: "Cancel" }).focus();
    await userEvent.tab();
    expect(screen.getByLabelText("Initial cash")).toHaveFocus();
  });

  it.each([
    [409, "Duplicate request conflict", "backtests:createPage.conflictError"],
    [422, "Validation failed", "backtests:createPage.validationError"],
    [500, "execution failed safely", "backtests:createPage.executionError"],
    [403, "Access was denied", "common:loadErrors.permission"],
    [
      404,
      "Backtest creation is unavailable",
      "backtests:createPage.unavailableError",
    ],
    [408, "The request timed out", "backtests:createPage.timeoutError"],
  ])("shows a safe HTTP %s submission error", async (status, expected, key) => {
    const fetch = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValue(jsonResponse({ detail: "safe detail" }, status));
    render(<CreateBacktestPage />);
    await userEvent.click(screen.getByRole("button", { name: "Run backtest" }));
    expect(await screen.findByRole("alert")).toHaveTextContent(expected);
    try {
      await act(async () => i18n.changeLanguage("zh-CN"));
      expect(screen.getByRole("alert")).toHaveTextContent(
        i18n.t(key, { message: "safe detail" }),
      );
      expect(screen.getByLabelText("初始资金")).toHaveValue("100000");
      expect(fetch).toHaveBeenCalledTimes(1);
    } finally {
      await act(async () => i18n.changeLanguage("en-US"));
    }
  });

  it("explains offline submission in both locales without exposing diagnostics", async () => {
    const fetch = vi
      .spyOn(globalThis, "fetch")
      .mockRejectedValue(new TypeError("Failed to fetch"));
    render(<CreateBacktestPage />);
    await userEvent.click(screen.getByRole("button", { name: "Run backtest" }));
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "The service is unavailable",
    );
    expect(screen.getByText("Failed to fetch")).not.toBeVisible();
    try {
      await act(async () => i18n.changeLanguage("zh-CN"));
      expect(screen.getByRole("alert")).toHaveTextContent(
        i18n.t("backtests:createPage.offlineError"),
      );
      expect(fetch).toHaveBeenCalledTimes(1);
    } finally {
      await act(async () => i18n.changeLanguage("en-US"));
    }
  });
});
