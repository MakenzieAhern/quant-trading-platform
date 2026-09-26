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
import { experimentApi } from "../product/experiments/api";
import { job, plan } from "../product/experiments/fixtures.test-data";
import { jsonResponse } from "../test/fixtures";
import { PAPER_ID, paperSession, paperSnapshot } from "../test/paperFixtures";
import { CreatePaperSessionPage } from "./CreatePaperSessionPage";
import { PaperSessionDetailPage } from "./PaperSessionDetailPage";
import { PaperSessionsPage } from "./PaperSessionsPage";

class MockWebSocket {
  static readonly OPEN = 1;
  static readonly CLOSED = 3;
  static instances: MockWebSocket[] = [];
  readyState = 0;
  onopen: (() => void) | null = null;
  onmessage: ((event: MessageEvent) => void) | null = null;
  onerror: (() => void) | null = null;
  onclose: (() => void) | null = null;

  constructor(public readonly url: string) {
    MockWebSocket.instances.push(this);
  }

  open() {
    this.readyState = MockWebSocket.OPEN;
    this.onopen?.();
  }

  message(value: unknown) {
    this.onmessage?.({ data: JSON.stringify(value) } as MessageEvent);
  }

  close() {
    if (this.readyState === MockWebSocket.CLOSED) return;
    this.readyState = MockWebSocket.CLOSED;
    this.onclose?.();
  }
}

function installWebSocket() {
  MockWebSocket.instances = [];
  vi.stubGlobal("WebSocket", MockWebSocket as unknown as typeof WebSocket);
}

describe("paper trading pages", () => {
  it("bounds events waiting for a slow REST hydration and reconnects", async () => {
    installWebSocket();
    vi.useFakeTimers();
    const fetch = vi
      .spyOn(globalThis, "fetch")
      .mockReturnValue(new Promise(() => {}));
    render(<PaperSessionDetailPage sessionId={PAPER_ID} />);
    await act(async () => MockWebSocket.instances[0]!.open());
    act(() => {
      for (let sequence = 1; sequence <= 257; sequence++) {
        MockWebSocket.instances[0]!.message({
          sequence,
          type: "portfolio.snapshot",
          occurred_at: "2024-01-09T00:00:00Z",
          payload: {
            timestamp: "2024-01-09T00:00:00Z",
            cash: "100000",
            market_value: "0",
            equity: "100000",
            realized_pnl: "0",
            unrealized_pnl: "0",
            cumulative_commission: "0",
            drawdown: "0",
            positions: [],
          },
        });
      }
    });
    expect(fetch.mock.calls[0]?.[1]?.signal?.aborted).toBe(true);
    expect(MockWebSocket.instances[0]!.readyState).toBe(MockWebSocket.CLOSED);
    await act(async () => vi.advanceTimersByTimeAsync(1000));
    expect(MockWebSocket.instances).toHaveLength(2);
  });

  it("rehydrates after one failed snapshot instead of leaving the page stuck", async () => {
    installWebSocket();
    vi.useFakeTimers();
    const fetch = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValueOnce(jsonResponse({ detail: "temporary" }, 503))
      .mockResolvedValueOnce(jsonResponse(paperSnapshot("STOPPED")));
    render(<PaperSessionDetailPage sessionId={PAPER_ID} />);
    await act(async () => MockWebSocket.instances[0]!.open());
    expect(MockWebSocket.instances[0]!.readyState).toBe(MockWebSocket.CLOSED);
    await act(async () => vi.advanceTimersByTimeAsync(1000));
    expect(MockWebSocket.instances).toHaveLength(2);
    await act(async () => MockWebSocket.instances[1]!.open());
    expect(fetch).toHaveBeenCalledTimes(2);
    expect(screen.getByText("Paper portfolio")).toBeInTheDocument();
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
  });

  it("hides stale financial values until a failed reconnect obtains a new snapshot", async () => {
    installWebSocket();
    vi.useFakeTimers();
    vi.spyOn(globalThis, "fetch")
      .mockResolvedValueOnce(jsonResponse(paperSnapshot("RUNNING")))
      .mockResolvedValueOnce(jsonResponse({ detail: "unavailable" }, 503))
      .mockResolvedValueOnce(jsonResponse(paperSnapshot("STOPPED")));
    render(<PaperSessionDetailPage sessionId={PAPER_ID} />);
    await act(async () => MockWebSocket.instances[0]!.open());
    expect(screen.getByText("Paper portfolio")).toBeInTheDocument();

    act(() => MockWebSocket.instances[0]!.close());
    await act(async () => vi.advanceTimersByTimeAsync(1000));
    await act(async () => MockWebSocket.instances[1]!.open());
    expect(screen.queryByText("Paper portfolio")).not.toBeInTheDocument();
    expect(screen.getByRole("alert")).toHaveTextContent("unavailable");

    await act(async () => vi.advanceTimersByTimeAsync(2000));
    await act(async () => MockWebSocket.instances[2]!.open());
    expect(screen.getByText("Paper portfolio")).toBeInTheDocument();
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
  });

  it("hides the last portfolio when socket reconnect attempts are exhausted", async () => {
    installWebSocket();
    vi.useFakeTimers();
    const fetch = vi.spyOn(globalThis, "fetch").mockResolvedValue(
      jsonResponse({
        ...paperSnapshot("RUNNING"),
        latest_portfolio: {
          timestamp: "2024-01-09T00:00:00Z",
          cash: "81309.8134",
          market_value: "18655",
          equity: "99964.8134",
          realized_pnl: "0",
          unrealized_pnl: "-5",
          cumulative_commission: "30.1866",
          drawdown: "0",
          positions: [],
        },
      }),
    );
    render(<PaperSessionDetailPage sessionId={PAPER_ID} />);
    await act(async () => MockWebSocket.instances[0]!.open());
    expect(screen.getByTitle("81309.8134")).toBeInTheDocument();

    for (const delay of [1000, 2000, 4000]) {
      act(() => MockWebSocket.instances.at(-1)!.close());
      await act(async () => vi.advanceTimersByTimeAsync(delay));
    }
    act(() => MockWebSocket.instances.at(-1)!.close());
    expect(MockWebSocket.instances).toHaveLength(4);
    expect(fetch).toHaveBeenCalledTimes(1);
    expect(screen.getByRole("alert")).toHaveTextContent("Reload page");
    expect(screen.queryByTitle("81309.8134")).not.toBeInTheDocument();
  });

  it("stops snapshot retries on denied access and bounds repeated service failures", async () => {
    installWebSocket();
    vi.useFakeTimers();
    const fetch = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValueOnce(jsonResponse({ detail: "forbidden" }, 403))
      .mockResolvedValue(jsonResponse({ detail: "unavailable" }, 503));
    const denied = render(<PaperSessionDetailPage sessionId={PAPER_ID} />);
    await act(async () => MockWebSocket.instances[0]!.open());
    expect(screen.getByRole("alert")).toHaveTextContent("Access was denied");
    await act(async () => vi.advanceTimersByTimeAsync(8000));
    expect(MockWebSocket.instances).toHaveLength(1);
    denied.unmount();

    installWebSocket();
    render(<PaperSessionDetailPage sessionId={PAPER_ID} />);
    for (const delay of [1000, 2000, 4000]) {
      await act(async () => MockWebSocket.instances.at(-1)!.open());
      await act(async () => vi.advanceTimersByTimeAsync(delay));
    }
    await act(async () => MockWebSocket.instances.at(-1)!.open());
    await act(async () => vi.advanceTimersByTimeAsync(8000));
    expect(MockWebSocket.instances).toHaveLength(4);
    expect(fetch).toHaveBeenCalledTimes(5);
    expect(screen.getByRole("alert")).toHaveTextContent("Reload page");
  });

  it("classifies a rejected opening socket through the authoritative REST snapshot", async () => {
    installWebSocket();
    vi.useFakeTimers();
    const fetch = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValue(
        jsonResponse({ detail: "paper session not found" }, 404),
      );
    render(<PaperSessionDetailPage sessionId={PAPER_ID} />);
    await act(async () => MockWebSocket.instances[0]!.close());
    expect(screen.getByRole("alert")).toHaveTextContent(
      "This record is unavailable",
    );
    expect(
      screen.getByRole("link", { name: "← All paper sessions" }),
    ).toHaveAttribute("href", "/paper");
    expect(fetch).toHaveBeenCalledTimes(1);
    await act(async () => vi.advanceTimersByTimeAsync(8000));
    expect(MockWebSocket.instances).toHaveLength(1);
  });

  it("renders persisted session history and the permanent safety warning", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      jsonResponse({ items: [paperSession()], limit: 20, offset: 0, total: 1 }),
    );
    render(<PaperSessionsPage />);
    expect(
      await screen.findByText("Created", { selector: ".statusBadge" }),
    ).toBeInTheDocument();
    expect(screen.getByText(/SIMULATED EXECUTION ONLY/)).toBeInTheDocument();
    expect(screen.getByText(/not A-share data/)).toBeInTheDocument();
    expect(
      screen.getByRole("link", {
        name: /Open session: Moving average crossover/,
      }),
    ).toHaveAttribute("href", `/paper/${PAPER_ID}`);
    expect(
      screen.getByRole("region", { name: /If columns are cut off/ }),
    ).toHaveAttribute("tabindex", "0");
  });

  it("distinguishes same-strategy sessions without making IDs the primary action", async () => {
    const secondId = "534d9730-a8c9-4f71-a0fc-c4b5d156f2ef";
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      jsonResponse({
        items: [
          paperSession(),
          {
            ...paperSession(),
            session_id: secondId,
            created_at: "2026-09-06T02:01:00Z",
          },
        ],
        limit: 20,
        offset: 0,
        total: 2,
      }),
    );
    render(<PaperSessionsPage />);
    const links = await screen.findAllByRole("link", {
      name: /Open session: Moving average crossover/,
    });
    expect(links).toHaveLength(2);
    expect(links[0]).toHaveTextContent("Open session");
    expect(links[0]).not.toHaveAttribute(
      "aria-label",
      links[1]?.getAttribute("aria-label"),
    );
    expect(screen.queryByText(/34d97303/)).not.toBeInTheDocument();
    await act(async () => i18n.changeLanguage("zh-CN"));
    expect(
      screen.getAllByRole("link", { name: /查看会话: 移动平均线交叉/ }),
    ).toHaveLength(2);
    await act(async () => i18n.changeLanguage("en-US"));
  });

  it("shows the account's dated plan without implying a live order", async () => {
    installWebSocket();
    const accountPlan = {
      ...plan,
      mode: "historical_exploration",
      as_of_trading_date: "2011-03-22",
      next_accepted_session: "2011-03-23",
      account_mode: "HISTORICAL_PAPER_REPLAY",
      submitted_to_account: true,
      paper_session_id: PAPER_ID,
      plan_version: "PAPER_ACCOUNT_PLAN_V1",
    };
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      jsonResponse({
        ...paperSnapshot("STOPPED"),
        last_rebalance_plan: accountPlan,
        session: {
          ...paperSession("STOPPED"),
          provider_type: "historical_a_share",
          strategy_type: "cn_a_cross_sectional_momentum_low_vol_v1",
        },
        latest_portfolio: {
          timestamp: "2011-03-23T07:00:00Z",
          cash: "90123",
          market_value: "9877",
          equity: "100000",
          realized_pnl: "0",
          unrealized_pnl: "0",
          cumulative_commission: "0",
          drawdown: "0",
          positions: [
            {
              symbol: "600000.SSE",
              quantity: "100",
              average_price: "10",
              market_price: "10.5",
              unrealized_pnl: "50",
              realized_pnl: "0",
            },
          ],
          plan: {
            ...accountPlan,
            status: "NOT_REBALANCE_SESSION",
            as_of_trading_date: "2011-03-23",
            candidates: [],
            submitted_to_account: false,
          },
        },
      }),
    );
    render(<PaperSessionDetailPage sessionId={PAPER_ID} />);
    await act(async () => MockWebSocket.instances[0]!.open());
    expect(
      await screen.findByText("This account's historical rebalance plan"),
    ).toBeVisible();
    expect(
      screen.getByText(/routed through this account's simulated risk/),
    ).toBeVisible();
    expect(screen.getByText("9.123456789123456789")).toBeVisible();
    expect(screen.getByText("2011-03-22")).toBeVisible();
    expect(screen.getByText("Cash at plan time (CNY)")).toBeVisible();
    expect(screen.getByText("Cash (CNY)")).toBeVisible();
    expect(screen.getByText("Market value (CNY)")).toBeVisible();
    expect(
      screen.getByRole("columnheader", { name: "Price (CNY)" }),
    ).toBeVisible();
    expect(
      screen.queryByRole("button", { name: /execute|submit/i }),
    ).not.toBeInTheDocument();
    await act(async () => i18n.changeLanguage("zh-CN"));
    expect(screen.getByText("此模拟账户的历史调仓计划")).toBeVisible();
    expect(screen.getByText(/不是今日交易建议/)).toBeVisible();
    expect(screen.getByText("计划时账户现金（人民币）")).toBeVisible();
    expect(screen.getByText("现金（人民币）")).toBeVisible();
    expect(
      screen.getByRole("columnheader", { name: "价格（人民币）" }),
    ).toBeVisible();
    await act(async () => i18n.changeLanguage("en-US"));
  });

  it("keeps a denied paper-list error typed for actionable guidance", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      jsonResponse({ detail: "forbidden" }, 403),
    );
    render(<PaperSessionsPage />);
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Access was denied",
    );
    expect(screen.getByRole("link", { name: "Reload page" })).toBeVisible();
  });

  it("keeps legacy AAPL replay explicit and creates it with one idempotency key", async () => {
    const fetch = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValue(jsonResponse(paperSession(), 201));
    render(<CreatePaperSessionPage />);
    expect(screen.getByLabelText("Provider")).toHaveValue("simulated_a_share");
    await userEvent.selectOptions(screen.getByLabelText("Provider"), "replay");
    expect(screen.getByLabelText("Provider")).toHaveValue("replay");
    expect(
      screen.getByRole("option", { name: "Legacy AAPL fixture (not A-share)" }),
    ).toBeInTheDocument();
    expect(screen.getByLabelText("Dataset")).toHaveValue("AAPL_fixture");
    await userEvent.click(
      screen.getByRole("button", { name: "Create paper session" }),
    );
    await waitFor(() =>
      expect(window.location.pathname).toBe(`/paper/${PAPER_ID}`),
    );
    expect(fetch).toHaveBeenCalledTimes(1);
    expect(
      new Headers(fetch.mock.calls[0]?.[1]?.headers).get("Idempotency-Key"),
    ).toBeTruthy();
    expect(JSON.parse(String(fetch.mock.calls[0]?.[1]?.body))).toMatchObject({
      provider_type: "replay",
      dataset_id: "AAPL_fixture",
      symbol: "AAPL",
    });
  });

  it("defaults to a clearly labeled synthetic A-share demo", async () => {
    const fetch = vi.spyOn(globalThis, "fetch").mockResolvedValue(
      jsonResponse(
        {
          ...paperSession(),
          provider_type: "simulated_a_share",
          dataset_id: "CN_A_SIMULATED_PAPER_FIXTURE_V1",
          symbol: "CN-A",
          strategy_type: "cn_a_cross_sectional_momentum_low_vol_v1",
          strategy_parameters: {},
        },
        201,
      ),
    );
    render(<CreatePaperSessionPage />);
    expect(screen.getByLabelText("Provider")).toHaveValue("simulated_a_share");
    expect(screen.getByLabelText("Initial cash")).toHaveValue("100000000");
    expect(screen.getByText(/not a recommended account size/)).toBeVisible();
    expect(screen.getByLabelText("Dataset")).toHaveValue(
      "CN_A_SIMULATED_PAPER_FIXTURE_V1",
    );
    expect(screen.getByLabelText("Symbol")).toHaveValue("CN-A");
    await userEvent.click(
      screen.getByRole("button", { name: "Create paper session" }),
    );
    await waitFor(() => expect(fetch).toHaveBeenCalledTimes(1));
    expect(JSON.parse(String(fetch.mock.calls[0]?.[1]?.body))).toMatchObject({
      provider_type: "simulated_a_share",
      dataset_id: "CN_A_SIMULATED_PAPER_FIXTURE_V1",
      symbol: "CN-A",
      strategy: {
        type: "cn_a_cross_sectional_momentum_low_vol_v1",
        parameters: {},
      },
    });
  });

  it("creates an explicitly historical A-share replay, never a forward session", async () => {
    const fetch = vi.spyOn(globalThis, "fetch").mockResolvedValue(
      jsonResponse(
        {
          ...paperSession(),
          provider_type: "historical_a_share",
          dataset_id: "cn-a-research-20100101-20251231-v1",
          symbol: "CN-A",
          strategy_type: "cn_a_cross_sectional_momentum_low_vol_v1",
        },
        201,
      ),
    );
    render(<CreatePaperSessionPage />);
    await userEvent.selectOptions(
      screen.getByLabelText("Provider"),
      "historical_a_share",
    );
    expect(screen.getByText(/Past audited sessions only/)).toBeInTheDocument();
    await userEvent.click(
      screen.getByText("Strategy, universe and cost settings"),
    );
    expect(
      screen.getByText(/simulation assumptions, not a verified broker quote/),
    ).toBeVisible();
    await act(async () => i18n.changeLanguage("zh-CN"));
    expect(screen.getByText(/模拟假设，不是已核实的券商报价/)).toBeVisible();
    await act(async () => i18n.changeLanguage("en-US"));
    fireEvent.input(screen.getByLabelText("End date"), {
      target: { value: "2011-03-23" },
    });
    await userEvent.click(
      screen.getByRole("button", { name: "Create paper session" }),
    );
    await waitFor(() => expect(fetch).toHaveBeenCalledTimes(1));
    expect(JSON.parse(String(fetch.mock.calls[0]?.[1]?.body))).toMatchObject({
      provider_type: "historical_a_share",
      dataset_id: "cn-a-research-20100101-20251231-v1",
      strategy: {
        parameters: { start_date: "2011-03-01", end_date: "2011-03-23" },
      },
      risk: {
        enforce_buying_power: true,
        max_leverage: "1",
        max_drawdown: "-0.2",
      },
    });
  });

  it("copies completed historical settings but requires an explicit 93-day replay range", async () => {
    window.history.replaceState(
      {},
      "",
      `/paper/new?from_experiment=${job.job_id}`,
    );
    vi.spyOn(experimentApi, "get").mockResolvedValue({
      ...job,
      name: "Saved historical study",
      status: "SUCCEEDED",
      result_available: true,
      mode: "historical_exploration",
      dataset_id: "cn-a-research-20100101-20251231-v1",
      configuration: {
        ...job.configuration,
        dataset_id: "cn-a-research-20100101-20251231-v1",
        start_date: "2010-01-04",
        end_date: "2011-03-22",
        initial_cash: "123456.789000000000001",
        universe: "SZSE",
        strategy: { rebalance_sessions: 23, maximum_holdings: 12 },
        costs: { commission_rate: "0.0007", minimum_commission: "7" },
        risk: { max_drawdown: "-0.35", max_position_weight: "0.08" },
      },
    });
    const fetch = vi.spyOn(globalThis, "fetch").mockResolvedValue(
      jsonResponse(
        {
          ...paperSession(),
          provider_type: "historical_a_share",
          dataset_id: "cn-a-research-20100101-20251231-v1",
        },
        201,
      ),
    );
    render(<CreatePaperSessionPage />);
    expect(
      await screen.findByText(/Settings copied from ‘Saved historical study’/),
    ).toBeVisible();
    expect(screen.getByText(/Choose the start date explicitly/)).toBeVisible();
    expect(screen.getByLabelText("Provider")).toHaveValue("historical_a_share");
    expect(screen.getByLabelText("Provider")).toBeDisabled();
    expect(screen.getByLabelText("Start date")).toHaveValue("");
    expect(screen.getByLabelText("End date")).toHaveValue("2011-03-22");
    expect(screen.getByLabelText("Initial cash")).toHaveValue(
      "123456.789000000000001",
    );
    screen
      .getByRole("link", { name: "Start an independent account instead" })
      .focus();
    await userEvent.tab();
    expect(screen.getByLabelText("Initial cash")).toHaveFocus();
    fireEvent.submit(
      screen
        .getByRole("button", { name: "Create paper session" })
        .closest("form")!,
    );
    expect(screen.getByRole("alert")).toHaveTextContent(
      "Choose no more than 93 calendar days",
    );
    expect(fetch).not.toHaveBeenCalled();
    await userEvent.click(
      screen.getByText("Strategy, universe and cost settings"),
    );
    expect(
      screen.getByLabelText("Drawdown risk limit (negative fraction)"),
    ).toHaveValue("-0.35");
    fireEvent.input(screen.getByLabelText("Start date"), {
      target: { value: "2011-01-01" },
    });
    await userEvent.click(
      screen.getByRole("button", { name: "Create paper session" }),
    );
    await waitFor(() => expect(fetch).toHaveBeenCalledTimes(1));
    expect(JSON.parse(String(fetch.mock.calls[0]?.[1]?.body))).toMatchObject({
      provider_type: "historical_a_share",
      initial_cash: "123456.789000000000001",
      strategy: {
        parameters: {
          start_date: "2011-01-01",
          end_date: "2011-03-22",
          rebalance_sessions: 23,
          maximum_holdings: 12,
          max_position_weight: "0.08",
          universe: "SZSE",
          commission_rate: "0.0007",
          minimum_commission: "7",
        },
      },
      risk: { max_drawdown: "-0.35" },
    });
  });

  it("does not turn a synthetic saved study into a historical paper account", async () => {
    window.history.replaceState(
      {},
      "",
      `/paper/new?from_experiment=${job.job_id}`,
    );
    vi.spyOn(experimentApi, "get").mockResolvedValue({
      ...job,
      status: "SUCCEEDED",
      result_available: true,
    });
    render(<CreatePaperSessionPage />);
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "cannot configure a historical paper account",
    );
    expect(
      screen.queryByRole("button", { name: "Create paper session" }),
    ).not.toBeInTheDocument();
    expect(
      screen.getByRole("link", { name: "Return to saved studies" }),
    ).toHaveAttribute("href", "/experiments");
  });

  it("labels persisted historical accounts without presenting archive IDs as the primary mode", async () => {
    installWebSocket();
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      jsonResponse({
        ...paperSnapshot("STOPPED"),
        session: {
          ...paperSession("STOPPED"),
          provider_type: "historical_a_share",
          dataset_id: "cn-a-research-20100101-20251231-v1",
          strategy_type: "cn_a_cross_sectional_momentum_low_vol_v1",
        },
        latest_session: {
          trading_date: "2011-03-23",
          security_count: 2065,
          source: "FROZEN_HISTORICAL_A_SHARE_REPLAY_V1",
        },
      }),
    );
    render(<PaperSessionDetailPage sessionId={PAPER_ID} />);
    await act(async () => MockWebSocket.instances[0]!.open());
    expect(
      await screen.findByText("Audited A-share historical replay"),
    ).toBeVisible();
    expect(
      screen.getByText("Audited historical archive · replay only"),
    ).toBeVisible();
    expect(
      screen.getByText("cn-a-research-20100101-20251231-v1"),
    ).not.toBeVisible();
    expect(screen.getByText(PAPER_ID)).not.toBeVisible();
  });

  it("offers pause while running and resume from a persisted paused account", async () => {
    installWebSocket();
    const fetch = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValueOnce(jsonResponse(paperSnapshot("RUNNING")))
      .mockResolvedValueOnce(jsonResponse(paperSession("PAUSING")));
    const view = render(<PaperSessionDetailPage sessionId={PAPER_ID} />);
    await act(async () => MockWebSocket.instances[0]!.open());
    await userEvent.click(screen.getByRole("button", { name: "Pause replay" }));
    expect(fetch.mock.calls[1]?.[0]).toContain(`/${PAPER_ID}/pause`);

    view.unmount();
    installWebSocket();
    fetch.mockResolvedValueOnce(jsonResponse(paperSnapshot("PAUSED")));
    render(<PaperSessionDetailPage sessionId={PAPER_ID} />);
    await act(async () => MockWebSocket.instances[0]!.open());
    expect(screen.getByRole("button", { name: "Resume replay" })).toBeVisible();
    expect(screen.getByRole("button", { name: "Stop replay" })).toBeVisible();
  });

  it("explains paper ledger enums and risk decisions in the selected language", async () => {
    installWebSocket();
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      jsonResponse({
        ...paperSnapshot("STOPPED"),
        latest_portfolio: {
          timestamp: "2011-03-23T07:00:00Z",
          cash: "81309.8134",
          market_value: "18655",
          equity: "99964.8134",
          realized_pnl: "0",
          unrealized_pnl: "-5",
          cumulative_commission: "30.1866",
          drawdown: "0",
          positions: [
            {
              symbol: "CN-A:SSE:600000",
              quantity: "100",
              average_price: "26",
              market_price: "26.19",
              unrealized_pnl: "19",
              realized_pnl: "0",
            },
          ],
        },
        signals: [
          {
            strategy_id: "cn_a_cross_sectional_momentum_low_vol_v1",
            symbol: "CN-A:SSE:600000",
            timestamp: "2011-03-22T07:00:00Z",
            signal_type: "BUY",
          },
        ],
        risk_decisions: [
          {
            proposal_id: PAPER_ID,
            approved: true,
            reason_code: "APPROVED",
            message: "proposal approved",
            timestamp: "2011-03-22T07:00:00Z",
          },
          {
            proposal_id: "00000000-0000-0000-0000-000000000001",
            approved: false,
            reason_code: "INSUFFICIENT_BUYING_POWER",
            message: "estimated purchase cost exceeds available cash",
            timestamp: "2011-03-22T07:00:00Z",
          },
        ],
        orders: [
          {
            order_id: PAPER_ID,
            strategy_id: "strategy",
            symbol: "CN-A:SSE:600000",
            side: "BUY",
            order_type: "LIMIT",
            quantity: "100",
            price: "26",
            status: "FILLED",
            created_at: "2011-03-22T07:00:00Z",
          },
        ],
        fills: [
          {
            order_id: PAPER_ID,
            strategy_id: "strategy",
            symbol: "CN-A:SSE:600000",
            side: "BUY",
            quantity: "100",
            price: "26",
            commission: "5.026",
            timestamp: "2011-03-23T01:25:00Z",
          },
        ],
      }),
    );
    await act(async () => i18n.changeLanguage("zh-CN"));
    try {
      render(<PaperSessionDetailPage sessionId={PAPER_ID} />);
      await act(async () => MockWebSocket.instances[0]!.open());
      expect(await screen.findByText("买入 / 限价单")).toBeVisible();
      expect(screen.getByText("已成交")).toBeVisible();
      expect(screen.getByText("风控检查通过")).toBeVisible();
      expect(screen.getByText("风控通过")).toBeVisible();
      expect(screen.getByText("提案已通过风控。")).toBeVisible();
      expect(screen.getByText("A股动量与低波动策略")).toBeVisible();
      expect(
        screen.queryByText("cn_a_cross_sectional_momentum_low_vol_v1"),
      ).not.toBeInTheDocument();
      expect(screen.getByText(/仅供模拟 \/ 不涉及真实资金/)).toBeVisible();
      expect(screen.getByText("会话连接: 已关闭")).toBeVisible();
      expect(screen.getByText("可用资金不足")).toBeVisible();
      expect(screen.getByText("预计买入成本超过可用现金。")).toBeVisible();
      for (const title of [
        "持仓",
        "信号",
        "风控决策",
        "模拟订单",
        "模拟成交",
      ]) {
        expect(
          screen.getByRole("region", {
            name: `${title} — ${i18n.t("research:scrollTable")}`,
          }),
        ).toHaveAttribute("tabindex", "0");
        expect(screen.getByRole("table", { name: title })).toBeVisible();
      }
      screen.getByRole("region", { name: /^持仓 —/ }).focus();
      await userEvent.tab();
      expect(screen.getByRole("region", { name: /^信号 —/ })).toHaveFocus();
      await act(async () => i18n.changeLanguage("en-US"));
      expect(screen.getByText("Buy / Limit")).toBeVisible();
      expect(screen.getByText("Filled")).toBeVisible();
      expect(screen.getByText("Risk check passed")).toBeVisible();
      expect(screen.getByText("Rejected by risk controls")).toBeVisible();
      expect(screen.getByText("Proposal approved.")).toBeVisible();
      expect(screen.getByText("Insufficient buying power")).toBeVisible();
      for (const title of [
        "Positions",
        "Signals",
        "Risk decisions",
        "Paper orders",
        "Paper fills",
      ]) {
        expect(
          screen.getByRole("region", {
            name: `${title} — ${i18n.t("research:scrollTable")}`,
          }),
        ).toHaveAttribute("tabindex", "0");
        expect(screen.getByRole("table", { name: title })).toBeVisible();
      }
      expect(screen.getByRole("region", { name: /^Signals —/ })).toHaveFocus();
    } finally {
      await act(async () => i18n.changeLanguage("en-US"));
    }
  });

  it("validates paper strategy parameters before submitting", async () => {
    const fetch = vi.spyOn(globalThis, "fetch");
    render(<CreatePaperSessionPage />);
    await userEvent.selectOptions(screen.getByLabelText("Provider"), "replay");
    fireEvent.change(screen.getByLabelText("Short period"), {
      target: { value: "4" },
    });
    fireEvent.change(screen.getByLabelText("Long period"), {
      target: { value: "3" },
    });
    fireEvent.submit(
      screen
        .getByRole("button", { name: "Create paper session" })
        .closest("form")!,
    );
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "short below long",
    );
    expect(fetch).not.toHaveBeenCalled();
  });

  it("hydrates from REST, ingests typed events once, and reconnects with rehydration", async () => {
    installWebSocket();
    vi.useFakeTimers();
    const fetch = vi
      .spyOn(globalThis, "fetch")
      .mockImplementation(async () => jsonResponse(paperSnapshot("RUNNING")));
    render(<PaperSessionDetailPage sessionId={PAPER_ID} />);
    expect(MockWebSocket.instances).toHaveLength(1);
    await act(async () => MockWebSocket.instances[0]!.open());
    expect(screen.getByText("Running")).toBeInTheDocument();
    expect(
      screen.getByText("Session connection: connected"),
    ).toBeInTheDocument();
    expect(
      screen
        .getByText("Session connection: connected")
        .closest('[role="status"]'),
    ).not.toBeNull();
    expect(
      screen.getByText("Running").closest('[role="status"]'),
    ).not.toBeNull();

    const portfolioEvent = {
      sequence: 1,
      type: "portfolio.snapshot",
      occurred_at: "2024-01-09T00:00:00Z",
      payload: {
        timestamp: "2024-01-09T00:00:00Z",
        cash: "98160.852500000000000001",
        market_value: "1851.4",
        equity: "100012.252500000000000001",
        realized_pnl: "0",
        unrealized_pnl: "12.2",
        cumulative_commission: "0",
        drawdown: "0",
        positions: [],
      },
    };
    act(() => MockWebSocket.instances[0]!.message(portfolioEvent));
    expect(screen.getByTitle("100012.252500000000000001")).toHaveTextContent(
      "100,012.252500000000000001",
    );
    expect(screen.queryByText("Cash (CNY)")).not.toBeInTheDocument();
    act(() => MockWebSocket.instances[0]!.message(portfolioEvent));
    expect(screen.getAllByText("Paper portfolio")).toHaveLength(1);

    act(() => MockWebSocket.instances[0]!.close());
    expect(
      screen.getByText("Session connection: reconnecting"),
    ).toBeInTheDocument();
    expect(
      screen
        .getByText("Session connection: reconnecting")
        .closest('[role="status"]'),
    ).not.toBeNull();
    expect(
      screen.getByText(/last verified snapshot/).closest('[role="status"]'),
    ).not.toBeNull();
    expect(screen.getByText("LAST VERIFIED PORTFOLIO")).toBeInTheDocument();
    expect(
      screen.queryByText("AUTHORITATIVE PORTFOLIO"),
    ).not.toBeInTheDocument();
    await act(async () => vi.advanceTimersByTimeAsync(1000));
    expect(MockWebSocket.instances).toHaveLength(2);
    await act(async () => MockWebSocket.instances[1]!.open());
    expect(fetch).toHaveBeenCalledTimes(2);
    expect(
      screen.queryByText(/last verified snapshot/),
    ).not.toBeInTheDocument();
    expect(screen.getByText("AUTHORITATIVE PORTFOLIO")).toBeInTheDocument();
  });

  it("closes terminal session streams without reconnecting", async () => {
    installWebSocket();
    vi.useFakeTimers();
    vi.spyOn(globalThis, "fetch")
      .mockResolvedValueOnce(jsonResponse(paperSnapshot("RUNNING")))
      .mockResolvedValue(
        jsonResponse({
          ...paperSnapshot("STOPPED"),
          last_sequence: 1,
          session: {
            ...paperSession("STOPPED"),
            stopped_at: "2026-09-06T02:01:00Z",
          },
        }),
      );
    render(<PaperSessionDetailPage sessionId={PAPER_ID} />);
    await act(async () => MockWebSocket.instances[0]!.open());
    act(() =>
      MockWebSocket.instances[0]!.message({
        sequence: 1,
        type: "session.status",
        occurred_at: "2026-09-06T02:01:00Z",
        payload: { status: "STOPPED" },
      }),
    );
    expect(
      screen.getByText("Stopped", { selector: ".statusBadge" }),
    ).toBeInTheDocument();
    expect(screen.getByText("Session connection: closed")).toBeInTheDocument();
    await act(async () => vi.advanceTimersByTimeAsync(2000));
    expect(MockWebSocket.instances).toHaveLength(1);
    expect(screen.getByText("2026-09-06 02:01:00Z (UTC)")).toBeInTheDocument();
  });

  it("hydrates terminal failure even when it arrives before the initial REST snapshot", async () => {
    installWebSocket();
    vi.spyOn(globalThis, "fetch")
      .mockReturnValueOnce(new Promise(() => {}))
      .mockResolvedValueOnce(
        jsonResponse({
          ...paperSnapshot("FAILED"),
          last_sequence: 1,
          session: {
            ...paperSession("FAILED"),
            error_message: "Paper execution failed safely.",
          },
        }),
      );
    render(<PaperSessionDetailPage sessionId={PAPER_ID} />);
    await act(async () => MockWebSocket.instances[0]!.open());
    await act(async () =>
      MockWebSocket.instances[0]!.message({
        sequence: 1,
        type: "session.status",
        occurred_at: "2026-09-06T02:01:00Z",
        payload: { status: "FAILED" },
      }),
    );
    expect(await screen.findByText("Failed")).toBeInTheDocument();
    expect(screen.getByRole("alert")).toHaveTextContent(
      "Paper execution failed safely.",
    );
    expect(screen.getByText("Session connection: closed")).toBeInTheDocument();
  });

  it("explains a backend interruption in Chinese and keeps the raw diagnostic for audit", async () => {
    installWebSocket();
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      jsonResponse({
        ...paperSnapshot("INTERRUPTED"),
        session: {
          ...paperSession("INTERRUPTED"),
          error_message: "Paper runtime interrupted by backend shutdown.",
        },
      }),
    );
    await act(async () => i18n.changeLanguage("zh-CN"));
    try {
      render(<PaperSessionDetailPage sessionId={PAPER_ID} />);
      await act(async () => MockWebSocket.instances[0]!.open());
      expect(await screen.findByRole("alert")).toHaveTextContent(
        "后端重启中断了本次回放",
      );
      expect(
        screen.getByRole("link", { name: "创建新模拟会话" }),
      ).toHaveAttribute("href", "/paper/new");
      expect(
        screen.getByText("Paper runtime interrupted by backend shutdown."),
      ).not.toBeVisible();
    } finally {
      await act(async () => i18n.changeLanguage("en-US"));
    }
  });

  it("rejects unknown stream events and rehydrates instead of advancing state", async () => {
    installWebSocket();
    vi.useFakeTimers();
    const fetch = vi
      .spyOn(globalThis, "fetch")
      .mockImplementation(async () => jsonResponse(paperSnapshot("RUNNING")));
    render(<PaperSessionDetailPage sessionId={PAPER_ID} />);
    await act(async () => MockWebSocket.instances[0]!.open());
    act(() =>
      MockWebSocket.instances[0]!.message({
        sequence: 1,
        type: "internal.python.object",
        occurred_at: "2026-09-06T02:01:00Z",
        payload: { secret: "must-not-render" },
      }),
    );
    expect(screen.getByRole("alert")).toHaveTextContent("malformed");
    expect(screen.queryByText("Paper portfolio")).not.toBeInTheDocument();
    expect(screen.queryByText("must-not-render")).not.toBeInTheDocument();
    await act(async () => vi.advanceTimersByTimeAsync(1000));
    await act(async () => MockWebSocket.instances[1]!.open());
    expect(fetch).toHaveBeenCalledTimes(2);
    expect(screen.getByText("Paper portfolio")).toBeInTheDocument();
  });

  it("aborts hydration and closes the socket when navigating away", async () => {
    installWebSocket();
    const fetch = vi
      .spyOn(globalThis, "fetch")
      .mockReturnValue(new Promise(() => {}));
    const view = render(<PaperSessionDetailPage sessionId={PAPER_ID} />);
    await act(async () => MockWebSocket.instances[0]!.open());
    const signal = fetch.mock.calls[0]?.[1]?.signal;
    expect(signal?.aborted).toBe(false);
    view.unmount();
    expect(signal?.aborted).toBe(true);
    expect(MockWebSocket.instances[0]!.readyState).toBe(MockWebSocket.CLOSED);
  });

  it("isolates route identity while an old hydration is in flight", async () => {
    installWebSocket();
    let resolveOld!: (response: Response) => void;
    const oldResponse = new Promise<Response>((resolve) => {
      resolveOld = resolve;
    });
    vi.spyOn(globalThis, "fetch")
      .mockReturnValueOnce(oldResponse)
      .mockResolvedValueOnce(
        jsonResponse({
          ...paperSnapshot("STOPPED"),
          session: {
            ...paperSession("STOPPED"),
            session_id: "a0975744-c58a-49d8-a72d-45f6ed700ca6",
          },
        }),
      );
    const view = render(<PaperSessionDetailPage sessionId={PAPER_ID} />);
    await act(async () => MockWebSocket.instances[0]!.open());
    view.rerender(
      <PaperSessionDetailPage sessionId="a0975744-c58a-49d8-a72d-45f6ed700ca6" />,
    );
    await act(async () => MockWebSocket.instances[1]!.open());
    expect(
      await screen.findByText("Stopped", { selector: ".statusBadge" }),
    ).toBeInTheDocument();
    resolveOld(jsonResponse(paperSnapshot("RUNNING")));
    await Promise.resolve();
    expect(screen.queryByText("Running")).not.toBeInTheDocument();
  });
});
