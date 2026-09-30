import {
  act,
  fireEvent,
  render,
  screen,
  waitFor,
  within,
} from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { i18n } from "../../i18n";
import { ApiError } from "../../api/client";
import { experimentApi, tradingDate } from "./api";
import { ExperimentCollections } from "./ExperimentCollections";
import { ExperimentExports } from "./ExperimentExports";
import { ExperimentHoldings } from "./ExperimentHoldings";
import { ExperimentDetailPage } from "./ExperimentDetailPage";
import { job, plan, result } from "./fixtures.test-data";
import type { ExperimentHolding } from "./types";

const point = {
  sequence: 0,
  trading_date: "2031-01-03",
  equity: "100000.000000000000000009",
  benchmark: null,
  drawdown: null,
};
const snapshot: ExperimentHolding = {
  sequence: 0,
  trading_date: "2031-01-03",
  timestamp: "2031-01-03T07:00:00Z",
  cash: "100000.000000000000000009",
  equity: "100000.000000000000000009",
  market_value: "0",
  realized_pnl: "0",
  unrealized_pnl: "0",
  cumulative_commission: "0",
  pending_corporate_action_value: "0",
  positions: [],
};
beforeEach(async () => {
  await i18n.changeLanguage("en-US");
});

describe("filtered durable experiment records", () => {
  it.each([
    [
      "equity",
      null,
      new ApiError(403, "denied"),
      "Access was denied",
      "访问被拒绝",
    ],
    [
      "trades",
      "Trades",
      new ApiError(408, "timeout"),
      "request timed out",
      "请求超时",
    ],
    [
      "decisions",
      "Risk decisions",
      new TypeError("offline"),
      "service is unavailable",
      "服务暂时无法连接",
    ],
    [
      "holdings",
      "Account & holdings",
      new ApiError(403, "denied"),
      "Access was denied",
      "访问被拒绝",
    ],
  ] as const)(
    "explains a failed read-only %s request without suggesting duplicate submission",
    async (collection, summary, failure, english, chinese) => {
      const equity = vi.spyOn(experimentApi, "equity").mockResolvedValue({
        items: [],
        total: 0,
        limit: 100,
        offset: 0,
      });
      const trades = vi.spyOn(experimentApi, "trades").mockResolvedValue({
        items: [],
        total: 0,
        limit: 20,
        offset: 0,
      });
      const decisions = vi.spyOn(experimentApi, "decisions").mockResolvedValue({
        items: [],
        total: 0,
        limit: 20,
        offset: 0,
      });
      const holdings = vi.spyOn(experimentApi, "holdings").mockResolvedValue({
        items: [],
        total: 0,
        limit: 1,
        offset: 0,
        availability: "AVAILABLE",
      });
      const create = vi.spyOn(experimentApi, "create");
      const read = { equity, trades, decisions, holdings }[collection];
      read.mockRejectedValueOnce(failure);
      render(<ExperimentCollections jobId={job.job_id} />);
      if (summary)
        await userEvent.click(
          screen.getByText(summary, { selector: "summary" }),
        );
      expect(await screen.findByRole("alert")).toHaveTextContent(english);
      expect(screen.getByRole("alert")).not.toHaveTextContent(
        "submission keeps the same request key",
      );
      await act(async () => i18n.changeLanguage("zh-CN"));
      expect(screen.getByRole("alert")).toHaveTextContent(chinese);
      expect(screen.getByRole("alert")).not.toHaveTextContent("避免重复创建");
      await userEvent.click(
        within(screen.getByRole("alert")).getByRole("button", {
          name: "重新尝试",
        }),
      );
      await waitFor(() => expect(read).toHaveBeenCalledTimes(2));
      await waitFor(() =>
        expect(screen.queryByRole("alert")).not.toBeInTheDocument(),
      );
      expect(create).not.toHaveBeenCalled();
    },
  );

  it("names research collection tables and keyboard regions distinctly across locales without changing exact values", async () => {
    const equity = vi
      .spyOn(experimentApi, "equity")
      .mockResolvedValue({ items: [point], total: 1, limit: 100, offset: 0 });
    vi.spyOn(experimentApi, "trades").mockResolvedValue({
      items: [
        {
          sequence: 1,
          order_id: "order",
          security_id: "SSE:600000",
          side: "BUY",
          quantity: "100",
          price: "9.123456789012345678",
          transaction_cost: "5",
          timestamp: snapshot.timestamp,
        },
      ],
      total: 1,
      limit: 20,
      offset: 0,
    });
    vi.spyOn(experimentApi, "decisions").mockResolvedValue({
      items: [
        {
          sequence: 2,
          proposal_id: "proposal",
          security_id: "SSE:600000",
          approved: true,
          reason_code: "APPROVED",
          message: "Approved",
          timestamp: snapshot.timestamp,
        },
      ],
      total: 1,
      limit: 20,
      offset: 0,
    });
    vi.spyOn(experimentApi, "holdings").mockResolvedValue({
      items: [
        {
          ...snapshot,
          positions: [
            {
              security_id: "SSE:600000",
              quantity: "100",
              average_price: "9.123456789012345678",
              market_price: "10",
              market_value: "1000",
              weight: null,
            },
          ],
        },
      ],
      total: 1,
      limit: 1,
      offset: 0,
      availability: "AVAILABLE",
    });
    render(<ExperimentCollections jobId={job.job_id} />);
    await screen.findByRole("combobox", { name: "Inspect a trading date" });
    await userEvent.click(
      screen.getByText("Exact chart data", { selector: "summary" }),
    );
    for (const name of ["Trades", "Account & holdings", "Risk decisions"])
      await userEvent.click(screen.getByText(name, { selector: "summary" }));
    for (const name of [
      "Exact chart data",
      "Trades",
      "Account & holdings",
      "Risk decisions",
    ]) {
      const region = await screen.findByRole("region", { name });
      expect(region).toHaveAttribute("tabindex", "0");
      expect(within(region).getByRole("table", { name })).toBeInTheDocument();
    }
    const table = screen.getByRole("table", { name: "Exact chart data" });
    expect(
      within(table).getByText("100,000.000000000000000009"),
    ).toBeInTheDocument();
    expect(within(table).getAllByText("N/A")).toHaveLength(2);
    expect(within(table).getAllByRole("columnheader")).toHaveLength(4);
    expect(within(table).getAllByRole("rowheader")).toHaveLength(1);
    const summary = screen.getByText("Exact chart data", {
      selector: "summary",
    });
    summary.focus();
    await userEvent.tab();
    expect(
      screen.getByRole("region", { name: "Exact chart data" }),
    ).toHaveFocus();
    await act(async () => {
      await i18n.changeLanguage("zh-CN");
    });
    for (const name of ["图表精确数据", "交易明细", "账户与持仓", "风控决策"]) {
      expect(
        within(screen.getByRole("region", { name })).getByRole("table", {
          name,
        }),
      ).toBeInTheDocument();
    }
    expect(screen.getByRole("region", { name: "图表精确数据" })).toHaveFocus();
    expect(equity).toHaveBeenCalledTimes(1);
  });

  it("names execution and plan tables without confusing the plan section and its scroll region", async () => {
    vi.spyOn(experimentApi, "get").mockResolvedValue({
      ...job,
      status: "SUCCEEDED",
      result_available: true,
    });
    vi.spyOn(experimentApi, "result").mockResolvedValue({
      ...result,
      simulation_plan: plan,
    });
    vi.spyOn(experimentApi, "equity").mockResolvedValue({
      items: [],
      total: 0,
      limit: 100,
      offset: 0,
    });
    render(<ExperimentDetailPage jobId={job.job_id} />);
    const execution = await screen.findByRole("region", {
      name: "Why orders did or did not fill",
    });
    expect(
      within(execution).getByRole("table", {
        name: "Why orders did or did not fill",
      }),
    ).toBeInTheDocument();
    const preview = screen.getByRole("region", {
      name: "Simulated rebalance preview",
    });
    const scroll = within(preview).getByRole("region", {
      name: /Simulated rebalance preview · Scroll this table/,
    });
    expect(
      within(scroll).getByRole("table", {
        name: "Simulated rebalance preview",
      }),
    ).toHaveTextContent("9.123456789123456789");
    await act(async () => {
      await i18n.changeLanguage("zh-CN");
    });
    expect(
      screen.getByRole("table", { name: "为什么订单成交或未成交" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("table", { name: "模拟调仓预览" }),
    ).toHaveTextContent("9.123456789123456789");
  });

  it("identifies each risk-decision technical disclosure by its security and sequence", async () => {
    vi.spyOn(experimentApi, "equity").mockResolvedValue({
      items: [],
      total: 0,
      limit: 100,
      offset: 0,
    });
    vi.spyOn(experimentApi, "decisions").mockResolvedValue({
      items: [
        {
          sequence: 7,
          proposal_id: "proposal-7",
          security_id: "600000.SSE",
          approved: true,
          reason_code: "APPROVED",
          message: "Approved",
          timestamp: "2031-01-03T07:00:00Z",
        },
        {
          sequence: 8,
          proposal_id: "proposal-8",
          security_id: "600000.SSE",
          approved: false,
          reason_code: "ORDER_NOTIONAL_LIMIT",
          message: "Rejected",
          timestamp: "2031-01-03T07:00:00Z",
        },
      ],
      total: 2,
      limit: 20,
      offset: 0,
    });
    render(<ExperimentCollections jobId={job.job_id} />);
    await userEvent.click(
      screen.getByText("Risk decisions", { selector: "summary" }),
    );
    expect(
      await screen.findByLabelText("Technical details: 600000.SSE · 7"),
    ).toBeInTheDocument();
    expect(
      screen.getByLabelText("Technical details: 600000.SSE · 8"),
    ).toBeInTheDocument();
    await act(async () => {
      await i18n.changeLanguage("zh-CN");
    });
    expect(
      screen.getByLabelText("技术详情: 600000.SSE · 7"),
    ).toBeInTheDocument();
  });

  it("does not claim a benchmark line when the displayed page has a gap", async () => {
    vi.spyOn(experimentApi, "equity").mockResolvedValue({
      items: [
        { ...point, benchmark: "100000" },
        { ...point, sequence: 1, trading_date: "2031-01-04" },
      ],
      total: 2,
      limit: 100,
      offset: 0,
    });
    const view = render(<ExperimentCollections jobId={job.job_id} />);
    expect(
      await screen.findByText(
        "No complete benchmark series for these displayed dates.",
      ),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("checkbox", { name: "Show benchmark" }),
    ).toBeDisabled();
    expect(view.container.querySelector(".experimentBenchmarkLine")).toBeNull();
    expect(
      view.container.querySelector(".experimentBenchmarkLegend"),
    ).toBeNull();
    expect(
      view.container.querySelector(".experimentDrawdownLegend"),
    ).toBeNull();
    const readout = view.container.querySelector(".experimentChartReadout");
    expect(readout).toHaveAttribute("aria-live", "polite");
    expect(readout).toHaveAttribute("aria-atomic", "true");
    await userEvent.selectOptions(
      screen.getByLabelText("Inspect a trading date"),
      "2031-01-03",
    );
    expect(readout).toHaveTextContent("Selected trading date: 2031-01-03");
    await act(async () => {
      await i18n.changeLanguage("zh-CN");
    });
    expect(
      screen.getByText("当前显示日期没有完整的基准序列。"),
    ).toBeInTheDocument();
    expect(
      screen.getByText("当前显示日期没有完整的回撤序列。"),
    ).toBeInTheDocument();
  });

  it("keeps the chosen benchmark visibility when chart pages change", async () => {
    vi.spyOn(experimentApi, "equity")
      .mockResolvedValueOnce({
        items: [{ ...point, benchmark: "100000" }],
        total: 101,
        limit: 100,
        offset: 0,
      })
      .mockResolvedValueOnce({
        items: [
          {
            ...point,
            sequence: 100,
            trading_date: "2031-01-04",
            benchmark: "100001",
          },
        ],
        total: 101,
        limit: 100,
        offset: 100,
      });
    const view = render(<ExperimentCollections jobId={job.job_id} />);
    const toggle = await screen.findByRole("checkbox", {
      name: "Show benchmark",
    });
    await userEvent.click(toggle);
    expect(toggle).not.toBeChecked();
    await userEvent.click(screen.getByRole("button", { name: "Next" }));
    await waitFor(() =>
      expect(screen.getByLabelText("Inspect a trading date")).toHaveValue(
        "2031-01-04",
      ),
    );
    expect(
      screen.getByRole("checkbox", { name: "Show benchmark" }),
    ).not.toBeChecked();
    expect(view.container.querySelector(".experimentBenchmarkLine")).toBeNull();
    expect(
      view.container.querySelector(".experimentBenchmarkLegend"),
    ).toBeNull();
    expect(
      view.container.querySelector(".experimentChartReadout"),
    ).not.toHaveTextContent("Benchmark");
    await userEvent.click(
      screen.getByRole("checkbox", { name: "Show benchmark" }),
    );
    expect(
      view.container.querySelector(".experimentBenchmarkLine"),
    ).not.toBeNull();
    expect(
      view.container.querySelector(".experimentBenchmarkLegend"),
    ).not.toBeNull();
  });

  it("shows corporate-action and total PnL without double-counting pending assets", async () => {
    vi.spyOn(experimentApi, "holdings").mockResolvedValue({
      items: [
        {
          ...snapshot,
          cash: "100010",
          equity: "100110.000000000000000001",
          market_value: "100.000000000000000001",
          realized_pnl: "0",
          corporate_action_realized_pnl: "10.000000000000000001",
          total_pnl: "110.000000000000000001",
          pending_corporate_action_value: "100.000000000000000001",
        },
      ],
      total: 1,
      limit: 1,
      offset: 0,
      availability: "AVAILABLE",
    });
    render(<ExperimentHoldings jobId={job.job_id} range={{}} />);
    expect(
      (await screen.findByText("Total profit / loss (CNY)")).nextSibling,
    ).toHaveTextContent("110.000000000000000001");
    expect(
      screen.getByText("Trading realized profit / loss (CNY)").nextSibling,
    ).toHaveTextContent("0");
    expect(
      screen.getByText("Corporate-action realized profit / loss (CNY)")
        .nextSibling,
    ).toHaveTextContent("10.000000000000000001");
    expect(
      screen.getByText("Positions + pending assets (CNY)").nextSibling,
    ).toHaveTextContent("100.000000000000000001");
    expect(screen.getByText(/It is not additional equity/)).toBeInTheDocument();
    await act(async () => {
      await i18n.changeLanguage("zh-CN");
    });
    expect(screen.getByText("总损益（人民币）").nextSibling).toHaveTextContent(
      "110.000000000000000001",
    );
  });

  it("filters bounded records and leaves original full-period metrics untouched", async () => {
    vi.spyOn(experimentApi, "get").mockResolvedValue({
      ...job,
      status: "SUCCEEDED",
      result_available: true,
    });
    const summary = vi.spyOn(experimentApi, "result").mockResolvedValue(result);
    const equity = vi
      .spyOn(experimentApi, "equity")
      .mockResolvedValue({ items: [point], total: 1, limit: 100, offset: 0 });
    render(<ExperimentDetailPage jobId={job.job_id} />);
    expect(await screen.findByText("12.00")).toBeInTheDocument();
    await userEvent.click(
      screen.getByRole("checkbox", { name: "Show full precision" }),
    );
    await screen.findByText("12.000000000000000001");
    fireEvent.input(screen.getByLabelText("First trading date"), {
      target: { value: "2031-01-02" },
    });
    fireEvent.input(screen.getByLabelText("Last trading date"), {
      target: { value: "2031-01-04" },
    });
    await userEvent.click(screen.getByRole("button", { name: "Apply dates" }));
    await waitFor(() =>
      expect(equity.mock.calls.at(-1)?.[3]).toEqual({
        start_date: "2031-01-02",
        end_date: "2031-01-04",
      }),
    );
    expect(equity.mock.calls.at(-1)?.[2]).toBe(0);
    expect(summary).toHaveBeenCalledTimes(1);
    expect(screen.getByText("12.000000000000000001")).toBeInTheDocument();
    fireEvent.input(screen.getByLabelText("First trading date"), {
      target: { value: "2031-01-05" },
    });
    await userEvent.click(screen.getByRole("button", { name: "Apply dates" }));
    const rangeError = screen.getByRole("alert");
    const firstDate = screen.getByLabelText("First trading date");
    const lastDate = screen.getByLabelText("Last trading date");
    expect(rangeError).toHaveTextContent("valid date range");
    expect(firstDate).toHaveFocus();
    for (const input of [firstDate, lastDate]) {
      expect(input).toHaveAttribute("aria-invalid", "true");
      expect(input).toHaveAttribute("aria-describedby", rangeError.id);
    }
    fireEvent.input(firstDate, { target: { value: "2031-01-03" } });
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
    expect(firstDate).not.toHaveAttribute("aria-invalid");
    expect(lastDate).not.toHaveAttribute("aria-invalid");
    expect(equity).toHaveBeenCalledTimes(2);
    await userEvent.click(
      screen.getByRole("button", { name: "Show full interval" }),
    );
    await waitFor(() => expect(equity.mock.calls.at(-1)?.[3]).toEqual({}));
  });

  it("links the selected chart date to trades and actual account snapshots without loading other dates", async () => {
    const equity = vi
      .spyOn(experimentApi, "equity")
      .mockResolvedValue({ items: [point], total: 1, limit: 100, offset: 0 });
    const trades = vi
      .spyOn(experimentApi, "trades")
      .mockResolvedValue({ items: [], total: 0, limit: 20, offset: 0 });
    const holdings = vi.spyOn(experimentApi, "holdings").mockResolvedValue({
      items: [snapshot],
      total: 1,
      limit: 1,
      offset: 0,
      availability: "AVAILABLE",
    });
    render(<ExperimentCollections jobId={job.job_id} />);
    fireEvent.input(screen.getByLabelText("First trading date"), {
      target: { value: point.trading_date },
    });
    fireEvent.input(screen.getByLabelText("Last trading date"), {
      target: { value: point.trading_date },
    });
    await userEvent.click(screen.getByRole("button", { name: "Apply dates" }));
    await userEvent.click(
      await screen.findByRole("button", {
        name: "Show trades and holdings for this date",
      }),
    );
    expect(
      await screen.findByText(/No open positions at this snapshot/),
    ).toBeInTheDocument();
    const range = {
      start_date: point.trading_date,
      end_date: point.trading_date,
    };
    expect(equity.mock.calls.at(-1)?.[3]).toEqual(range);
    expect(trades.mock.calls.at(-1)?.[3]).toEqual(range);
    expect(holdings.mock.calls.at(-1)?.[3]).toEqual(range);
    expect(
      screen.getAllByText("100,000.000000000000000009").length,
    ).toBeGreaterThan(0);
    for (const name of ["Trades", "Account & holdings"]) {
      await userEvent.click(screen.getByText(name, { selector: "summary" }));
      expect(
        screen.getByText(name, { selector: "summary" }).parentElement,
      ).not.toHaveAttribute("open");
    }
    await userEvent.click(
      screen.getByRole("button", {
        name: "Show trades and holdings for this date",
      }),
    );
    expect(
      await screen.findByText(/No open positions at this snapshot/),
    ).toBeInTheDocument();
    for (const name of ["Trades", "Account & holdings"])
      expect(
        screen.getByText(name, { selector: "summary" }).parentElement,
      ).toHaveAttribute("open");
    await userEvent.click(
      screen.getByRole("button", { name: "Clear linked date" }),
    );
    await waitFor(() => expect(equity.mock.calls.at(-1)?.[3]).toEqual(range));
    await userEvent.click(
      screen.getByRole("button", { name: "Show full interval" }),
    );
    await waitFor(() => expect(equity.mock.calls.at(-1)?.[3]).toEqual({}));
  });

  it("converts legacy UTC trade timestamps into Shanghai trading dates and links that exact day", async () => {
    expect(tradingDate({ timestamp: "2031-01-02T18:00:00Z" })).toBe(
      "2031-01-03",
    );
    expect(tradingDate({ timestamp: "bad" })).toBeNull();
    expect(
      tradingDate({
        timestamp: "2031-01-02T18:00:00Z",
        trading_date: "2031-01-04",
      }),
    ).toBe("2031-01-04");
    const equity = vi
      .spyOn(experimentApi, "equity")
      .mockResolvedValue({ items: [point], total: 1, limit: 100, offset: 0 });
    vi.spyOn(experimentApi, "trades").mockResolvedValue({
      items: [
        {
          sequence: 0,
          order_id: "order",
          security_id: "SSE:600000",
          side: "BUY",
          quantity: "100",
          price: "9.123456789012345678",
          transaction_cost: "5",
          timestamp: "2031-01-02T18:00:00Z",
        },
      ],
      total: 1,
      limit: 20,
      offset: 0,
    });
    vi.spyOn(experimentApi, "holdings").mockResolvedValue({
      items: [],
      total: 0,
      limit: 1,
      offset: 0,
      availability: "NOT_RECORDED",
    });
    render(<ExperimentCollections jobId={job.job_id} />);
    await screen.findByRole("button", {
      name: "Show trades and holdings for this date",
    });
    await userEvent.click(screen.getByText("Trades", { selector: "summary" }));
    await userEvent.click(
      await screen.findByRole("button", {
        name: "Inspect this trading date: 2031-01-03",
      }),
    );
    await waitFor(() =>
      expect(equity.mock.calls.at(-1)?.[3]).toEqual({
        start_date: "2031-01-03",
        end_date: "2031-01-03",
      }),
    );
  });

  it("distinguishes unrecorded legacy holdings from real all-cash snapshots and retains null weight", async () => {
    vi.spyOn(experimentApi, "holdings")
      .mockResolvedValueOnce({
        items: [],
        total: 0,
        limit: 1,
        offset: 0,
        availability: "NOT_RECORDED",
      })
      .mockResolvedValueOnce({
        items: [
          {
            ...snapshot,
            positions: [
              {
                security_id: "SSE:600000",
                quantity: "100",
                average_price: "9.123456789012345678",
                market_price: "10",
                market_value: "1000",
                weight: null,
              },
            ],
          },
        ],
        total: 3,
        limit: 1,
        offset: 0,
        availability: "AVAILABLE",
      });
    const first = render(<ExperimentHoldings jobId={job.job_id} range={{}} />);
    expect(
      await screen.findByText(/older run did not record account snapshots/),
    ).toBeInTheDocument();
    expect(screen.queryByText(/No open positions/)).not.toBeInTheDocument();
    first.unmount();
    render(<ExperimentHoldings jobId={job.job_id} range={{}} />);
    const row = await screen.findByRole("row", { name: /SSE:600000/ });
    expect(within(row).getByText("9.123456789012345678")).toBeInTheDocument();
    expect(within(row).getByText("N/A")).toBeInTheDocument();
    expect(
      screen.getByText("Total profit / loss (CNY)").nextSibling,
    ).toHaveTextContent("N/A");
    expect(screen.getByRole("button", { name: "Next" })).toBeEnabled();
  });
});

describe("server-generated report downloads", () => {
  it("keeps a prepared report available when a replacement download fails", async () => {
    const blob = new Blob(["first report"], { type: "text/csv" });
    const replacement = new Blob(["replacement report"], { type: "text/csv" });
    const revoke = vi.fn();
    vi.stubGlobal(
      "URL",
      Object.assign(URL, {
        createObjectURL: vi
          .fn()
          .mockReturnValueOnce("blob:first-report")
          .mockReturnValueOnce("blob:replacement"),
        revokeObjectURL: revoke,
      }),
    );
    vi.spyOn(HTMLAnchorElement.prototype, "click").mockImplementation(
      () => undefined,
    );
    vi.spyOn(experimentApi, "export")
      .mockResolvedValueOnce(blob)
      .mockRejectedValueOnce(new ApiError(503, "Unavailable"))
      .mockResolvedValueOnce(replacement);

    const view = render(<ExperimentExports jobId={job.job_id} range={{}} />);
    const download = screen.getByRole("button", {
      name: "Download records (CSV)",
    });
    await userEvent.click(download);
    const fallback = await screen.findByRole("link", {
      name: "Save prepared report",
    });
    expect(fallback).toHaveAttribute("href", "blob:first-report");

    await userEvent.click(download);
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "The report could not be downloaded",
    );
    expect(fallback).toHaveAttribute("href", "blob:first-report");
    expect(revoke).not.toHaveBeenCalled();

    await userEvent.click(download);
    await waitFor(() =>
      expect(
        screen.getByRole("link", { name: "Save prepared report" }),
      ).toHaveAttribute("href", "blob:replacement"),
    );
    expect(revoke).toHaveBeenCalledWith("blob:first-report");

    view.unmount();
    expect(revoke).toHaveBeenCalledWith("blob:replacement");
  });

  it("downloads the unchanged server blob once and shows real pending feedback", async () => {
    const blob = new Blob(["server metadata,exact amounts"], {
      type: "text/csv",
    });
    const createUrl = vi.fn().mockReturnValue("blob:report");
    vi.stubGlobal(
      "URL",
      Object.assign(URL, {
        createObjectURL: createUrl,
        revokeObjectURL: vi.fn(),
      }),
    );
    const click = vi
      .spyOn(HTMLAnchorElement.prototype, "click")
      .mockImplementation(() => undefined);
    let resolve: ((value: Blob) => void) | undefined;
    const download = vi.spyOn(experimentApi, "export").mockImplementation(
      () =>
        new Promise((done) => {
          resolve = done;
        }),
    );
    const view = render(
      <ExperimentExports
        jobId={job.job_id}
        range={{ start_date: "2031-01-02" }}
      />,
    );
    const exportButton = screen.getByRole("button", {
      name: "Download records (CSV)",
    });
    exportButton.focus();
    await userEvent.dblClick(exportButton);
    expect(exportButton).toHaveFocus();
    expect(exportButton).toHaveAttribute("aria-disabled", "true");
    expect(exportButton).toBeEnabled();
    expect(download).toHaveBeenCalledTimes(1);
    expect(download).toHaveBeenCalledWith(job.job_id, "csv", "trades", {
      start_date: "2031-01-02",
    });
    expect(screen.getByRole("status")).toHaveTextContent("Preparing download");
    await act(async () => {
      resolve?.(blob);
    });
    expect(exportButton).toHaveFocus();
    expect(exportButton).toHaveAttribute("aria-disabled", "false");
    expect(createUrl).toHaveBeenCalledWith(blob);
    expect(click).toHaveBeenCalledOnce();
    expect(screen.getByRole("status")).toHaveTextContent(
      "Check your browser downloads",
    );
    const fallback = screen.getByRole("link", { name: "Save prepared report" });
    expect(fallback).toHaveAttribute("href", "blob:report");
    expect(fallback).toHaveAttribute(
      "download",
      `experiment-${job.job_id}-trades.csv`,
    );
    expect(URL.revokeObjectURL).not.toHaveBeenCalled();
    view.unmount();
    expect(URL.revokeObjectURL).toHaveBeenCalledWith("blob:report");
  });

  it("explains missing legacy holdings export instead of producing an empty CSV", async () => {
    vi.spyOn(experimentApi, "export").mockRejectedValue(
      new ApiError(409, "Missing", "HOLDINGS_NOT_RECORDED_FOR_THIS_RUN"),
    );
    render(<ExperimentExports jobId={job.job_id} range={{}} />);
    await userEvent.selectOptions(
      screen.getByLabelText("Records to export"),
      "holdings",
    );
    await userEvent.click(
      screen.getByRole("button", { name: "Download records (CSV)" }),
    );
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "older run did not record account snapshots",
    );
  });
});
