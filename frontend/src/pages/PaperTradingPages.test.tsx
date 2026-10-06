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
import { paperApi } from "../api/paper";
import { i18n } from "../i18n";
import { experimentApi } from "../product/experiments/api";
import { job, plan } from "../product/experiments/fixtures.test-data";
import { jsonResponse } from "../test/fixtures";
import {
  PAPER_ID,
  paperCollection,
  paperSession,
  paperSnapshot,
  paperState,
} from "../test/paperFixtures";
import type { PaperCollection, PaperSnapshot } from "../types/paper";
import { CreatePaperSessionPage } from "./CreatePaperSessionPage";
import {
  PAPER_CREATE_PENDING_PREFIX,
  confirmPaperCreate,
  preparePaperCreate,
} from "./paperCreateRecovery";
import { PaperSessionDetailPage } from "./PaperSessionDetailPage";
import { PaperSessionsPage } from "./PaperSessionsPage";

const paperRequests: Array<{ url: string; options?: RequestInit }> = [];

function mockPaperServer(
  collectionResponse?: (
    url: URL,
    snapshot: PaperSnapshot,
    options?: RequestInit,
  ) => Promise<Response>,
) {
  // Existing scripted calls are state/command/log responses. Collection requests
  // use that finite server fixture without consuming a command's response queue.
  const responses = vi.fn<typeof fetch>();
  const windows = new Map<string, PaperSnapshot>();
  vi.stubGlobal(
    "fetch",
    async (input: RequestInfo | URL, options?: RequestInit) => {
      const url = new URL(String(input), "http://test.local");
      paperRequests.push({ url: String(input), options });
      if (url.pathname.endsWith("/snapshot"))
        throw new Error(
          "Paper detail must not request the legacy full snapshot.",
        );
      const match = url.pathname.match(
        /\/sessions\/([^/]+)\/collections\/([^/]+)$/,
      );
      if (match) {
        const watermark = Number(url.searchParams.get("as_of_sequence"));
        const offset = Number(url.searchParams.get("offset") ?? 0);
        const snapshot = windows.get(`${match[1]}:${watermark}`);
        if (!snapshot)
          throw new Error("Collection requested without its state watermark.");
        expect(url.searchParams.get("limit")).toBe("100");
        expect(options?.method).toBeUndefined();
        if (collectionResponse)
          return collectionResponse(url, snapshot, options);
        return jsonResponse(
          paperCollection(
            snapshot,
            match[2] as PaperCollection,
            watermark,
            offset,
          ),
        );
      }
      const response = await responses(input, options);
      if (!url.pathname.endsWith("/state") || !response.ok) return response;
      const snapshot = (await response.json()) as PaperSnapshot;
      windows.set(
        `${snapshot.session.session_id}:${snapshot.last_sequence}`,
        snapshot,
      );
      return jsonResponse(paperState(snapshot), response.status);
    },
  );
  return responses;
}

function financialTableFixture() {
  const snapshot = paperSnapshot("RUNNING");
  const records = Array.from({ length: 201 }, (_, index) => ({
    id: `00000000-0000-0000-0000-${String(index + 1).padStart(12, "0")}`,
    symbol: `TEST-${index + 1}`,
    quantity: `${index + 1}.000000000000000001`,
  }));
  snapshot.signals = records.map((record) => ({
    strategy_id: "moving_average_crossover",
    symbol: record.symbol,
    signal_type: "BUY",
    timestamp: "2026-09-06T02:01:00Z",
  }));
  snapshot.risk_decisions = records.map((record) => ({
    proposal_id: record.id,
    approved: true,
    reason_code: "APPROVED",
    message: "proposal approved",
    timestamp: "2026-09-06T02:01:00Z",
  }));
  snapshot.orders = records.map((record) => ({
    order_id: record.id,
    strategy_id: "moving_average_crossover",
    symbol: record.symbol,
    side: "BUY",
    order_type: "MARKET",
    quantity: record.quantity,
    price: null,
    status: "FILLED",
    created_at: "2026-09-06T02:01:00Z",
  }));
  snapshot.fills = records.map((record) => ({
    order_id: record.id,
    strategy_id: "moving_average_crossover",
    symbol: record.symbol,
    side: "BUY",
    quantity: record.quantity,
    price: "12.000000000000000001",
    commission: "0.000000000000000001",
    timestamp: "2026-09-06T02:02:00Z",
  }));
  snapshot.latest_portfolio = {
    timestamp: "2026-09-06T02:02:00Z",
    cash: "100000",
    market_value: "0",
    equity: "100000",
    realized_pnl: "0",
    unrealized_pnl: "0",
    cumulative_commission: "0",
    drawdown: "0",
    plan: null,
    positions: records.map((record) => ({
      symbol: record.symbol,
      quantity: record.quantity,
      average_price: "12",
      market_price: "12",
      unrealized_pnl: "0",
      realized_pnl: "0",
    })),
  };
  snapshot.last_sequence = 1000;
  return { snapshot, records };
}

function tableCells(title: string) {
  return within(screen.getByRole("table", { name: title }))
    .getAllByRole("row")
    .slice(1)
    .map((row) =>
      Array.from(row.querySelectorAll("th,td"), (cell) =>
        cell.getAttribute("title")!,
      ),
    );
}

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
    paperRequests.length = 0;
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
    "shows distinct saved order transitions in a bounded read-only event log (%s)",
    async (language) => {
      await act(async () => i18n.changeLanguage(language));
      installWebSocket();
      const order = {
        order_id: "966db07d-e61f-4ca8-aad0-e5774a63fc09",
        strategy_id: "moving_average_crossover",
        symbol: "AAPL",
        side: "BUY",
        order_type: "MARKET",
        quantity: "10",
        price: null,
        created_at: "2026-09-06T02:01:00Z",
      };
      const fetch = mockPaperServer().mockImplementation(async (input) =>
        jsonResponse(
          String(input).includes("/events?")
            ? [
                {
                  sequence: 11,
                  type: "order.updated",
                  occurred_at: "2026-09-06T02:03:00Z",
                  payload: {
                    ...order,
                    order_id: "d35b2e06-6946-48e5-8f5f-f3bf22fa91d1",
                    status: "CANCELLED",
                    cancellation_reason_code: "INSUFFICIENT_BUYING_POWER",
                  },
                },
                {
                  sequence: 10,
                  type: "order.updated",
                  occurred_at: "2026-09-06T02:02:00Z",
                  payload: { ...order, status: "FILLED" },
                },
                {
                  sequence: 9,
                  type: "order.updated",
                  occurred_at: "2026-09-06T02:01:00Z",
                  payload: { ...order, status: "ACCEPTED" },
                },
              ]
            : paperSnapshot("STOPPED"),
        ),
      );
      try {
        render(<PaperSessionDetailPage sessionId={PAPER_ID} />);
        await act(async () => MockWebSocket.instances[0]!.open());
        const heading = i18n.t("detail.eventLog", { ns: "paper" });
        expect(
          await screen.findByRole("heading", { name: heading }),
        ).toBeInTheDocument();
        expect(
          fetch.mock.calls.some(([url]) => String(url).includes("/events?")),
        ).toBe(false);
        await userEvent.click(
          screen.getByRole("button", {
            name: i18n.t("detail.viewEventLog", { ns: "paper" }),
          }),
        );
        const table = await screen.findByRole("table", { name: heading });
        expect(
          fetch.mock.calls.some(([url]) =>
            String(url).includes(`/sessions/${PAPER_ID}/events?limit=51`),
          ),
        ).toBe(true);
        expect(within(table).getAllByRole("row")).toHaveLength(4);
        expect(
          within(table).getByText(
            language === "zh-CN"
              ? /实际成交价及费用超出可用资金/
              : /Actual fill price and fees exceed available cash/,
          ),
        ).toBeInTheDocument();
        expect(
          within(table).getByRole("rowheader", { name: "10" }),
        ).toBeInTheDocument();
        expect(
          within(table).getByRole("rowheader", { name: "9" }),
        ).toBeInTheDocument();
        expect(
          within(table).getByText(language === "zh-CN" ? /已成交/ : /Filled/),
        ).toBeInTheDocument();
        expect(
          within(table).getByText(language === "zh-CN" ? /已接受/ : /Accepted/),
        ).toBeInTheDocument();
        expect(
          fetch.mock.calls.every(([, options]) => options?.method !== "POST"),
        ).toBe(true);
      } finally {
        vi.restoreAllMocks();
        await act(async () => i18n.changeLanguage("en-US"));
      }
    },
  );

  it("discards an old account's delayed event page after route change", async () => {
    installWebSocket();
    const otherId = "a0975744-c58a-49d8-a72d-45f6ed700ca6";
    let resolveOld!: (response: Response) => void;
    const oldPage = new Promise<Response>((resolve) => {
      resolveOld = resolve;
    });
    mockPaperServer().mockImplementation(async (input) => {
      const url = String(input);
      if (url.includes(`/sessions/${PAPER_ID}/events?`)) return oldPage;
      if (url.includes(`/sessions/${otherId}/events?`))
        return jsonResponse([
          {
            sequence: 2,
            type: "session.status",
            occurred_at: "2026-09-06T02:02:00Z",
            payload: { status: "STOPPED" },
          },
        ]);
      const snapshot = paperSnapshot("STOPPED");
      snapshot.session.session_id = url.includes(otherId) ? otherId : PAPER_ID;
      return jsonResponse(snapshot);
    });
    const view = render(<PaperSessionDetailPage sessionId={PAPER_ID} />);
    await act(async () => MockWebSocket.instances[0]!.open());
    await userEvent.click(
      await screen.findByRole("button", { name: "View saved events" }),
    );
    view.rerender(<PaperSessionDetailPage sessionId={otherId} />);
    await act(async () => MockWebSocket.instances[1]!.open());
    expect(
      await screen.findByRole("rowheader", { name: "2" }),
    ).toBeInTheDocument();
    resolveOld(
      jsonResponse([
        {
          sequence: 999,
          type: "session.status",
          occurred_at: "2026-09-06T02:01:00Z",
          payload: { status: "FAILED" },
        },
      ]),
    );
    await act(async () => Promise.resolve());
    expect(
      screen.queryByRole("rowheader", { name: "999" }),
    ).not.toBeInTheDocument();
  });

  it("pages one saved event window at a time and Refresh returns to the latest", async () => {
    installWebSocket();
    const event = (sequence: number) => ({
      sequence,
      type: "session.status",
      occurred_at: "2026-09-06T02:00:00Z",
      payload: { status: "STOPPED" },
    });
    const fetch = mockPaperServer().mockImplementation(async (input) => {
      const url = String(input);
      if (!url.includes("/events?"))
        return jsonResponse(paperSnapshot("STOPPED"));
      return jsonResponse(
        url.includes("before_sequence=53")
          ? [event(52), event(51)]
          : Array.from({ length: 51 }, (_, index) => event(102 - index)),
      );
    });
    render(<PaperSessionDetailPage sessionId={PAPER_ID} />);
    await act(async () => MockWebSocket.instances[0]!.open());
    await userEvent.click(
      await screen.findByRole("button", { name: "View saved events" }),
    );
    expect(
      await screen.findByRole("rowheader", { name: "102" }),
    ).toBeInTheDocument();
    expect(screen.getAllByRole("rowheader")).toHaveLength(50);
    await userEvent.click(screen.getByRole("button", { name: "Older" }));
    expect(
      await screen.findByRole("rowheader", { name: "52" }),
    ).toBeInTheDocument();
    expect(
      screen.queryByRole("rowheader", { name: "102" }),
    ).not.toBeInTheDocument();
    expect(screen.getByText(/Saved events 52–51/)).toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: "Refresh" }));
    expect(
      await screen.findByRole("rowheader", { name: "102" }),
    ).toBeInTheDocument();
    expect(fetch.mock.calls.at(-1)?.[0]).toContain(
      `/sessions/${PAPER_ID}/events?limit=51`,
    );
    expect(String(fetch.mock.calls.at(-1)?.[0])).not.toContain(
      "before_sequence",
    );
  });

  it("keeps keyboard focus on saved-event paging while requests disable buttons", async () => {
    await act(async () => i18n.changeLanguage("en-US"));
    installWebSocket();
    const event = (sequence: number) => ({
      sequence,
      type: "session.status",
      occurred_at: "2026-09-06T02:00:00Z",
      payload: { status: "STOPPED" },
    });
    let resolveOlder!: (response: Response) => void;
    let resolveRefresh!: (response: Response) => void;
    const olderPage = new Promise<Response>((resolve) => {
      resolveOlder = resolve;
    });
    const refreshPage = new Promise<Response>((resolve) => {
      resolveRefresh = resolve;
    });
    let latestRequests = 0;
    mockPaperServer().mockImplementation(async (input) => {
      const url = String(input);
      if (!url.includes("/events?"))
        return jsonResponse(paperSnapshot("STOPPED"));
      if (url.includes("before_sequence=53")) return olderPage;
      latestRequests += 1;
      return latestRequests === 1
        ? jsonResponse(
            Array.from({ length: 51 }, (_, index) => event(102 - index)),
          )
        : refreshPage;
    });

    render(<PaperSessionDetailPage sessionId={PAPER_ID} />);
    await act(async () => MockWebSocket.instances[0]!.open());
    await userEvent.click(
      await screen.findByRole("button", { name: "View saved events" }),
    );
    await screen.findByRole("rowheader", { name: "102" });
    const pager = screen.getByRole("group", { name: "Paper event log" });
    const older = within(pager).getByRole("button", { name: "Older" });
    older.focus();
    await userEvent.keyboard("{Enter}");
    expect(older).toBeDisabled();
    expect(pager).toHaveAttribute("aria-busy", "true");
    expect(pager).toHaveFocus();

    await act(async () => resolveOlder(jsonResponse([event(52), event(51)])));
    await screen.findByRole("rowheader", { name: "52" });
    const refresh = within(pager).getByRole("button", { name: "Refresh" });
    refresh.focus();
    await userEvent.keyboard("{Enter}");
    expect(refresh).toBeDisabled();
    expect(pager).toHaveFocus();

    await act(async () =>
      resolveRefresh(
        jsonResponse(
          Array.from({ length: 51 }, (_, index) => event(102 - index)),
        ),
      ),
    );
    await screen.findByRole("rowheader", { name: "102" });
    expect(pager).toHaveFocus();
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
          mockPaperServer().mockResolvedValue(jsonResponse(snapshot));
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
    const fetch = mockPaperServer().mockReturnValue(new Promise(() => {}));
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
    const fetch = mockPaperServer()
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
    mockPaperServer()
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
    const fetch = mockPaperServer().mockResolvedValue(
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
    const fetch = mockPaperServer()
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
    const fetch = mockPaperServer().mockResolvedValue(
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
    snapshot.last_sequence = 2;
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
    const fetch = mockPaperServer().mockResolvedValue(jsonResponse(snapshot));
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
    mockPaperServer().mockResolvedValue(jsonResponse(snapshot));
    render(<PaperSessionDetailPage sessionId={PAPER_ID} />);
    await act(async () => MockWebSocket.instances[0]!.close());
    expect(screen.queryByTitle("81309.8134")).not.toBeInTheDocument();
    await act(async () => vi.advanceTimersByTimeAsync(1000));
    expect(MockWebSocket.instances).toHaveLength(2);
  });

  it("renders persisted session history and the permanent safety warning", async () => {
    mockPaperServer().mockResolvedValue(
      jsonResponse({ items: [paperSession()], limit: 20, offset: 0, total: 1 }),
    );
    render(<PaperSessionsPage />);
    expect(
      await screen.findByText("Created", { selector: ".statusBadge" }),
    ).toBeInTheDocument();
    expect(screen.getByText(/SIMULATED EXECUTION ONLY/)).toBeInTheDocument();
    expect(
      screen.getByText(/not A-share data/, { selector: ".paperSessionMode" }),
    ).toHaveAttribute("aria-hidden", "true");
    expect(
      screen.getByRole("link", {
        name: /Open session: Moving average crossover/,
      }),
    ).toHaveAttribute("href", `/paper/${PAPER_ID}`);
    expect(
      screen.getByRole("region", { name: /If columns are cut off/ }),
    ).toHaveAttribute("tabindex", "0");
  });

  it("updates a running session from the server and stops polling when it stops", async () => {
    await act(async () => i18n.changeLanguage("en-US"));
    vi.useFakeTimers();
    const list = vi
      .spyOn(paperApi, "list")
      .mockResolvedValueOnce({
        items: [paperSession("RUNNING")],
        limit: 20,
        offset: 0,
        total: 1,
      })
      .mockResolvedValueOnce({
        items: [paperSession("STOPPED")],
        limit: 20,
        offset: 0,
        total: 1,
      });
    render(<PaperSessionsPage />);
    await act(async () => {});
    expect(
      screen.getByText("Running", { selector: ".statusBadge" }),
    ).toBeInTheDocument();
    const account = screen.getByRole("link", {
      name: /Open session: Moving average crossover.*Running/,
    });
    account.focus();

    await act(async () => vi.advanceTimersByTimeAsync(5000));
    expect(list).toHaveBeenCalledTimes(2);
    expect(
      screen.getByText("Stopped", { selector: ".statusBadge" }),
    ).toBeInTheDocument();
    expect(screen.getByRole("status", { name: /Stopped/ })).toBeInTheDocument();
    expect(account).toHaveAccessibleName(/Open session:.*Stopped/);
    expect(account).toHaveFocus();
    await act(async () => vi.advanceTimersByTimeAsync(10000));
    expect(list).toHaveBeenCalledTimes(2);
  });

  it("refreshes an idle session without polling it", async () => {
    await act(async () => i18n.changeLanguage("en-US"));
    vi.useFakeTimers();
    const list = vi
      .spyOn(paperApi, "list")
      .mockResolvedValueOnce({
        items: [paperSession("CREATED")],
        limit: 20,
        offset: 0,
        total: 1,
      })
      .mockResolvedValueOnce({
        items: [paperSession("PAUSED")],
        limit: 20,
        offset: 0,
        total: 1,
      });
    render(<PaperSessionsPage />);
    await act(async () => {});
    await act(async () => vi.advanceTimersByTimeAsync(10000));
    expect(list).toHaveBeenCalledTimes(1);
    fireEvent.click(screen.getByRole("button", { name: "Refresh" }));
    await act(async () => {});
    expect(list).toHaveBeenCalledTimes(2);
    expect(screen.getByRole("status", { name: /Paused/ })).toBeInTheDocument();
  });

  it("moves focus to the error when polling invalidates a focused session", async () => {
    await act(async () => i18n.changeLanguage("en-US"));
    vi.useFakeTimers();
    vi.spyOn(paperApi, "list")
      .mockResolvedValueOnce({
        items: [paperSession("RUNNING")],
        limit: 20,
        offset: 0,
        total: 1,
      })
      .mockRejectedValueOnce(new Error("Connection failed"));
    render(<PaperSessionsPage />);
    await act(async () => {});
    screen.getByRole("link", { name: /Open session:.*Running/ }).focus();
    await act(async () => vi.advanceTimersByTimeAsync(5000));
    expect(screen.getByRole("alert")).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: "Persisted sessions" }),
    ).toHaveFocus();
  });

  it("moves focus to the list heading when a polled row disappears", async () => {
    await act(async () => i18n.changeLanguage("en-US"));
    vi.useFakeTimers();
    vi.spyOn(paperApi, "list")
      .mockResolvedValueOnce({
        items: [paperSession("RUNNING")],
        limit: 20,
        offset: 0,
        total: 1,
      })
      .mockResolvedValueOnce({ items: [], limit: 20, offset: 0, total: 0 });
    render(<PaperSessionsPage />);
    await act(async () => {});
    screen.getByRole("link", { name: /Open session:.*Running/ }).focus();
    await act(async () => vi.advanceTimersByTimeAsync(5000));
    expect(screen.getByText(/No paper sessions yet/)).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: "Persisted sessions" }),
    ).toHaveFocus();
  });

  it("distinguishes same-strategy sessions without making IDs the primary action", async () => {
    const secondId = "534d9730-a8c9-4f71-a0fc-c4b5d156f2ef";
    mockPaperServer().mockResolvedValue(
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
    const statuses = screen.getAllByRole("status", { name: /Created/ });
    expect(statuses).toHaveLength(2);
    expect(statuses[0]).not.toHaveAttribute(
      "aria-label",
      statuses[1]?.getAttribute("aria-label"),
    );
    expect(screen.queryByText(/34d97303/)).not.toBeInTheDocument();
    await act(async () => i18n.changeLanguage("zh-CN"));
    expect(
      screen.getAllByRole("link", { name: /查看会话: 移动平均线交叉/ }),
    ).toHaveLength(2);
    await act(async () => i18n.changeLanguage("en-US"));
  });

  it.each(
    ["en-US", "zh-CN"].flatMap((locale) =>
      [
        "HISTORICAL_DATASET_QUALITY_UNKNOWN",
        "KNOWN_ECONOMIC_COVERAGE_GAP",
      ].flatMap((quality) =>
        [true, false].map((hasPlan) => ({ locale, quality, hasPlan })),
      ),
    ),
  )(
    "shows current quality before portfolio amounts and inside the plan ($locale / $quality / saved plan $hasPlan)",
    async ({ locale, quality, hasPlan }) => {
      await act(async () => i18n.changeLanguage(locale));
      installWebSocket();
      const saved = {
        ...paperSnapshot("STOPPED"),
        current_dataset_quality: quality,
        latest_portfolio: {
          timestamp: "2011-03-23T07:00:00Z",
          cash: "81309.813400000000000001",
          market_value: "18655",
          equity: "99964.813400000000000001",
          realized_pnl: "0",
          unrealized_pnl: "-5",
          cumulative_commission: "30.1866",
          drawdown: "0.000351866",
          plan: null,
          positions: [],
        },
        last_rebalance_plan: hasPlan
          ? {
              ...plan,
              mode: "historical_exploration",
              account_mode: "HISTORICAL_PAPER_REPLAY",
              submitted_to_account: true,
              paper_session_id: PAPER_ID,
              plan_version: "PAPER_ACCOUNT_PLAN_V3",
            }
          : null,
        session: {
          ...paperSession("STOPPED"),
          provider_type: "historical_a_share",
          strategy_type: "cn_a_cross_sectional_momentum_low_vol_v1",
        },
      };
      const before = JSON.stringify(saved);
      mockPaperServer().mockResolvedValue(jsonResponse(saved));
      render(<PaperSessionDetailPage sessionId={PAPER_ID} />);
      await act(async () => MockWebSocket.instances[0]!.open());
      const portfolio = (
        await screen.findByRole("heading", {
          name: locale === "en-US" ? "Paper portfolio" : "模拟交易组合",
        })
      ).closest("section")!;
      const notice = within(portfolio).getByRole("note");
      const planRegion = screen.getByRole("region", {
        name:
          locale === "en-US"
            ? "This account's historical rebalance plan"
            : "此模拟账户的历史调仓计划",
      });
      expect(within(planRegion).getByRole("note")).toHaveTextContent(
        notice.textContent!,
      );
      expect(notice).toHaveTextContent(
        quality === "KNOWN_ECONOMIC_COVERAGE_GAP"
          ? locale === "en-US"
            ? "Economic completeness is not validated"
            : "经济完整性尚未验证"
          : locale === "en-US"
            ? "Economic completeness is unknown"
            : "经济完整性未知",
      );
      const metrics = portfolio.querySelector(".metricsGrid")!;
      expect(
        notice.compareDocumentPosition(metrics) &
          Node.DOCUMENT_POSITION_FOLLOWING,
      ).not.toBe(0);
      expect(
        Array.from(metrics.querySelectorAll("strong"), (item) => item.title),
      ).toEqual([
        "81309.813400000000000001",
        "18655",
        "99964.813400000000000001",
        "0",
        "-5",
        "30.1866",
      ]);
      if (hasPlan)
        expect(screen.getByText("90,123.000000000000000001")).toBeVisible();
      else
        expect(planRegion).toHaveTextContent(
          locale === "en-US"
            ? "This older account has no saved account-native plan"
            : "该较早账户未保存账户专属计划",
        );
      expect(JSON.stringify(saved)).toBe(before);
      expect(
        paperRequests.every(
          ({ options }) => !options?.method || options.method === "GET",
        ),
      ).toBe(true);
      await act(async () => i18n.changeLanguage("en-US"));
    },
  );

  it.each([
    ["historical_a_share", null],
    ["historical_a_share", undefined],
    ["simulated_a_share", "KNOWN_ECONOMIC_COVERAGE_GAP"],
    ["replay", "HISTORICAL_DATASET_QUALITY_UNKNOWN"],
  ])(
    "does not invent historical portfolio quality advice (%s / %s)",
    async (provider, quality) => {
      installWebSocket();
      mockPaperServer().mockResolvedValue(
        jsonResponse({
          ...paperSnapshot("STOPPED"),
          session: { ...paperSession("STOPPED"), provider_type: provider },
          current_dataset_quality: quality,
        }),
      );
      render(<PaperSessionDetailPage sessionId={PAPER_ID} />);
      await act(async () => MockWebSocket.instances[0]!.open());
      const portfolio = (
        await screen.findByRole("heading", { name: "Paper portfolio" })
      ).closest("section")!;
      expect(within(portfolio).queryByRole("note")).not.toBeInTheDocument();
      expect(
        paperRequests.every(
          ({ options }) => !options?.method || options.method === "GET",
        ),
      ).toBe(true);
    },
  );

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
    mockPaperServer().mockResolvedValue(
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
        mockPaperServer().mockResolvedValue(jsonResponse(snapshot));
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
    mockPaperServer().mockResolvedValue(jsonResponse(snapshot));
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
    mockPaperServer().mockResolvedValue(
      jsonResponse({ detail: "forbidden" }, 403),
    );
    render(<PaperSessionsPage />);
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Access was denied",
    );
    expect(screen.getByRole("link", { name: "Reload page" })).toBeVisible();
  });

  it("keeps legacy AAPL replay explicit and creates it with one idempotency key", async () => {
    const fetch = mockPaperServer().mockResolvedValue(
      jsonResponse(paperSession(), 201),
    );
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
    const fetch = mockPaperServer().mockResolvedValue(
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
    const fetch = mockPaperServer()
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
    const fetch = mockPaperServer()
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
    const fetch = mockPaperServer().mockRejectedValue(
      new TypeError("response lost"),
    );
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
    const fetch = mockPaperServer().mockImplementation(() =>
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
    const fetch = mockPaperServer()
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
      const fetch = mockPaperServer().mockResolvedValueOnce(
        jsonResponse(paperSession(), 201),
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
    const fetch = mockPaperServer()
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
    const fetch = mockPaperServer()
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
    const fetch = mockPaperServer()
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
    const fetch = mockPaperServer().mockImplementation(
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
    const fetch = mockPaperServer().mockResolvedValue(
      jsonResponse(paperSession(), 201),
    );
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
    const fetch = mockPaperServer();
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
    const fetch = mockPaperServer();
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
    const fetch = mockPaperServer();
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
    const fetch = mockPaperServer()
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
    const fetch = mockPaperServer()
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
    const fetch = mockPaperServer()
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
    const fetch = mockPaperServer()
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
      const fetch = mockPaperServer()
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
    const fetch = mockPaperServer();
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
    const fetch = mockPaperServer().mockResolvedValue(
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
    const fetch = mockPaperServer().mockImplementation(
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
      const fetch = mockPaperServer().mockRejectedValue(
        new ApiError(status, "diagnostic"),
      );
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
    const fetch = mockPaperServer().mockResolvedValue(
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
    const fetch = mockPaperServer();
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
    const fetch = mockPaperServer();
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
    const fetch = mockPaperServer().mockResolvedValue(
      jsonResponse(paperSession(), 201),
    );
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
    const fetch = mockPaperServer().mockResolvedValue(
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
    mockPaperServer().mockResolvedValue(
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
    const fetch = mockPaperServer()
      .mockResolvedValueOnce(jsonResponse(paperSnapshot("RUNNING")))
      .mockResolvedValueOnce(jsonResponse(paperSession("PAUSING")))
      .mockResolvedValueOnce(
        jsonResponse({ ...paperSnapshot("PAUSING"), last_sequence: 1 }),
      );
    const view = render(<PaperSessionDetailPage sessionId={PAPER_ID} />);
    await act(async () => MockWebSocket.instances[0]!.open());
    await userEvent.click(screen.getByRole("button", { name: "Pause replay" }));
    expect(fetch.mock.calls[1]?.[0]).toContain(`/${PAPER_ID}/pause`);
    expect(fetch.mock.calls[2]?.[0]).toContain(`/${PAPER_ID}/state`);
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

  it("can stop an unstarted account without starting its provider", async () => {
    installWebSocket();
    const fetch = mockPaperServer()
      .mockResolvedValueOnce(jsonResponse(paperSnapshot("CREATED")))
      .mockResolvedValueOnce(jsonResponse(paperSession("STOPPED")))
      .mockResolvedValueOnce(jsonResponse(paperSnapshot("STOPPED")));
    render(<PaperSessionDetailPage sessionId={PAPER_ID} />);
    await act(async () => MockWebSocket.instances[0]!.open());

    screen.getByRole("button", { name: "Stop replay" }).focus();
    await userEvent.keyboard("{Enter}");
    expect(fetch.mock.calls[1]?.[0]).toContain(`/${PAPER_ID}/stop`);
    expect(fetch.mock.calls[1]?.[1]?.method).toBe("POST");
    expect(
      fetch.mock.calls.some(([url]) => String(url).endsWith("/start")),
    ).toBe(false);
    expect(
      screen.getByText("Stopped", { selector: ".statusBadge" }),
    ).toBeVisible();
    expect(screen.queryByRole("button", { name: "Start replay" })).toBeNull();
  });

  it("reconciles an accepted command while the paper stream is reconnecting", async () => {
    installWebSocket();
    const fetch = mockPaperServer()
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
    expect(fetch.mock.calls[2]?.[0]).toContain(`/${PAPER_ID}/state`);
    expect(
      screen.getByText("Pausing", { selector: ".statusBadge" }),
    ).toBeVisible();
    expect(screen.queryByRole("button", { name: "Pause replay" })).toBeNull();
    expect(screen.getByRole("button", { name: "Stop replay" })).toBeVisible();
    expect(screen.getByText("Session connection: reconnecting")).toBeVisible();
  });

  it("keeps an accepted transition when a disconnect aborts its snapshot read", async () => {
    installWebSocket();
    const fetch = mockPaperServer()
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
    const fetch = mockPaperServer()
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
    const fetch = mockPaperServer()
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
    mockPaperServer()
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
    const fetch = mockPaperServer()
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
        const fetch = mockPaperServer()
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
      const fetch = mockPaperServer()
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
    mockPaperServer()
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
    mockPaperServer().mockResolvedValueOnce(
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
      const fetch = mockPaperServer()
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
    mockPaperServer().mockResolvedValue(
      jsonResponse({
        ...paperSnapshot("STOPPED"),
        last_sequence: 6,
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

  it.each([
    "Positions",
    "Signals",
    "Risk decisions",
    "Paper orders",
    "Paper fills",
  ])(
    "bounds %s with exact ordered rows and independent page focus",
    async (title) => {
      installWebSocket();
      const { snapshot, records } = financialTableFixture();
      const fetch = mockPaperServer().mockImplementation(async () =>
        jsonResponse(snapshot),
      );
      render(<PaperSessionDetailPage sessionId={PAPER_ID} />);
      await act(async () => MockWebSocket.instances[0]!.open());
      for (const other of [
        "Positions",
        "Signals",
        "Risk decisions",
        "Paper orders",
        "Paper fills",
      ])
        await waitFor(() => expect(tableCells(other)).toHaveLength(100));
      const pager = screen.getByRole("group", {
        name: `${title} — Pagination`,
      });
      const seen: string[][] = [];
      for (const count of [100, 100, 1]) {
        const rows = tableCells(title);
        expect(rows).toHaveLength(count);
        seen.push(...rows);
        if (count === 100) {
          const first = rows[0];
          await userEvent.click(
            within(pager).getByRole("button", { name: "Next" }),
          );
          await waitFor(() => expect(tableCells(title)[0]).not.toEqual(first));
          expect(pager).toHaveFocus();
        }
      }
      expect(seen).toHaveLength(201);
      if (["Positions", "Paper orders", "Paper fills"].includes(title))
        expect(seen.map((row) => row[title === "Positions" ? 1 : 2])).toEqual(
          records.map((record) => record.quantity),
        );
      expect(
        within(pager).getByRole("button", { name: "Next" }),
      ).toBeDisabled();
      for (const other of [
        "Positions",
        "Signals",
        "Risk decisions",
        "Paper orders",
        "Paper fills",
      ])
        if (other !== title) expect(tableCells(other)).toHaveLength(100);
      expect(
        fetch.mock.calls.every(([input]) => String(input).endsWith("/state")),
      ).toBe(true);
      expect(
        paperRequests.every(
          ({ url, options }) =>
            (url.endsWith("/state") || url.includes("/collections/")) &&
            options?.method === undefined,
        ),
      ).toBe(true);
      expect(
        paperRequests.some(({ url }) => url.includes("/collections/")),
      ).toBe(true);
    },
  );

  it("retains the last fill page and exact appended value through locale changes", async () => {
    installWebSocket();
    const { snapshot } = financialTableFixture();
    snapshot.signals = [];
    snapshot.risk_decisions = [];
    snapshot.orders = [];
    snapshot.latest_portfolio!.positions =
      snapshot.latest_portfolio!.positions.slice(0, 1);
    snapshot.last_sequence = 202;
    mockPaperServer().mockImplementation(async () => jsonResponse(snapshot));
    render(<PaperSessionDetailPage sessionId={PAPER_ID} />);
    await act(async () => MockWebSocket.instances[0]!.open());
    await waitFor(() => expect(tableCells("Paper fills")).toHaveLength(100));
    const pager = screen.getByRole("group", {
      name: "Paper fills — Pagination",
    });
    for (const count of [100, 1]) {
      const first = tableCells("Paper fills")[0];
      await userEvent.click(
        within(pager).getByRole("button", { name: "Next" }),
      );
      await waitFor(() =>
        expect(tableCells("Paper fills")[0]).not.toEqual(first),
      );
      expect(tableCells("Paper fills")).toHaveLength(count);
      expect(pager).toHaveFocus();
    }
    const extraFill = {
      ...snapshot.fills[0]!,
      order_id: "00000000-0000-0000-0000-000000000999",
      quantity: "202.000000000000000001",
    };
    snapshot.fills.push(extraFill);
    snapshot.last_sequence = 203;
    await act(async () =>
      MockWebSocket.instances[0]!.message({
        sequence: 203,
        type: "fill.created",
        occurred_at: "2026-09-06T02:03:00Z",
        payload: extraFill,
      }),
    );
    await waitFor(() => expect(tableCells("Paper fills")).toHaveLength(2));
    expect(pager).toHaveFocus();
    try {
      await act(async () => i18n.changeLanguage("zh-CN"));
      await act(async () => MockWebSocket.instances.at(-1)!.open());
      await waitFor(() => expect(tableCells("模拟成交")).toHaveLength(2));
      expect(
        screen.getByRole("group", {
          name: `模拟成交 — ${i18n.t("common:pagination")}`,
        }),
      ).toHaveFocus();
      expect(screen.getByText("202.000000000000000001")).toHaveAttribute(
        "title",
        "202.000000000000000001",
      );
    } finally {
      await act(async () => i18n.changeLanguage("en-US"));
      await act(async () => MockWebSocket.instances.at(-1)!.open());
    }
    expect(tableCells("Paper fills")).toHaveLength(2);
    expect(
      paperRequests
        .filter(({ url }) => url.includes("/collections/fills"))
        .every(
          ({ url }) =>
            new URL(url, "http://test.local").searchParams.get("offset") !==
            "300",
        ),
    ).toBe(true);
  });

  it("persists the position-page clamp through shrink, empty and regrow without losing focus", async () => {
    installWebSocket();
    const { snapshot } = financialTableFixture();
    snapshot.signals = [];
    snapshot.risk_decisions = [];
    snapshot.orders = [];
    snapshot.fills = [];
    snapshot.last_sequence = 0;
    mockPaperServer().mockImplementation(async () => jsonResponse(snapshot));
    render(<PaperSessionDetailPage sessionId={PAPER_ID} />);
    await act(async () => MockWebSocket.instances[0]!.open());
    await screen.findByRole("table", { name: "Positions" });
    const pager = screen.getByRole("group", { name: "Positions — Pagination" });
    for (const count of [100, 1]) {
      const first = tableCells("Positions")[0];
      await userEvent.click(
        within(pager).getByRole("button", { name: "Next" }),
      );
      await waitFor(() =>
        expect(tableCells("Positions")[0]).not.toEqual(first),
      );
      expect(tableCells("Positions")).toHaveLength(count);
    }
    const fullPositions = snapshot.latest_portfolio!.positions;
    pager.focus();
    for (const [index, positions] of [
      fullPositions.slice(0, 1),
      [],
      fullPositions,
    ].entries()) {
      snapshot.latest_portfolio!.positions = positions;
      snapshot.last_sequence = index + 1;
      await act(async () =>
        MockWebSocket.instances.at(-1)!.message({
          sequence: index + 1,
          type: "portfolio.snapshot",
          occurred_at: "2026-09-06T02:03:00Z",
          payload: snapshot.latest_portfolio,
        }),
      );
      expect(pager).toHaveFocus();
      if (positions.length)
        expect(tableCells("Positions")).toHaveLength(
          Math.min(100, positions.length),
        );
      else
        expect(
          screen.queryByRole("table", { name: "Positions" }),
        ).not.toBeInTheDocument();
      expect(
        within(pager).getByRole("button", { name: "Previous" }),
      ).toBeDisabled();
    }
  });

  it("resets financial collection offsets when switching saved accounts", async () => {
    installWebSocket();
    const { snapshot } = financialTableFixture();
    snapshot.signals = [];
    snapshot.risk_decisions = [];
    snapshot.orders = [];
    snapshot.last_sequence = 202;
    snapshot.latest_portfolio!.positions = [];
    const otherId = "00000000-0000-0000-0000-000000000999";
    mockPaperServer().mockImplementation(async (input) =>
      jsonResponse({
        ...snapshot,
        session: {
          ...snapshot.session,
          session_id: String(input).includes(otherId) ? otherId : PAPER_ID,
        },
      }),
    );
    const view = render(<PaperSessionDetailPage sessionId={PAPER_ID} />);
    await act(async () => MockWebSocket.instances[0]!.open());
    await waitFor(() => expect(tableCells("Paper fills")).toHaveLength(100));
    const pager = screen.getByRole("group", {
      name: "Paper fills — Pagination",
    });
    for (const count of [100, 1]) {
      const first = tableCells("Paper fills")[0];
      await userEvent.click(
        within(pager).getByRole("button", { name: "Next" }),
      );
      await waitFor(() =>
        expect(tableCells("Paper fills")[0]).not.toEqual(first),
      );
      expect(tableCells("Paper fills")).toHaveLength(count);
    }
    view.rerender(<PaperSessionDetailPage sessionId={otherId} />);
    await act(async () => MockWebSocket.instances.at(-1)!.open());
    await waitFor(() => expect(tableCells("Paper fills")).toHaveLength(100));
    expect(
      within(
        screen.getByRole("group", { name: "Paper fills — Pagination" }),
      ).getByRole("button", { name: "Previous" }),
    ).toBeDisabled();
    expect(
      paperRequests
        .filter(({ url }) => url.includes(`/sessions/${otherId}/collections/`))
        .every(
          ({ url }) =>
            new URL(url, "http://test.local").searchParams.get("offset") ===
            "0",
        ),
    ).toBe(true);
  });

  it.each(["watermark", "account"] as const)(
    "discards a delayed financial page after the %s changes",
    async (change) => {
      installWebSocket();
      const { snapshot } = financialTableFixture();
      snapshot.signals = [];
      snapshot.risk_decisions = [];
      snapshot.orders = [];
      snapshot.latest_portfolio!.positions = [];
      snapshot.last_sequence = 202;
      const otherId = "00000000-0000-0000-0000-000000000999";
      let resolveOld!: (response: Response) => void;
      let oldSignal: AbortSignal | null | undefined;
      let oldResponse: Response | undefined;
      mockPaperServer(async (url, window, options) => {
        const collection = url.pathname.split("/").at(-1) as PaperCollection;
        const watermark = Number(url.searchParams.get("as_of_sequence"));
        const offset = Number(url.searchParams.get("offset") ?? 0);
        const response = jsonResponse(
          paperCollection(window, collection, watermark, offset),
        );
        if (collection === "fills" && watermark === 202 && offset === 200) {
          oldSignal = options?.signal;
          oldResponse = response;
          return new Promise<Response>((resolve) => {
            resolveOld = resolve;
          });
        }
        return response;
      }).mockImplementation(async (input) =>
        jsonResponse(
          String(input).includes(otherId)
            ? {
                ...snapshot,
                session: { ...snapshot.session, session_id: otherId },
                last_sequence: 2,
                fills: [
                  { ...snapshot.fills[0]!, quantity: "888.000000000000000001" },
                ],
              }
            : snapshot,
        ),
      );
      const view = render(<PaperSessionDetailPage sessionId={PAPER_ID} />);
      await act(async () => MockWebSocket.instances[0]!.open());
      await waitFor(() => expect(tableCells("Paper fills")).toHaveLength(100));
      const pager = screen.getByRole("group", {
        name: "Paper fills — Pagination",
      });
      const first = tableCells("Paper fills")[0];
      await userEvent.click(
        within(pager).getByRole("button", { name: "Next" }),
      );
      await waitFor(() =>
        expect(tableCells("Paper fills")[0]).not.toEqual(first),
      );
      await userEvent.click(
        within(pager).getByRole("button", { name: "Next" }),
      );
      await waitFor(() => expect(oldResponse).toBeDefined());
      if (change === "watermark") {
        const extraFill = {
          ...snapshot.fills[0]!,
          quantity: "202.000000000000000001",
        };
        snapshot.fills.push(extraFill);
        snapshot.last_sequence = 203;
        await act(async () =>
          MockWebSocket.instances[0]!.message({
            sequence: 203,
            type: "fill.created",
            occurred_at: "2026-09-06T02:03:00Z",
            payload: extraFill,
          }),
        );
        await waitFor(() => expect(tableCells("Paper fills")).toHaveLength(2));
        expect(screen.getByTitle("202.000000000000000001")).toBeVisible();
      } else {
        view.rerender(<PaperSessionDetailPage sessionId={otherId} />);
        await act(async () => MockWebSocket.instances.at(-1)!.open());
        expect(
          await screen.findByTitle("888.000000000000000001"),
        ).toBeVisible();
        expect(tableCells("Paper fills")).toHaveLength(1);
      }
      expect(oldSignal?.aborted).toBe(true);
      await act(async () => resolveOld(oldResponse!));
      expect(tableCells("Paper fills")).toHaveLength(
        change === "watermark" ? 2 : 1,
      );
      expect(screen.queryByTitle("201.000000000000000001")).toBe(
        change === "watermark"
          ? screen.getByTitle("201.000000000000000001")
          : null,
      );
      if (change === "watermark")
        expect(screen.getByTitle("202.000000000000000001")).toBeVisible();
      else expect(screen.getByTitle("888.000000000000000001")).toBeVisible();
    },
  );

  it("validates paper strategy parameters before submitting", async () => {
    const fetch = mockPaperServer();
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
    const fetch = mockPaperServer();
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

  it.each([503, 403])(
    "retries a failed collection page without losing focus or treating HTTP %s as empty",
    async (status) => {
      installWebSocket();
      vi.useFakeTimers();
      const snapshot = paperSnapshot("RUNNING");
      snapshot.last_sequence = 2;
      const fill = {
        order_id: PAPER_ID,
        strategy_id: "moving_average_crossover",
        symbol: "AAPL",
        side: "BUY",
        quantity: "1.000000000000000001",
        price: "12",
        commission: "0.000000000000000001",
        timestamp: "2024-01-09T00:00:00Z",
      };
      snapshot.fills = [fill];
      let failed = false;
      mockPaperServer(async (url, window) => {
        const collection = url.pathname.split("/").at(-1) as PaperCollection;
        return collection === "fills" && failed
          ? jsonResponse({ detail: "collection unavailable" }, status)
          : jsonResponse(
              paperCollection(
                window,
                collection,
                Number(url.searchParams.get("as_of_sequence")),
                Number(url.searchParams.get("offset")),
              ),
            );
      }).mockImplementation(async () => jsonResponse(snapshot));
      render(<PaperSessionDetailPage sessionId={PAPER_ID} />);
      await act(async () => MockWebSocket.instances[0]!.open());
      expect(tableCells("Paper fills")).toHaveLength(1);
      const panel = screen
        .getByRole("heading", { name: "Paper fills" })
        .closest("section")!;
      const pager = within(panel).getByRole("group");
      failed = true;
      snapshot.last_sequence = 3;
      const nextFill = { ...fill, quantity: "2.000000000000000001" };
      snapshot.fills.push(nextFill);
      act(() =>
        MockWebSocket.instances[0]!.message({
          sequence: 3,
          type: "fill.created",
          occurred_at: fill.timestamp,
          payload: nextFill,
        }),
      );
      await act(async () => vi.advanceTimersByTimeAsync(100));
      expect(within(panel).getByRole("alert")).toHaveTextContent(
        "collection unavailable",
      );
      expect(
        within(panel).queryByText(i18n.t("paper:detail.noFills")),
      ).not.toBeInTheDocument();
      if (status === 503) {
        expect(tableCells("Paper fills")).toHaveLength(1);
        expect(within(panel).getByRole("status")).toHaveTextContent(
          "last verified page",
        );
      } else {
        expect(within(panel).queryByRole("table")).not.toBeInTheDocument();
        expect(
          within(panel).queryByTitle(fill.quantity),
        ).not.toBeInTheDocument();
      }
      failed = false;
      await act(async () =>
        fireEvent.click(
          within(panel).getByRole("button", { name: "Retry Paper fills" }),
        ),
      );
      expect(pager).toHaveFocus();
      expect(tableCells("Paper fills")).toHaveLength(2);
      expect(within(panel).queryByRole("alert")).not.toBeInTheDocument();
      expect(
        within(panel).queryByText(/last verified page/),
      ).not.toBeInTheDocument();
      expect(
        paperRequests.every(
          ({ url, options }) =>
            !url.includes("/snapshot") && options?.method === undefined,
        ),
      ).toBe(true);
    },
  );

  it("coalesces bounded financial-page refreshes, ignores old events and rehydrates a resync", async () => {
    installWebSocket();
    vi.useFakeTimers();
    const snapshot = paperSnapshot("RUNNING");
    snapshot.last_sequence = 1;
    const fill = {
      order_id: PAPER_ID,
      strategy_id: "moving_average_crossover",
      symbol: "AAPL",
      side: "BUY",
      quantity: "1.000000000000000001",
      price: "12.123456789123456789",
      commission: "0.000000000000000001",
      timestamp: "2024-01-09T00:00:00Z",
    };
    let resolveHeld!: (response: Response) => void;
    const fetch = mockPaperServer()
      .mockResolvedValueOnce(jsonResponse(snapshot))
      .mockImplementationOnce(
        () => new Promise((resolve) => (resolveHeld = resolve)),
      )
      .mockImplementation(async () => jsonResponse(snapshot));
    render(<PaperSessionDetailPage sessionId={PAPER_ID} />);
    await act(async () => MockWebSocket.instances[0]!.open());
    const append = (sequence: number) => {
      snapshot.fills.push(fill);
      snapshot.last_sequence = sequence;
      MockWebSocket.instances[0]!.message({
        sequence,
        type: "fill.created",
        occurred_at: fill.timestamp,
        payload: fill,
      });
    };
    act(() => {
      for (let sequence = 2; sequence <= 101; sequence++) append(sequence);
    });
    expect(fetch).toHaveBeenCalledOnce();
    const fillPanel = screen
      .getByRole("heading", { name: "Paper fills" })
      .closest("section")!;
    expect(within(fillPanel).getByRole("status")).toHaveTextContent(
      "last verified page",
    );
    expect(
      screen.queryByRole("table", { name: "Paper fills" }),
    ).not.toBeInTheDocument();
    await act(async () => vi.advanceTimersByTimeAsync(99));
    expect(fetch).toHaveBeenCalledOnce();
    await act(async () => vi.advanceTimersByTimeAsync(1));
    expect(fetch).toHaveBeenCalledTimes(2);
    const captured = jsonResponse(snapshot);
    act(() => {
      append(102);
      append(103);
    });
    await act(async () => vi.advanceTimersByTimeAsync(100));
    expect(fetch).toHaveBeenCalledTimes(2);
    await act(async () => resolveHeld(captured));
    expect(tableCells("Paper fills")).toHaveLength(100);
    expect(within(fillPanel).getByRole("status")).toHaveTextContent(
      "last verified page",
    );
    await act(async () => vi.advanceTimersByTimeAsync(100));
    expect(fetch).toHaveBeenCalledTimes(3);
    expect(
      within(fillPanel).queryByText(/last verified page/),
    ).not.toBeInTheDocument();
    const pager = screen.getByRole("group", {
      name: "Paper fills — Pagination",
    });
    expect(pager).toHaveTextContent(
      i18n.t("common:pageOf", { start: 1, end: 100, total: 102 }),
    );
    await act(async () =>
      fireEvent.click(within(pager).getByRole("button", { name: "Next" })),
    );
    expect(tableCells("Paper fills")).toHaveLength(2);
    expect(pager).toHaveFocus();
    act(() => {
      for (const sequence of [103, 102])
        MockWebSocket.instances[0]!.message({
          sequence,
          type: "fill.created",
          occurred_at: fill.timestamp,
          payload: fill,
        });
    });
    await act(async () => vi.advanceTimersByTimeAsync(500));
    expect(fetch).toHaveBeenCalledTimes(3);
    expect(tableCells("Paper fills")).toHaveLength(2);
    act(() =>
      MockWebSocket.instances[0]!.message({
        sequence: null,
        type: "stream.resync_required",
        occurred_at: null,
        payload: {},
      }),
    );
    expect(MockWebSocket.instances[0]!.readyState).toBe(MockWebSocket.CLOSED);
    await act(async () => vi.advanceTimersByTimeAsync(1000));
    expect(MockWebSocket.instances).toHaveLength(2);
    await act(async () => MockWebSocket.instances[1]!.open());
    expect(fetch).toHaveBeenCalledTimes(4);
    expect(tableCells("Paper fills")).toHaveLength(2);
    expect(pager).toHaveFocus();
    expect(
      paperRequests.every(
        ({ url, options }) =>
          !url.includes("/snapshot") && options?.method === undefined,
      ),
    ).toBe(true);
    expect(
      paperRequests
        .filter(({ url }) => url.includes("/collections/"))
        .every(
          ({ url }) =>
            new URL(url, "http://test.local").searchParams.get("limit") ===
            "100",
        ),
    ).toBe(true);
  });

  it("fails closed on another account's streamed plan without crashing the detail page", async () => {
    installWebSocket();
    const snapshot = paperSnapshot("RUNNING");
    snapshot.session.provider_type = "historical_a_share";
    snapshot.last_sequence = 1;
    mockPaperServer().mockResolvedValue(jsonResponse(snapshot));
    render(<PaperSessionDetailPage sessionId={PAPER_ID} />);
    await act(async () => MockWebSocket.instances[0]!.open());
    act(() =>
      MockWebSocket.instances[0]!.message({
        sequence: 2,
        type: "portfolio.snapshot",
        occurred_at: "2011-03-22T07:00:00Z",
        payload: {
          timestamp: "2011-03-22T07:00:00Z",
          cash: "100000",
          market_value: "0",
          equity: "100000",
          realized_pnl: "0",
          unrealized_pnl: "0",
          cumulative_commission: "0",
          drawdown: "0",
          positions: [],
          plan: {
            ...plan,
            mode: "historical_exploration",
            account_mode: "HISTORICAL_PAPER_REPLAY",
            submitted_to_account: true,
            paper_session_id: "a0975744-c58a-49d8-a72d-45f6ed700ca6",
            plan_version: "PAPER_ACCOUNT_PLAN_V3",
          },
        },
      }),
    );
    expect(screen.getByRole("alert")).toHaveTextContent("malformed");
    expect(screen.queryByText("Paper portfolio")).not.toBeInTheDocument();
    expect(screen.queryByText("100000")).not.toBeInTheDocument();
    expect(MockWebSocket.instances[0]!.readyState).toBe(MockWebSocket.CLOSED);
  });

  it("fails closed when a late REST state would roll back an accepted stream status and portfolio", async () => {
    installWebSocket();
    vi.useFakeTimers();
    const initial = paperSnapshot("RUNNING");
    initial.last_sequence = 5;
    initial.latest_portfolio = {
      timestamp: "2024-01-09T00:00:00Z",
      cash: "1000.000000000000000001",
      market_value: "0",
      equity: "1000.000000000000000001",
      realized_pnl: "0",
      unrealized_pnl: "0",
      cumulative_commission: "0",
      drawdown: "0",
      positions: [],
      plan: null,
    };
    let resolveOld!: (response: Response) => void;
    const fetch = mockPaperServer()
      .mockResolvedValueOnce(jsonResponse(initial))
      .mockImplementationOnce(
        () => new Promise((resolve) => (resolveOld = resolve)),
      )
      .mockImplementation(async () => jsonResponse(initial));
    render(<PaperSessionDetailPage sessionId={PAPER_ID} />);
    await act(async () => MockWebSocket.instances[0]!.open());
    act(() => {
      MockWebSocket.instances[0]!.message({
        sequence: 6,
        type: "portfolio.snapshot",
        occurred_at: initial.latest_portfolio!.timestamp,
        payload: {
          ...initial.latest_portfolio,
          cash: "1100.000000000000000001",
          equity: "1100.000000000000000001",
        },
      });
      MockWebSocket.instances[0]!.message({
        sequence: 7,
        type: "session.status",
        occurred_at: "2024-01-09T00:00:01Z",
        payload: { status: "PAUSED" },
      });
    });
    expect(screen.getAllByTitle("1100.000000000000000001")).toHaveLength(2);
    expect(
      screen.getByText("Paused", { selector: ".statusBadge" }),
    ).toBeInTheDocument();
    expect(fetch).toHaveBeenCalledTimes(2);
    await act(async () => resolveOld(jsonResponse(initial)));
    expect(screen.getByRole("alert")).toHaveTextContent(
      "watermark moved backwards",
    );
    expect(
      screen.queryByTitle("1000.000000000000000001"),
    ).not.toBeInTheDocument();
    expect(
      screen.queryByTitle("1100.000000000000000001"),
    ).not.toBeInTheDocument();
    expect(screen.queryByText("Paper portfolio")).not.toBeInTheDocument();
    await act(async () => vi.advanceTimersByTimeAsync(1000));
    await act(async () => MockWebSocket.instances[1]!.open());
    expect(fetch).toHaveBeenCalledTimes(3);
    expect(screen.getByRole("alert")).toHaveTextContent(
      "watermark moved backwards",
    );
    expect(screen.queryByText("Paper portfolio")).not.toBeInTheDocument();
    expect(paperRequests.every(({ url }) => !url.includes("/snapshot"))).toBe(
      true,
    );
  });

  it("hydrates from REST, ingests typed events once, and reconnects with rehydration", async () => {
    installWebSocket();
    vi.useFakeTimers();
    const snapshot = paperSnapshot("RUNNING");
    const fetch = mockPaperServer().mockImplementation(async () =>
      jsonResponse(snapshot),
    );
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

    snapshot.last_sequence = portfolioEvent.sequence;
    snapshot.latest_portfolio = { ...portfolioEvent.payload, plan: null };
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

  it("announces only new stream fills once per sequence and clears them on locale changes", async () => {
    installWebSocket();
    const fill = {
      order_id: PAPER_ID,
      strategy_id: "moving_average_crossover",
      symbol: "AAPL",
      side: "BUY",
      quantity: "10",
      price: "12",
      commission: "0.5",
      timestamp: "2026-09-06T02:01:00Z",
    };
    let resolveInitial!: (response: Response) => void;
    mockPaperServer()
      .mockImplementationOnce(
        () => new Promise((resolve) => (resolveInitial = resolve)),
      )
      .mockImplementation(() =>
        Promise.resolve(
          jsonResponse({
            ...paperSnapshot("RUNNING"),
            last_sequence: 6,
            fills: [fill, fill, fill, fill, fill],
          }),
        ),
      );
    const view = render(<PaperSessionDetailPage sessionId={PAPER_ID} />);
    const status = document.getElementById("paper-fill-announcement")!;
    expect(status).toHaveAttribute("role", "status");
    expect(status).toHaveAttribute("aria-atomic", "true");
    expect(status).toBeEmptyDOMElement();
    try {
      await act(async () => MockWebSocket.instances[0]!.open());
      act(() =>
        MockWebSocket.instances[0]!.message({
          sequence: 2,
          type: "fill.created",
          occurred_at: fill.timestamp,
          payload: fill,
        }),
      );
      await act(async () =>
        resolveInitial(
          jsonResponse({
            ...paperSnapshot("RUNNING"),
            last_sequence: 2,
            fills: [fill],
          }),
        ),
      );
      expect(document.getElementById("paper-fill-announcement")).toBe(status);
      expect(status).toBeEmptyDOMElement();

      const live = {
        sequence: 3,
        type: "fill.created",
        occurred_at: fill.timestamp,
        payload: fill,
      };
      act(() => MockWebSocket.instances[0]!.message(live));
      expect(status).toHaveTextContent(
        "New simulated fill: Buy 10 AAPL at 12.",
      );
      const firstMessage = status.firstElementChild;
      act(() => MockWebSocket.instances[0]!.message(live));
      expect(status.firstElementChild).toBe(firstMessage);
      act(() => MockWebSocket.instances[0]!.message({ ...live, sequence: 4 }));
      const secondMessage = status.firstElementChild;
      expect(secondMessage).not.toBe(firstMessage);
      expect(status).toHaveTextContent(
        "New simulated fill: Buy 10 AAPL at 12.",
      );

      await act(async () => i18n.changeLanguage("zh-CN"));
      expect(document.getElementById("paper-fill-announcement")).toBe(status);
      expect(status).toBeEmptyDOMElement();
      await act(async () => i18n.changeLanguage("en-US"));
      expect(status).toBeEmptyDOMElement();
      await act(async () => i18n.changeLanguage("zh-CN"));
      expect(status).toBeEmptyDOMElement();
      await act(async () => MockWebSocket.instances.at(-1)!.open());
      expect(status).toBeEmptyDOMElement();
      act(() =>
        MockWebSocket.instances.at(-1)!.message({ ...live, sequence: 7 }),
      );
      expect(status).toHaveTextContent(
        "新增模拟成交：买入 10 股 AAPL，成交价 12。",
      );
      expect(status.firstElementChild).toHaveAttribute("lang", "zh-CN");
      await act(async () => i18n.changeLanguage("en-US"));
      expect(status).toBeEmptyDOMElement();
      await act(async () => i18n.changeLanguage("zh-CN"));
      expect(status).toBeEmptyDOMElement();
    } finally {
      view.unmount();
      await act(async () => i18n.changeLanguage("en-US"));
    }
  });

  it("does not replay an old fill announcement after A→B→A while B hydration is pending", async () => {
    installWebSocket();
    const otherId = "534d9730-a8c9-4f71-a0fc-c4b5d156f2ef";
    const fill = {
      order_id: PAPER_ID,
      strategy_id: "moving_average_crossover",
      symbol: "AAPL",
      side: "BUY",
      quantity: "10",
      price: "12",
      commission: "0.5",
      timestamp: "2026-09-06T02:01:00Z",
    };
    const fetch = mockPaperServer()
      .mockResolvedValueOnce(jsonResponse(paperSnapshot("RUNNING")))
      .mockReturnValueOnce(new Promise<Response>(() => {}))
      .mockResolvedValueOnce(
        jsonResponse({
          ...paperSnapshot("RUNNING"),
          last_sequence: 2,
          fills: [fill],
        }),
      );
    const view = render(<PaperSessionDetailPage sessionId={PAPER_ID} />);
    await act(async () => MockWebSocket.instances[0]!.open());
    act(() =>
      MockWebSocket.instances[0]!.message({
        sequence: 1,
        type: "fill.created",
        occurred_at: fill.timestamp,
        payload: fill,
      }),
    );
    const status = document.getElementById("paper-fill-announcement")!;
    expect(status).toHaveTextContent("New simulated fill: Buy 10 AAPL at 12.");

    view.rerender(<PaperSessionDetailPage sessionId={otherId} />);
    expect(status).toBeEmptyDOMElement();
    await act(async () => MockWebSocket.instances[1]!.open());
    expect(fetch).toHaveBeenCalledTimes(2);

    const observer = new MutationObserver(() => {});
    observer.observe(status, { childList: true, subtree: true });
    view.rerender(<PaperSessionDetailPage sessionId={PAPER_ID} />);
    const inserted = observer
      .takeRecords()
      .flatMap((record) => Array.from(record.addedNodes));
    observer.disconnect();
    expect(
      inserted.some((node) => node.textContent?.includes("New simulated fill")),
    ).toBe(false);
    expect(document.getElementById("paper-fill-announcement")).toBe(status);
    expect(status).toBeEmptyDOMElement();
    expect(fetch.mock.calls[1]?.[1]?.signal?.aborted).toBe(true);

    await act(async () => MockWebSocket.instances[2]!.open());
    expect(fetch).toHaveBeenCalledTimes(3);
    expect(status).toBeEmptyDOMElement();
  });

  it("closes terminal session streams without reconnecting", async () => {
    installWebSocket();
    vi.useFakeTimers();
    mockPaperServer()
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
    const fetch = mockPaperServer()
      .mockResolvedValueOnce(jsonResponse(paperSnapshot("RUNNING")))
      .mockResolvedValueOnce(jsonResponse({ detail: "temporary" }, 503))
      .mockResolvedValueOnce(
        jsonResponse({ ...paperSnapshot("STOPPED"), last_sequence: 1 }),
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
    const fetch = mockPaperServer()
      .mockResolvedValueOnce(jsonResponse(paperSnapshot("RUNNING")))
      .mockReturnValueOnce(new Promise(() => {}))
      .mockResolvedValueOnce(
        jsonResponse({ ...paperSnapshot("STOPPED"), last_sequence: 1 }),
      );
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
    mockPaperServer()
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

  it.each(["en-US", "zh-CN"])(
    "explains unsupported distribution inputs on a reopened paper account (%s)",
    async (locale) => {
      installWebSocket();
      mockPaperServer().mockResolvedValue(
        jsonResponse({
          ...paperSnapshot("FAILED"),
          session: {
            ...paperSession("FAILED"),
            error_message: "UNSUPPORTED_ORDINARY_DISTRIBUTION_INPUT",
          },
        }),
      );
      await act(async () => i18n.changeLanguage(locale));
      render(<PaperSessionDetailPage sessionId={PAPER_ID} />);
      await act(async () => MockWebSocket.instances[0]!.open());
      const alert = await screen.findByRole("alert");
      expect(alert).toHaveTextContent(
        locale === "en-US"
          ? "unchanged retries will not repair the source gap"
          : "沿用相同数据重试不能修复来源缺口",
      );
      expect(
        screen.queryByRole("button", { name: /Start replay|开始回放/ }),
      ).not.toBeInTheDocument();
    },
  );

  it("explains a backend interruption in Chinese and keeps the raw diagnostic for audit", async () => {
    installWebSocket();
    mockPaperServer().mockResolvedValue(
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
      ).toHaveAttribute("href", `/paper/new?from_session=${PAPER_ID}`);
      expect(
        screen.getByText("Paper runtime interrupted by backend shutdown."),
      ).not.toBeVisible();
    } finally {
      await act(async () => i18n.changeLanguage("en-US"));
    }
  });

  it("offers a configuration-preserving retry for an interrupted session without a stored diagnostic", async () => {
    installWebSocket();
    mockPaperServer().mockResolvedValue(
      jsonResponse(paperSnapshot("INTERRUPTED")),
    );
    render(<PaperSessionDetailPage sessionId={PAPER_ID} />);
    await act(async () => MockWebSocket.instances[0]!.open());
    expect(
      await screen.findByRole("link", { name: "Create another paper session" }),
    ).toHaveAttribute("href", `/paper/new?from_session=${PAPER_ID}`);
    expect(
      screen.queryByText("Original diagnostic (audit)"),
    ).not.toBeInTheDocument();
  });

  it("copies an interrupted historical account into a new independent form without changing its ledger", async () => {
    window.history.replaceState({}, "", `/paper/new?from_session=${PAPER_ID}`);
    const source = {
      ...paperSession("INTERRUPTED"),
      provider_type: "historical_a_share" as const,
      dataset_id: "cn-a-research-20100101-20251231-v1",
      symbol: "CN-A",
      strategy_type: "cn_a_cross_sectional_momentum_low_vol_v1" as const,
      strategy_parameters: {
        start_date: "2011-03-01",
        end_date: "2011-03-23",
        rebalance_sessions: 23,
        maximum_holdings: 12,
        max_position_weight: "0.08",
        universe: "SZSE",
        commission_rate: "0.0007",
        minimum_commission: "7",
        dataset_sha256: "a".repeat(64),
        plan_version: "PAPER_ACCOUNT_PLAN_V3",
      },
      initial_cash: "123456.789000000000001",
      default_order_quantity: "1",
      risk: {
        enforce_buying_power: true,
        max_leverage: "1",
        max_drawdown: "-0.35",
        allow_limit_orders: false,
        max_order_notional: null,
      },
    };
    vi.spyOn(paperApi, "get").mockResolvedValue(source);
    const create = vi.spyOn(paperApi, "create").mockResolvedValue({
      ...source,
      session_id: "c9c01cd0-425e-4cf0-9ae4-ad76501025a6",
      status: "CREATED",
    });
    try {
      render(<CreatePaperSessionPage />);
      expect(
        await screen.findByText(/Settings copied from paper session/),
      ).toBeVisible();
      expect(screen.getByLabelText("Provider")).toHaveValue(
        "historical_a_share",
      );
      expect(screen.getByLabelText("Provider")).toBeDisabled();
      expect(screen.getByLabelText("Initial cash")).toHaveValue(
        "123456.789000000000001",
      );
      expect(screen.getByLabelText("Start date")).toHaveValue("2011-03-01");
      expect(screen.getByLabelText("End date")).toHaveValue("2011-03-23");
      await userEvent.click(
        screen.getByText("Strategy, universe and cost settings"),
      );
      expect(screen.getByLabelText("Share universe")).toHaveValue("SZSE");
      expect(
        screen.getByLabelText("Drawdown risk limit (negative fraction)"),
      ).toHaveValue("-0.35");
      expect(create).not.toHaveBeenCalled();
      await userEvent.click(
        screen.getByRole("button", { name: "Create paper session" }),
      );
      await waitFor(() => expect(create).toHaveBeenCalledOnce());
      expect(create.mock.calls[0]?.[0]).toMatchObject({
        provider_type: "historical_a_share",
        initial_cash: "123456.789000000000001",
        strategy: {
          parameters: {
            start_date: "2011-03-01",
            end_date: "2011-03-23",
            rebalance_sessions: 23,
            maximum_holdings: 12,
            universe: "SZSE",
            commission_rate: "0.0007",
            minimum_commission: "7",
          },
        },
        risk: { max_drawdown: "-0.35" },
      });
      expect(create.mock.calls[0]?.[0].strategy.parameters).not.toHaveProperty(
        "dataset_sha256",
      );
      expect(create.mock.calls[0]?.[0].strategy.parameters).not.toHaveProperty(
        "plan_version",
      );
      expect(paperApi.get).toHaveBeenCalledWith(PAPER_ID, expect.anything());
    } finally {
      window.history.replaceState({}, "", "/paper/new");
    }
  });

  it("copies replay settings without creating an account until explicit submission", async () => {
    window.history.replaceState({}, "", `/paper/new?from_session=${PAPER_ID}`);
    const source = {
      ...paperSession("FAILED"),
      strategy_parameters: { short_period: 7, long_period: 30 },
      initial_cash: "76543.21",
      default_order_quantity: "3.5",
    };
    vi.spyOn(paperApi, "get").mockResolvedValue(source);
    const create = vi.spyOn(paperApi, "create");
    try {
      render(<CreatePaperSessionPage />);
      expect(
        await screen.findByText(/Settings copied from paper session/),
      ).toBeVisible();
      expect(screen.getByLabelText("Provider")).toHaveValue("replay");
      expect(screen.getByLabelText("Initial cash")).toHaveValue("76543.21");
      expect(screen.getByLabelText("Order quantity")).toHaveValue("3.5");
      expect(screen.getByLabelText("Short period")).toHaveValue(7);
      expect(screen.getByLabelText("Long period")).toHaveValue(30);
      expect(create).not.toHaveBeenCalled();
    } finally {
      window.history.replaceState({}, "", "/paper/new");
    }
  });

  it("uses a fresh idempotency key when copying after a confirmed paper account", async () => {
    window.history.replaceState({}, "", `/paper/new?from_session=${PAPER_ID}`);
    const source = paperSession("FAILED");
    const prior = preparePaperCreate({
      provider_type: "replay",
      dataset_id: "AAPL_fixture",
      symbol: "AAPL",
      strategy: {
        type: "moving_average_crossover",
        parameters: { short_period: 2, long_period: 3 },
      },
      initial_cash: source.initial_cash,
      default_order_quantity: source.default_order_quantity,
      risk: { enforce_buying_power: true },
    });
    confirmPaperCreate(prior, PAPER_ID);
    vi.spyOn(paperApi, "get").mockResolvedValue(source);
    const receipt = vi.spyOn(paperApi, "receipt").mockResolvedValue(source);
    const create = vi.spyOn(paperApi, "create").mockResolvedValue({
      ...source,
      session_id: "c9c01cd0-425e-4cf0-9ae4-ad76501025a6",
      status: "CREATED",
    });
    try {
      render(<CreatePaperSessionPage />);
      await screen.findByText(/Settings copied from paper session/);
      await userEvent.click(
        screen.getByRole("button", { name: "Create paper session" }),
      );
      await waitFor(() => expect(create).toHaveBeenCalledOnce());
      expect(receipt).toHaveBeenCalledWith(prior.key);
      expect(create.mock.calls[0]?.[1]).not.toBe(prior.key);
    } finally {
      window.history.replaceState({}, "", "/paper/new");
    }
  });

  it("does not reuse an unresolved paper request when copying a terminal account", async () => {
    window.history.replaceState({}, "", `/paper/new?from_session=${PAPER_ID}`);
    const source = paperSession("INTERRUPTED");
    preparePaperCreate({
      provider_type: "replay",
      dataset_id: "AAPL_fixture",
      symbol: "AAPL",
      strategy: {
        type: "moving_average_crossover",
        parameters: { short_period: 2, long_period: 3 },
      },
      initial_cash: source.initial_cash,
      default_order_quantity: source.default_order_quantity,
      risk: { enforce_buying_power: true },
    });
    vi.spyOn(paperApi, "get").mockResolvedValue(source);
    const create = vi.spyOn(paperApi, "create");
    try {
      render(<CreatePaperSessionPage />);
      await screen.findByText(/Settings copied from paper session/);
      await userEvent.click(
        screen.getByRole("button", { name: "Create paper session" }),
      );
      expect(await screen.findByRole("alert")).toHaveTextContent(
        "A saved creation already exists",
      );
      expect(create).not.toHaveBeenCalled();
    } finally {
      window.history.replaceState({}, "", "/paper/new");
    }
  });

  it("refuses paper source settings the form cannot preserve", async () => {
    window.history.replaceState({}, "", `/paper/new?from_session=${PAPER_ID}`);
    vi.spyOn(paperApi, "get").mockResolvedValue({
      ...paperSession("INTERRUPTED"),
      risk: { enforce_buying_power: true, max_order_notional: "100" },
    });
    const create = vi.spyOn(paperApi, "create");
    try {
      render(<CreatePaperSessionPage />);
      expect(await screen.findByRole("alert")).toHaveTextContent(
        "cannot safely configure a new account",
      );
      expect(screen.queryByLabelText("Provider")).not.toBeInTheDocument();
      expect(create).not.toHaveBeenCalled();
    } finally {
      window.history.replaceState({}, "", "/paper/new");
    }
  });

  it("rejects ambiguous or mismatched paper sources without using a default account", async () => {
    window.history.replaceState(
      {},
      "",
      `/paper/new?from_session=${PAPER_ID}&from_experiment=${job.job_id}`,
    );
    const get = vi.spyOn(paperApi, "get");
    try {
      const page = render(<CreatePaperSessionPage />);
      expect(await screen.findByRole("alert")).toHaveTextContent(
        "cannot safely configure a new account",
      );
      expect(get).not.toHaveBeenCalled();
      page.unmount();
      window.history.replaceState(
        {},
        "",
        `/paper/new?from_session=${PAPER_ID}`,
      );
      get.mockResolvedValue({
        ...paperSession("INTERRUPTED"),
        session_id: "f86a98c6-16ad-44c5-822e-f20404173142",
      });
      const mismatchedPage = render(<CreatePaperSessionPage />);
      expect(await screen.findByRole("alert")).toHaveTextContent(
        "cannot safely configure a new account",
      );
      expect(screen.queryByLabelText("Provider")).not.toBeInTheDocument();
      mismatchedPage.unmount();
      window.history.replaceState(
        {},
        "",
        `/paper/new?from_session=${PAPER_ID.toUpperCase()}`,
      );
      get.mockResolvedValue(paperSession("INTERRUPTED"));
      render(<CreatePaperSessionPage />);
      expect(
        await screen.findByText(/Settings copied from paper session/),
      ).toBeVisible();
      expect(get).toHaveBeenCalledWith(PAPER_ID, expect.anything());
    } finally {
      window.history.replaceState({}, "", "/paper/new");
    }
  });

  it("rejects unknown stream events and rehydrates instead of advancing state", async () => {
    installWebSocket();
    vi.useFakeTimers();
    const fetch = mockPaperServer().mockImplementation(async () =>
      jsonResponse(paperSnapshot("RUNNING")),
    );
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
    const fetch = mockPaperServer().mockReturnValue(new Promise(() => {}));
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
    mockPaperServer()
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
