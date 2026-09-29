import {
  act,
  fireEvent,
  render,
  screen,
  waitFor,
  within,
} from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { ApiError } from "../api/client";
import { i18n } from "../i18n";
import { experimentApi } from "../product/experiments/api";
import { job, plan } from "../product/experiments/fixtures.test-data";
import { jsonResponse } from "../test/fixtures";
import { PAPER_ID, paperSession, paperSnapshot } from "../test/paperFixtures";
import { CreatePaperSessionPage } from "./CreatePaperSessionPage";
import {
  PAPER_CREATE_PENDING_PREFIX,
  preparePaperCreate,
} from "./paperCreateRecovery";
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
  let lockTail = Promise.resolve();
  const pendingKeys = () =>
    Array.from({ length: window.localStorage.length }, (_, index) =>
      window.localStorage.key(index),
    ).filter((key): key is string =>
      Boolean(key?.startsWith(PAPER_CREATE_PENDING_PREFIX)),
    );
  const clearPending = () =>
    pendingKeys().forEach((key) => window.localStorage.removeItem(key));
  beforeEach(() => {
    clearPending();
    lockTail = Promise.resolve();
    Object.defineProperty(window.navigator, "locks", {
      configurable: true,
      value: {
        request: (_name: string, work: () => Promise<unknown>) => {
          const result = lockTail.then(work);
          lockTail = result.then(
            () => undefined,
            () => undefined,
          );
          return result;
        },
      },
    });
  });
  afterEach(() => {
    clearPending();
    Reflect.deleteProperty(window.navigator, "locks");
  });

  it.each(["en-US", "zh-CN"])(
    "uses provider-specific empty states before any market data arrives (%s)",
    async (language) => {
      await act(async () => i18n.changeLanguage(language));
      try {
        for (const provider of [
          "replay",
          "simulated_a_share",
          "historical_a_share",
        ] as const) {
          installWebSocket();
          const snapshot = paperSnapshot();
          snapshot.session.provider_type = provider;
          vi.spyOn(globalThis, "fetch").mockResolvedValue(
            jsonResponse(snapshot),
          );
          const view = render(<PaperSessionDetailPage sessionId={PAPER_ID} />);
          await act(async () => MockWebSocket.instances[0]!.open());
          const aShare = provider !== "replay";
          expect(
            screen.getByText(
              i18n.t(aShare ? "detail.latestSession" : "detail.latestBar", {
                ns: "paper",
              }),
            ),
          ).toBeInTheDocument();
          expect(
            screen.getByRole("heading", {
              name: i18n.t(
                aShare ? "detail.marketSession" : "detail.marketData",
                { ns: "paper" },
              ),
            }),
          ).toBeInTheDocument();
          const emptyText =
            language === "zh-CN"
              ? "尚未收到完整的 A 股交易日数据。"
              : "No completed A-share trading days received yet.";
          const portfolioText =
            language === "zh-CN"
              ? "完成首个 A 股交易日回放后显示组合。"
              : "The portfolio appears after the first completed A-share trading day.";
          expect(
            screen.getByText(
              aShare ? emptyText : i18n.t("detail.noBars", { ns: "paper" }),
            ),
          ).toBeInTheDocument();
          expect(
            screen.getByText(
              aShare
                ? portfolioText
                : i18n.t("detail.noPortfolio", { ns: "paper" }),
            ),
          ).toBeInTheDocument();
          view.unmount();
          vi.restoreAllMocks();
        }
      } finally {
        await act(async () => i18n.changeLanguage("en-US"));
      }
    },
  );

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

  it("shows a stopped account from REST when the opening socket is blocked", async () => {
    installWebSocket();
    vi.useFakeTimers();
    const snapshot = paperSnapshot("STOPPED");
    snapshot.latest_portfolio = {
      timestamp: "2024-01-09T00:00:00Z",
      cash: "81309.8134",
      market_value: "18655",
      equity: "99964.8134",
      realized_pnl: "0",
      unrealized_pnl: "-5",
      cumulative_commission: "30.1866",
      drawdown: "0",
      positions: [],
      plan: null,
    };
    snapshot.fills = [
      {
        order_id: "11111111-1111-4111-8111-111111111111",
        strategy_id: "moving_average_crossover",
        symbol: "AAPL",
        side: "BUY",
        quantity: "10",
        price: "25",
        commission: "2.36",
        timestamp: "2024-01-09T00:00:00Z",
      },
    ];
    const fetch = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValue(jsonResponse(snapshot));
    render(<PaperSessionDetailPage sessionId={PAPER_ID} />);
    await act(async () => MockWebSocket.instances[0]!.close());
    expect(screen.getByTitle("81309.8134")).toBeInTheDocument();
    expect(screen.getByTitle("2.36")).toBeInTheDocument();
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
    expect(fetch).toHaveBeenCalledTimes(1);
    await act(async () => vi.advanceTimersByTimeAsync(8000));
    expect(MockWebSocket.instances).toHaveLength(1);
  });

  it("does not present an active account as live when only REST is reachable", async () => {
    installWebSocket();
    vi.useFakeTimers();
    const snapshot = paperSnapshot("RUNNING");
    snapshot.latest_portfolio = {
      timestamp: "2024-01-09T00:00:00Z",
      cash: "81309.8134",
      market_value: "18655",
      equity: "99964.8134",
      realized_pnl: "0",
      unrealized_pnl: "-5",
      cumulative_commission: "30.1866",
      drawdown: "0",
      positions: [],
      plan: null,
    };
    vi.spyOn(globalThis, "fetch").mockResolvedValue(jsonResponse(snapshot));
    render(<PaperSessionDetailPage sessionId={PAPER_ID} />);
    await act(async () => MockWebSocket.instances[0]!.close());
    expect(screen.queryByTitle("81309.8134")).not.toBeInTheDocument();
    await act(async () => vi.advanceTimersByTimeAsync(1000));
    expect(MockWebSocket.instances).toHaveLength(2);
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
      account_snapshot_trading_date: "2011-03-22",
      next_accepted_session: "2011-03-23",
      account_mode: "HISTORICAL_PAPER_REPLAY",
      submitted_to_account: true,
      paper_session_id: PAPER_ID,
      plan_version: "PAPER_ACCOUNT_PLAN_V3",
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
    const planDates = screen.getAllByText("2011-03-22");
    expect(planDates).toHaveLength(2);
    for (const date of planDates) expect(date).toBeVisible();
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
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

  it.each(["en-US", "zh-CN"])(
    "labels a prior-day portfolio as last verified after an empty accepted session (%s)",
    async (language) => {
      await act(async () => i18n.changeLanguage(language));
      try {
        installWebSocket();
        const snapshot = paperSnapshot("STOPPED");
        snapshot.session.provider_type = "historical_a_share";
        snapshot.latest_session = {
          trading_date: "2011-03-23",
          security_count: 0,
          source: "FROZEN_HISTORICAL_A_SHARE_REPLAY_V1",
        };
        snapshot.latest_portfolio = {
          timestamp: "2011-03-22T07:00:00Z",
          cash: "100000",
          market_value: "0",
          equity: "100000",
          realized_pnl: "0",
          unrealized_pnl: "0",
          cumulative_commission: "0",
          drawdown: "0",
          positions: [],
          plan: null,
        };
        vi.spyOn(globalThis, "fetch").mockResolvedValue(jsonResponse(snapshot));
        render(<PaperSessionDetailPage sessionId={PAPER_ID} />);
        await act(async () => MockWebSocket.instances[0]!.open());

        expect(
          screen.getByText(
            i18n.t("detail.lastVerifiedPortfolioKicker", { ns: "paper" }),
          ),
        ).toBeVisible();
        expect(
          screen.queryByText(i18n.t("detail.portfolioKicker", { ns: "paper" })),
        ).not.toBeInTheDocument();
        expect(screen.getByText("2011-03-23")).toBeVisible();
        expect(screen.getByRole("alert")).toHaveTextContent("2011-03-22");
        expect(screen.getByRole("alert")).toHaveTextContent("2011-03-23");
        expect(screen.getByRole("alert")).toHaveTextContent(
          language === "zh-CN"
            ? "下方组合、现金及持仓"
            : "portfolio, cash, and positions",
        );
      } finally {
        await act(async () => i18n.changeLanguage("en-US"));
      }
    },
  );

  it("keeps a same-day portfolio authoritative until the next empty session event", async () => {
    installWebSocket();
    const snapshot = paperSnapshot("RUNNING");
    snapshot.session.provider_type = "historical_a_share";
    snapshot.latest_session = {
      trading_date: "2011-03-22",
      security_count: 1,
      source: "FROZEN_HISTORICAL_A_SHARE_REPLAY_V1",
    };
    snapshot.latest_portfolio = {
      timestamp: "2011-03-21T18:00:00Z",
      cash: "100000",
      market_value: "0",
      equity: "100000",
      realized_pnl: "0",
      unrealized_pnl: "0",
      cumulative_commission: "0",
      drawdown: "0",
      positions: [],
      plan: null,
    };
    vi.spyOn(globalThis, "fetch").mockResolvedValue(jsonResponse(snapshot));
    render(<PaperSessionDetailPage sessionId={PAPER_ID} />);
    await act(async () => MockWebSocket.instances[0]!.open());
    expect(screen.getByText("AUTHORITATIVE PORTFOLIO")).toBeVisible();
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();

    act(() =>
      MockWebSocket.instances[0]!.message({
        sequence: 1,
        type: "market.session",
        occurred_at: "2011-03-22T07:00:00Z",
        payload: {
          trading_date: "2011-03-23",
          security_count: 0,
          source: "FROZEN_HISTORICAL_A_SHARE_REPLAY_V1",
        },
      }),
    );
    expect(screen.getByText("LAST VERIFIED PORTFOLIO")).toBeVisible();
    expect(screen.getByRole("alert")).toHaveTextContent("2011-03-22");
    expect(screen.getByRole("alert")).toHaveTextContent("2011-03-23");
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

  it("keeps the create action focused through a failed request and prevents a pending duplicate", async () => {
    let rejectCreate: ((reason: Error) => void) | undefined;
    const fetch = vi
      .spyOn(globalThis, "fetch")
      .mockImplementationOnce(
        () =>
          new Promise<Response>((_, reject) => {
            rejectCreate = reject;
          }),
      )
      .mockRejectedValue(new TypeError("offline"));
    render(<CreatePaperSessionPage />);
    const create = screen.getByRole("button", {
      name: "Create paper session",
    });
    await userEvent.click(create);
    expect(fetch).toHaveBeenCalledTimes(1);
    const firstHeaders = fetch.mock.calls[0]?.[1]?.headers;
    expect(create).toHaveFocus();
    expect(create).not.toBeDisabled();
    expect(create).toHaveAttribute("aria-disabled", "true");
    await userEvent.click(create);
    expect(fetch).toHaveBeenCalledTimes(1);
    await act(async () => rejectCreate?.(new TypeError("offline")));
    expect(await screen.findByRole("alert")).toBeVisible();
    expect(screen.getByRole("alert")).toHaveTextContent(
      "Check the paper-session list and service status",
    );
    expect(
      screen.getByRole("button", { name: "Retry saved request 1" }),
    ).toBeVisible();
    expect(create).toHaveFocus();
    expect(create).toHaveAttribute("aria-disabled", "false");
    try {
      await act(async () => i18n.changeLanguage("zh-CN"));
      expect(screen.getByRole("alert")).toHaveTextContent(
        "先查看会话列表和服务状态",
      );
    } finally {
      await act(async () => i18n.changeLanguage("en-US"));
    }
    await userEvent.click(create);
    await waitFor(() => expect(fetch).toHaveBeenCalledTimes(2));
    expect(fetch.mock.calls[1]?.[1]?.headers).toEqual(firstHeaders);
  });

  it("retries the exact saved request after a lost response and page remount", async () => {
    window.history.replaceState({}, "", "/paper/new");
    const fetch = vi
      .spyOn(globalThis, "fetch")
      .mockRejectedValueOnce(new TypeError("response lost"))
      .mockResolvedValueOnce(jsonResponse(paperSession(), 201));
    const first = render(<CreatePaperSessionPage />);
    fireEvent.change(screen.getByLabelText("Initial cash"), {
      target: { value: "123456.75" },
    });
    await userEvent.click(
      screen.getByRole("button", { name: "Create paper session" }),
    );
    expect(await screen.findByRole("alert")).toBeVisible();
    first.unmount();

    render(<CreatePaperSessionPage />);
    expect(screen.getByLabelText("Initial cash")).toHaveValue("100000000");
    await userEvent.click(
      screen.getByRole("button", { name: "Create paper session" }),
    );
    expect(fetch).toHaveBeenCalledTimes(1);
    expect(screen.getByRole("alert")).toHaveTextContent(
      "A saved creation already exists",
    );
    await userEvent.click(
      screen.getByRole("button", { name: "Retry saved request 1" }),
    );
    await waitFor(() =>
      expect(window.location.pathname).toBe(`/paper/${PAPER_ID}`),
    );
    expect(fetch).toHaveBeenCalledTimes(2);
    expect(fetch.mock.calls[1]?.[1]?.body).toBe(fetch.mock.calls[0]?.[1]?.body);
    expect(
      new Headers(fetch.mock.calls[1]?.[1]?.headers).get("Idempotency-Key"),
    ).toBe(
      new Headers(fetch.mock.calls[0]?.[1]?.headers).get("Idempotency-Key"),
    );
    expect(pendingKeys()).toHaveLength(1);
    expect(
      screen.getByRole("button", {
        name: "Verify and open saved paper account",
      }),
    ).toBeVisible();
  });

  it("blocks a changed request until the uncertain one is reconciled", async () => {
    const fetch = vi
      .spyOn(globalThis, "fetch")
      .mockRejectedValue(new TypeError("response lost"));
    render(<CreatePaperSessionPage />);
    const create = screen.getByRole("button", {
      name: "Create paper session",
    });
    await userEvent.click(create);
    await screen.findByRole("alert");
    fireEvent.change(screen.getByLabelText("Initial cash"), {
      target: { value: "123456.75" },
    });
    await userEvent.click(create);
    expect(fetch).toHaveBeenCalledTimes(1);
    expect(screen.getByRole("alert")).toHaveTextContent(
      "A saved creation already exists",
    );
    fireEvent.change(screen.getByLabelText("Initial cash"), {
      target: { value: "100000000" },
    });
    await userEvent.click(create);
    await waitFor(() => expect(fetch).toHaveBeenCalledTimes(2));
    const keys = fetch.mock.calls.map(([, init]) =>
      new Headers(init?.headers).get("Idempotency-Key"),
    );
    expect(keys[0]).toBeTruthy();
    expect(keys[1]).toBe(keys[0]);
    expect(fetch.mock.calls[1]?.[1]?.body).toBe(fetch.mock.calls[0]?.[1]?.body);
  });

  it("requires an explicit new-account action after a confirmed creation", async () => {
    const fetch = vi
      .spyOn(globalThis, "fetch")
      .mockImplementation(() =>
        Promise.resolve(jsonResponse(paperSession(), 201)),
      );
    const first = render(<CreatePaperSessionPage />);
    await userEvent.click(
      screen.getByRole("button", { name: "Create paper session" }),
    );
    await waitFor(() =>
      expect(
        JSON.parse(window.localStorage.getItem(pendingKeys()[0]) ?? "{}"),
      ).toMatchObject({ confirmedSessionId: PAPER_ID }),
    );
    first.unmount();
    window.history.replaceState({}, "", "/paper/new");
    render(<CreatePaperSessionPage />);
    expect(
      screen.getByRole("button", {
        name: "Verify and open saved paper account",
      }),
    ).toBeVisible();
    await userEvent.click(
      screen.getByRole("button", { name: "Create paper session" }),
    );
    expect(fetch).toHaveBeenCalledTimes(1);
    await userEvent.click(
      screen.getByRole("button", { name: "Create another paper account" }),
    );
    await waitFor(() => expect(fetch).toHaveBeenCalledTimes(3));
    expect(fetch.mock.calls[1]?.[0]).toContain("/sessions/receipt");
    expect(fetch.mock.calls[2]?.[1]?.body).toBe(fetch.mock.calls[0]?.[1]?.body);
    expect(
      new Headers(fetch.mock.calls[2]?.[1]?.headers).get("Idempotency-Key"),
    ).not.toBe(
      new Headers(fetch.mock.calls[0]?.[1]?.headers).get("Idempotency-Key"),
    );
  });

  it("verifies a saved confirmed account before opening it", async () => {
    window.history.replaceState({}, "", "/paper/new");
    const fetch = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValueOnce(jsonResponse(paperSession(), 201))
      .mockResolvedValueOnce(jsonResponse(paperSession()));
    const first = render(<CreatePaperSessionPage />);
    await userEvent.click(
      screen.getByRole("button", { name: "Create paper session" }),
    );
    await waitFor(() =>
      expect(
        JSON.parse(window.localStorage.getItem(pendingKeys()[0]) ?? "{}"),
      ).toMatchObject({ confirmedSessionId: PAPER_ID }),
    );
    first.unmount();
    window.history.replaceState({}, "", "/paper/new");
    render(<CreatePaperSessionPage />);
    await userEvent.click(
      screen.getByRole("button", {
        name: "Verify and open saved paper account",
      }),
    );
    await waitFor(() =>
      expect(window.location.pathname).toBe(`/paper/${PAPER_ID}`),
    );
    expect(fetch).toHaveBeenCalledTimes(2);
    expect(fetch.mock.calls[1]?.[0]).toContain("/sessions/receipt");
    expect(fetch.mock.calls[1]?.[1]?.method).toBeUndefined();
  });

  it.each(["missing", "mismatch", "offline"] as const)(
    "does not open a locally confirmed account when the current server is %s",
    async (failure) => {
      window.history.replaceState({}, "", "/paper/new");
      const fetch = vi
        .spyOn(globalThis, "fetch")
        .mockResolvedValueOnce(jsonResponse(paperSession(), 201));
      const first = render(<CreatePaperSessionPage />);
      await userEvent.click(
        screen.getByRole("button", { name: "Create paper session" }),
      );
      await waitFor(() =>
        expect(
          JSON.parse(window.localStorage.getItem(pendingKeys()[0]) ?? "{}"),
        ).toMatchObject({ confirmedSessionId: PAPER_ID }),
      );
      first.unmount();
      window.history.replaceState({}, "", "/paper/new");
      if (failure === "missing")
        fetch.mockImplementation(() =>
          Promise.resolve(jsonResponse({ detail: "not found" }, 404)),
        );
      else if (failure === "mismatch")
        fetch.mockImplementation(() =>
          Promise.resolve(
            jsonResponse({
              ...paperSession(),
              session_id: "00000000-0000-0000-0000-000000000002",
            }),
          ),
        );
      else fetch.mockRejectedValue(new TypeError("offline"));

      const key = pendingKeys()[0];
      render(<CreatePaperSessionPage />);
      await userEvent.click(
        screen.getByRole("button", {
          name: "Verify and open saved paper account",
        }),
      );
      expect(await screen.findByRole("alert")).toHaveTextContent(
        "could not be verified against the current server",
      );
      expect(window.location.pathname).toBe("/paper/new");
      expect(fetch).toHaveBeenCalledTimes(2);
      expect(fetch.mock.calls[1]?.[0]).toContain("/sessions/receipt");
      expect(
        new Headers(fetch.mock.calls[1]?.[1]?.headers).get("Idempotency-Key"),
      ).toBe(key?.slice(PAPER_CREATE_PENDING_PREFIX.length));
      expect(
        JSON.parse(window.localStorage.getItem(key) ?? "{}"),
      ).toMatchObject({
        confirmedSessionId: PAPER_ID,
      });
      await userEvent.click(
        screen.getByRole("button", { name: "Create another paper account" }),
      );
      await waitFor(() => expect(fetch).toHaveBeenCalledTimes(3));
      expect(
        screen
          .getAllByRole("alert")
          .some((item) => item.textContent?.includes("could not be verified")),
      ).toBe(true);
      expect(fetch.mock.calls[2]?.[0]).toContain("/sessions/receipt");
      expect(fetch.mock.calls[2]?.[1]?.method).toBeUndefined();
      expect(pendingKeys()).toEqual([key]);
    },
  );

  it("verifies a receipt that was confirmed while a saved retry waited for the lock", async () => {
    window.history.replaceState({}, "", "/paper/new");
    let resolveFirst: ((response: Response) => void) | undefined;
    const fetch = vi
      .spyOn(globalThis, "fetch")
      .mockImplementationOnce(
        () =>
          new Promise<Response>((resolve) => {
            resolveFirst = resolve;
          }),
      )
      .mockResolvedValueOnce(jsonResponse({ detail: "not found" }, 404));
    const first = render(<CreatePaperSessionPage />);
    await userEvent.click(
      screen.getByRole("button", { name: "Create paper session" }),
    );
    await waitFor(() => expect(fetch).toHaveBeenCalledTimes(1));
    const key = pendingKeys()[0];
    render(<CreatePaperSessionPage />);
    await userEvent.click(
      screen.getByRole("button", { name: "Retry saved request 1" }),
    );
    first.unmount();
    await act(async () => resolveFirst?.(jsonResponse(paperSession(), 201)));
    await waitFor(() => expect(fetch).toHaveBeenCalledTimes(2));
    expect(fetch.mock.calls[1]?.[0]).toContain("/sessions/receipt");
    expect(fetch.mock.calls[1]?.[1]?.method).toBeUndefined();
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "could not be verified against the current server",
    );
    expect(window.location.pathname).toBe("/paper/new");
    expect(pendingKeys()).toEqual([key]);
    expect(JSON.parse(window.localStorage.getItem(key) ?? "{}")).toMatchObject({
      confirmedSessionId: PAPER_ID,
    });
  });

  it("serializes two same-origin creation forms before choosing a second key", async () => {
    window.history.replaceState({}, "", "/paper/new");
    let resolveFirst: ((response: Response) => void) | undefined;
    const fetch = vi
      .spyOn(globalThis, "fetch")
      .mockImplementationOnce(
        () =>
          new Promise<Response>((resolve) => {
            resolveFirst = resolve;
          }),
      )
      .mockResolvedValue(jsonResponse(paperSession(), 201));
    render(<CreatePaperSessionPage />);
    render(<CreatePaperSessionPage />);
    const creates = screen.getAllByRole("button", {
      name: "Create paper session",
    });
    await userEvent.click(creates[0]);
    await waitFor(() => expect(fetch).toHaveBeenCalledTimes(1));
    await userEvent.click(creates[1]);
    expect(fetch).toHaveBeenCalledTimes(1);
    await act(async () => resolveFirst?.(jsonResponse(paperSession(), 201)));
    await waitFor(() =>
      expect(
        screen.getAllByRole("button", {
          name: "Verify and open saved paper account",
        }),
      ).toHaveLength(2),
    );
    expect(fetch).toHaveBeenCalledTimes(1);
    expect(pendingKeys()).toHaveLength(1);
    expect(
      JSON.parse(window.localStorage.getItem(pendingKeys()[0]) ?? "{}"),
    ).toMatchObject({ confirmedSessionId: PAPER_ID });
  });

  it("reuses one key when a second form waits for a lost response", async () => {
    window.history.replaceState({}, "", "/paper/new");
    let rejectFirst: ((reason: Error) => void) | undefined;
    const fetch = vi
      .spyOn(globalThis, "fetch")
      .mockImplementationOnce(
        () =>
          new Promise<Response>((_, reject) => {
            rejectFirst = reject;
          }),
      )
      .mockResolvedValue(jsonResponse(paperSession(), 201));
    render(<CreatePaperSessionPage />);
    render(<CreatePaperSessionPage />);
    const creates = screen.getAllByRole("button", {
      name: "Create paper session",
    });
    await userEvent.click(creates[0]);
    await waitFor(() => expect(fetch).toHaveBeenCalledTimes(1));
    await userEvent.click(creates[1]);
    await act(async () => rejectFirst?.(new TypeError("response lost")));
    await waitFor(() => expect(fetch).toHaveBeenCalledTimes(2));
    expect(
      new Headers(fetch.mock.calls[1]?.[1]?.headers).get("Idempotency-Key"),
    ).toBe(
      new Headers(fetch.mock.calls[0]?.[1]?.headers).get("Idempotency-Key"),
    );
    expect(pendingKeys()).toHaveLength(1);
    await waitFor(() =>
      expect(
        JSON.parse(window.localStorage.getItem(pendingKeys()[0]) ?? "{}"),
      ).toMatchObject({ confirmedSessionId: PAPER_ID }),
    );
  });

  it("does not send a queued create after its page has been cancelled", async () => {
    window.history.replaceState({}, "", "/paper/new");
    let resolveFirst: ((response: Response) => void) | undefined;
    const fetch = vi.spyOn(globalThis, "fetch").mockImplementation(
      () =>
        new Promise<Response>((resolve) => {
          resolveFirst = resolve;
        }),
    );
    render(<CreatePaperSessionPage />);
    render(<CreatePaperSessionPage />);
    const creates = screen.getAllByRole("button", {
      name: "Create paper session",
    });
    await userEvent.click(creates[0]);
    await waitFor(() => expect(fetch).toHaveBeenCalledTimes(1));
    await userEvent.click(creates[1]);
    await userEvent.click(screen.getAllByRole("link", { name: "Cancel" })[1]);
    expect(window.location.pathname).toBe("/paper");
    await act(async () => resolveFirst?.(jsonResponse(paperSession(), 201)));
    expect(fetch).toHaveBeenCalledTimes(1);
    expect(pendingKeys()).toHaveLength(1);
  });

  it("retains the original key if confirmed-receipt storage fails after 201", async () => {
    window.history.replaceState({}, "", "/paper/new");
    const setItem = Storage.prototype.setItem;
    vi.spyOn(Storage.prototype, "setItem").mockImplementation(function (
      this: Storage,
      key: string,
      value: string,
    ) {
      if (
        key.startsWith(PAPER_CREATE_PENDING_PREFIX) &&
        value.includes('"confirmedSessionId"')
      )
        throw new Error("quota exceeded");
      return setItem.call(this, key, value);
    });
    const fetch = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValue(jsonResponse(paperSession(), 201));
    const first = render(<CreatePaperSessionPage />);
    await userEvent.click(
      screen.getByRole("button", { name: "Create paper session" }),
    );
    await waitFor(() => expect(fetch).toHaveBeenCalledTimes(1));
    expect(pendingKeys()).toHaveLength(1);
    expect(
      JSON.parse(window.localStorage.getItem(pendingKeys()[0]) ?? "{}")
        .confirmedSessionId,
    ).toBeUndefined();
    first.unmount();
    window.history.replaceState({}, "", "/paper/new");
    render(<CreatePaperSessionPage />);
    await userEvent.click(
      screen.getByRole("button", { name: "Create paper session" }),
    );
    await waitFor(() => expect(fetch).toHaveBeenCalledTimes(2));
    expect(
      new Headers(fetch.mock.calls[1]?.[1]?.headers).get("Idempotency-Key"),
    ).toBe(
      new Headers(fetch.mock.calls[0]?.[1]?.headers).get("Idempotency-Key"),
    );
  });

  it("does not POST if the uncertain-create key cannot be saved", async () => {
    const fetch = vi.spyOn(globalThis, "fetch");
    const setItem = Storage.prototype.setItem;
    vi.spyOn(Storage.prototype, "setItem").mockImplementation(function (
      this: Storage,
      key: string,
      value: string,
    ) {
      if (key.startsWith(PAPER_CREATE_PENDING_PREFIX))
        throw new Error("quota exceeded");
      return setItem.call(this, key, value);
    });
    render(<CreatePaperSessionPage />);
    await userEvent.click(
      screen.getByRole("button", { name: "Create paper session" }),
    );
    expect(fetch).not.toHaveBeenCalled();
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Could not save this creation request",
    );
  });

  it("does not POST when browser cross-tab locking is unavailable", async () => {
    Reflect.deleteProperty(window.navigator, "locks");
    const fetch = vi.spyOn(globalThis, "fetch");
    render(<CreatePaperSessionPage />);
    await userEvent.click(
      screen.getByRole("button", { name: "Create paper session" }),
    );
    expect(fetch).not.toHaveBeenCalled();
    expect(pendingKeys()).toHaveLength(0);
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Could not save this creation request",
    );
  });

  it("does not POST or poison storage when a request exceeds the recovery bound", async () => {
    const fetch = vi.spyOn(globalThis, "fetch");
    render(<CreatePaperSessionPage />);
    fireEvent.change(screen.getByLabelText("Initial cash"), {
      target: { value: "1".repeat(8300) },
    });
    await userEvent.click(
      screen.getByRole("button", { name: "Create paper session" }),
    );
    expect(fetch).not.toHaveBeenCalled();
    expect(pendingKeys()).toHaveLength(0);
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Could not save this creation request",
    );
  });

  it("clears a definitely rejected request so its settings can be corrected", async () => {
    const fetch = vi
      .spyOn(globalThis, "fetch")
      .mockRejectedValueOnce(new ApiError(422, "invalid"))
      .mockResolvedValueOnce(jsonResponse(paperSession(), 201));
    render(<CreatePaperSessionPage />);
    await userEvent.click(
      screen.getByRole("button", { name: "Create paper session" }),
    );
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Please check the submitted paper session values",
    );
    expect(pendingKeys()).toHaveLength(0);
    fireEvent.change(screen.getByLabelText("Initial cash"), {
      target: { value: "123456.75" },
    });
    await userEvent.click(
      screen.getByRole("button", { name: "Create paper session" }),
    );
    await waitFor(() => expect(fetch).toHaveBeenCalledTimes(2));
    expect(fetch.mock.calls[1]?.[1]?.body).not.toBe(
      fetch.mock.calls[0]?.[1]?.body,
    );
  });

  it("keeps an uncertain key when a later ordinary retry is rejected", async () => {
    const fetch = vi
      .spyOn(globalThis, "fetch")
      .mockRejectedValueOnce(new TypeError("response lost"))
      .mockRejectedValueOnce(new ApiError(422, "schema changed"))
      .mockResolvedValueOnce(jsonResponse({}, 404));
    render(<CreatePaperSessionPage />);
    const create = screen.getByRole("button", { name: "Create paper session" });
    await userEvent.click(create);
    await screen.findByRole("alert");
    const key = pendingKeys()[0];
    await userEvent.click(create);
    await waitFor(() => expect(fetch).toHaveBeenCalledTimes(3));
    expect(pendingKeys()).toEqual([key]);
    expect(fetch.mock.calls[2]?.[0]).toContain("/sessions/receipt");
    fireEvent.change(screen.getByLabelText("Initial cash"), {
      target: { value: "123456.75" },
    });
    await userEvent.click(create);
    expect(fetch).toHaveBeenCalledTimes(3);
  });

  it("recovers a committed receipt after a later ordinary retry gets 422", async () => {
    const fetch = vi
      .spyOn(globalThis, "fetch")
      .mockRejectedValueOnce(new TypeError("response lost"))
      .mockRejectedValueOnce(new ApiError(422, "schema changed"))
      .mockResolvedValueOnce(jsonResponse(paperSession()));
    render(<CreatePaperSessionPage />);
    const create = screen.getByRole("button", { name: "Create paper session" });
    await userEvent.click(create);
    await screen.findByRole("alert");
    const key = pendingKeys()[0];
    await userEvent.click(create);
    await waitFor(() =>
      expect(window.location.pathname).toBe(`/paper/${PAPER_ID}`),
    );
    expect(fetch).toHaveBeenCalledTimes(3);
    expect(fetch.mock.calls[2]?.[0]).toContain("/sessions/receipt");
    expect(
      new Headers(fetch.mock.calls[2]?.[1]?.headers).get("Idempotency-Key"),
    ).toBe(key?.slice(PAPER_CREATE_PENDING_PREFIX.length));
    expect(JSON.parse(window.localStorage.getItem(key) ?? "{}")).toMatchObject({
      confirmedSessionId: PAPER_ID,
    });
  });

  it("keeps an uncertain key when a saved-request retry is rejected", async () => {
    const fetch = vi
      .spyOn(globalThis, "fetch")
      .mockRejectedValueOnce(new TypeError("response lost"))
      .mockRejectedValueOnce(new ApiError(422, "schema changed"))
      .mockResolvedValueOnce(jsonResponse({}, 404));
    const first = render(<CreatePaperSessionPage />);
    await userEvent.click(
      screen.getByRole("button", { name: "Create paper session" }),
    );
    await screen.findByRole("alert");
    const key = pendingKeys()[0];
    first.unmount();
    render(<CreatePaperSessionPage />);
    await userEvent.click(
      screen.getByRole("button", { name: "Retry saved request 1" }),
    );
    await waitFor(() => expect(fetch).toHaveBeenCalledTimes(3));
    expect(pendingKeys()).toEqual([key]);
    expect(
      new Headers(fetch.mock.calls[1]?.[1]?.headers).get("Idempotency-Key"),
    ).toBe(
      new Headers(fetch.mock.calls[0]?.[1]?.headers).get("Idempotency-Key"),
    );
  });

  it.each([400, 404, 422])(
    "recovers a committed receipt after a saved retry gets %s",
    async (status) => {
      const fetch = vi
        .spyOn(globalThis, "fetch")
        .mockRejectedValueOnce(new TypeError("response lost"))
        .mockRejectedValueOnce(new ApiError(status, "request rejected"))
        .mockResolvedValueOnce(jsonResponse(paperSession()));
      const first = render(<CreatePaperSessionPage />);
      await userEvent.click(
        screen.getByRole("button", { name: "Create paper session" }),
      );
      await screen.findByRole("alert");
      const key = pendingKeys()[0];
      first.unmount();
      window.history.replaceState({}, "", "/paper/new");
      render(<CreatePaperSessionPage />);
      await userEvent.click(
        screen.getByRole("button", { name: "Retry saved request 1" }),
      );
      await waitFor(() =>
        expect(window.location.pathname).toBe(`/paper/${PAPER_ID}`),
      );
      expect(fetch).toHaveBeenCalledTimes(3);
      expect(fetch.mock.calls[2]?.[0]).toContain("/sessions/receipt");
      expect(
        JSON.parse(window.localStorage.getItem(key) ?? "{}"),
      ).toMatchObject({
        confirmedSessionId: PAPER_ID,
      });
    },
  );

  it("blocks new creation when saved-request storage is corrupt", async () => {
    window.localStorage.setItem(
      `${PAPER_CREATE_PENDING_PREFIX}00000000-0000-0000-0000-000000000001`,
      "{invalid",
    );
    const fetch = vi.spyOn(globalThis, "fetch");
    render(<CreatePaperSessionPage />);
    expect(screen.getByRole("alert")).toHaveTextContent(
      "Saved creation requests cannot be read safely",
    );
    await userEvent.click(
      screen.getByRole("button", { name: "Create paper session" }),
    );
    expect(fetch).not.toHaveBeenCalled();
    expect(screen.getAllByRole("alert")).toHaveLength(2);
  });

  it("can retry a saved exact request when its source study no longer loads", async () => {
    window.history.replaceState(
      {},
      "",
      `/paper/new?from_experiment=${job.job_id}`,
    );
    preparePaperCreate({
      provider_type: "historical_a_share",
      dataset_id: "cn-a-research-20100101-20251231-v1",
      symbol: "CN-A",
      strategy: {
        type: "cn_a_cross_sectional_momentum_low_vol_v1",
        parameters: {
          start_date: "2011-03-01",
          end_date: "2011-03-23",
          rebalance_sessions: 20,
          maximum_holdings: 20,
          max_position_weight: "0.1",
          universe: "ALL",
          commission_rate: "0.0003",
          minimum_commission: "5",
        },
      },
      initial_cash: "123456.75",
      default_order_quantity: "1",
      risk: {
        enforce_buying_power: true,
        max_leverage: "1",
        max_drawdown: "-0.2",
      },
    });
    vi.spyOn(experimentApi, "get").mockRejectedValue(new Error("offline"));
    const fetch = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValue(
        jsonResponse(
          { ...paperSession(), provider_type: "historical_a_share" },
          201,
        ),
      );
    render(<CreatePaperSessionPage />);
    expect(await screen.findByRole("alert")).toBeVisible();
    expect(
      screen.queryByRole("button", { name: "Create paper session" }),
    ).toBeNull();
    await userEvent.click(
      screen.getByRole("button", { name: "Retry saved request 1" }),
    );
    await waitFor(() => expect(fetch).toHaveBeenCalledTimes(1));
    expect(JSON.parse(String(fetch.mock.calls[0]?.[1]?.body))).toMatchObject({
      provider_type: "historical_a_share",
      initial_cash: "123456.75",
    });
  });

  it("does not reopen a created session after leaving while the request is pending", async () => {
    window.history.replaceState({}, "", "/paper/new");
    let resolveCreate: ((response: Response) => void) | undefined;
    const fetch = vi.spyOn(globalThis, "fetch").mockImplementation(
      () =>
        new Promise<Response>((resolve) => {
          resolveCreate = resolve;
        }),
    );
    const view = render(<CreatePaperSessionPage />);
    await userEvent.click(
      screen.getByRole("button", { name: "Create paper session" }),
    );
    expect(fetch).toHaveBeenCalledTimes(1);
    await userEvent.click(screen.getByRole("link", { name: "Cancel" }));
    expect(window.location.pathname).toBe("/paper");
    view.unmount();
    await act(async () => resolveCreate?.(jsonResponse(paperSession(), 201)));
    expect(window.location.pathname).toBe("/paper");
    expect(pendingKeys()).toHaveLength(1);
    window.history.replaceState({}, "", "/paper/new");
    render(<CreatePaperSessionPage />);
    expect(
      screen.getByRole("button", {
        name: "Verify and open saved paper account",
      }),
    ).toBeVisible();
    expect(fetch).toHaveBeenCalledTimes(1);
  });

  it.each([401, 403])(
    "treats HTTP %s as denied access, not uncertain creation, in both locales",
    async (status) => {
      const fetch = vi
        .spyOn(globalThis, "fetch")
        .mockRejectedValue(new ApiError(status, "diagnostic"));
      render(<CreatePaperSessionPage />);
      await userEvent.click(
        screen.getByRole("button", { name: "Create paper session" }),
      );
      expect(await screen.findByRole("alert")).toHaveTextContent(
        i18n.t("common:loadErrors.permission"),
      );
      expect(screen.getByRole("alert")).not.toHaveTextContent(
        "Check the paper-session list",
      );
      try {
        await act(async () => i18n.changeLanguage("zh-CN"));
        expect(screen.getByRole("alert")).toHaveTextContent(
          i18n.t("common:loadErrors.permission"),
        );
        expect(fetch).toHaveBeenCalledTimes(1);
      } finally {
        await act(async () => i18n.changeLanguage("en-US"));
      }
    },
  );

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

  it("rejects historical cash above the engine limit without rounding or submitting", async () => {
    const fetch = vi.spyOn(globalThis, "fetch");
    render(<CreatePaperSessionPage />);
    await userEvent.selectOptions(
      screen.getByLabelText("Provider"),
      "historical_a_share",
    );
    await userEvent.clear(screen.getByLabelText("Initial cash"));
    await userEvent.type(
      screen.getByLabelText("Initial cash"),
      "1000000000000.000000000000001",
    );
    await userEvent.click(
      screen.getByRole("button", { name: "Create paper session" }),
    );
    expect(screen.getByRole("alert")).toHaveTextContent(
      "Historical simulated-account cash",
    );
    expect(fetch).not.toHaveBeenCalled();
    try {
      await act(async () => i18n.changeLanguage("zh-CN"));
      expect(screen.getByRole("alert")).toHaveTextContent(
        "历史模拟账户初始资金须大于 0",
      );
      expect(screen.getByLabelText("初始资金")).toHaveValue(
        "1000000000000.000000000000001",
      );
      await userEvent.click(
        screen.getByRole("button", { name: "创建模拟交易会话" }),
      );
      expect(screen.getByRole("alert")).toHaveTextContent("1,000,000,000,000");
      expect(fetch).not.toHaveBeenCalled();
    } finally {
      await act(async () => i18n.changeLanguage("en-US"));
    }
  });

  it("rejects historical excess cash with surrounding whitespace before submitting", async () => {
    const fetch = vi.spyOn(globalThis, "fetch");
    render(<CreatePaperSessionPage />);
    await userEvent.selectOptions(
      screen.getByLabelText("Provider"),
      "historical_a_share",
    );
    await userEvent.clear(screen.getByLabelText("Initial cash"));
    await userEvent.type(
      screen.getByLabelText("Initial cash"),
      " 1000000000000.000000000000001 ",
    );
    await userEvent.click(
      screen.getByRole("button", { name: "Create paper session" }),
    );
    expect(screen.getByRole("alert")).toHaveTextContent(
      "Historical simulated-account cash",
    );
    expect(fetch).not.toHaveBeenCalled();
  });

  it("reveals and focuses an invalid advanced historical setting in both languages", async () => {
    const fetch = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValue(jsonResponse(paperSession(), 201));
    render(<CreatePaperSessionPage />);
    await userEvent.selectOptions(
      screen.getByLabelText("Provider"),
      "historical_a_share",
    );
    const summary = screen.getByText("Strategy, universe and cost settings");
    await userEvent.click(summary);
    const details = summary.closest("details");
    const weight = screen.getByLabelText("Maximum weight per holding");
    await userEvent.clear(weight);
    await userEvent.type(weight, "1.2");
    await userEvent.click(summary);
    expect(details).not.toHaveAttribute("open");
    const focusStates: Array<{
      invalid: string | null;
      describedBy: string | null;
      expanded: boolean;
    }> = [];
    weight.addEventListener("focus", () => {
      focusStates.push({
        invalid: weight.getAttribute("aria-invalid"),
        describedBy: weight.getAttribute("aria-describedby"),
        expanded: Boolean(details?.open),
      });
    });
    screen.getByRole("button", { name: "Create paper session" }).focus();
    await userEvent.keyboard("{Enter}");
    expect(fetch).not.toHaveBeenCalled();
    expect(details).toHaveAttribute("open");
    expect(weight).toHaveFocus();
    expect(weight).toHaveAttribute("aria-invalid", "true");
    const errorId = weight.getAttribute("aria-describedby");
    expect(errorId).toBeTruthy();
    expect(focusStates).toEqual([
      { invalid: "true", describedBy: errorId, expanded: true },
    ]);
    expect(document.getElementById(errorId!)).toHaveTextContent(
      "strategy, cost and risk limits",
    );
    await userEvent.click(
      screen.getByRole("button", { name: "Create paper session" }),
    );
    expect(fetch).not.toHaveBeenCalled();
    expect(weight).toHaveFocus();
    expect(focusStates).toHaveLength(2);
    try {
      await act(async () => i18n.changeLanguage("zh-CN"));
      expect(screen.getByLabelText("单只证券最大权重")).toBe(weight);
      expect(document.getElementById(errorId!)).toHaveTextContent(
        "策略、成本和风控限制",
      );
      await userEvent.clear(weight);
      await userEvent.type(weight, "0.1");
      expect(weight).not.toHaveAttribute("aria-invalid");
      await userEvent.click(
        screen.getByRole("button", { name: "创建模拟交易会话" }),
      );
      await waitFor(() => expect(fetch).toHaveBeenCalledTimes(1));
    } finally {
      await act(async () => i18n.changeLanguage("en-US"));
    }
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
      .mockResolvedValueOnce(jsonResponse(paperSession("PAUSING")))
      .mockResolvedValueOnce(
        jsonResponse({ ...paperSnapshot("PAUSING"), last_sequence: 1 }),
      );
    const view = render(<PaperSessionDetailPage sessionId={PAPER_ID} />);
    await act(async () => MockWebSocket.instances[0]!.open());
    await userEvent.click(screen.getByRole("button", { name: "Pause replay" }));
    expect(fetch.mock.calls[1]?.[0]).toContain(`/${PAPER_ID}/pause`);
    expect(fetch.mock.calls[2]?.[0]).toContain(`/${PAPER_ID}/snapshot`);
    expect(
      screen.getByText("Pausing", { selector: ".statusBadge" }),
    ).toBeVisible();
    expect(screen.queryByRole("button", { name: "Pause replay" })).toBeNull();

    view.unmount();
    installWebSocket();
    fetch.mockResolvedValueOnce(jsonResponse(paperSnapshot("PAUSED")));
    render(<PaperSessionDetailPage sessionId={PAPER_ID} />);
    await act(async () => MockWebSocket.instances[0]!.open());
    expect(screen.getByRole("button", { name: "Resume replay" })).toBeVisible();
    expect(screen.getByRole("button", { name: "Stop replay" })).toBeVisible();
  });

  it("reconciles an accepted command while the paper stream is reconnecting", async () => {
    installWebSocket();
    const fetch = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValueOnce(jsonResponse(paperSnapshot("RUNNING")))
      .mockResolvedValueOnce(jsonResponse(paperSession("PAUSING")))
      .mockResolvedValueOnce(
        jsonResponse({ ...paperSnapshot("PAUSING"), last_sequence: 1 }),
      );
    render(<PaperSessionDetailPage sessionId={PAPER_ID} />);
    await act(async () => MockWebSocket.instances[0]!.open());
    act(() => MockWebSocket.instances[0]!.close());
    expect(screen.getByText("Session connection: reconnecting")).toBeVisible();

    await userEvent.click(screen.getByRole("button", { name: "Pause replay" }));
    expect(fetch.mock.calls[2]?.[0]).toContain(`/${PAPER_ID}/snapshot`);
    expect(
      screen.getByText("Pausing", { selector: ".statusBadge" }),
    ).toBeVisible();
    expect(screen.queryByRole("button", { name: "Pause replay" })).toBeNull();
    expect(screen.getByRole("button", { name: "Stop replay" })).toBeVisible();
    expect(screen.getByText("Session connection: reconnecting")).toBeVisible();
  });

  it("keeps an accepted transition when a disconnect aborts its snapshot read", async () => {
    installWebSocket();
    const fetch = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValueOnce(jsonResponse(paperSnapshot("RUNNING")))
      .mockResolvedValueOnce(jsonResponse(paperSession("PAUSING")))
      .mockImplementationOnce(
        (_input, init) =>
          new Promise<Response>((_resolve, reject) => {
            init?.signal?.addEventListener("abort", () =>
              reject(new DOMException("aborted", "AbortError")),
            );
          }),
      );
    render(<PaperSessionDetailPage sessionId={PAPER_ID} />);
    await act(async () => MockWebSocket.instances[0]!.open());
    await userEvent.click(screen.getByRole("button", { name: "Pause replay" }));
    await waitFor(() => expect(fetch).toHaveBeenCalledTimes(3));

    act(() => MockWebSocket.instances[0]!.close());
    await waitFor(() =>
      expect(fetch.mock.calls[2]?.[1]?.signal?.aborted).toBe(true),
    );
    expect(
      screen.getByText("Pausing", { selector: ".statusBadge" }),
    ).toBeVisible();
    expect(screen.queryByRole("button", { name: "Pause replay" })).toBeNull();
    expect(screen.getByText("Session connection: reconnecting")).toBeVisible();
  });

  it("keeps a newer stream status over an older command response", async () => {
    installWebSocket();
    let finishPost!: (response: Response) => void;
    const fetch = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValueOnce(jsonResponse(paperSnapshot("RUNNING")))
      .mockImplementationOnce(
        () => new Promise((resolve) => (finishPost = resolve)),
      )
      .mockResolvedValueOnce(
        jsonResponse({ ...paperSnapshot("PAUSED"), last_sequence: 1 }),
      )
      .mockReturnValueOnce(new Promise(() => {}));
    render(<PaperSessionDetailPage sessionId={PAPER_ID} />);
    await act(async () => MockWebSocket.instances[0]!.open());
    await userEvent.click(screen.getByRole("button", { name: "Pause replay" }));
    await act(async () =>
      MockWebSocket.instances[0]!.message({
        sequence: 1,
        type: "session.status",
        occurred_at: "2026-09-06T02:01:00Z",
        payload: { status: "PAUSED" },
      }),
    );
    expect(
      screen.getByText("Paused", { selector: ".statusBadge" }),
    ).toBeVisible();

    await act(async () => finishPost(jsonResponse(paperSession("PAUSING"))));
    expect(fetch).toHaveBeenCalledTimes(4);
    expect(
      screen.getByText("Paused", { selector: ".statusBadge" }),
    ).toBeVisible();
    expect(
      screen.queryByText("Pausing", { selector: ".statusBadge" }),
    ).toBeNull();
  });

  it("does not apply a command response from another paper account", async () => {
    installWebSocket();
    const fetch = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValueOnce(jsonResponse(paperSnapshot("RUNNING")))
      .mockResolvedValueOnce(
        jsonResponse({
          ...paperSession("PAUSING"),
          session_id: "534d9730-a8c9-4f71-a0fc-c4b5d156f2ef",
        }),
      )
      .mockResolvedValue(
        jsonResponse({ ...paperSnapshot("PAUSED"), last_sequence: 1 }),
      );
    render(<PaperSessionDetailPage sessionId={PAPER_ID} />);
    await act(async () => MockWebSocket.instances[0]!.open());
    await userEvent.click(screen.getByRole("button", { name: "Pause replay" }));
    expect(fetch).toHaveBeenCalledTimes(2);
    expect(screen.getByRole("alert")).toHaveTextContent(
      "The server returned a different paper account",
    );
    expect(screen.queryByRole("button", { name: "Pause replay" })).toBeNull();
    await act(async () =>
      MockWebSocket.instances[0]!.message({
        sequence: 1,
        type: "session.status",
        occurred_at: "2026-09-06T02:01:00Z",
        payload: { status: "PAUSED" },
      }),
    );
    expect(fetch).toHaveBeenCalledTimes(3);
    expect(screen.getByRole("alert")).toHaveTextContent(
      "The server returned a different paper account",
    );
    await act(async () => i18n.changeLanguage("zh-CN"));
    expect(screen.getByRole("alert")).toHaveTextContent(
      "服务器对该指令返回了另一个模拟账户",
    );
    await act(async () => i18n.changeLanguage("en-US"));
  });

  it("does not call an accepted command failed when its follow-up read fails", async () => {
    installWebSocket();
    vi.useFakeTimers();
    vi.spyOn(globalThis, "fetch")
      .mockResolvedValueOnce(jsonResponse(paperSnapshot("RUNNING")))
      .mockResolvedValueOnce(jsonResponse(paperSession("PAUSING")))
      .mockResolvedValueOnce(jsonResponse({ detail: "unavailable" }, 503))
      .mockResolvedValueOnce(jsonResponse(paperSnapshot("FAILED")));
    render(<PaperSessionDetailPage sessionId={PAPER_ID} />);
    await act(async () => MockWebSocket.instances[0]!.open());
    act(() => MockWebSocket.instances[0]!.close());

    await act(async () =>
      fireEvent.click(screen.getByRole("button", { name: "Pause replay" })),
    );
    expect(screen.getByRole("alert")).toHaveTextContent("unavailable");
    await act(async () => vi.advanceTimersByTimeAsync(1000));
    await act(async () => MockWebSocket.instances[1]!.open());
    expect(
      screen.getByText("Failed", { selector: ".statusBadge" }),
    ).toBeVisible();
    expect(screen.queryByText(/Unable to pause the paper session/)).toBeNull();
  });

  it("keeps the focused paper command during an in-flight failure without duplicate POSTs", async () => {
    installWebSocket();
    let finish!: (response: Response) => void;
    const fetch = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValueOnce(jsonResponse(paperSnapshot("CREATED")))
      .mockImplementationOnce(
        () => new Promise((resolve) => (finish = resolve)),
      );
    render(<PaperSessionDetailPage sessionId={PAPER_ID} />);
    await act(async () => MockWebSocket.instances[0]!.open());
    const start = screen.getByRole("button", { name: "Start replay" });
    start.focus();
    await userEvent.keyboard("{Enter}{Enter}");
    expect(fetch).toHaveBeenCalledTimes(2);
    expect(start).toHaveFocus();
    expect(start).toHaveAttribute("aria-disabled", "true");
    await userEvent.click(start);
    expect(fetch).toHaveBeenCalledTimes(2);
    await act(async () => finish(jsonResponse({ detail: "unavailable" }, 503)));
    expect(start).toHaveFocus();
    expect(screen.getByRole("alert")).toHaveTextContent(
      "Unable to start the paper session",
    );
  });

  it.each([
    [
      "start",
      "CREATED",
      "STARTING",
      "Start replay",
      "Starting",
      ["RUNNING", "STOPPED"],
    ],
    [
      "pause",
      "RUNNING",
      "PAUSING",
      "Pause replay",
      "Pausing",
      ["PAUSED", "STARTING", "RUNNING"],
    ],
    ["stop", "PAUSED", "STOPPING", "Stop replay", "Stopping", ["STOPPED"]],
  ] as const)(
    "clears an uncertain %s failure only after the authoritative state changes",
    async (action, before, after, button, statusLabel, laterStatuses) => {
      for (const statusFirst of [false, true]) {
        installWebSocket();
        let finishPost!: (response: Response) => void;
        const fetch = vi
          .spyOn(globalThis, "fetch")
          .mockResolvedValueOnce(jsonResponse(paperSnapshot(before)))
          .mockImplementationOnce(
            () => new Promise((resolve) => (finishPost = resolve)),
          )
          .mockResolvedValueOnce(
            jsonResponse({ ...paperSnapshot(after), last_sequence: 1 }),
          );
        for (const [index, nextStatus] of laterStatuses.entries())
          fetch.mockResolvedValueOnce(
            jsonResponse({
              ...paperSnapshot(nextStatus),
              last_sequence: index + 2,
            }),
          );
        const view = render(<PaperSessionDetailPage sessionId={PAPER_ID} />);
        await act(async () => MockWebSocket.instances[0]!.open());
        await userEvent.click(screen.getByRole("button", { name: button }));
        expect(fetch.mock.calls[1]?.[0]).toContain(`/${PAPER_ID}/${action}`);

        const confirmStatus = async (
          nextStatus: NonNullable<Parameters<typeof paperSnapshot>[0]>,
          sequence: number,
        ) => {
          await act(async () =>
            MockWebSocket.instances[0]!.message({
              sequence,
              type: "session.status",
              occurred_at: "2026-09-06T02:01:00Z",
              payload: { status: nextStatus },
            }),
          );
          expect(
            screen.getByText(
              sequence === 1
                ? statusLabel
                : i18n.t(`statuses.${nextStatus}`, { ns: "common" }),
              { selector: ".statusBadge" },
            ),
          ).toBeInTheDocument();
        };

        if (statusFirst) await confirmStatus(after, 1);
        await act(async () =>
          finishPost(jsonResponse({ detail: "unavailable" }, 503)),
        );
        if (!statusFirst) {
          expect(screen.getByRole("alert")).toHaveTextContent(
            `Unable to ${action} the paper session`,
          );
          expect(
            screen.getByText(
              before === "CREATED"
                ? "Created"
                : before === "RUNNING"
                  ? "Running"
                  : "Paused",
              {
                selector: ".statusBadge",
              },
            ),
          ).toBeInTheDocument();
          await confirmStatus(after, 1);
        }
        expect(screen.queryByRole("alert")).not.toBeInTheDocument();
        for (const [index, nextStatus] of laterStatuses.entries()) {
          await confirmStatus(nextStatus, index + 2);
          expect(screen.queryByRole("alert")).not.toBeInTheDocument();
        }
        expect(fetch).toHaveBeenCalledTimes(3 + laterStatuses.length);
        if (action === "pause") {
          fetch.mockResolvedValueOnce(
            jsonResponse({ detail: "unavailable" }, 503),
          );
          await userEvent.click(screen.getByRole("button", { name: button }));
          expect(screen.getByRole("alert")).toHaveTextContent(
            "Unable to pause the paper session",
          );
          expect(fetch).toHaveBeenCalledTimes(4 + laterStatuses.length);
        }
        view.unmount();
        vi.restoreAllMocks();
      }
    },
  );

  it.each([
    ["start", "CREATED", "Start replay", ["STARTING", "RUNNING", "STOPPED"]],
    [
      "pause",
      "RUNNING",
      "Pause replay",
      ["PAUSING", "PAUSED", "STARTING", "RUNNING"],
    ],
  ] as const)(
    "does not revive a confirmed %s failure when the POST fails after later statuses",
    async (action, before, button, statuses) => {
      installWebSocket();
      let finishPost!: (response: Response) => void;
      const fetch = vi
        .spyOn(globalThis, "fetch")
        .mockResolvedValueOnce(jsonResponse(paperSnapshot(before)))
        .mockImplementationOnce(
          () => new Promise((resolve) => (finishPost = resolve)),
        );
      for (const [index, status] of statuses.entries())
        fetch.mockResolvedValueOnce(
          jsonResponse({ ...paperSnapshot(status), last_sequence: index + 1 }),
        );
      render(<PaperSessionDetailPage sessionId={PAPER_ID} />);
      await act(async () => MockWebSocket.instances[0]!.open());
      await userEvent.click(screen.getByRole("button", { name: button }));
      expect(fetch.mock.calls[1]?.[0]).toContain(`/${PAPER_ID}/${action}`);
      for (const [index, status] of statuses.entries()) {
        await act(async () =>
          MockWebSocket.instances[0]!.message({
            sequence: index + 1,
            type: "session.status",
            occurred_at: "2026-09-06T02:01:00Z",
            payload: { status },
          }),
        );
      }
      expect(screen.queryByRole("alert")).not.toBeInTheDocument();
      await act(async () =>
        finishPost(jsonResponse({ detail: "unavailable" }, 503)),
      );
      expect(
        screen.getByText(
          i18n.t(`statuses.${statuses.at(-1)}`, { ns: "common" }),
          { selector: ".statusBadge" },
        ),
      ).toBeInTheDocument();
      expect(screen.queryByRole("alert")).not.toBeInTheDocument();
      expect(fetch).toHaveBeenCalledTimes(2 + statuses.length);
    },
  );

  it("moves focus to the durable status only when a focused paper action disappears", async () => {
    installWebSocket();
    vi.spyOn(globalThis, "fetch")
      .mockResolvedValueOnce(jsonResponse(paperSnapshot("CREATED")))
      .mockResolvedValueOnce(jsonResponse(paperSession("STARTING")))
      .mockResolvedValue(
        jsonResponse({ ...paperSnapshot("STARTING"), last_sequence: 1 }),
      );
    render(<PaperSessionDetailPage sessionId={PAPER_ID} />);
    await act(async () => MockWebSocket.instances[0]!.open());
    const start = screen.getByRole("button", { name: "Start replay" });
    start.focus();
    await userEvent.keyboard("{Enter}");
    act(() =>
      MockWebSocket.instances[0]!.message({
        sequence: 1,
        type: "session.status",
        occurred_at: "2026-09-06T02:01:00Z",
        payload: { status: "STARTING" },
      }),
    );
    expect(screen.queryByRole("button", { name: "Start replay" })).toBeNull();
    expect(
      screen.getByText("Starting", { selector: ".statusBadge" }).parentElement,
    ).toHaveFocus();
  });

  it("does not steal focus after the user leaves a paper command before a status change", async () => {
    installWebSocket();
    vi.spyOn(globalThis, "fetch").mockResolvedValueOnce(
      jsonResponse(paperSnapshot("CREATED")),
    );
    render(<PaperSessionDetailPage sessionId={PAPER_ID} />);
    await act(async () => MockWebSocket.instances[0]!.open());
    screen.getByRole("button", { name: "Start replay" }).focus();
    const back = screen.getByRole("link", { name: "← All paper sessions" });
    back.focus();
    act(() =>
      MockWebSocket.instances[0]!.message({
        sequence: 1,
        type: "session.status",
        occurred_at: "2026-09-06T02:01:00Z",
        payload: { status: "STARTING" },
      }),
    );
    expect(back).toHaveFocus();
  });

  it.each([
    [
      "CREATED",
      "Start replay",
      "start",
      "Unable to start the paper session. Check the current session status and connection before retrying.",
      "无法开始模拟交易会话。重试前请先检查当前会话状态和连接。",
    ],
    [
      "RUNNING",
      "Pause replay",
      "pause",
      "Unable to pause the paper session. Check the current session status and connection before retrying.",
      "无法暂停模拟交易会话。重试前请先检查当前会话状态和连接。",
    ],
    [
      "PAUSED",
      "Stop replay",
      "stop",
      "Unable to stop the paper session. Check the current session status and connection before retrying.",
      "无法停止模拟交易会话。重试前请先检查当前会话状态和连接。",
    ],
  ] as const)(
    "translates a failed %s account command without resubmitting",
    async (status, button, action, english, chinese) => {
      installWebSocket();
      const fetch = vi
        .spyOn(globalThis, "fetch")
        .mockResolvedValueOnce(jsonResponse(paperSnapshot(status)))
        .mockResolvedValueOnce(jsonResponse({ detail: "unavailable" }, 503));
      render(<PaperSessionDetailPage sessionId={PAPER_ID} />);
      await act(async () => MockWebSocket.instances[0]!.open());
      await userEvent.click(
        await screen.findByRole("button", { name: button }),
      );
      expect(screen.getByRole("alert")).toHaveTextContent(english);
      expect(screen.getByText(english)).toBeVisible();
      expect(screen.getByRole("alert")).toHaveTextContent(
        "Check the current session status and connection before retrying.",
      );
      expect(fetch.mock.calls[1]?.[0]).toContain(`/${PAPER_ID}/${action}`);
      try {
        await act(async () => i18n.changeLanguage("zh-CN"));
        expect(screen.getByRole("alert")).toHaveTextContent(chinese);
        expect(screen.getByText(chinese)).toBeVisible();
        expect(screen.getByRole("alert")).toHaveTextContent(
          "重试前请先检查当前会话状态和连接。",
        );
        expect(fetch).toHaveBeenCalledTimes(2);
      } finally {
        await act(async () => i18n.changeLanguage("en-US"));
      }
    },
  );

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
      for (const [title, rowCount] of [
        ["持仓", 1],
        ["信号", 1],
        ["风控决策", 2],
        ["模拟订单", 1],
        ["模拟成交", 1],
      ] as const) {
        expect(
          screen.getByRole("region", {
            name: `${title} — ${i18n.t("research:scrollTable")}`,
          }),
        ).toHaveAttribute("tabindex", "0");
        const table = screen.getByRole("table", { name: title });
        expect(table).toBeVisible();
        expect(within(table).getAllByRole("rowheader")).toHaveLength(rowCount);
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
      for (const [title, rowCount] of [
        ["Positions", 1],
        ["Signals", 1],
        ["Risk decisions", 2],
        ["Paper orders", 1],
        ["Paper fills", 1],
      ] as const) {
        expect(
          screen.getByRole("region", {
            name: `${title} — ${i18n.t("research:scrollTable")}`,
          }),
        ).toHaveAttribute("tabindex", "0");
        const table = screen.getByRole("table", { name: title });
        expect(table).toBeVisible();
        expect(within(table).getAllByRole("rowheader")).toHaveLength(rowCount);
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

  it("focuses an impossible RSI oversold threshold before submitting", async () => {
    const fetch = vi.spyOn(globalThis, "fetch");
    render(<CreatePaperSessionPage />);
    await userEvent.selectOptions(screen.getByLabelText("Provider"), "replay");
    await userEvent.selectOptions(
      screen.getByLabelText("Strategy type"),
      "rsi_mean_reversion",
    );
    const oversold = screen.getByLabelText("Oversold");
    await userEvent.clear(oversold);
    await userEvent.type(oversold, "100");
    await userEvent.click(
      screen.getByRole("button", { name: "Create paper session" }),
    );
    expect(fetch).not.toHaveBeenCalled();
    expect(oversold).toHaveFocus();
    expect(oversold).toHaveAttribute("aria-invalid", "true");
    expect(screen.getByLabelText("Overbought")).not.toHaveAttribute(
      "aria-invalid",
    );
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
    await act(async () =>
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

  it("recovers a terminal notification after a transient final snapshot failure", async () => {
    installWebSocket();
    vi.useFakeTimers();
    const fetch = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValueOnce(jsonResponse(paperSnapshot("RUNNING")))
      .mockResolvedValueOnce(jsonResponse({ detail: "temporary" }, 503))
      .mockResolvedValueOnce(jsonResponse(paperSnapshot("STOPPED")));
    render(<PaperSessionDetailPage sessionId={PAPER_ID} />);
    await act(async () => MockWebSocket.instances[0]!.open());
    await act(async () =>
      MockWebSocket.instances[0]!.message({
        sequence: 1,
        type: "session.status",
        occurred_at: "2026-09-06T02:01:00Z",
        payload: { status: "STOPPED" },
      }),
    );
    expect(screen.getByRole("alert")).toHaveTextContent("temporary");
    await act(async () => vi.advanceTimersByTimeAsync(1000));
    expect(MockWebSocket.instances).toHaveLength(2);
    await act(async () => MockWebSocket.instances[1]!.open());
    expect(fetch).toHaveBeenCalledTimes(3);
    expect(
      screen.getByText("Stopped", { selector: ".statusBadge" }),
    ).toBeInTheDocument();
    expect(screen.getByText("Session connection: closed")).toBeInTheDocument();
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
  });

  it("rehydrates terminal state when the server closes before the final snapshot", async () => {
    installWebSocket();
    vi.useFakeTimers();
    const fetch = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValueOnce(jsonResponse(paperSnapshot("RUNNING")))
      .mockReturnValueOnce(new Promise(() => {}))
      .mockResolvedValueOnce(jsonResponse(paperSnapshot("STOPPED")));
    render(<PaperSessionDetailPage sessionId={PAPER_ID} />);
    await act(async () => MockWebSocket.instances[0]!.open());
    act(() => {
      MockWebSocket.instances[0]!.message({
        sequence: 1,
        type: "session.status",
        occurred_at: "2026-09-06T02:01:00Z",
        payload: { status: "STOPPED" },
      });
      MockWebSocket.instances[0]!.close();
    });
    expect(fetch.mock.calls[1]?.[1]?.signal?.aborted).toBe(true);
    await act(async () => vi.advanceTimersByTimeAsync(1000));
    expect(MockWebSocket.instances).toHaveLength(2);
    await act(async () => MockWebSocket.instances[1]!.open());
    expect(fetch).toHaveBeenCalledTimes(3);
    expect(
      screen.getByText("Stopped", { selector: ".statusBadge" }),
    ).toBeInTheDocument();
    expect(screen.getByText("Session connection: closed")).toBeInTheDocument();
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
