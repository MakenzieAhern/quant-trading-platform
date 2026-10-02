import { act, render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { i18n } from "../i18n";
import { jsonResponse } from "../test/fixtures";
import {
  PAPER_ID,
  paperCalendarEvent,
  paperSnapshot,
} from "../test/paperFixtures";
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

describe("paper calendar control events", () => {
  it.each(["en-US", "zh-CN"])(
    "shows saved calendar summaries without new market data or fill announcements (%s)",
    async (language) => {
      await act(async () => i18n.changeLanguage(language));
      MockWebSocket.instances = [];
      vi.stubGlobal("WebSocket", MockWebSocket as unknown as typeof WebSocket);
      const events = [paperCalendarEvent("extension", 2), paperCalendarEvent()];
      const snapshot = paperSnapshot("RUNNING");
      snapshot.session.provider_type = "historical_a_share";
      snapshot.session.dataset_id = "cn-a-research-20100101-20251231-v1";
      snapshot.session.strategy_type =
        "cn_a_cross_sectional_momentum_low_vol_v1";
      snapshot.session.symbol = "CN-A";
      const fetch = vi
        .spyOn(globalThis, "fetch")
        .mockImplementation(async (url) =>
          jsonResponse(String(url).includes("/events?") ? events : snapshot),
        );
      const view = render(<PaperSessionDetailPage sessionId={PAPER_ID} />);
      try {
        await act(async () => MockWebSocket.instances[0]!.open());
        const heading = i18n.t("detail.eventLog", { ns: "paper" });
        expect(
          await screen.findByRole("heading", { name: heading }),
        ).toBeInTheDocument();
        expect(
          fetch.mock.calls.some(([url]) => String(url).includes("/events?")),
        ).toBe(false);
        act(() => {
          MockWebSocket.instances[0]!.message(events[1]);
          MockWebSocket.instances[0]!.message(events[0]);
          MockWebSocket.instances[0]!.message(events[0]);
        });
        expect(
          document.getElementById("paper-fill-announcement"),
        ).toBeEmptyDOMElement();
        expect(screen.queryByRole("alert")).not.toBeInTheDocument();
        expect(MockWebSocket.instances[0]!.readyState).toBe(MockWebSocket.OPEN);
        await userEvent.click(
          screen.getByRole("button", {
            name: i18n.t("detail.viewEventLog", { ns: "paper" }),
          }),
        );
        const table = await screen.findByRole("table", { name: heading });
        expect(within(table).getAllByRole("row")).toHaveLength(3);
        expect(
          within(table).getAllByText(
            language === "zh-CN" ? "日历控制记录" : "Calendar control",
          ),
        ).toHaveLength(2);
        expect(
          within(table).getByText(
            language === "zh-CN"
              ? "日历初始化：共 2 个日期，已完成 0 个交易日。仅日历控制记录，不代表新行情或成交。"
              : "Calendar initialized. Dates recorded: 2. Completed sessions: 0. Calendar control only; no new market data or fills.",
          ),
        ).toBeInTheDocument();
        expect(
          within(table).getByText(
            language === "zh-CN"
              ? "日历扩展至 3 个日期，已完成 1 个交易日。仅日历控制记录，不代表新行情或成交。"
              : "Calendar extended. Dates recorded: 3. Completed sessions: 1. Calendar control only; no new market data or fills.",
          ),
        ).toBeInTheDocument();
        expect(table).not.toHaveTextContent(/undefined|Equity|权益/);
        expect(
          document.getElementById("paper-fill-announcement"),
        ).toBeEmptyDOMElement();
        expect(
          fetch.mock.calls.some(([url]) =>
            String(url).includes(`/sessions/${PAPER_ID}/events?limit=51`),
          ),
        ).toBe(true);
        expect(
          fetch.mock.calls.every(([, options]) => options?.method !== "POST"),
        ).toBe(true);
      } finally {
        view.unmount();
        await act(async () => i18n.changeLanguage("en-US"));
      }
    },
  );
});
