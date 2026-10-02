import { act, render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, expect, test, vi } from "vitest";

import { researchApi } from "../../api/research";
import type { ResearchPoint, ResearchRun } from "../../types/research";
import { ResearchRunPage } from "./ResearchRunPage";

vi.mock("../../api/research", () => ({
  researchApi: {
    run: vi.fn(),
    metrics: vi.fn(),
    points: vi.fn(),
    monthlyReturns: vi.fn(),
    rollingMetrics: vi.fn(),
    holdings: vi.fn(),
    rebalances: vi.fn(),
    trades: vi.fn(),
  },
}));
vi.mock("react-i18next", () => ({
  useTranslation: () => ({
    t: (key: string, values?: { start?: string; end?: string }) =>
      values?.start ? `${key}:${values.start}–${values.end}` : key,
  }),
}));

const empty = { items: [], limit: 200, offset: 0, total: 0 };
const savedRun = {
  run_id: "saved",
  strategy_id: "saved-strategy",
  period_kind: "VALIDATION",
  dataset_id: "saved-dataset",
  provider: "audited",
  provider_version: "1",
  dataset_checksum: "abc",
  market_rule_version: "1",
  benchmark_id: "CSI300",
  created_at: "2024-01-01T00:00:00Z",
  git_commit: "abc",
  strategy_config_hash: "abc",
  diagnostics: {},
} as ResearchRun;

function pointPage(offset: number, count: number) {
  const items: ResearchPoint[] = Array.from({ length: count }, (_, index) => ({
    sequence: offset + index,
    trading_date: offset === 0 ? "2024-01-02" : "2024-04-01",
    value: "100.000000000000000001",
  }));
  return { items, limit: 200, offset, total: 201 };
}

beforeEach(() => {
  vi.clearAllMocks();
  vi.mocked(researchApi.run).mockResolvedValue(savedRun);
  vi.mocked(researchApi.metrics).mockResolvedValue(empty);
  vi.mocked(researchApi.monthlyReturns).mockResolvedValue(empty);
  vi.mocked(researchApi.rollingMetrics).mockResolvedValue(empty);
  vi.mocked(researchApi.holdings).mockResolvedValue(empty);
  vi.mocked(researchApi.rebalances).mockResolvedValue(empty);
  vi.mocked(researchApi.trades).mockResolvedValue(empty);
  vi.mocked(researchApi.points).mockImplementation(async (_id, _kind, offset) =>
    pointPage(offset ?? 0, offset === 0 ? 200 : 1),
  );
});

test("one curve page advances all three series without changing stored metrics", async () => {
  render(<ResearchRunPage runId="saved" />);
  await screen.findByText("research:displayedDateRange:2024-01-02–2024-01-02");
  const equitySection = (
    await screen.findByRole("heading", {
      name: "research:equity / research:benchmarkCurve",
    })
  ).closest("section")!;
  const pager = within(equitySection).getByRole("group", {
    name: "research:equity / research:benchmarkCurve — pagination",
  });
  const pagerNames = screen
    .getAllByRole("group", { name: /pagination/ })
    .map((group) => group.getAttribute("aria-label"));
  expect(new Set(pagerNames).size).toBe(5);
  await userEvent.click(
    within(equitySection).getByRole("button", { name: "next" }),
  );
  await screen.findByText("research:displayedDateRange:2024-04-01–2024-04-01");
  expect(pager).toHaveFocus();
  expect(researchApi.points).toHaveBeenCalledTimes(6);
  for (const kind of ["equity", "benchmark", "drawdown"])
    expect(researchApi.points).toHaveBeenCalledWith(
      "saved",
      kind,
      200,
      expect.any(AbortSignal),
    );
  expect(researchApi.metrics).toHaveBeenCalledTimes(1);
  await userEvent.click(
    within(pager).getByRole("button", { name: "previous" }),
  );
  await screen.findByText("research:displayedDateRange:2024-01-02–2024-01-02");
  expect(pager).toHaveFocus();
});

test("benchmark visibility preserves exact data, requests, paging and rolling drawdown", async () => {
  vi.mocked(researchApi.points).mockImplementation(
    async (_id, _kind, offset = 0) => {
      const page = pointPage(offset, offset === 0 ? 200 : 1);
      return {
        ...page,
        items: page.items.map((point) => ({
          ...point,
          trading_date: new Date(Date.UTC(2024, 0, 2 + point.sequence))
            .toISOString()
            .slice(0, 10),
        })),
      };
    },
  );
  vi.mocked(researchApi.rollingMetrics).mockResolvedValue({
    items: [
      { trading_date: "2024-01-02", metric_name: "sharpe", value: null },
      { trading_date: "2024-01-02", metric_name: "drawdown", value: "-0.1" },
      { trading_date: "2024-01-03", metric_name: "sharpe", value: "1.2" },
      { trading_date: "2024-01-03", metric_name: "drawdown", value: "-0.2" },
    ],
    limit: 200,
    offset: 0,
    total: 4,
  });
  render(<ResearchRunPage runId="saved" />);
  const equityFigure = await screen.findByRole("figure", {
    name: "accessibility:benchmarkChart",
  });
  const equitySection = equityFigure.closest("section")!;
  const rollingFigure = await screen.findByRole("figure", {
    name: "accessibility:rollingChart",
  });
  const toggle = within(equitySection).getByRole("checkbox", {
    name: "research:showBenchmark",
  });
  expect(toggle).toBeChecked();
  await userEvent.click(within(equityFigure).getByText("chartData"));
  const table = within(equityFigure).getByRole("table");
  const exactData = table.textContent;
  await userEvent.click(toggle);
  expect(toggle).not.toBeChecked();
  expect(equityFigure.querySelector(".strategyLine")).not.toBeNull();
  expect(equityFigure.querySelector(".benchmarkLine")).toBeNull();
  expect(equityFigure.querySelector(".benchmarkLegend")).toBeNull();
  expect(table.textContent).toBe(exactData);
  expect(within(table).getAllByText("research:benchmark")).toHaveLength(50);
  expect(within(table).getAllByText("100.000000000000000001")).toHaveLength(
    100,
  );
  expect(rollingFigure.querySelector(".benchmarkLine")).not.toBeNull();
  expect(rollingFigure.querySelectorAll("circle.strategyLine")).toHaveLength(1);
  expect(researchApi.points).toHaveBeenCalledTimes(3);
  expect(researchApi.metrics).toHaveBeenCalledTimes(1);
  expect(researchApi.rollingMetrics).toHaveBeenCalledTimes(1);
  await userEvent.keyboard(" ");
  expect(toggle).toBeChecked();
  expect(equityFigure.querySelector(".benchmarkLine")).not.toBeNull();
  expect(equityFigure.querySelector(".benchmarkLegend")).not.toBeNull();
  expect(table.textContent).toBe(exactData);
  await userEvent.keyboard(" ");
  const pager = within(equitySection).getByRole("group", {
    name: "research:equity / research:benchmarkCurve — pagination",
  });
  await userEvent.click(within(pager).getByRole("button", { name: "next" }));
  await screen.findByText("research:displayedDateRange:2024-07-20–2024-07-20");
  expect(toggle).not.toBeChecked();
  expect(equitySection.querySelector(".benchmarkLine")).toBeNull();
  expect(researchApi.points).toHaveBeenCalledTimes(6);
  expect(researchApi.metrics).toHaveBeenCalledTimes(1);
  expect(researchApi.rollingMetrics).toHaveBeenCalledTimes(1);
  expect(rollingFigure.querySelector(".benchmarkLine")).not.toBeNull();
});

test("research table pager retains keyboard focus through loading and error", async () => {
  let rejectPage!: (reason: Error) => void;
  vi.mocked(researchApi.holdings).mockImplementation((_id, offset) =>
    offset === 0
      ? Promise.resolve({
          items: Array.from({ length: 200 }, (_, sequence) => ({
            sequence,
            trading_date: "2024-01-02",
            security_id: "CN-A:SSE:600000",
            quantity: "1",
            weight: "0.01",
            market_value: "1",
          })),
          limit: 200,
          offset: 0,
          total: 201,
        })
      : new Promise((_resolve, reject) => {
          rejectPage = reject;
        }),
  );
  render(<ResearchRunPage runId="saved" />);
  const holdingsSection = (
    await screen.findByRole("heading", { name: "research:holdings" })
  ).closest("section")!;
  const pager = within(holdingsSection).getByRole("group", {
    name: "research:holdings — pagination",
  });
  await userEvent.click(within(pager).getByRole("button", { name: "next" }));
  expect(pager).toHaveFocus();
  expect(pager).toHaveAttribute("aria-busy", "true");
  await act(async () => rejectPage(new TypeError("offline")));
  expect(within(holdingsSection).getByRole("alert")).toBeInTheDocument();
  expect(pager).toHaveFocus();
  await userEvent.click(
    within(pager).getByRole("button", { name: "previous" }),
  );
  await within(holdingsSection).findByRole("table", {
    name: "research:holdings",
  });
  expect(pager).toHaveFocus();
});

test("failed curve request is not reported as empty data", async () => {
  vi.mocked(researchApi.points).mockImplementation(
    async (_id, kind, offset) => {
      if (kind === "benchmark") throw new TypeError("offline");
      return pointPage(offset ?? 0, 200);
    },
  );
  render(<ResearchRunPage runId="saved" />);
  const equitySection = (
    await screen.findByRole("heading", {
      name: "research:equity / research:benchmarkCurve",
    })
  ).closest("section")!;
  await within(equitySection).findByRole("alert");
  expect(within(equitySection).queryByText("common:noData")).toBeNull();
  expect(
    within(equitySection).getByText("loadErrors.offline"),
  ).toBeInTheDocument();
});

test("rolling page retains a valid drawdown when the same date has no Sharpe value", async () => {
  vi.mocked(researchApi.rollingMetrics).mockResolvedValue({
    items: [
      { trading_date: "2024-01-02", metric_name: "drawdown", value: "-0.1" },
      { trading_date: "2024-01-02", metric_name: "sharpe", value: null },
      { trading_date: "2024-01-03", metric_name: "drawdown", value: "-0.2" },
      { trading_date: "2024-01-03", metric_name: "sharpe", value: "1.2" },
    ],
    limit: 200,
    offset: 0,
    total: 4,
  });
  render(<ResearchRunPage runId="saved" />);
  const section = (
    await screen.findByRole("heading", { name: "research:rollingMetrics" })
  ).closest("section")!;
  const figure = await within(section).findByRole("figure", {
    name: "accessibility:rollingChart",
  });
  expect(figure.querySelectorAll("polyline.benchmarkLine")).toHaveLength(1);
  expect(figure.querySelectorAll("circle.strategyLine")).toHaveLength(1);
  await userEvent.click(within(section).getByText("chartData"));
  const table = within(section).getByRole("table", {
    name: "accessibility:rollingChart",
  });
  expect(within(table).getAllByRole("row")).toHaveLength(5);
  const unavailable = within(table).getByText("common:unavailable");
  expect(
    within(unavailable.closest("tr")!).getByText("2024-01-02"),
  ).toBeInTheDocument();
  expect(within(table).getByText("-0.1")).toBeInTheDocument();
});

test("saved research trades and canonical limitations use localized presentation", async () => {
  vi.mocked(researchApi.run).mockResolvedValue({
    ...savedRun,
    diagnostics: {
      known_limitations:
        "Daily-bar simulation; Validation did not establish robust alpha; no guarantee of future returns.",
    },
  });
  vi.mocked(researchApi.trades).mockResolvedValue({
    items: [
      {
        sequence: 0,
        order_id: "first",
        security_id: "CN-A:SSE:600000",
        side: "BUY",
        quantity: "100",
        price: "10",
        transaction_cost: "1",
        timestamp: "2024-01-02T01:25:00Z",
      },
      {
        sequence: 1,
        order_id: "second",
        security_id: "CN-A:SSE:600000",
        side: "SELL",
        quantity: "100",
        price: "11",
        transaction_cost: "1",
        timestamp: "2024-01-03T01:25:00Z",
      },
    ],
    limit: 200,
    offset: 0,
    total: 2,
  });
  render(<ResearchRunPage runId="saved" />);
  const tradeTable = await screen.findByRole("table", {
    name: "research:trades",
  });
  expect(
    within(tradeTable).getByText("paper:detail.directions.BUY"),
  ).toBeInTheDocument();
  expect(
    within(tradeTable).getByText("paper:detail.directions.SELL"),
  ).toBeInTheDocument();
  expect(within(tradeTable).queryByText("BUY")).toBeNull();
  expect(
    screen.getByText("research:formalKnownLimitations"),
  ).toBeInTheDocument();
});
