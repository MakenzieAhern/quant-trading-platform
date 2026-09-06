import { act, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { jsonResponse, metrics, run, RUN_ID } from "../test/fixtures";
import { BacktestDetailPage } from "./BacktestDetailPage";

describe("backtest detail", () => {
  it("prevents an in-flight old route from overwriting a newer run", async () => {
    let resolveA!: (response: Response) => void;
    let resolveB!: (response: Response) => void;
    const responseA = new Promise<Response>((resolve) => {
      resolveA = resolve;
    });
    const responseB = new Promise<Response>((resolve) => {
      resolveB = resolve;
    });
    vi.spyOn(globalThis, "fetch")
      .mockReturnValueOnce(responseA)
      .mockReturnValueOnce(responseB);
    const view = render(<BacktestDetailPage runId={RUN_ID} />);
    view.rerender(
      <BacktestDetailPage runId="a0975744-c58a-49d8-a72d-45f6ed700ca6" />,
    );
    resolveB(jsonResponse({ ...run("FAILED"), error_message: "run B failed" }));
    expect(await screen.findByText("run B failed")).toBeInTheDocument();
    resolveA(jsonResponse({ ...run("FAILED"), error_message: "stale run A" }));
    await waitFor(() =>
      expect(screen.queryByText("stale run A")).not.toBeInTheDocument(),
    );
    expect(screen.getByText("run B failed")).toBeInTheDocument();
  });

  it("polls active runs once per interval and stops on a terminal state", async () => {
    vi.useFakeTimers();
    const fetch = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValueOnce(jsonResponse(run("RUNNING")))
      .mockResolvedValueOnce(jsonResponse(run("FAILED")));
    render(<BacktestDetailPage runId={RUN_ID} />);
    await act(async () => undefined);
    expect(screen.getByText("Backtest in progress")).toBeInTheDocument();
    await act(async () => vi.advanceTimersByTimeAsync(5000));
    expect(screen.getByText("Backtest failed")).toBeInTheDocument();
    await act(async () => vi.advanceTimersByTimeAsync(10_000));
    expect(fetch).toHaveBeenCalledTimes(2);
  });

  it("cleans up active polling after unmount", async () => {
    vi.useFakeTimers();
    const fetch = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValue(jsonResponse(run("RUNNING")));
    const view = render(<BacktestDetailPage runId={RUN_ID} />);
    await act(async () => undefined);
    expect(screen.getByText("Backtest in progress")).toBeInTheDocument();
    view.unmount();
    await act(async () => vi.advanceTimersByTimeAsync(10_000));
    expect(fetch).toHaveBeenCalledTimes(1);
  });

  it("shows only sanitized failure state without successful results", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      jsonResponse(run("FAILED")),
    );
    render(<BacktestDetailPage runId={RUN_ID} />);
    expect(await screen.findByText("Backtest failed")).toBeInTheDocument();
    expect(
      screen.getByText("RuntimeError: backtest execution failed"),
    ).toBeInTheDocument();
    expect(screen.queryByText("Performance")).not.toBeInTheDocument();
    expect(screen.queryByText("Equity curve")).not.toBeInTheDocument();
  });

  it("renders backend text as text rather than executable markup", async () => {
    const markup = '<img src=x onerror="window.__injected=true">';
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      jsonResponse({ ...run("FAILED"), error_message: markup }),
    );
    render(<BacktestDetailPage runId={RUN_ID} />);
    expect(await screen.findByText(markup)).toBeInTheDocument();
    expect(document.querySelector("img")).not.toBeInTheDocument();
  });

  it("renders authoritative metrics, N/A values, Decimal strings, and event tables", async () => {
    vi.spyOn(globalThis, "fetch").mockImplementation((input) => {
      const url = String(input);
      if (url.endsWith(`/api/backtests/${RUN_ID}`))
        return Promise.resolve(jsonResponse(run()));
      if (url.includes("/result"))
        return Promise.resolve(
          jsonResponse({
            run_id: RUN_ID,
            status: "SUCCEEDED",
            metrics,
            signal_count: 1,
            proposal_count: 1,
            risk_decision_count: 1,
            risk_rejection_count: 0,
            order_count: 1,
            fill_count: 1,
            snapshot_count: 1,
            reservation_count: 0,
            start_time: "2024-01-02T00:00:00Z",
            end_time: "2024-01-03T00:00:00Z",
          }),
        );
      if (url.includes("/equity"))
        return Promise.resolve(
          jsonResponse({
            items: [
              {
                timestamp: "2024-01-02T00:00:00Z",
                equity: metrics.initial_equity,
                cash: metrics.initial_equity,
                market_value: "0",
              },
            ],
            limit: 200,
            offset: 0,
            total: 1,
          }),
        );
      if (url.includes("/signals"))
        return Promise.resolve(
          jsonResponse({
            items: [
              {
                strategy_id: "moving_average_crossover:AAPL",
                symbol: "AAPL",
                timestamp: "2024-01-02T00:00:00Z",
                signal_type: "BUY",
              },
            ],
            limit: 25,
            offset: 0,
            total: 1,
          }),
        );
      if (url.includes("/risk-decisions"))
        return Promise.resolve(
          jsonResponse({
            items: [
              {
                proposal_id: RUN_ID,
                approved: true,
                reason_code: "APPROVED",
                message: "proposal approved",
                timestamp: "2024-01-02T00:00:00Z",
                risk_increasing: true,
                reference_price: "185.14",
                order_notional: "1851.40",
                projected_position_quantity: "10",
                projected_symbol_exposure: "1851.40",
                projected_gross_exposure: "1851.40",
                projected_net_exposure: "1851.40",
                projected_gross_leverage: "0.018514",
                projected_cash: "98148.60",
                estimated_transaction_cost: "0",
              },
            ],
            limit: 25,
            offset: 0,
            total: 1,
          }),
        );
      if (url.includes("/orders"))
        return Promise.resolve(
          jsonResponse({
            items: [
              {
                order_id: RUN_ID,
                strategy_id: "moving_average_crossover:AAPL",
                symbol: "AAPL",
                side: "BUY",
                order_type: "MARKET",
                quantity: "10.000000000000000001",
                price: null,
                status: "FILLED",
                created_at: "2024-01-02T00:00:00Z",
              },
            ],
            limit: 25,
            offset: 0,
            total: 1,
          }),
        );
      if (url.includes("/fills"))
        return Promise.resolve(
          jsonResponse({
            items: [
              {
                order_id: RUN_ID,
                strategy_id: "moving_average_crossover:AAPL",
                symbol: "AAPL",
                side: "BUY",
                quantity: "10.000000000000000001",
                price: "185.140000000000000001",
                commission: metrics.total_commission,
                timestamp: "2024-01-03T00:00:00Z",
              },
            ],
            limit: 25,
            offset: 0,
            total: 1,
          }),
        );
      return Promise.reject(new Error(`Unexpected URL: ${url}`));
    });
    render(<BacktestDetailPage runId={RUN_ID} />);
    expect(await screen.findByText("Performance")).toBeInTheDocument();
    expect(await screen.findAllByText("N/A")).toHaveLength(3);
    expect(
      await screen.findByTitle("185.140000000000000001"),
    ).toHaveTextContent("185.140000000000000001");
    expect(screen.getByText("BUY / MARKET")).toBeInTheDocument();
    expect(screen.getByText("proposal approved")).toBeInTheDocument();
    expect(screen.getByText("Equity curve")).toBeInTheDocument();
  });
});
