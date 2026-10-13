import { act, render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import { i18n } from "../i18n";
import { jsonResponse } from "../test/fixtures";
import {
  forwardCommit,
  forwardInput,
  forwardSnapshot,
} from "../test/forwardPaperFixtures";
import {
  PAPER_ID,
  paperCapabilities,
  paperCollection,
  paperState,
} from "../test/paperFixtures";
import type { PaperCollection } from "../types/paper";
import { CreatePaperSessionPage } from "./CreatePaperSessionPage";
import { PaperSessionDetailPage } from "./PaperSessionDetailPage";

class MockWebSocket {
  static readonly OPEN = 1;
  static readonly CLOSED = 3;
  static instances: MockWebSocket[] = [];
  readyState = 0;
  onopen: (() => void) | null = null;
  onmessage: ((event: MessageEvent) => void) | null = null;
  onclose: (() => void) | null = null;
  constructor() {
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

function server(snapshot = forwardSnapshot()) {
  MockWebSocket.instances = [];
  vi.stubGlobal("WebSocket", MockWebSocket as unknown as typeof WebSocket);
  return vi.spyOn(globalThis, "fetch").mockImplementation(async (input) => {
    const url = new URL(String(input), "http://test.local");
    if (url.pathname.endsWith("/capabilities"))
      return jsonResponse(paperCapabilities());
    if (url.pathname.endsWith("/events"))
      return jsonResponse([forwardCommit()]);
    if (url.pathname.endsWith("/state"))
      return jsonResponse(paperState(snapshot));
    if (url.pathname.endsWith(`/sessions/${PAPER_ID}`))
      return jsonResponse(snapshot.session);
    expect(url.pathname).toContain(`/sessions/${PAPER_ID}/collections/`);
    return jsonResponse(
      paperCollection(
        snapshot,
        url.pathname.split("/").at(-1) as PaperCollection,
        Number(url.searchParams.get("as_of_sequence")),
        Number(url.searchParams.get("offset") ?? 0),
      ),
    );
  });
}

afterEach(async () => {
  window.history.replaceState({}, "", "/paper");
  await i18n.changeLanguage("en-US");
});

describe("receipt-bound forward paper display", () => {
  it.each(["en-US", "zh-CN"])(
    "shows truthful labels and control-only commits (%s)",
    async (language) => {
      await act(async () => i18n.changeLanguage(language));
      const fetch = server();
      const view = render(<PaperSessionDetailPage sessionId={PAPER_ID} />);
      try {
        await act(async () => MockWebSocket.instances[0]!.open());
        expect(
          await screen.findByText(
            i18n.t("providers.forward_a_share", { ns: "paper" }),
          ),
        ).toBeVisible();
        expect(
          screen.getByText(i18n.t("detail.forwardBoundary", { ns: "paper" })),
        ).toBeVisible();
        expect(
          screen.getByRole("heading", {
            name:
              language === "zh-CN"
                ? "此模拟账户的回执绑定前向计划"
                : "This account's receipt-bound forward plan",
          }),
        ).toBeVisible();
        expect(
          screen.queryByText(
            i18n.t("providers.historical_a_share", { ns: "paper" }),
          ),
        ).not.toBeInTheDocument();
        expect(
          screen.getByRole("button", {
            name: i18n.t("detail.forwardPause", { ns: "paper" }),
          }),
        ).toBeVisible();
        await userEvent.click(
          screen.getByText(
            `${i18n.t("detail.marketInput", { ns: "paper" })} · ${forwardInput().trading_date}`,
          ),
        );
        expect(
          screen
            .getAllByText(forwardInput().input_sha256)
            .some((element) => element.closest("details")?.open),
        ).toBe(true);
        act(() => MockWebSocket.instances[0]!.message(forwardCommit()));
        expect(
          document.getElementById("paper-fill-announcement"),
        ).toBeEmptyDOMElement();
        expect(screen.queryByRole("alert")).not.toBeInTheDocument();
        await userEvent.click(
          screen.getByRole("button", {
            name: i18n.t("detail.viewEventLog", { ns: "paper" }),
          }),
        );
        const table = await screen.findByRole("table", {
          name: i18n.t("detail.eventLog", { ns: "paper" }),
        });
        expect(
          within(table).getByText(
            i18n.t("detail.eventTypes.input.committed", { ns: "paper" }),
          ),
        ).toBeVisible();
        expect(table).toHaveTextContent(
          i18n.t("detail.inputCommitSummary", {
            ns: "paper",
            date: forwardInput().trading_date,
            first: 2,
            last: 10,
          }),
        );
        expect(table).not.toHaveTextContent("undefined");
        expect(
          fetch.mock.calls.every(([, options]) => options?.method !== "POST"),
        ).toBe(true);
      } finally {
        view.unmount();
      }
    },
  );

  it("fails closed on a cross-account forward stream without retaining financial display", async () => {
    server();
    const view = render(<PaperSessionDetailPage sessionId={PAPER_ID} />);
    try {
      await act(async () => MockWebSocket.instances[0]!.open());
      expect(
        await screen.findByText("Receipt-bound A-share forward simulation"),
      ).toBeVisible();
      act(() =>
        MockWebSocket.instances[0]!.message({
          sequence: 1,
          type: "market.session",
          occurred_at: forwardInput().closed_at,
          payload: {
            ...forwardSnapshot().latest_session,
            input_provenance: {
              ...forwardInput(),
              paper_session_id: "bb000000-0000-4000-8000-000000000001",
            },
          },
        }),
      );
      expect(await screen.findByRole("alert")).toHaveTextContent(
        "malformed paper stream event",
      );
      expect(
        screen.queryByText("Receipt-bound A-share forward simulation"),
      ).not.toBeInTheDocument();
      expect(MockWebSocket.instances[0]!.readyState).toBe(MockWebSocket.CLOSED);
    } finally {
      view.unmount();
    }
  });

  it("keeps prior-day portfolio warning for forward inputs", async () => {
    const snapshot = forwardSnapshot();
    snapshot.latest_session = {
      ...snapshot.latest_session,
      trading_date: "2026-10-13",
      input_provenance: {
        ...forwardInput(),
        trading_date: "2026-10-13",
        closed_at: "2026-10-13T07:00:00Z",
        next_open_at: "2026-10-14T01:30:00Z",
        receipts: [
          {
            ...forwardInput().receipts[0]!,
            first_received_at: "2026-10-13T07:01:00Z",
          },
        ],
      },
    };
    server(snapshot);
    const view = render(<PaperSessionDetailPage sessionId={PAPER_ID} />);
    try {
      await act(async () => MockWebSocket.instances[0]!.open());
      expect(await screen.findByRole("alert")).toHaveTextContent("2026-10-12");
      expect(screen.getByRole("alert")).toHaveTextContent("2026-10-13");
      expect(
        screen.getByRole("heading", {
          name: "This account's receipt-bound forward plan",
        }),
      ).toBeVisible();
    } finally {
      view.unmount();
    }
  });

  it("rejects conflicting same-day stream inputs within the connection error boundary", async () => {
    server();
    const view = render(<PaperSessionDetailPage sessionId={PAPER_ID} />);
    try {
      await act(async () => MockWebSocket.instances[0]!.open());
      expect(
        await screen.findByText("Receipt-bound A-share forward simulation"),
      ).toBeVisible();
      act(() =>
        MockWebSocket.instances[0]!.message({
          sequence: 1,
          type: "market.session",
          occurred_at: forwardInput().closed_at,
          payload: {
            ...forwardSnapshot().latest_session,
            input_provenance: {
              ...forwardInput(),
              input_sha256: "0".repeat(64),
            },
          },
        }),
      );
      expect(await screen.findByRole("alert")).toHaveTextContent(
        "malformed paper stream event",
      );
      expect(
        screen.queryByText("Receipt-bound A-share forward simulation"),
      ).not.toBeInTheDocument();
    } finally {
      view.unmount();
    }
  });

  it("bounds displayed receipts while retaining the complete recorded count", async () => {
    const snapshot = forwardSnapshot();
    const receipts = Array.from({ length: 11 }, (_, index) => ({
      ...forwardInput().receipts[0]!,
      security_id: `CN-A:SZSE:${String(index + 1).padStart(6, "0")}`,
      receipt_id: `aa000000-0000-4000-8000-${String(index + 1).padStart(12, "0")}`,
    }));
    snapshot.latest_session.security_count = receipts.length;
    snapshot.latest_session.input_provenance.receipts = receipts;
    snapshot.latest_portfolio.input_provenance.receipts = receipts;
    snapshot.latest_portfolio.plan.input_provenance.receipts = receipts;
    snapshot.last_rebalance_plan.input_provenance.receipts = receipts;
    server(snapshot);
    const view = render(<PaperSessionDetailPage sessionId={PAPER_ID} />);
    try {
      await act(async () => MockWebSocket.instances[0]!.open());
      expect(
        await screen.findAllByText(
          "Showing 10 of 11 recorded receipts. Complete lineage remains in the saved API record.",
        ),
      ).toHaveLength(2);
      expect(screen.getAllByText(receipts[9]!.receipt_id)).toHaveLength(2);
      expect(
        screen.queryByText(receipts[10]!.receipt_id),
      ).not.toBeInTheDocument();
    } finally {
      view.unmount();
    }
  });

  it("does not offer a replay copy of an ended forward account", async () => {
    const snapshot = forwardSnapshot();
    snapshot.session.status = "FAILED";
    server(snapshot);
    const view = render(<PaperSessionDetailPage sessionId={PAPER_ID} />);
    try {
      await act(async () => MockWebSocket.instances[0]!.open());
      expect(
        await screen.findByText(/Forward accounts cannot be copied/),
      ).toBeVisible();
      expect(
        screen.queryByRole("link", { name: "Create another paper session" }),
      ).not.toBeInTheDocument();
    } finally {
      view.unmount();
    }
  });

  it("rejects an explicit forward copy deep link instead of choosing a replay default", async () => {
    const snapshot = forwardSnapshot();
    snapshot.session.status = "STOPPED";
    const fetch = server(snapshot);
    window.history.replaceState({}, "", `/paper/new?from_session=${PAPER_ID}`);
    const view = await act(async () => render(<CreatePaperSessionPage />));
    try {
      expect(await screen.findByRole("alert")).toHaveTextContent(
        "cannot safely configure a new account",
      );
      expect(screen.queryByLabelText("Provider")).not.toBeInTheDocument();
      expect(
        fetch.mock.calls.every(([, options]) => options?.method !== "POST"),
      ).toBe(true);
    } finally {
      view.unmount();
    }
  });
});
