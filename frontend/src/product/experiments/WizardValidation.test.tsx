import { act, fireEvent, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, expect, it, vi } from "vitest";
import { i18n } from "../../i18n";
import { ApiError } from "../../api/client";
import { experimentApi } from "./api";
import { CreateExperimentPage } from "./CreateExperimentPage";
import {
  EXPERIMENT_DRAFT_KEY,
  DRAFT_RECOVERY_PREFIX,
  readExperimentDraft,
  saveExperimentDraft,
} from "./draft";
import { capabilities, configuration } from "./fixtures.test-data";
import { explainExperimentCode } from "./codes";

beforeEach(async () => {
  localStorage.removeItem(EXPERIMENT_DRAFT_KEY);
  for (const key of Object.keys(localStorage))
    if (key.startsWith(DRAFT_RECOVERY_PREFIX)) localStorage.removeItem(key);
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

it.each([
  "KNOWN_ECONOMIC_COVERAGE_GAP",
  "HISTORICAL_DATASET_QUALITY_UNKNOWN",
] as const)(
  "discloses selected source quality before running, preserving the translated exact draft: %s",
  async (quality) => {
    const create = vi.spyOn(experimentApi, "create");
    const historical = {
      ...capabilities.datasets[0]!,
      dataset_id: "cn-a-test-history-v1",
      mode: "historical_exploration" as const,
      current_dataset_quality: quality,
    };
    vi.mocked(experimentApi.capabilities).mockResolvedValue({
      ...capabilities,
      datasets: [historical, capabilities.datasets[0]!],
    });
    const form = { ...configuration, dataset_id: historical.dataset_id };
    saveExperimentDraft(form, 1, "quality-disclosure");
    render(<CreateExperimentPage />);
    const source = await screen.findByLabelText("Data source");
    const english = explainExperimentCode(quality, "en-US");
    expect(screen.getByRole("note")).toHaveTextContent(english);
    expect(source).toHaveAccessibleDescription(
      `Data source: ${historical.dataset_id} ${english}`,
    );
    await act(async () => {
      await i18n.changeLanguage("zh-CN");
    });
    const chinese = explainExperimentCode(quality, "zh-CN");
    expect(screen.getByRole("note")).toHaveTextContent(chinese);
    expect(source).toHaveAccessibleDescription(
      `数据来源: ${historical.dataset_id} ${chinese}`,
    );
    expect(screen.getByLabelText("初始本金（人民币）")).toHaveValue(
      form.initial_cash,
    );
    await userEvent.click(screen.getByRole("button", { name: "继续" }));
    await userEvent.click(screen.getByRole("button", { name: "继续" }));
    expect(screen.getByRole("heading", { name: "确认运行" })).toHaveFocus();
    expect(screen.getByRole("note")).toHaveTextContent(chinese);
    expect(screen.getByRole("button", { name: "运行当前配置" })).toBeDisabled();
    expect(readExperimentDraft()?.form).toEqual(form);
    expect(readExperimentDraft()?.idempotencyKey).toBe("quality-disclosure");
    expect(create).not.toHaveBeenCalled();
    await userEvent.click(screen.getByRole("button", { name: "上一步" }));
    await userEvent.click(screen.getByRole("button", { name: "上一步" }));
    const demoSource = screen.getByLabelText("数据来源");
    await userEvent.selectOptions(demoSource, configuration.dataset_id);
    expect(screen.queryByRole("note")).toBeNull();
    expect(demoSource).toHaveAccessibleDescription(
      `数据来源: ${configuration.dataset_id}`,
    );
    await userEvent.click(screen.getByRole("button", { name: "继续" }));
    await userEvent.click(screen.getByRole("button", { name: "继续" }));
    expect(screen.queryByRole("note")).toBeNull();
    expect(
      screen.getByText(
        "这里使用合成价格演示操作流程。模拟收益不可作为投资证据。",
      ),
    ).toBeVisible();
    expect(create).not.toHaveBeenCalled();
  },
);
