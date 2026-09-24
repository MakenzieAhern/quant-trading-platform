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
import { job, result } from "./fixtures.test-data";
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
    expect(screen.getByRole("alert")).toHaveTextContent("valid date range");
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
    await userEvent.click(
      screen.getByRole("button", { name: "Clear linked date" }),
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
    await userEvent.dblClick(
      screen.getByRole("button", { name: "Download records (CSV)" }),
    );
    expect(download).toHaveBeenCalledTimes(1);
    expect(download).toHaveBeenCalledWith(job.job_id, "csv", "trades", {
      start_date: "2031-01-02",
    });
    expect(screen.getByRole("status")).toHaveTextContent("Preparing download");
    await act(async () => {
      resolve?.(blob);
    });
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
