import { act, render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, expect, test, vi } from "vitest";

import { researchApi } from "../../api/research";
import type { ResearchPoint, ResearchRun } from "../../types/research";
import { ResearchRunPage } from "./ResearchRunPage";

let language = "en-US";

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
    i18n: { language },
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
  language = "en-US";
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

test.each(["DEVELOPMENT", "VALIDATION", "OUT_OF_SAMPLE"] as const)(
  "%s shows the known execution issue in both languages without changing saved values",
  async (period_kind) => {
    vi.mocked(researchApi.run).mockResolvedValue({
      ...savedRun,
      period_kind,
      dataset_id: "cn-a-research-20100101-20251231-v1",
      created_at: "2030-01-01T00:00:00Z",
      diagnostics: { candidate: "S4" },
    });
    vi.mocked(researchApi.metrics).mockResolvedValue({
      ...empty,
      total: 1,
      items: [
        {
          period_kind,
          metric_name: "transaction_costs",
          value: "12.000000000000000001",
        },
      ],
    });
    const page = render(<ResearchRunPage runId="saved" />);
    const notice = await screen.findByText(
      /Earlier versions of this historical execution engine/,
    );
    expect(notice).toHaveTextContent(
      "impact on a particular report is not quantified",
    );
    expect(notice).toHaveTextContent("does not revalidate old returns");
    const cost = await screen.findByTitle("12.000000000000000001");
    await userEvent.click(
      screen.getByRole("checkbox", { name: "research:fullPrecision" }),
    );
    expect(cost).toHaveTextContent("12.000000000000000001");
    language = "zh-CN";
    page.rerender(<ResearchRunPage runId="saved" />);
    expect(
      screen.getByText(/旧版历史执行引擎可能错误拒绝本可成交的证券/),
    ).toHaveTextContent("具体影响尚未量化");
    expect(cost).toHaveTextContent("12.000000000000000001");
    expect(researchApi.run).toHaveBeenCalledTimes(1);
    expect(researchApi.metrics).toHaveBeenCalledTimes(1);
    expect(researchApi.points).toHaveBeenCalledTimes(3);
  },
);

test.each([undefined, ["S0"], ["S1"]])(
  "missing or malformed formal execution provenance %j stays unverified rather than being declared unaffected",
  async (candidate) => {
    vi.mocked(researchApi.run).mockResolvedValue({
      ...savedRun,
      dataset_id: "cn-a-research-20100101-20251231-v1",
      diagnostics: { candidate },
    });
    const page = render(<ResearchRunPage runId="saved" />);
    expect(
      await screen.findByText(
        /The saved execution source is not sufficiently verified/,
      ),
    ).toHaveTextContent(
      "cannot determine whether this report involves the known older-engine rejection issue",
    );
    expect(
      screen.queryByText(
        /Earlier versions of this historical execution engine/,
      ),
    ).toBeNull();
    language = "zh-CN";
    page.rerender(<ResearchRunPage runId="saved" />);
    expect(screen.getByText(/已保存的执行来源尚未充分核验/)).toHaveTextContent(
      "不能据此视为未受影响",
    );
    expect(researchApi.run).toHaveBeenCalledTimes(1);
  },
);

test.each([
  {
    candidate: "S0",
    period_kind: "VALIDATION",
    dataset_id: "cn-a-research-20100101-20251231-v1",
  },
  {
    candidate: "S1",
    period_kind: "VALIDATION",
    dataset_id: "cn-a-research-20100101-20251231-v1",
  },
  {
    candidate: "S4",
    period_kind: "PILOT_SMOKE",
    dataset_id: "cn-a-research-20100101-20251231-v1",
  },
  { candidate: "S4", period_kind: "VALIDATION", dataset_id: "saved-dataset" },
] as const)(
  "does not attach the FullDataset issue to $candidate / $period_kind / $dataset_id",
  async ({ candidate, period_kind, dataset_id }) => {
    vi.mocked(researchApi.run).mockResolvedValue({
      ...savedRun,
      strategy_id: "cn_a_cross_sectional_momentum_low_vol_v1",
      period_kind,
      dataset_id,
      diagnostics: { candidate },
    });
    render(<ResearchRunPage runId="saved" />);
    await screen.findByRole("heading", {
      name: "cn_a_cross_sectional_momentum_low_vol_v1",
    });
    expect(
      screen.queryByText(
        /Earlier versions of this historical execution engine/,
      ),
    ).toBeNull();
    expect(
      screen.queryByText(
        /The saved execution source is not sufficiently verified/,
      ),
    ).toBeNull();
  },
);

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
      {},
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

test("formal ranges and linked dates query the server without recalculating metrics or fetching on hover", async () => {
  vi.mocked(researchApi.points).mockImplementation(
    async (_id, kind, offset = 0, _signal, range = {}) => {
      if (range.start_date === "2024-04-02") return { ...empty, offset };
      const dates = range.start_date
        ? ["2024-01-03", "2024-04-01"]
        : ["2024-01-02", "2024-01-03"];
      return {
        items: (offset ? dates.slice(1) : dates).map((trading_date, index) => ({
          sequence: offset + index,
          trading_date,
          value:
            kind === "drawdown"
              ? "-0.000000000000000001"
              : "100.000000000000000001",
        })),
        limit: 200,
        offset,
        total: 201,
      };
    },
  );
  render(<ResearchRunPage runId="saved" />);
  const equity = await screen.findByRole("figure", {
    name: "accessibility:benchmarkChart",
  });
  const drawdown = screen.getByRole("figure", {
    name: "accessibility:drawdownChart",
  });
  const first = screen.getByLabelText("First trading date");
  const last = screen.getByLabelText("Last trading date");
  expect(
    screen.getByRole("region", { name: "Displayed trading dates" }),
  ).toHaveClass("experimentPanel");
  expect(
    screen.getByRole("region", { name: "Linked trading date" }),
  ).toHaveClass("experimentPanel");
  await userEvent.type(first, "2024-01-03");
  await userEvent.type(last, "2024-04-01");
  expect(researchApi.points).toHaveBeenCalledTimes(3);
  await userEvent.selectOptions(
    within(equity).getByRole("combobox"),
    "2024-01-02",
  );
  expect(within(drawdown).getByRole("status")).toHaveTextContent("2024-01-02");
  expect(within(drawdown).getByRole("status")).toHaveTextContent(
    "-0.000000000000000001",
  );
  await userEvent.hover(
    within(drawdown).getByTitle("2024-01-03: -0.000000000000000001"),
  );
  expect(within(equity).getByRole("combobox")).toHaveValue("2024-01-03");
  expect(researchApi.points).toHaveBeenCalledTimes(3);
  expect(researchApi.holdings).toHaveBeenCalledTimes(1);
  expect(researchApi.trades).toHaveBeenCalledTimes(1);
  await userEvent.click(screen.getByRole("button", { name: "Apply dates" }));
  await screen.findByText("research:displayedDateRange:2024-01-03–2024-04-01");
  const range = { start_date: "2024-01-03", end_date: "2024-04-01" };
  for (const kind of ["equity", "benchmark", "drawdown"])
    expect(researchApi.points).toHaveBeenCalledWith(
      "saved",
      kind,
      0,
      expect.any(AbortSignal),
      range,
    );
  for (const method of [
    researchApi.holdings,
    researchApi.trades,
    researchApi.rebalances,
    researchApi.rollingMetrics,
  ])
    expect(method).toHaveBeenLastCalledWith(
      "saved",
      0,
      expect.any(AbortSignal),
      range,
    );
  const equitySection = screen
    .getByRole("heading", { name: "research:equity / research:benchmarkCurve" })
    .closest("section")!;
  await userEvent.click(
    within(equitySection).getByRole("button", { name: "next" }),
  );
  await screen.findByText("research:displayedDateRange:2024-04-01–2024-04-01");
  for (const kind of ["equity", "benchmark", "drawdown"])
    expect(researchApi.points).toHaveBeenCalledWith(
      "saved",
      kind,
      200,
      expect.any(AbortSignal),
      range,
    );
  const curveCalls = vi.mocked(researchApi.points).mock.calls.length;
  await userEvent.click(
    screen.getByRole("button", {
      name: "Show trades and holdings for this date",
    }),
  );
  const linked = { start_date: "2024-04-01", end_date: "2024-04-01" };
  for (const method of [
    researchApi.holdings,
    researchApi.trades,
    researchApi.rebalances,
  ])
    expect(method).toHaveBeenLastCalledWith(
      "saved",
      0,
      expect.any(AbortSignal),
      linked,
    );
  expect(researchApi.points).toHaveBeenCalledTimes(curveCalls);
  expect(
    screen.getByRole("region", { name: "Linked trading date" }),
  ).toHaveFocus();
  await userEvent.click(
    within(equitySection).getByRole("button", { name: "previous" }),
  );
  await screen.findByText("research:displayedDateRange:2024-01-03–2024-04-01");
  await userEvent.selectOptions(
    screen.getByRole("combobox", {
      name: "accessibility:benchmarkChart — research:columns.date",
    }),
    "2024-01-03",
  );
  expect(
    screen.getByRole("region", { name: "Linked trading date" }),
  ).toHaveTextContent("2024-04-01");
  expect(researchApi.holdings).toHaveBeenCalledTimes(3);
  await userEvent.click(
    screen.getByRole("button", { name: "Clear linked date" }),
  );
  expect(
    screen.getByRole("region", { name: "Displayed trading dates" }),
  ).toHaveFocus();
  expect(researchApi.holdings).toHaveBeenLastCalledWith(
    "saved",
    0,
    expect.any(AbortSignal),
    range,
  );
  expect(researchApi.metrics).toHaveBeenCalledTimes(1);
  expect(researchApi.monthlyReturns).toHaveBeenCalledTimes(1);
  await userEvent.clear(first);
  await userEvent.type(first, "2024-04-02");
  const beforeInvalid = vi.mocked(researchApi.points).mock.calls.length;
  await userEvent.click(screen.getByRole("button", { name: "Apply dates" }));
  expect(screen.getByRole("alert")).toHaveTextContent(
    "Choose a valid date range",
  );
  expect(first).toHaveFocus();
  expect(first).toHaveAttribute("aria-invalid", "true");
  expect(researchApi.points).toHaveBeenCalledTimes(beforeInvalid);
  await userEvent.clear(last);
  await userEvent.type(last, "2024-04-03");
  await userEvent.click(screen.getByRole("button", { name: "Apply dates" }));
  expect(
    await within(equitySection).findByText(
      "No records match these dates. Clear the date selection or widen the interval.",
    ),
  ).toBeInTheDocument();
  expect(
    screen.queryByRole("button", {
      name: "Show trades and holdings for this date",
    }),
  ).toBeNull();
  await userEvent.click(
    screen.getByRole("button", { name: "Show full interval" }),
  );
  await screen.findByText("research:displayedDateRange:2024-01-02–2024-01-03");
  expect(first).toHaveValue("");
  expect(last).toHaveValue("");
  expect(researchApi.metrics).toHaveBeenCalledTimes(1);
  expect(researchApi.monthlyReturns).toHaveBeenCalledTimes(1);
});
