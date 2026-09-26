import { act, fireEvent, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, expect, it, vi } from "vitest";
import { i18n } from "../../i18n";
import { ApiError } from "../../api/client";
import { experimentApi } from "./api";
import { CreateExperimentPage } from "./CreateExperimentPage";
import {
  EXPERIMENT_DRAFT_KEY,
  readExperimentDraft,
  saveExperimentDraft,
} from "./draft";
import { capabilities, configuration } from "./fixtures.test-data";

beforeEach(async () => {
  localStorage.removeItem(EXPERIMENT_DRAFT_KEY);
  await i18n.changeLanguage("en-US");
  window.history.replaceState({}, "", "/research/new");
  vi.spyOn(experimentApi, "capabilities").mockResolvedValue(capabilities);
});

it("identifies and focuses invalid capital, translates its explanation and clears it after correction", async () => {
  const create = vi.spyOn(experimentApi, "create");
  saveExperimentDraft(
    { ...configuration, initial_cash: "-1" },
    1,
    "invalid-capital",
  );
  render(<CreateExperimentPage />);
  const capital = await screen.findByLabelText("Starting capital (CNY)");
  await userEvent.click(screen.getByRole("button", { name: "Continue" }));
  expect(capital).toHaveFocus();
  expect(capital).toHaveAttribute("aria-invalid", "true");
  expect(capital).toHaveAccessibleDescription(
    /Starting capital must be a positive decimal/,
  );
  expect(screen.getByRole("alert")).toHaveTextContent("1,000,000,000,000 CNY");
  await userEvent.tab();
  await userEvent.click(screen.getByRole("button", { name: "Continue" }));
  expect(capital).toHaveFocus();
  await act(async () => {
    await i18n.changeLanguage("zh-CN");
  });
  expect(screen.getByLabelText("初始本金（人民币）")).toHaveValue("-1");
  expect(capital).toHaveAccessibleDescription(/初始本金须为正小数/);
  fireEvent.change(capital, { target: { value: configuration.initial_cash } });
  expect(capital).not.toHaveAttribute("aria-invalid");
  expect(screen.queryByRole("alert")).toBeNull();
  await userEvent.click(screen.getByRole("button", { name: "继续" }));
  expect(screen.getByRole("heading", { name: "成本与风险" })).toHaveFocus();
  expect(readExperimentDraft()?.form.initial_cash).toBe(
    configuration.initial_cash,
  );
  expect(create).not.toHaveBeenCalled();
});

it.each([
  ["name", { name: " " }, "Experiment name"],
  ["long-name", { name: "a".repeat(121) }, "Experiment name"],
  ["empty-date", { start_date: "" }, "First trading date"],
  ["invalid-date", { start_date: "2031-02-29" }, "First trading date"],
  ["date-order", { end_date: "2030-12-31" }, "Last trading date"],
  [
    "cash-limit",
    { initial_cash: "1000000000000.000000000000000001" },
    "Starting capital (CNY)",
  ],
  [
    "hidden-rebalance",
    { strategy: { ...configuration.strategy, rebalance_sessions: 0 } },
    "Sessions between rebalances",
  ],
  [
    "holdings-limit",
    { strategy: { ...configuration.strategy, maximum_holdings: 101 } },
    "Maximum holdings",
  ],
  [
    "commission",
    {
      costs: {
        ...configuration.costs,
        commission_rate: "0.010000000000000001",
      },
    },
    "Commission rate (decimal fraction)",
  ],
  [
    "minimum",
    { costs: { ...configuration.costs, minimum_commission: "" } },
    "Minimum commission per trade (CNY)",
  ],
  [
    "drawdown",
    { risk: { ...configuration.risk, max_drawdown: "0.1" } },
    "Drawdown risk limit (negative fraction)",
  ],
  [
    "weight",
    { risk: { ...configuration.risk, max_position_weight: "0" } },
    "Maximum target weight per security",
  ],
] as const)(
  "returns an invalid restored review to its mounted field: %s",
  async (_case, change, label) => {
    const create = vi.spyOn(experimentApi, "create");
    saveExperimentDraft({ ...configuration, ...change }, 3, "invalid-review");
    render(<CreateExperimentPage />);
    await screen.findByRole("checkbox", { name: /I understand/ });
    await userEvent.click(
      screen.getByRole("checkbox", { name: /I understand/ }),
    );
    await userEvent.click(
      screen.getByRole("button", { name: "Run this configuration" }),
    );
    const field = screen.getByLabelText(label);
    expect(field).toHaveAttribute("aria-invalid", "true");
    expect(field).toHaveFocus();
    expect(field).toHaveAttribute(
      "aria-describedby",
      screen.getByRole("alert").id,
    );
    if (field.closest("details"))
      expect(field.closest("details")).toHaveAttribute("open");
    expect(create).not.toHaveBeenCalled();
  },
);

it("accepts exact permitted boundaries without floating-point rounding", async () => {
  saveExperimentDraft(
    {
      ...configuration,
      initial_cash: "1000000000000",
      costs: { commission_rate: "0", minimum_commission: "1000" },
      risk: { max_drawdown: "-1", max_position_weight: "1" },
    },
    2,
    "boundary",
  );
  render(<CreateExperimentPage />);
  await screen.findByLabelText("Commission rate (decimal fraction)");
  await userEvent.click(screen.getByRole("button", { name: "Continue" }));
  expect(screen.queryByRole("alert")).toBeNull();
  expect(screen.getByRole("heading", { name: "Review & run" })).toHaveFocus();
});

it("opens hidden advanced settings and focuses a fractional integer error", async () => {
  saveExperimentDraft(configuration, 1, "fractional-setting");
  render(<CreateExperimentPage />);
  const holdings = await screen.findByLabelText("Maximum holdings");
  fireEvent.change(holdings, { target: { value: "1.5" } });
  await userEvent.click(screen.getByRole("button", { name: "Continue" }));
  expect(holdings).toHaveFocus();
  expect(holdings.closest("details")).toHaveAttribute("open");
  expect(holdings).toHaveAccessibleDescription(/whole-number maximum holdings/);
});

it("focuses an asynchronous server error summary without inventing an invalid field", async () => {
  const create = vi
    .spyOn(experimentApi, "create")
    .mockRejectedValue(new ApiError(503, "Unavailable"));
  saveExperimentDraft(configuration, 3, "server-error");
  render(<CreateExperimentPage />);
  await screen.findByRole("checkbox", { name: /I understand/ });
  await userEvent.click(screen.getByRole("checkbox", { name: /I understand/ }));
  await userEvent.click(
    screen.getByRole("button", { name: "Run this configuration" }),
  );
  expect(await screen.findByRole("alert")).toHaveFocus();
  expect(document.querySelector('[aria-invalid="true"]')).toBeNull();
  expect(readExperimentDraft()?.idempotencyKey).toBe("server-error");
  expect(create).toHaveBeenCalledTimes(1);
});
