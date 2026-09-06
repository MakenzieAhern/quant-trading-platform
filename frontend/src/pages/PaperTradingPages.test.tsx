import {
  act,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

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

  it("renders persisted session history and the permanent safety warning", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      jsonResponse({ items: [paperSession()], limit: 20, offset: 0, total: 1 }),
    );
    render(<PaperSessionsPage />);
    expect(await screen.findByText("CREATED")).toBeInTheDocument();
    expect(screen.getByText(/SIMULATED EXECUTION ONLY/)).toBeInTheDocument();
    expect(screen.getByTitle(PAPER_ID)).toBeInTheDocument();
  });

  it("creates only a registered replay session with one idempotency key", async () => {
    const fetch = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValue(jsonResponse(paperSession(), 201));
    render(<CreatePaperSessionPage />);
    expect(screen.getByLabelText("Provider")).toBeDisabled();
    expect(screen.getByLabelText("Dataset")).toBeDisabled();
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

  it("validates paper strategy parameters before submitting", async () => {
    const fetch = vi.spyOn(globalThis, "fetch");
    render(<CreatePaperSessionPage />);
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
      .mockResolvedValue(jsonResponse(paperSnapshot("RUNNING")));
    render(<PaperSessionDetailPage sessionId={PAPER_ID} />);
    expect(MockWebSocket.instances).toHaveLength(1);
    await act(async () => MockWebSocket.instances[0]!.open());
    expect(screen.getByText("RUNNING")).toBeInTheDocument();
    expect(screen.getByText("WebSocket: connected")).toBeInTheDocument();

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
    act(() => MockWebSocket.instances[0]!.message(portfolioEvent));
    expect(screen.getAllByText("Paper portfolio")).toHaveLength(1);

    act(() => MockWebSocket.instances[0]!.close());
    expect(screen.getByText("WebSocket: reconnecting")).toBeInTheDocument();
    await act(async () => vi.advanceTimersByTimeAsync(1000));
    expect(MockWebSocket.instances).toHaveLength(2);
    await act(async () => MockWebSocket.instances[1]!.open());
    expect(fetch).toHaveBeenCalledTimes(2);
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
    expect(screen.getByText("STOPPED")).toBeInTheDocument();
    expect(screen.getByText("WebSocket: closed")).toBeInTheDocument();
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
    expect(await screen.findByText("FAILED")).toBeInTheDocument();
    expect(screen.getByRole("alert")).toHaveTextContent(
      "Paper execution failed safely.",
    );
    expect(screen.getByText("WebSocket: closed")).toBeInTheDocument();
  });

  it("rejects unknown stream events and rehydrates instead of advancing state", async () => {
    installWebSocket();
    vi.useFakeTimers();
    const fetch = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValue(jsonResponse(paperSnapshot("RUNNING")));
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
    expect(screen.queryByText("must-not-render")).not.toBeInTheDocument();
    expect(screen.getByText("WebSocket: reconnecting")).toBeInTheDocument();
    await act(async () => vi.advanceTimersByTimeAsync(1000));
    await act(async () => MockWebSocket.instances[1]!.open());
    expect(fetch).toHaveBeenCalledTimes(2);
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
    expect(await screen.findByText("STOPPED")).toBeInTheDocument();
    resolveOld(jsonResponse(paperSnapshot("RUNNING")));
    await Promise.resolve();
    expect(screen.queryByText("RUNNING")).not.toBeInTheDocument();
  });
});
